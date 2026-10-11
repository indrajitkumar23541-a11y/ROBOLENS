from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.submission import SubmissionStatus, AssetType, AssetStatus
from app.models.annotation import AnnotationSource
from app.models.review import ReviewDecision


class MediaAssetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    asset_type: AssetType
    file_size_bytes: int
    mime_type: str
    duration_seconds: Optional[float] = None
    width: Optional[int] = None
    height: Optional[int] = None
    fps: Optional[float] = None
    status: AssetStatus
    created_at: datetime


class AnnotationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    label: str
    start_time_ms: int
    end_time_ms: int
    confidence: Optional[float] = None
    source: AnnotationSource
    model_name: Optional[str] = None
    model_version: Optional[str] = None
    revision: int
    created_at: datetime


class QualityReviewResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    decision: ReviewDecision
    rejection_reason: Optional[str] = None
    feedback_notes: Optional[str] = None
    created_at: datetime


class SubmissionCreate(BaseModel):
    task_id: str
    consent_agreed: bool = True
    policy_version: str = "1.0"


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    task_id: str
    user_id: str
    episode_id: str
    status: SubmissionStatus
    task_version: int
    rejection_reason: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    media_assets: List[MediaAssetResponse] = []
    annotations: List[AnnotationResponse] = []
    quality_reviews: List[QualityReviewResponse] = []


class SubmissionList(BaseModel):
    items: List[SubmissionResponse]
    total: int
    page: int
    size: int
