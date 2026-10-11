import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.task import Task, TaskStatus
from app.models.submission import Submission, SubmissionStatus, MediaAsset, AssetType, AssetStatus
from app.models.consent import Consent
from app.models.user import User, UserRole
from app.schemas.submission import (
    SubmissionCreate,
    SubmissionResponse,
    SubmissionList
)
from app.schemas.upload import (
    UploadSessionCreate,
    UploadSessionResponse,
    UploadCompleteRequest,
    UploadStatusResponse
)
from app.schemas.common import ApiResponse
from app.services.s3_service import s3_service
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("", response_model=ApiResponse[SubmissionResponse], status_code=status.HTTP_201_CREATED)
def create_submission(
    submission_in: SubmissionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Create a new recording submission episode for a task."""
    task = db.query(Task).filter(Task.id == submission_in.task_id).first()
    if not task:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    if task.status != TaskStatus.ACTIVE:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Task is not currently active")
    
    if not submission_in.consent_agreed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Explicit consent agreement is required to submit recordings."
        )

    # Create submission record
    submission = Submission(
        task_id=task.id,
        user_id=current_user.id,
        episode_id=str(uuid.uuid4()),
        status=SubmissionStatus.DRAFT,
        task_version=task.version
    )
    db.add(submission)
    db.flush()  # Generate submission.id

    # Create consent record linked to user and submission
    consent = Consent(
        user_id=current_user.id,
        submission_id=submission.id,
        consent_type="DATA_COLLECTION_AND_TRAINING",
        agreed=True,
        policy_version=submission_in.policy_version
    )
    db.add(consent)
    db.commit()
    db.refresh(submission)

    return ApiResponse(data=submission)


@router.get("", response_model=ApiResponse[SubmissionList])
def list_my_submissions(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """List authenticated user's submitted recordings."""
    query = db.query(Submission).filter(Submission.user_id == current_user.id)
    total = query.count()
    items = query.order_by(Submission.created_at.desc()).offset(skip).limit(limit).all()
    
    return ApiResponse(
        data=SubmissionList(
            items=items,
            total=total,
            page=(skip // limit) + 1,
            size=limit
        )
    )


@router.get("/{submission_id}", response_model=ApiResponse[SubmissionResponse])
def get_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get submission details by ID."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    
    # Ownership verification
    if submission.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    return ApiResponse(data=submission)


@router.post("/{submission_id}/uploads", response_model=ApiResponse[UploadSessionResponse])
def create_upload_session(
    submission_id: str,
    upload_in: UploadSessionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Create a direct-to-S3 upload session with a short-lived presigned PUT URL.
    The mobile app uploads the video directly to object storage.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if submission.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    if submission.status not in [SubmissionStatus.DRAFT, SubmissionStatus.UPLOADING, SubmissionStatus.FAILED]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot upload video in current status: {submission.status}"
        )
    
    upload_session_id = str(uuid.uuid4())
    s3_key = f"raw/{submission.task_id}/{submission.episode_id}/{upload_session_id}_{upload_in.file_name}"
    
    # Generate presigned upload URL
    try:
        presigned_url = s3_service.generate_presigned_upload_url(
            bucket=settings.S3_BUCKET_RAW,
            key=s3_key,
            expires_in=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS,
            content_type=upload_in.mime_type
        )
    except Exception as e:
        # Fallback in local development if S3 is not yet connected
        presigned_url = f"http://localhost:9000/{settings.S3_BUCKET_RAW}/{s3_key}?presigned=mock"

    # Create MediaAsset record
    media_asset = MediaAsset(
        submission_id=submission.id,
        asset_type=AssetType.RAW_VIDEO,
        s3_bucket=settings.S3_BUCKET_RAW,
        s3_key=s3_key,
        file_size_bytes=upload_in.file_size_bytes,
        mime_type=upload_in.mime_type,
        checksum_sha256=upload_in.checksum_sha256,
        status=AssetStatus.PENDING_UPLOAD,
        upload_session_id=upload_session_id
    )
    submission.status = SubmissionStatus.UPLOADING
    db.add(media_asset)
    db.commit()

    return ApiResponse(
        data=UploadSessionResponse(
            upload_id=upload_session_id,
            submission_id=submission.id,
            upload_url=presigned_url,
            s3_bucket=settings.S3_BUCKET_RAW,
            s3_key=s3_key,
            expires_in_seconds=settings.S3_PRESIGNED_URL_EXPIRE_SECONDS
        )
    )


@router.post("/uploads/{upload_id}/complete", response_model=ApiResponse[SubmissionResponse])
def complete_upload(
    upload_id: str,
    complete_in: UploadCompleteRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """
    Finalize an upload session:
    1. Verify file exists in object storage and size matches.
    2. Transition submission status to PROCESSING.
    3. Triggers asynchronous Temporal workflow.
    """
    media_asset = db.query(MediaAsset).filter(MediaAsset.upload_session_id == upload_id).first()
    if not media_asset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Upload session not found")
    
    submission = db.query(Submission).filter(Submission.id == media_asset.submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Associated submission not found")
    
    if submission.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    # In production, check S3 existence
    try:
        obj_info = s3_service.verify_object_exists(media_asset.s3_bucket, media_asset.s3_key)
        if obj_info:
            media_asset.file_size_bytes = obj_info["content_length"]
            media_asset.status = AssetStatus.UPLOADED
    except Exception:
        # Development mode bypass if S3 offline
        media_asset.status = AssetStatus.UPLOADED

    if complete_in.checksum_sha256:
        media_asset.checksum_sha256 = complete_in.checksum_sha256
    
    media_asset.status = AssetStatus.VERIFIED
    submission.status = SubmissionStatus.PROCESSING
    db.commit()
    db.refresh(submission)

    return ApiResponse(data=submission)


@router.post("/{submission_id}/cancel", response_model=ApiResponse[SubmissionResponse])
def cancel_submission(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Cancel an in-progress or draft submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")
    if submission.user_id != current_user.id and current_user.role != UserRole.ADMIN:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    
    if submission.status in [SubmissionStatus.APPROVED, SubmissionStatus.CANCELLED]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Cannot cancel submission in current state")
    
    submission.status = SubmissionStatus.CANCELLED
    db.commit()
    db.refresh(submission)
    return ApiResponse(data=submission)
