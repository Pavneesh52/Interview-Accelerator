from sqlalchemy import String, Text, DateTime, ForeignKey, func, JSON, Integer, Float, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.db.session import Base
from datetime import datetime
import uuid
import enum


class SessionStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisSession(Base):
    __tablename__ = "analysis_sessions"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    jd_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("job_descriptions.id", ondelete="CASCADE"), nullable=False)
    resume_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("resumes.id", ondelete="CASCADE"), nullable=False)
    status: Mapped[SessionStatus] = mapped_column(SQLEnum(SessionStatus), default=SessionStatus.PENDING, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="sessions")
    job_description: Mapped["JobDescription"] = relationship(back_populates="sessions")
    resume: Mapped["Resume"] = relationship(back_populates="sessions")
    jd_analysis: Mapped["JDAnalysis"] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)
    resume_analysis: Mapped["ResumeAnalysis"] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)
    job_fit: Mapped["JobFitAssessment"] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)
    interview: Mapped["Interview"] = relationship(back_populates="session", cascade="all, delete-orphan", uselist=False)


class JDAnalysis(Base):
    __tablename__ = "jd_analyses"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    role_title: Mapped[str] = mapped_column(String(255), nullable=False)
    responsibilities: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    required_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    preferred_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    technical_competencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    behavioral_competencies: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    experience_expectations: Mapped[str] = mapped_column(Text, nullable=True)
    keywords: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    concepts: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    qualifications: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    raw_llm_response: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session: Mapped["AnalysisSession"] = relationship(back_populates="jd_analysis")


class ResumeAnalysis(Base):
    __tablename__ = "resume_analyses"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    experience: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    projects: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    achievements: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    strengths: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_skills: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    weak_areas: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    questionable_claims: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    raw_llm_response: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session: Mapped["AnalysisSession"] = relationship(back_populates="resume_analysis")


class JobFitAssessment(Base):
    __tablename__ = "job_fit_assessments"
    
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    session_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("analysis_sessions.id", ondelete="CASCADE"), nullable=False, unique=True)
    
    score: Mapped[int] = mapped_column(Integer, nullable=False)
    rating: Mapped[str] = mapped_column(String(50), nullable=False)
    strong_matches: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    partial_matches: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    missing_weak: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    methodology: Mapped[str] = mapped_column(Text, nullable=True)
    skill_match_details: Mapped[dict] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    # Relationships
    session: Mapped["AnalysisSession"] = relationship(back_populates="job_fit")