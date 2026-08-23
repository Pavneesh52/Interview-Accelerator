from fastapi import APIRouter
from app.api.v1 import auth, documents, analysis, interviews, video

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(documents.router, prefix="/documents", tags=["documents"])
api_router.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
api_router.include_router(interviews.router, prefix="/interviews", tags=["interviews"])
api_router.include_router(video.router, prefix="/video", tags=["video"])