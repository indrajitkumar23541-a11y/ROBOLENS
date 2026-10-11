from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.submission import AssetStatus


class UploadSessionCreate(BaseModel):
    file_name: str
    file_size_bytes: int
    mime_type: str = "video/mp4"
    checksum_sha256: Optional[str] = None


class UploadSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    submission_id: str
    upload_url: str
    s3_bucket: str
    s3_key: str
    expires_in_seconds: int


class UploadCompleteRequest(BaseModel):
    checksum_sha256: Optional[str] = None
    actual_file_size: Optional[int] = None


class UploadStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    upload_id: str
    submission_id: str
    status: AssetStatus
    file_size_bytes: int
    s3_key: str
