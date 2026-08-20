from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
import uuid
import os
from datetime import datetime, timedelta

from app.db.session import get_db
from app.services.auth import get_current_user_dependency
from app.models.user import User
from app.models.analysis import AnalysisSession
from app.models.interview import Interview, InterviewStatus

router = APIRouter()


@router.post("/interviews/{interview_id}/video-token")
async def get_video_token(
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
    
    if interview.status not in [InterviewStatus.IN_PROGRESS, InterviewStatus.PAUSED]:
        raise HTTPException(status_code=400, detail="Interview not in progress")
    
    livekit_url = os.getenv("LIVEKIT_URL", "wss://your-livekit-server.com")
    livekit_api_key = os.getenv("LIVEKIT_API_KEY", "")
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "")
    
    if not livekit_api_key or not livekit_api_secret:
        raise HTTPException(status_code=503, detail="Video service not configured")
    
    from livekit import api
    
    room_name = f"interview-{interview_id}"
    participant_name = f"candidate-{current_user.id}"
    
    token = api.AccessToken(livekit_api_key, livekit_api_secret) \
        .with_identity(participant_name) \
        .with_name(current_user.full_name or current_user.email) \
        .with_grants(api.VideoGrants(
            room_join=True,
            room=room_name,
            can_publish=True,
            can_subscribe=True,
            can_publish_data=True,
        )) \
        .with_ttl(timedelta(hours=2)) \
        .to_jwt()
    
    return {
        "token": token,
        "url": livekit_url,
        "room_name": room_name,
    }