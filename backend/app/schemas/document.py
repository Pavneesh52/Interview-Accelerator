from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
import uuid


class JobDescriptionBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    raw_text: str = Field(..., min_length=10)


class JobDescriptionCreate(JobDescriptionBase):
    pass


class JobDescriptionUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    raw_text: Optional[str] = Field(None, min_length=10)


class JobDescriptionResponse(JobDescriptionBase):
    id: uuid.UUID
    user_id: uuid.UUID
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    parsed_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class ResumeBase(BaseModel):
    raw_text: str = Field(..., min_length=10)


class ResumeCreate(ResumeBase):
    pass


class ResumeUpdate(BaseModel):
    raw_text: Optional[str] = Field(None, min_length=10)


class ResumeResponse(ResumeBase):
    id: uuid.UUID
    user_id: uuid.UUID
    file_url: Optional[str] = None
    file_name: Optional[str] = None
    file_size: Optional[int] = None
    parsed_json: Optional[dict] = None
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True


class DocumentUploadResponse(BaseModel):
    document_id: uuid.UUID
    file_url: str
    message: str