"""Resume router — URL mapping only."""
from __future__ import annotations

from fastapi import APIRouter, Depends, UploadFile, File

from app.controllers.resume_controller import handle_resume_upload
from app.core.database import get_db
from app.middleware.auth_middleware import get_current_user_id
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter()


@router.post("", summary="Upload and parse resume PDF")
async def upload_resume(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    user_id: str = Depends(get_current_user_id),
):
    return await handle_resume_upload(db=db, user_id=user_id, file=file)
