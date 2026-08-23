from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
import uuid

from app.db.session import get_db
from app.services.auth import get_current_user_dependency
from app.services.analysis import analysis_service
from app.models.user import User
from app.models.document import JobDescription, Resume
from app.models.analysis import AnalysisSession, JDAnalysis, ResumeAnalysis, JobFitAssessment, SessionStatus
from app.schemas.analysis import (
    JDAnalysisResponse,
    ResumeAnalysisResponse,
    JobFitAssessmentResponse,
    AnalysisSessionResponse,
    AnalysisSessionCreateResponse,
    SessionCreate,
    SessionStatus,
)

router = APIRouter()


@router.post("/sessions", response_model=AnalysisSessionCreateResponse, status_code=status.HTTP_201_CREATED)
async def create_analysis_session(
    session_data: SessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    jd_result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == session_data.jd_id,
            JobDescription.user_id == current_user.id,
        )
    )
    jd = jd_result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    
    resume_result = await db.execute(
        select(Resume).where(
            Resume.id == session_data.resume_id,
            Resume.user_id == current_user.id,
        )
    )
    resume = resume_result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    
    session = AnalysisSession(
        user_id=current_user.id,
        jd_id=session_data.jd_id,
        resume_id=session_data.resume_id,
        status=SessionStatus.PENDING,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    
    return AnalysisSessionCreateResponse.model_validate(session)


@router.get("/sessions", response_model=List[AnalysisSessionCreateResponse])
async def list_sessions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(AnalysisSession)
        .where(AnalysisSession.user_id == current_user.id)
        .order_by(AnalysisSession.created_at.desc())
    )
    sessions = result.scalars().all()
    return [AnalysisSessionCreateResponse.model_validate(s) for s in sessions]


@router.get("/sessions/{session_id}", response_model=AnalysisSessionResponse)
async def get_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    from sqlalchemy.orm import selectinload
    result = await db.execute(
        select(AnalysisSession)
        .options(
            selectinload(AnalysisSession.jd_analysis),
            selectinload(AnalysisSession.resume_analysis),
            selectinload(AnalysisSession.job_fit),
        )
        .where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    return AnalysisSessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/analyze")
async def run_analysis(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    if session.status == SessionStatus.PROCESSING:
        raise HTTPException(status_code=400, detail="Analysis already in progress")
    
    session.status = SessionStatus.PROCESSING
    await db.commit()
    
    try:
        jd_result = await db.execute(select(JobDescription).where(JobDescription.id == session.jd_id))
        jd = jd_result.scalar_one()
        
        resume_result = await db.execute(select(Resume).where(Resume.id == session.resume_id))
        resume = resume_result.scalar_one()
        
        jd_analysis = await analysis_service.analyze_jd(jd.raw_text)
        
        jd_analysis_db = JDAnalysis(
            session_id=session.id,
            role_title=jd_analysis.role_title,
            responsibilities=jd_analysis.responsibilities,
            required_skills=jd_analysis.required_skills,
            preferred_skills=jd_analysis.preferred_skills,
            technical_competencies=[c.model_dump() for c in jd_analysis.technical_competencies],
            behavioral_competencies=[c.model_dump() for c in jd_analysis.behavioral_competencies],
            experience_expectations=jd_analysis.experience_expectations,
            keywords=jd_analysis.keywords,
            concepts=jd_analysis.concepts,
            qualifications=jd_analysis.qualifications,
            raw_llm_response=jd_analysis.model_dump(),
        )
        db.add(jd_analysis_db)
        
        resume_analysis = await analysis_service.analyze_resume(resume.raw_text, jd_analysis)
        
        resume_analysis_db = ResumeAnalysis(
            session_id=session.id,
            skills=resume_analysis.skills,
            experience=[e.model_dump() for e in resume_analysis.experience],
            projects=[p.model_dump() for p in resume_analysis.projects],
            achievements=resume_analysis.achievements,
            strengths=resume_analysis.strengths,
            missing_skills=resume_analysis.missing_skills,
            weak_areas=[w.model_dump() for w in resume_analysis.weak_areas],
            questionable_claims=[q.model_dump() for q in resume_analysis.questionable_claims],
            raw_llm_response=resume_analysis.model_dump(),
        )
        db.add(resume_analysis_db)
        
        job_fit = await analysis_service.calculate_job_fit(jd_analysis, resume_analysis)
        
        job_fit_db = JobFitAssessment(
            session_id=session.id,
            score=job_fit["score"],
            rating=job_fit["rating"],
            strong_matches=job_fit["strong_matches"],
            partial_matches=job_fit["partial_matches"],
            missing_weak=job_fit["missing_weak"],
            methodology=job_fit["methodology"],
            skill_match_details=job_fit["skill_match_details"],
        )
        db.add(job_fit_db)
        
        session.status = SessionStatus.COMPLETED
        from datetime import datetime
        session.completed_at = datetime.utcnow()
        await db.commit()
        
        return {"message": "Analysis completed successfully", "session_id": str(session.id)}
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        session.status = SessionStatus.FAILED
        await db.commit()
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/sessions/{session_id}/jd-analysis", response_model=JDAnalysisResponse)
async def get_jd_analysis(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    jd_analysis_result = await db.execute(
        select(JDAnalysis).where(JDAnalysis.session_id == session_id)
    )
    jd_analysis = jd_analysis_result.scalar_one_or_none()
    if not jd_analysis:
        raise HTTPException(status_code=404, detail="JD analysis not found")
    
    return JDAnalysisResponse.model_validate(jd_analysis)


@router.get("/sessions/{session_id}/resume-analysis", response_model=ResumeAnalysisResponse)
async def get_resume_analysis(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    resume_analysis_result = await db.execute(
        select(ResumeAnalysis).where(ResumeAnalysis.session_id == session_id)
    )
    resume_analysis = resume_analysis_result.scalar_one_or_none()
    if not resume_analysis:
        raise HTTPException(status_code=404, detail="Resume analysis not found")
    
    return ResumeAnalysisResponse.model_validate(resume_analysis)


@router.get("/sessions/{session_id}/job-fit", response_model=JobFitAssessmentResponse)
async def get_job_fit(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    result = await db.execute(
        select(AnalysisSession).where(
            AnalysisSession.id == session_id,
            AnalysisSession.user_id == current_user.id,
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    job_fit_result = await db.execute(
        select(JobFitAssessment).where(JobFitAssessment.session_id == session_id)
    )
    job_fit = job_fit_result.scalar_one_or_none()
    if not job_fit:
        raise HTTPException(status_code=404, detail="Job fit assessment not found")
    
    return JobFitAssessmentResponse.model_validate(job_fit)