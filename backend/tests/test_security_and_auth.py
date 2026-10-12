import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.core.database import SessionLocal
from app.core.security import create_access_token
from app.models.user import User, UserRole
from app.models.task import Task, TaskStatus
from app.models.submission import Submission, SubmissionStatus


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def contributor_token():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_contributor@robolens.ai").first()
        if not user:
            user = User(
                email="test_contributor@robolens.ai",
                hashed_password="mockhashedpassword",
                full_name="Test Contributor",
                role=UserRole.CONTRIBUTOR,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return create_access_token(user.id)
    finally:
        db.close()


@pytest.fixture
def reviewer_token():
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.email == "test_reviewer@robolens.ai").first()
        if not user:
            user = User(
                email="test_reviewer@robolens.ai",
                hashed_password="mockhashedpassword",
                full_name="Test Reviewer",
                role=UserRole.REVIEWER,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        return create_access_token(user.id)
    finally:
        db.close()


def test_unauthenticated_requests_blocked(client):
    """Verify private endpoints reject requests without valid Bearer tokens."""
    # 1. Tasks
    resp = client.get("/api/v1/tasks")
    assert resp.status_code == 401

    # 2. Submissions
    resp = client.get("/api/v1/submissions")
    assert resp.status_code == 401

    # 3. Reviews Queue
    resp = client.get("/api/v1/reviews/queue")
    assert resp.status_code == 401


def test_role_based_access_control(client, contributor_token, reviewer_token):
    """Verify contributors cannot access Reviewer/Admin endpoints."""
    # Contributor cannot access review queue
    resp = client.get(
        "/api/v1/reviews/queue",
        headers={"Authorization": f"Bearer {contributor_token}"}
    )
    assert resp.status_code == 403

    # Reviewer can access review queue
    resp2 = client.get(
        "/api/v1/reviews/queue",
        headers={"Authorization": f"Bearer {reviewer_token}"}
    )
    assert resp2.status_code == 200
    assert resp2.json()["success"] is True


def test_consent_enforcement_on_submission(client, contributor_token):
    """Verify submitting without explicit consent is rejected with 400 Bad Request."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.status == TaskStatus.ACTIVE).first()
        if not task:
            task = Task(
                id="task_seed_security",
                title="Seed Security Test Task",
                description="Seed task for security and consent verification",
                instructions_md="Follow prompt instructions",
                category="tabletop_manipulation",
                expected_duration_min=5,
                expected_duration_max=60,
                reward_amount=10.0,
                status=TaskStatus.ACTIVE,
                version=1,
                max_submissions=100
            )
            db.add(task)
            db.commit()
            db.refresh(task)

        # Attempt submission with consent_agreed = False
        payload = {
            "task_id": task.id,
            "consent_agreed": False,
            "policy_version": "1.0"
        }
        resp = client.post(
            "/api/v1/submissions",
            json=payload,
            headers={"Authorization": f"Bearer {contributor_token}"}
        )
        assert resp.status_code == 400
        assert "consent" in resp.json()["error"]["message"].lower()
    finally:
        db.close()


def test_task_eligibility_and_processing_endpoints(client, contributor_token):
    """Verify task eligibility check and submission processing status endpoints."""
    db = SessionLocal()
    try:
        task = db.query(Task).filter(Task.status == TaskStatus.ACTIVE).first()
        if not task:
            task = Task(
                id="task_seed_eligibility",
                title="Seed Eligibility Test Task",
                description="Seed task for eligibility verification",
                instructions_md="Follow prompt instructions",
                category="tabletop_manipulation",
                expected_duration_min=5,
                expected_duration_max=60,
                reward_amount=10.0,
                status=TaskStatus.ACTIVE,
                version=1,
                max_submissions=100
            )
            db.add(task)
            db.commit()
            db.refresh(task)

        # Check eligibility
        resp = client.get(
            f"/api/v1/tasks/{task.id}/eligibility",
            headers={"Authorization": f"Bearer {contributor_token}"}
        )
        assert resp.status_code == 200
        assert resp.json()["data"]["eligible"] is True

        # Create valid submission
        sub_resp = client.post(
            "/api/v1/submissions",
            json={"task_id": task.id, "consent_agreed": True, "policy_version": "1.0"},
            headers={"Authorization": f"Bearer {contributor_token}"}
        )
        assert sub_resp.status_code == 201
        sub_id = sub_resp.json()["data"]["id"]

        # Check processing status
        proc_resp = client.get(
            f"/api/v1/submissions/{sub_id}/processing",
            headers={"Authorization": f"Bearer {contributor_token}"}
        )
        assert proc_resp.status_code == 200
        proc_data = proc_resp.json()["data"]
        assert proc_data["submission_id"] == sub_id
        assert proc_data["current_stage"] in ["RECEIVE_VERIFY", "PREPROCESS", "AI_ANALYSIS"]

        # Check reviews list
        rev_resp = client.get(
            f"/api/v1/submissions/{sub_id}/reviews",
            headers={"Authorization": f"Bearer {contributor_token}"}
        )
        assert rev_resp.status_code == 200
        assert isinstance(rev_resp.json()["data"], list)
    finally:
        db.close()
