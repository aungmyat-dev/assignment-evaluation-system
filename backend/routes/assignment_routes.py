from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from ..auth import CurrentUser, require_role
from ..database import get_db
from ..models import Assignment, User

router = APIRouter(prefix="/api/assignments", tags=["Assignments"])


class AssignmentRequest(BaseModel):
    title: str = Field(min_length=3, max_length=180)
    description: str | None = None
    reference_answer: str | None = None
    keywords: list[str] = Field(default_factory=list)
    rubric: dict = Field(default_factory=dict)
    min_words: int = Field(default=150, ge=1, le=100000)
    max_words: int = Field(default=2000, ge=1, le=100000)
    due_date: datetime | None = None


def serialize_assignment(item: Assignment) -> dict:
    return {"id": item.id, "title": item.title, "description": item.description, "reference_answer": item.reference_answer, "keywords": item.keywords or [], "rubric": item.rubric or {}, "min_words": item.min_words, "max_words": item.max_words, "due_date": item.due_date, "created_at": item.created_at}


@router.get("")
def list_assignments(user: CurrentUser, db: Session = Depends(get_db)):
    query = select(Assignment).order_by(Assignment.created_at.desc())
    if user.role == "teacher":
        query = query.where(Assignment.teacher_id == user.id)
    return [serialize_assignment(item) for item in db.scalars(query).all()]


@router.post("", status_code=201)
def create_assignment(payload: AssignmentRequest, teacher: User = Depends(require_role("teacher")), db: Session = Depends(get_db)):
    if payload.max_words < payload.min_words:
        raise HTTPException(status_code=422, detail="max_words must be greater than or equal to min_words")
    item = Assignment(teacher_id=teacher.id, **payload.model_dump())
    db.add(item)
    db.commit()
    db.refresh(item)
    return serialize_assignment(item)


@router.get("/{assignment_id}")
def get_assignment(assignment_id: int, user: CurrentUser, db: Session = Depends(get_db)):
    item = db.get(Assignment, assignment_id)
    if not item or (user.role == "teacher" and item.teacher_id != user.id):
        raise HTTPException(status_code=404, detail="Assignment not found")
    return serialize_assignment(item)


@router.put("/{assignment_id}")
def update_assignment(assignment_id: int, payload: AssignmentRequest, teacher: User = Depends(require_role("teacher")), db: Session = Depends(get_db)):
    item = db.get(Assignment, assignment_id)
    if not item or item.teacher_id != teacher.id:
        raise HTTPException(status_code=404, detail="Assignment not found")
    if payload.max_words < payload.min_words:
        raise HTTPException(status_code=422, detail="max_words must be greater than or equal to min_words")
    for key, value in payload.model_dump().items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    return serialize_assignment(item)
