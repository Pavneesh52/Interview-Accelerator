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
    SkipQuestionRequest,
    InterviewerIntroResponse,
    CurrentQuestionResponse,
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


async def _get_interview_with_auth(db: AsyncSession, interview_id: uuid.UUID, user_id: uuid.UUID) -> Interview:
    """Helper to fetch interview with full relations and verify ownership."""
    result = await db.execute(
        select(Interview)
        .options(
            selectinload(Interview.questions).selectinload(InterviewQuestion.answer),
            selectinload(Interview.evaluation),
            selectinload(Interview.session).selectinload(AnalysisSession.jd_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.resume_analysis),
            selectinload(Interview.session).selectinload(AnalysisSession.job_fit),
        )
        .where(Interview.id == interview_id)
    )
    interview = result.scalar_one_or_none()
    if not interview:
        raise HTTPException(status_code=404, detail="Interview not found")
    if interview.session.user_id != user_id:
        raise HTTPException(status_code=403, detail="Not authorized")
    return interview


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
            return InterviewResponse.model_validate(session.interview)
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

    # Re-fetch with relations for proper serialization
    refreshed = await _get_interview_with_auth(db, interview.id, current_user.id)
    return InterviewResponse.model_validate(refreshed)


@router.get("/interviews/{interview_id}", response_model=InterviewResponse)
async def get_interview(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    interview = await _get_interview_with_auth(db, interview_id, current_user.id)
    return InterviewResponse.model_validate(interview)


@router.get("/interviews/session/{session_id}", response_model=InterviewResponse)
async def get_interview_by_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Fetch the interview associated with a given analysis session."""
    session = await get_session_with_relations(db, session_id, current_user.id)

    if not session.interview:
        raise HTTPException(status_code=404, detail="No interview found for this session")

    return InterviewResponse.model_validate(session.interview)


@router.get("/interviews/{interview_id}/intro", response_model=InterviewerIntroResponse)
async def get_interviewer_intro(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Generate a personalized interviewer introduction."""
    interview = await _get_interview_with_auth(db, interview_id, current_user.id)

    context = interview_service.build_context(
        session_data={
            "jd_analysis": interview.session.jd_analysis.__dict__ if interview.session.jd_analysis else {},
            "resume_analysis": interview.session.resume_analysis.__dict__ if interview.session.resume_analysis else {},
            "job_fit": interview.session.job_fit.__dict__ if interview.session.job_fit else {},
        },
        interview_state={
            "current_level": interview.current_level.value if isinstance(interview.current_level, InterviewLevel) else interview.current_level,
            "questions": [],
        }
    )

    intro = await interview_service.generate_interviewer_intro(context)
    return InterviewerIntroResponse(
        greeting=intro.greeting,
        interviewer_name=intro.interviewer_name,
        interviewer_title=intro.interviewer_title,
        focus_areas=intro.focus_areas,
        estimated_duration_minutes=intro.estimated_duration_minutes,
        tips=intro.tips,
    )


@router.get("/interviews/{interview_id}/current-question", response_model=CurrentQuestionResponse)
async def get_current_question(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Get the current question with progress context."""
    interview = await _get_interview_with_auth(db, interview_id, current_user.id)

    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail=f"Interview is {interview.status.value}")

    if interview.current_question_index >= interview.total_questions:
        raise HTTPException(status_code=400, detail="All questions completed")

    current_question = interview.questions[interview.current_question_index]
    questions_answered = sum(1 for q in interview.questions if q.answer is not None)

    level_names = {1: "Screening", 2: "Competency", 3: "Deep Dive"}
    current_level_val = interview.current_level.value if isinstance(interview.current_level, InterviewLevel) else interview.current_level

    return CurrentQuestionResponse(
        question=InterviewQuestionResponse.model_validate(current_question),
        progress=round((questions_answered / max(interview.total_questions, 1)) * 100, 1),
        questions_answered=questions_answered,
        questions_remaining=interview.total_questions - questions_answered,
        current_level=interview.current_level,
        level_name=level_names.get(current_level_val, "Unknown"),
        is_last_question=(interview.current_question_index >= interview.total_questions - 1),
        interview_status=interview.status,
    )


@router.post("/interviews/questions/{question_id}/answer", response_model=InterviewAnswerResponse)
async def submit_answer(
    question_id: uuid.UUID,
    answer_data: InterviewAnswerCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    import traceback
    try:
        result = await db.execute(
            select(InterviewQuestion)
            .options(
                selectinload(InterviewQuestion.interview).selectinload(Interview.session),
                selectinload(InterviewQuestion.answer),
            )
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

        # Compute speech analytics from transcript
        analytics = interview_service.compute_speech_analytics(
            answer_data.transcript,
            answer_data.duration_seconds
        )

        answer = InterviewAnswer(
            question_id=question.id,
            transcript=answer_data.transcript,
            audio_url=answer_data.audio_url,
            video_url=answer_data.video_url,
            duration_seconds=answer_data.duration_seconds,
            filler_words_count=analytics["filler_words_count"],
            speaking_pace_wpm=analytics["speaking_pace_wpm"],
            long_pauses_count=analytics["long_pauses_count"],
        )
        db.add(answer)

        interview.current_question_index += 1
        topics = interview.topics_covered or []
        expected = question.expected_competencies or []
        interview.topics_covered = list(set(topics + expected))

        # Mark question as asked
        question.asked_at = datetime.utcnow()

        await db.commit()
        await db.refresh(answer)

        return InterviewAnswerResponse.model_validate(answer)
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@router.post("/interviews/{interview_id}/skip-question", response_model=InterviewQuestionResponse)
async def skip_question(
    interview_id: uuid.UUID,
    skip_data: SkipQuestionRequest = SkipQuestionRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    """Skip the current question and move to the next one."""
    interview = await _get_interview_with_auth(db, interview_id, current_user.id)

    if interview.status != InterviewStatus.IN_PROGRESS:
        raise HTTPException(status_code=400, detail="Interview not in progress")

    if interview.current_question_index >= interview.total_questions:
        raise HTTPException(status_code=400, detail="No more questions to skip")

    skipped_question = interview.questions[interview.current_question_index]

    # Create an empty answer to mark it as skipped
    answer = InterviewAnswer(
        question_id=skipped_question.id,
        transcript="[SKIPPED]",
        duration_seconds=0,
        filler_words_count=0,
        speaking_pace_wpm=0.0,
        long_pauses_count=0,
    )
    db.add(answer)

    interview.current_question_index += 1
    skipped_question.asked_at = datetime.utcnow()

    await db.commit()

    # Return the next question if available
    if interview.current_question_index < interview.total_questions:
        next_question = interview.questions[interview.current_question_index]
        return InterviewQuestionResponse.model_validate(next_question)
    else:
        # Return the skipped question since there are no more
        return InterviewQuestionResponse.model_validate(skipped_question)


@router.post("/interviews/{interview_id}/next-question", response_model=InterviewQuestionResponse)
async def get_next_question(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    interview = await _get_interview_with_auth(db, interview_id, current_user.id)

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

        return InterviewQuestionResponse.model_validate(new_question)

    return InterviewQuestionResponse.model_validate(current_question)


@router.post("/interviews/{interview_id}/evaluate-answer")
async def evaluate_answer(
    interview_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    interview = await _get_interview_with_auth(db, interview_id, current_user.id)

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
    interview = await _get_interview_with_auth(db, interview_id, current_user.id)

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