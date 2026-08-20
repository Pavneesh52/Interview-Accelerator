from sqlalchemy import String, Text, DateTime, ForeignKey, func, JSON, Integer, Float, Enum as SQLEnum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime
import uuid
import enum


class InterviewStatus(str, enum.Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewLevel(int, enum.Enum):
    SCREENING = 1
    COMPETENCY = 2
    DEEP_DIVE = 3


class QuestionType(str, enum.Enum):
    SCREENING = "screening"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SCENARIO = "scenario"
    FOLLOW_UP = "follow_up"
    DEEP_DIVE = "deep_dive"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class Interview(Base):
    __tablename__ = "interviews"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    status: Mapped[InterviewStatus] = mapped_column(SQLEnum(InterviewStatus), default=InterviewStatus.NOT_STARTED, nullable=False)
    current_level: Mapped[InterviewLevel] = mapped_column(SQLEnum(InterviewLevel), default=InterviewLevel.SCREENING, nullable=False)
    current_question_index: Mapped[int] = mapped_column(Integer, default=0)
    total_questions: Mapped[int] = mapped_column(Integer, default=0)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Adaptive state
    difficulty_adjustment: Mapped[float] = mapped_column(Float, default=0.0)
    topics_covered: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    weaknesses_identified: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    strengths_confirmed: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    # Relationships
    session: Mapped["AnalysisSession"] = relationship(back_populates="interview")
    questions: Mapped[list["InterviewQuestion"]] = relationship(back_populates="interview", cascade="all, delete-orphan", order_by="InterviewQuestion.order_index")
    evaluation: Mapped["InterviewEvaluation"] = relationship(back_populates="interview", cascade="all, delete-orphan", uselist=False)


class InterviewQuestion(Base):
    __tablename__ = "interview_questions"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, index=True)
    level: Mapped[InterviewLevel] = mapped_column(SQLEnum(InterviewLevel), nullable=False)
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    question_type: Mapped[QuestionType] = mapped_column(SQLEnum(QuestionType), nullable=False)
    expected_competencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    difficulty: Mapped[DifficultyLevel] = mapped_column(SQLEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM, nullable=False)
    order_index: Mapped[int] = mapped_column(Integer, nullable=False)
    is_follow_up: Mapped[bool] = mapped_column(Boolean, default=False)
    parent_question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_questions.id"), nullable=True)
    generated_context: Mapped[dict] = mapped_column(JSON, nullable=True)
    asked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    interview: Mapped["Interview"] = relationship(back_populates="questions")
    answer: Mapped["InterviewAnswer"] = relationship(back_populates="question", cascade="all, delete-orphan", uselist=False)


class InterviewAnswer(Base):
    __tablename__ = "interview_answers"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    question_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interview_questions.id", ondelete="CASCADE"), nullable=False, unique=True)
    transcript: Mapped[str] = mapped_column(Text, nullable=True)
    audio_url: Mapped[str] = mapped_column(String(500), nullable=True)
    video_url: Mapped[str] = mapped_column(String(500), nullable=True)
    duration_seconds: Mapped[int] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[float] = mapped_column(Float, nullable=True)
    submitted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Analysis
    filler_words_count: Mapped[int] = mapped_column(Integer, default=0)
    speaking_pace_wpm: Mapped[float] = mapped_column(Float, nullable=True)
    long_pauses_count: Mapped[int] = mapped_column(Integer, default=0)
    
    # Relationships
    question: Mapped["InterviewQuestion"] = relationship(back_populates="answer")


class InterviewEvaluation(Base):
    __tablename__ = "interview_evaluations"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    interview_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("interviews.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    overall_score: Mapped[int] = mapped_column(Integer, nullable=True)
    
    # Competency scores
    role_fit_score: Mapped[int] = mapped_column(Integer, nullable=True)
    technical_knowledge_score: Mapped[int] = mapped_column(Integer, nullable=True)
    problem_solving_score: Mapped[int] = mapped_column(Integer, nullable=True)
    communication_score: Mapped[int] = mapped_column(Integer, nullable=True)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=True)
    depth_of_understanding_score: Mapped[int] = mapped_column(Integer, nullable=True)
    behavioral_fit_score: Mapped[int] = mapped_column(Integer, nullable=True)
    
    competency_scores: Mapped[dict] = mapped_column(JSON, nullable=True)
    question_feedbacks: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    strengths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    weaknesses: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    preparation_gaps: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    readiness_level: Mapped[str] = mapped_column(String(50), nullable=True)
    readiness_score: Mapped[int] = mapped_column(Integer, nullable=True)
    
    raw_evaluation: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    interview: Mapped["Interview"] = relationship(back_populates="evaluation")