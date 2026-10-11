from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.review import ReviewDecision
from app.models.annotation import AnnotationSource


class AnnotationCreate(BaseModel):
    label: str
    start_time_ms: int
    end_time_ms: int
    notes: Optional[str] = None


class ReviewSubmitRequest(BaseModel):
    decision: ReviewDecision  # APPROVED or REJECTED
    rejection_reason: Optional[str] = None
    feedback_notes: Optional[str] = None


class ReviewQueueItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    submission_id: str
    episode_id: str
    task_id: str
    task_title: str
    category: str
    status: str
    created_at: datetime
    annotation_count: int
