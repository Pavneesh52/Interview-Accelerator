from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum


class TechnicalCompetency(BaseModel):
    name: str
    description: str
    importance: str = Field(..., pattern="^(high|medium|low)$")


class BehavioralCompetency(BaseModel):
    name: str
    description: str
    importance: str = Field(..., pattern="^(high|medium|low)$")


class JDAnalysisResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role_title: str
    responsibilities: List[str]
    required_skills: List[str]
    preferred_skills: List[str]
    technical_competencies: List[TechnicalCompetency]
    behavioral_competencies: List[BehavioralCompetency]
    experience_expectations: Optional[str] = None
    keywords: List[str]
    concepts: List[str]
    qualifications: List[str]
    created_at: datetime
    
    class Config:
        from_attributes = True


class ExperienceItem(BaseModel):
    role: str
    company: str
    duration: str
    description: str


class ProjectItem(BaseModel):
    name: str
    description: str
    technologies: List[str]
    impact: str


class WeakArea(BaseModel):
    area: str
    reason: str


class QuestionableClaim(BaseModel):
    claim: str
    why_questionable: str
    follow_up_questions: List[str]


class ResumeAnalysisResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    skills: List[str]
    experience: List[ExperienceItem]
    projects: List[ProjectItem]
    achievements: List[str]
    strengths: List[str]
    missing_skills: List[str]
    weak_areas: List[WeakArea]
    questionable_claims: List[QuestionableClaim]
    created_at: datetime
    
    class Config:
        from_attributes = True


class JobFitAssessmentResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    score: int = Field(..., ge=0, le=100)
    rating: str
    strong_matches: List[str]
    partial_matches: List[str]
    missing_weak: List[str]
    methodology: Optional[str] = None
    skill_match_details: Optional[Dict[str, Any]] = None
    created_at: datetime
    
    class Config:
        from_attributes = True


class SessionStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class AnalysisSessionResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    jd_id: uuid.UUID
    resume_id: uuid.UUID
    status: SessionStatus
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime] = None
    jd_analysis: Optional[JDAnalysisResponse] = None
    resume_analysis: Optional[ResumeAnalysisResponse] = None
    job_fit: Optional[JobFitAssessmentResponse] = None
    
    class Config:
        from_attributes = True


class SessionCreate(BaseModel):
    jd_id: uuid.UUID
    resume_id: uuid.UUID