import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.models.submission import Submission, SubmissionStatus
from app.models.dataset import Dataset, DatasetVersion, DatasetVersionStatus
from app.services.dataset_export_service import dataset_export_service


@pytest.fixture
def enterprise_client():
    client = TestClient(app)
    db = SessionLocal()
    try:
        # Create enterprise user
        user = db.query(User).filter(User.email == "research@physical-ai.org").first()
        if not user:
            user = User(
                email="research@physical-ai.org",
                hashed_password="mockpassword",
                full_name="Physical AI Research Lab",
                role=UserRole.ENTERPRISE,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)

        token = create_access_token(user.id)
        client.headers.update({"Authorization": f"Bearer {token}"})
        return client, user
    finally:
        db.close()


def test_dataset_export_manifest_and_lerobot_format(enterprise_client):
    client, user = enterprise_client
    db = SessionLocal()
    try:
        dataset = db.query(Dataset).filter(Dataset.slug == "mobile-manipulation-v1").first()
        if not dataset:
            dataset = Dataset(
                name="Mobile Manipulation Benchmark",
                slug="mobile-manipulation-v1",
                description="Ego-centric physical AI manipulation dataset",
                license="CC-BY-4.0"
            )
            db.add(dataset)
            db.flush()

        version = db.query(DatasetVersion).filter(DatasetVersion.dataset_id == dataset.id).first()
        if not version:
            version = DatasetVersion(
                dataset_id=dataset.id,
                version_tag="v1.0.0",
                status=DatasetVersionStatus.PUBLISHED,
                total_episodes=1,
                manifest_s3_key=f"datasets/{dataset.slug}/v1.0.0/export.tar.gz"
            )
            db.add(version)
            db.commit()
            db.refresh(version)

        # 1. Test service manifest generation directly
        manifest = dataset_export_service.generate_export_manifest(
            db=db,
            dataset=dataset,
            version=version,
            format_type="LEROBOT"
        )
        assert manifest["dataset_info"]["name"] == dataset.name
        assert manifest["dataset_info"]["format"] == "LEROBOT"
        assert "lerobot_features" in manifest
        assert "episodes" in manifest

        # 2. Test export API endpoint
        resp = client.post(
            f"/api/v1/datasets/{dataset.id}/exports",
            json={"format": "LEROBOT"}
        )
        assert resp.status_code == 200
        data = resp.json()["data"]
        assert data["format"] == "LEROBOT"
        assert data["status"] == "READY"
        assert "download_url" in data
        assert data["version_tag"] == version.version_tag
    finally:
        db.close()
