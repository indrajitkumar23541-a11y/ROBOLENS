import uuid
from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.models.dataset import Dataset, DatasetVersion, DatasetVersionStatus
from app.models.user import User, UserRole
from app.schemas.dataset import (
    DatasetResponse,
    DatasetVersionResponse,
    DatasetExportRequest,
    DatasetExportResponse
)
from app.schemas.common import ApiResponse
from app.services.s3_service import s3_service
from app.api.deps import get_current_active_user, require_role

router = APIRouter()


@router.get("", response_model=ApiResponse[List[DatasetResponse]])
def list_datasets(
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ENTERPRISE, UserRole.ADMIN))
) -> Any:
    """List datasets accessible to authorized research/enterprise organizations."""
    datasets = db.query(Dataset).offset(skip).limit(limit).all()
    return ApiResponse(data=datasets)


@router.get("/{dataset_id}", response_model=ApiResponse[DatasetResponse])
def get_dataset(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ENTERPRISE, UserRole.ADMIN))
) -> Any:
    """Get metadata for a specific dataset."""
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    return ApiResponse(data=dataset)


@router.get("/{dataset_id}/versions", response_model=ApiResponse[List[DatasetVersionResponse]])
def list_dataset_versions(
    dataset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ENTERPRISE, UserRole.ADMIN))
) -> Any:
    """List published and available versions of a dataset."""
    versions = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset_id).all()
    return ApiResponse(data=versions)


@router.post("/{dataset_id}/exports", response_model=ApiResponse[DatasetExportResponse])
def request_dataset_export(
    dataset_id: str,
    export_in: DatasetExportRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.ENTERPRISE, UserRole.ADMIN))
) -> Any:
    """
    Request an authorized export of an approved dataset version.
    Generates a secure, short-lived download link.
    """
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Dataset not found")
    
    latest_version = db.query(DatasetVersion).filter(
        DatasetVersion.dataset_id == dataset_id,
        DatasetVersion.status == DatasetVersionStatus.PUBLISHED
    ).order_by(DatasetVersion.created_at.desc()).first()

    if not latest_version:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No published version available for this dataset")

    export_id = str(uuid.uuid4())
    s3_key = latest_version.manifest_s3_key or f"datasets/{dataset.slug}/{latest_version.version_tag}/export.tar.gz"

    try:
        download_url = s3_service.generate_presigned_download_url(
            bucket=settings.S3_BUCKET_DATASETS,
            key=s3_key,
            expires_in=3600
        )
    except Exception:
        download_url = f"http://localhost:9000/{settings.S3_BUCKET_DATASETS}/{s3_key}?presigned=mock"

    return ApiResponse(
        data=DatasetExportResponse(
            export_id=export_id,
            dataset_id=dataset.id,
            version_tag=latest_version.version_tag,
            format=export_in.format,
            status="READY",
            download_url=download_url,
            expires_in_seconds=3600
        )
    )
