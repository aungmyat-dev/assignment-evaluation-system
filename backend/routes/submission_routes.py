from datetime import datetime
from pathlib import Path
from uuid import uuid4
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload
from ..auth import CurrentUser, require_role
from ..config import settings
from ..database import get_db
from ..models import Assignment, EvaluationResult, PlagiarismMatch, Submission, User
from ..services.evaluation_engine import compare_submissions, evaluate_submission
from ..services.nlp_processor import extract_text

router = APIRouter(prefix="/api/submissions", tags=["Submissions"])
ALLOWED_EXTENSIONS = {".pdf", ".txt"}


class ApprovalRequest(BaseModel):
    final_score: float | None = None
    teacher_comment: str | None = None


def serialize_submission(item: Submission) -> dict:
    result = item.evaluation
    return {"id": item.id, "assignment_id": item.assignment_id, "assignment_title": item.assignment.title if item.assignment else None, "student_id": item.student_id, "student_name": item.student.full_name if item.student else None, "original_filename": item.original_filename, "status": item.status, "submitted_at": item.submitted_at, "evaluated_at": item.evaluated_at, "evaluation": ({"predicted_score": float(result.predicted_score), "final_score": float(result.final_score) if result.final_score is not None else None, "keyword_coverage": float(result.keyword_coverage), "reference_similarity": float(result.reference_similarity), "vocabulary_richness": float(result.vocabulary_richness), "word_count_score": float(result.word_count_score), "plagiarism_risk": float(result.plagiarism_risk), "feedback": result.feedback or [], "teacher_comment": result.teacher_comment} if result else None)}


@router.get("")
def list_submissions(user: CurrentUser, db: Session = Depends(get_db)):
    query = select(Submission).options(joinedload(Submission.assignment), joinedload(Submission.student), joinedload(Submission.evaluation)).order_by(Submission.submitted_at.desc())
    if user.role == "student":
        query = query.where(Submission.student_id == user.id)
    else:
        query = query.join(Assignment).where(Assignment.teacher_id == user.id)
    return [serialize_submission(item) for item in db.scalars(query).unique().all()]


@router.post("/upload", status_code=status.HTTP_201_CREATED)
async def upload_submission(assignment_id: int = Form(...), file: UploadFile = File(...), student: User = Depends(require_role("student")), db: Session = Depends(get_db)):
    assignment = db.get(Assignment, assignment_id)
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if db.scalar(select(Submission).where(Submission.assignment_id == assignment_id, Submission.student_id == student.id)):
        raise HTTPException(status_code=409, detail="You have already submitted this assignment")
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only PDF and TXT files are supported")
    content = await file.read()
    if len(content) > settings.max_upload_size_mb * 1024 * 1024:
        raise HTTPException(status_code=413, detail="The uploaded file is too large")
    stored_name = f"{uuid4().hex}{suffix}"
    stored_path = settings.upload_path / stored_name
    stored_path.write_bytes(content)
    try:
        extracted = extract_text(stored_path)
    except Exception as exc:
        stored_path.unlink(missing_ok=True)
        raise HTTPException(status_code=422, detail=f"Could not extract text from the file: {exc}")
    if not extracted.strip():
        raise HTTPException(status_code=422, detail="The uploaded document does not contain readable text")
    submission = Submission(assignment_id=assignment.id, student_id=student.id, original_filename=file.filename or stored_name, stored_filename=stored_name, extracted_text=extracted, status="processing")
    db.add(submission)
    db.flush()
    previous = db.scalars(select(Submission).where(Submission.assignment_id == assignment.id, Submission.id != submission.id)).all()
    metrics = evaluate_submission(extracted, assignment.reference_answer, assignment.keywords or [], assignment.min_words, assignment.max_words)
    risk, matches = compare_submissions(extracted, [(item.id, item.extracted_text) for item in previous], settings.plagiarism_threshold)
    result = EvaluationResult(submission_id=submission.id, predicted_score=metrics["predicted_score"], keyword_coverage=metrics["keyword_coverage"], reference_similarity=metrics["reference_similarity"], vocabulary_richness=metrics["vocabulary_richness"], word_count_score=metrics["word_count_score"], plagiarism_risk=risk, feedback=metrics["feedback"])
    submission.status = "flagged" if matches else "evaluated"
    submission.evaluated_at = datetime.utcnow()
    db.add(result)
    for match in matches:
        db.add(PlagiarismMatch(submission_id=submission.id, **match))
    db.commit()
    db.refresh(submission)
    return serialize_submission(submission)


@router.get("/{submission_id}")
def get_submission(submission_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    item = db.scalar(select(Submission).options(joinedload(Submission.assignment), joinedload(Submission.student), joinedload(Submission.evaluation)).where(Submission.id == submission_id))
    if not item or (user.role == "student" and item.student_id != user.id) or (user.role == "teacher" and item.assignment.teacher_id != user.id):
        raise HTTPException(status_code=404, detail="Submission not found")
    return serialize_submission(item)


@router.get("/{submission_id}/matches")
def plagiarism_matches(submission_id: int, teacher: User = Depends(require_role("teacher")), db: Session = Depends(get_db)):
    item = db.scalar(select(Submission).options(joinedload(Submission.assignment)).where(Submission.id == submission_id))
    if not item or item.assignment.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Submission not found")
    matches = db.scalars(select(PlagiarismMatch).where(PlagiarismMatch.submission_id == submission_id).order_by(PlagiarismMatch.similarity_score.desc())).all()
    return [{"compared_submission_id": m.compared_submission_id, "similarity_score": float(m.similarity_score), "matching_phrases": m.matching_phrases or []} for m in matches]


@router.patch("/{submission_id}/approve")
def approve_submission(submission_id: int, payload: ApprovalRequest, teacher: User = Depends(require_role("teacher")), db: Session = Depends(get_db)):
    item = db.scalar(select(Submission).options(joinedload(Submission.assignment), joinedload(Submission.evaluation)).where(Submission.id == submission_id))
    if not item or item.assignment.teacher_id != teacher.id or not item.evaluation:
        raise HTTPException(status_code=404, detail="Evaluated submission not found")
    if payload.final_score is not None and not 0 <= payload.final_score <= 100:
        raise HTTPException(status_code=422, detail="final_score must be between 0 and 100")
    item.evaluation.final_score = payload.final_score if payload.final_score is not None else item.evaluation.predicted_score
    item.evaluation.teacher_comment = payload.teacher_comment
    item.evaluation.approved_by = teacher.id
    item.evaluation.approved_at = datetime.utcnow()
    item.status = "overridden" if payload.final_score is not None else "approved"
    db.commit()
    db.refresh(item)
    return serialize_submission(item)
