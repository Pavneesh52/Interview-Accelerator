from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from typing import List, Optional
import uuid
from datetime import datetime

from app.db.session import get_db
from app.services.auth import get_current_user_dependency
from app.services.interview import interview_service
from app.services.evaluation import evaluation_service
from app.models.user import User
from app.models.analysis import AnalysisSession
from app.models.interview import (
    Interview,
    InterviewQuestion,
    InterviewAnswer,
    InterviewEvaluation,
    InterviewStatus,
    InterviewLevel,
    QuestionType,
    DifficultyLevel,
)
from app.schemas.interview import (
    InterviewResponse,
    InterviewQuestionResponse,
    InterviewAnswerCreate,
    InterviewAnswerResponse,
    StartInterviewRequest,
    InterviewStatus as InterviewStatusEnum,
    InterviewLevel as InterviewLevelEnum,
    QuestionType as QuestionTypeEnum,
    DifficultyLevel as DifficultyLevelEnum,
)

router = APIRouter()


async def get_session_with_relations(db: AsyncSession, session_id: uuid.UUID, user_id: uuid.UUID) -> AnalysisSession:
    result = await db.execute(
        select(AnalysisSession)
        .options(
            selectinload(AnalysisSession.jd_analysis),
            selectinload(AnalysisSession.resume_analysis),
            selectinload(AnalysisSession.job_fit),
            selectinload(AnalysisSession.interview).selectinload(Interview.questions).selectinload(InterviewQuestion.answer),
            selectinload(AnalysisSession.interview).selectinload(Interview.evaluation),
        )
        .where(AnalysisSession.id == session_id, AnalysisSession.user_id == user_id)
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return session


@router.post("/interviews/start", response_model=InterviewResponse)
async def start_interview(
    request: StartInterviewRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    session = await get_session_with_relations(db, request.session_id, current_user.id)
    
    if session.status.value != "completed":
        raise HTTPException(status_code=400, detail="Analysis not completed yet")
    
    if session.interview:
        if session.interview.status in [InterviewStatus.IN_PROGRESS, InterviewStatus.PAUSED]:
            return InterviewResponse.from_orm(session.interview)
        elif session.interview.status == InterviewStatus.COMPLETED:
            raise HTTPException(status_code=400, detail="Interview already completed")
    
    jd_analysis = session.jd_analysis
    resume_analysis = session.resume_analysis
    job_fit = session.job_fit
    
    context = interview_service.build_context(
        session_data={
            "jd_analysis": jd_analysis.__dict__ if jd_analysis else {},
            "resume_analysis": resume_analysis.__dict__ if resume_analysis else {},
            "job_fit": job_fit.__dict__ if job_fit else {},
        },
        interview_state={"current_level": 1, "questions": []}
    )
    
    questions = await interview_service.generate_initial_questions(context)
    
    interview = Interview(
        session_id=session.id,
        status=InterviewStatus.IN_PROGRESS,
        current_level=InterviewLevel.SCREENING,
        current_question_index=0,
        total_questions=len(questions),
        started_at=datetime.utcnow(),
        difficulty_adjustment=0.0,
        topics_covered=[],
        weaknesses_identified=[],
        strengths_confirmed=[],
    )
    db.add(interview)
    await db.flush()
    
    for i, q in enumerate(questions):
        question = InterviewQuestion(
            interview_id=interview.id,
            level=InterviewLevel(interview.current_level),
            question_text=q.question_text,
            question_type=QuestionType(q.question_type),
            expected_competencies=q.expected_competencies,
            difficulty=DifficultyLevel(q.difficulty),
            order_index=i,
            is_follow_up=q.is_follow_up,
            parent_question_id=q.parent_question_id,
            generated_context=q.generated_context,
        )
        db.add(question)
    
    interview.total_questions = len(questions)
    await db.commit()
    await db.refresh(interview)
    
    return InterviewResponse.from_orm(interview)


@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(Interview)
        .options(
            selectinload(Interview.questions).selectinload(InterviewQuestion.answer),
            selectinload(Interview.evaluation),
            selectinload(Interview.session),
        )
        .where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    return InterviewResponse.from_orm(interview)


@router.post("/interviews/questions/{question_id}/answer", response_model=InterviewAnswerResponse)
async def submit_answer(
    question_id: uuid.UUID,
    answer_data: InterviewAnswerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(InterviewQuestion)
        .options(selectinload(InterviewQuestion.interview).selectinload(Interview.session))
        .where(InterviewQuestion.id == question_id)
    )
    question = result.scalar_one_or_none()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    
    if question.interview.session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if question.answer:
        raise HTTPException(status_code=400, detail="Answer already submitted")
    
    interview = question.interview
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Interview not in progress")
    
    answer = InterviewAnswer(
        question_id=question.id,
        transcript=answer_data.transcript,
        audio_url=answer_data.audio_url,
        video_url=answer_data.video_url,
        duration_seconds=answer_data.duration_seconds,
        filler_words_count=0,
        speaking_pace_wpm=0.0,
        long_pauses_count=0,
    )
    db.add(answer)
    
    interview.current_question_index += 1
    interview.topics_covered = list(set(interview.topics_covered + question.expected_competencies))
    await db.commit()
    await db.refresh(answer)
    
    return InterviewAnswerResponse.from_orm(answer)


@router.post("/interviews/{interview_id}/next-question", response_model=InterviewQuestionResponse)
async def get_next_question(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(Interview)
        .options(
            selectinload(Interview.questions).selectinload(InterviewQuestion.answer),
            selectinload(Interview.session).selectinload(AnalysisSession.jd_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.resume_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.job_fit),
        )
        .where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Interview not in progress")
    
    if interview.current_question_index >= interview.total_questions:
        interview.status = InterviewStatus.COMPLETED
        interview.completed_at = datetime.utcnow()
        await db.commit()
        raise HTTPException(status_code=400, detail="Interview completed")
    
    current_question = interview.questions[interview.current_question_index]
    
    if current_question.answer and interview_service.should_generate_follow_up(
        current_question.answer.__dict__, 
        current_question.__dict__
    ):
        context = interview_service.build_context(
            session_data={
                "jd_analysis": interview.session.jd_analysis.__dict__ if interview.session.jd_analysis else {},
                "resume_analysis": interview.session.resume_analysis.__dict__ if interview.session.resume_analysis else {},
                "job_fit": interview.session.job_fit.__dict__ if interview.session.job_fit else {},
            },
            interview_state={
                "current_level": interview.current_level,
                "questions": [
                    {
                        "question_text": q.question_text,
                        "level": q.level,
                        "answer": q.answer.__dict__ if q.answer else None
                    }
                    for q in interview.questions
                ],
                "difficulty_adjustment": interview.difficulty_adjustment,
                "topics_covered": interview.topics_covered,
                "weaknesses_identified": interview.weaknesses_identified,
                "strengths_confirmed": interview.strengths_confirmed,
            }
        )
        
        follow_up = await interview_service.generate_follow_up(context)
        
        new_question = InterviewQuestion(
            interview_id=interview.id,
            level=InterviewLevel(interview.current_level),
            question_text=follow_up.question_text,
            question_type=QuestionType(follow_up.question_type),
            expected_competencies=follow_up.expected_competencies,
            difficulty=DifficultyLevel(follow_up.difficulty),
            order_index=interview.total_questions,
            is_follow_up=True,
            parent_question_id=current_question.id,
            generated_context=follow_up.generated_context,
        )
        db.add(new_question)
        interview.total_questions += 1
        await db.commit()
        await db.refresh(new_question)
        
        return InterviewQuestionResponse.from_orm(new_question)
    
    return InterviewQuestionResponse.from_orm(current_question)


@router.post("/interviews/{interview_id}/evaluate-answer")
async def evaluate_answer(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(Interview)
        .options(
            selectinload(Interview.questions).selectinload(InterviewQuestion.answer),
            selectinload(Interview.session).selectinload(AnalysisSession.jd_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.resume_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.job_fit),
        )
        .where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    last_question = None
    for q in interview.questions:
        if q.answer and q.order_index == interview.current_question_index - 1:
            last_question = q
            break
    
    if not last_question or not last_question.answer:
        raise HTTPException(status_code=400, detail="No answer to evaluate")
    
    return {"message": "Answer evaluation queued", "question_id": str(last_question.id)}


@router.post("/interviews/{interview_id}/complete")
async def complete_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(Interview)
        .options(selectinload(Interview.session))
        .where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    interview.status = InterviewStatus.COMPLETED
    interview.completed_at = datetime.utcnow()
    await db.commit()
    
    return {"message": "Interview completed", "interview_id": str(interview.id)}


@router.post("/interviews/{interview_id}/evaluate", response_model=dict)
async def evaluate_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(Interview)
        .options(
            selectinload(Interview.questions).selectinload(InterviewQuestion.answer),
            selectinload(Interview.session).selectinload(AnalysisSession.jd_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.resume_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.job_fit),
        )
        .where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    
    if interview.session.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    if interview.status != InterviewStatus.COMPLETED:
        raise HTTPException(status_code=400, detail="Interview not completed yet")
    
    jd_analysis = interview.session.jd_analysis
    resume_analysis = interview.session.resume_analysis
    job_fit = interview.session.job_fit
    
    if not all([jd_analysis, resume_analysis, job_fit]):
        raise HTTPException(status_code=400, detail="Missing analysis data")
    
    qa_history = []
    for q in interview.questions:
        qa_history.append({
            "id": str(q.id),
            "question_text": q.question_text,
            "level": q.level,
            "question_type": q.question_type,
            "expected_competencies": q.expected_competencies,
            "difficulty": q.difficulty,
            "answer": q.answer.__dict__ if q.answer else None
        })
    
    evaluation_result = await evaluation_service.evaluate_interview(
        jd_analysis=jd_analysis.__dict__,
        resume_analysis=resume_analysis.__dict__,
        job_fit=job_fit.__dict__,
        interview_questions=qa_history,
    )
    
    evaluation = InterviewEvaluation(
        interview_id=interview.id,
        overall_score=evaluation_result.overall_score,
        role_fit_score=evaluation_result.role_fit_score,
        technical_knowledge_score=evaluation_result.technical_knowledge_score,
        problem_solving_score=evaluation_result.problem_solving_score,
        communication_score=evaluation_result.communication_score,
        confidence_score=evaluation_result.confidence_score,
        depth_of_understanding_score=evaluation_result.depth_of_understanding_score,
        behavioral_fit_score=evaluation_result.behavioral_fit_score,
        competency_scores=evaluation_result.competency_scores,
        question_feedbacks=[f.model_dump() for f in evaluation_result.question_feedbacks],
        strengths=evaluation_result.strengths,
        weaknesses=evaluation_result.weaknesses,
        preparation_gaps=[g.model_dump() for g in evaluation_result.preparation_gaps],
        readiness_level=evaluation_result.readiness_level,
        readiness_score=evaluation_result.readiness_score,
        raw_evaluation=evaluation_result.model_dump(),
    )
    db.add(evaluation)
    await db.commit()
    
    return {"message": "Evaluation completed", "evaluation_id": str(evaluation.id)}