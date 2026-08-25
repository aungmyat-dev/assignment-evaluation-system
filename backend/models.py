from datetime import datetime
from typing import Any
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    full_name: Mapped[str] = mapped_column(String(120), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(20), default="student", index=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    assignments: Mapped[list["Assignment"]] = relationship(back_populates="teacher")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="student")


class Assignment(Base):
    __tablename__ = "assignments"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    teacher_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(180), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    reference_answer: Mapped[str | None] = mapped_column(Text)
    keywords: Mapped[list[str]] = mapped_column(JSON, default=list)
    rubric: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    min_words: Mapped[int] = mapped_column(Integer, default=150)
    max_words: Mapped[int] = mapped_column(Integer, default=2000)
    due_date: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    teacher: Mapped[User] = relationship(back_populates="assignments")
    submissions: Mapped[list["Submission"]] = relationship(back_populates="assignment", cascade="all, delete-orphan")


class Submission(Base):
    __tablename__ = "submissions"
    __table_args__ = (UniqueConstraint("assignment_id", "student_id", name="uq_assignment_student_submission"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    assignment_id: Mapped[int] = mapped_column(ForeignKey("assignments.id", ondelete="CASCADE"), index=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    stored_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(20), default="processing", index=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    evaluated_at: Mapped[datetime | None] = mapped_column(DateTime)
    assignment: Mapped[Assignment] = relationship(back_populates="submissions")
    student: Mapped[User] = relationship(back_populates="submissions")
    evaluation: Mapped["EvaluationResult | None"] = relationship(back_populates="submission", uselist=False, cascade="all, delete-orphan")
    plagiarism_matches: Mapped[list["PlagiarismMatch"]] = relationship(foreign_keys="PlagiarismMatch.submission_id", cascade="all, delete-orphan")


class EvaluationResult(Base):
    __tablename__ = "evaluation_results"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"), unique=True)
    predicted_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    final_score: Mapped[float | None] = mapped_column(Numeric(5, 2))
    keyword_coverage: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    reference_similarity: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    vocabulary_richness: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    word_count_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    plagiarism_risk: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    feedback: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    teacher_comment: Mapped[str | None] = mapped_column(Text)
    approved_by: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"))
    approved_at: Mapped[datetime | None] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    submission: Mapped[Submission] = relationship(back_populates="evaluation")


class PlagiarismMatch(Base):
    __tablename__ = "plagiarism_matches"
    __table_args__ = (UniqueConstraint("submission_id", "compared_submission_id", name="uq_plagiarism_pair"),)
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    compared_submission_id: Mapped[int] = mapped_column(ForeignKey("submissions.id", ondelete="CASCADE"))
    similarity_score: Mapped[float] = mapped_column(Numeric(5, 2), default=0)
    matching_phrases: Mapped[list[str]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
