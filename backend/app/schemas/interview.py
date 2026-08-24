from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid
from enum import Enum


class InterviewStatus(str, Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PAUSED = "paused"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class InterviewLevel(int, Enum):
    SCREENING = 1
    COMPETENCY = 2
    DEEP_DIVE = 3


class QuestionType(str, Enum):
    SCREENING = "screening"
    TECHNICAL = "technical"
    BEHAVIORAL = "behavioral"
    SCENARIO = "scenario"
    FOLLOW_UP = "follow_up"
    DEEP_DIVE = "deep_dive"


class DifficultyLevel(str, Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class ReadinessLevel(str, Enum):
    NOT_READY = "not_ready"
    NEEDS_PREPARATION = "needs_preparation"
    INTERVIEW_READY = "interview_ready"
    STRONG_CANDIDATE = "strong_candidate"


class InterviewQuestionResponse(BaseModel):
    id: uuid.UUID
    interview_id: uuid.UUID
    level: InterviewLevel
    question_text: str
    question_type: QuestionType
    expected_competencies: List[str]
    difficulty: DifficultyLevel
    order_index: int
    is_follow_up: bool
    parent_question_id: Optional[uuid.UUID] = None
    generated_context: Optional[Dict[str, Any]] = None
    asked_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class InterviewAnswerCreate(BaseModel):
    transcript: str
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None


class InterviewAnswerResponse(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID
    transcript: Optional[str] = None
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    confidence_score: Optional[float] = None
    filler_words_count: int
    speaking_pace_wpm: Optional[float] = None
    long_pauses_count: int
    submitted_at: datetime

    class Config:
        from_attributes = True


class QuestionFeedback(BaseModel):
    question_id: uuid.UUID
    question: str
    candidate_answer: str
    assessment: str
    what_was_good: List[str]
    what_could_be_better: List[str]
    ideal_direction: str
    competencies_evaluated: List[str]
    score: int


class PreparationGap(BaseModel):
    priority: int
    topic: str
    review_items: List[str]


class InterviewEvaluationResponse(BaseModel):
    id: uuid.UUID
    interview_id: uuid.UUID
    overall_score: Optional[int] = None
    role_fit_score: Optional[int] = None
    technical_knowledge_score: Optional[int] = None
    problem_solving_score: Optional[int] = None
    communication_score: Optional[int] = None
    confidence_score: Optional[int] = None
    depth_of_understanding_score: Optional[int] = None
    behavioral_fit_score: Optional[int] = None
    competency_scores: Optional[Dict[str, int]] = None
    question_feedbacks: List[QuestionFeedback] = []
    strengths: List[str] = []
    weaknesses: List[str] = []
    preparation_gaps: List[PreparationGap] = []
    readiness_level: Optional[ReadinessLevel] = None
    readiness_score: Optional[int] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InterviewResponse(BaseModel):
    id: uuid.UUID
    session_id: uuid.UUID
    status: InterviewStatus
    current_level: InterviewLevel
    current_question_index: int
    total_questions: int
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    difficulty_adjustment: float
    topics_covered: List[str]
    weaknesses_identified: List[str]
    strengths_confirmed: List[str]
    questions: List[InterviewQuestionResponse] = []
    evaluation: Optional[InterviewEvaluationResponse] = None

    class Config:
        from_attributes = True


class StartInterviewRequest(BaseModel):
    session_id: uuid.UUID


class SkipQuestionRequest(BaseModel):
    reason: Optional[str] = None


class InterviewerIntroResponse(BaseModel):
    greeting: str
    interviewer_name: str
    interviewer_title: str
    focus_areas: List[str]
    estimated_duration_minutes: int
    tips: List[str]


class CurrentQuestionResponse(BaseModel):
    question: InterviewQuestionResponse
    progress: float  # 0-100
    questions_answered: int
    questions_remaining: int
    current_level: InterviewLevel
    level_name: str
    is_last_question: bool
    interview_status: InterviewStatus