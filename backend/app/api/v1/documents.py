from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List
import uuid

from app.db.session import get_db
from app.services.auth import get_current_user_dependency
from app.services.storage import storage_service
from app.services.document_processor import DocumentProcessor
from app.models.user import User
from app.models.document import JobDescription, Resume
from app.schemas.document import (
    JobDescriptionCreate,
    JobDescriptionUpdate,
    JobDescriptionResponse,
    ResumeCreate,
    ResumeUpdate,
    ResumeResponse,
    DocumentUploadResponse,
)
from app.schemas.auth import UserResponse
from app.core.config import settings

router = APIRouter()


@router.post("/jd/upload", response_model=DocumentUploadResponse)
async def upload_jd(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed",
        )
    
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit",
        )
    
    file_url = storage_service.upload_bytes(
        content,
        file.filename or "jd.pdf",
        file.content_type,
        folder="job_descriptions",
    )
    
    text = DocumentProcessor.extract_text(content, file.content_type)
    cleaned_text = DocumentProcessor.clean_text(text)
    
    jd = JobDescription(
        user_id=current_user.id,
        title=file.filename or "Job Description",
        raw_text=cleaned_text,
        file_url=file_url,
        file_name=file.filename,
        file_size=len(content),
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)
    
    return DocumentUploadResponse(
        document_id=jd.id,
        file_url=file_url,
        message="Job description uploaded successfully",
    )


@router.post("/jd/paste", response_model=JobDescriptionResponse)
async def paste_jd(
    jd_data: JobDescriptionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    cleaned_text = DocumentProcessor.clean_text(jd_data.raw_text)
    
    jd = JobDescription(
        user_id=current_user.id,
        title=jd_data.title,
        raw_text=cleaned_text,
    )
    db.add(jd)
    await db.commit()
    await db.refresh(jd)
    
    return jd


@router.get("/jd/{jd_id}", response_model=JobDescriptionResponse)
async def get_jd(
    jd_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    from sqlalchemy import select
    result = await db.execute(
        select(JobDescription).where(
            JobDescription.id == jd_id,
            JobDescription.user_id == current_user.id,
        )
    )
    jd = result.scalar_one_or_none()
    if not jd:
        raise HTTPException(status_code=404, detail="Job description not found")
    return jd


@router.post("/resume/upload", response_model=DocumentUploadResponse)
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    if file.content_type not in settings.ALLOWED_FILE_TYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type {file.content_type} not allowed",
        )
    
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File size exceeds 10MB limit",
        )
    
    file_url = storage_service.upload_bytes(
        content,
        file.filename or "resume.pdf",
        file.content_type,
        folder="resumes",
    )
    
    text = DocumentProcessor.extract_text(content, file.content_type)
    cleaned_text = DocumentProcessor.clean_text(text)
    
    resume = Resume(
        user_id=current_user.id,
        raw_text=cleaned_text,
        file_url=file_url,
        file_name=file.filename,
        file_size=len(content),
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    
    return DocumentUploadResponse(
        document_id=resume.id,
        file_url=file_url,
        message="Resume uploaded successfully",
    )


@router.post("/resume/paste", response_model=ResumeResponse)
async def paste_resume(
    resume_data: ResumeCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    cleaned_text = DocumentProcessor.clean_text(resume_data.raw_text)
    
    resume = Resume(
        user_id=current_user.id,
        raw_text=cleaned_text,
    )
    db.add(resume)
    await db.commit()
    await db.refresh(resume)
    
    return resume


@router.get("/resume/{resume_id}", response_model=ResumeResponse)
async def get_resume(
    resume_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user_dependency),
):
    from sqlalchemy import select
    result = await db.execute(
        select(Resume).where(
            Resume.id == resume_id,
            Resume.user_id == current_user.id,
        )
    )
    resume = result.scalar_one_or_none()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    return resume