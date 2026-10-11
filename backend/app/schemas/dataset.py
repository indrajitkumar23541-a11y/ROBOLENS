from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.models.dataset import DatasetVersionStatus


class DatasetResponse(BaseModel):
    id: str
    name: str
    slug: str
    description: str
    license: str
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetVersionResponse(BaseModel):
    id: str
    dataset_id: str
    version_tag: str
    status: DatasetVersionStatus
    total_episodes: int
    created_at: datetime

    class Config:
        from_attributes = True


class DatasetExportRequest(BaseModel):
    format: str = "LEROBOT"  # LEROBOT, RLDS, JSON_MANIFEST


class DatasetExportResponse(BaseModel):
    export_id: str
    dataset_id: str
    version_tag: str
    format: str
    status: str
    download_url: Optional[str] = None
    expires_in_seconds: Optional[int] = None
