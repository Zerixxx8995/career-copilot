"""
Resume validator — input validation for resume uploads.
"""
from __future__ import annotations

from fastapi import HTTPException, UploadFile, status

ALLOWED_CONTENT_TYPES = {"application/pdf"}
MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB


def validate_resume_file(file: UploadFile) -> None:
    """
    Raise HTTP 422 if the uploaded file is not a valid PDF within size limits.
    """
    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid file type '{file.content_type}'. Only PDF files are accepted.",
        )

    if file.filename and not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="File must have a .pdf extension.",
        )
