from fastapi.testclient import TestClient
from app.models.task import Task, TaskStatus


def test_root_endpoint(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["product"] == "ROBOLENS"
    assert data["tagline"] == "Every Action Teaches AI."


def test_health_endpoint(client: TestClient):
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    res = response.json()
    assert res["success"] is True
    assert "services" in res["data"]
    assert res["data"]["services"]["api"] == "UP"


def test_auth_registration_and_login(client: TestClient):
    # 1. Register new contributor
    register_payload = {
        "email": "contributor@example.com",
        "password": "Password123!",
        "full_name": "Test Contributor"
    }
    reg_response = client.post("/api/v1/auth/register", json=register_payload)
    assert reg_response.status_code == 201
    reg_data = reg_response.json()
    assert reg_data["success"] is True
    assert reg_data["data"]["email"] == "contributor@example.com"
    assert reg_data["data"]["role"] == "CONTRIBUTOR"

    # 2. Login
    login_response = client.post(
        "/api/v1/auth/login",
        data={"username": "contributor@example.com", "password": "Password123!"}
    )
    assert login_response.status_code == 200
    login_data = login_response.json()
    assert login_data["success"] is True
    assert "access_token" in login_data["data"]
    assert "refresh_token" in login_data["data"]
    token = login_data["data"]["access_token"]

    # 3. Access profile with token
    profile_response = client.get(
        "/api/v1/auth/users/me",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert profile_response.status_code == 200
    profile_data = profile_response.json()
    assert profile_data["data"]["email"] == "contributor@example.com"


def test_task_submission_and_upload_flow(client: TestClient, db_session):
    # 1. Seed a sample task in DB
    sample_task = Task(
        id="task_cup_manipulation",
        title="Cup Pick and Place",
        description="Pick up cup from table and place into tray",
        instructions_md="## Instructions\n1. Ensure good lighting\n2. Grasp cup firmly",
        category="tabletop_manipulation",
        expected_duration_min=5,
        expected_duration_max=60,
        reward_amount=15.0,
        status=TaskStatus.ACTIVE,
        version=1,
        max_submissions=100
    )
    db_session.add(sample_task)
    db_session.commit()

    # 2. Register & login contributor
    reg_res = client.post("/api/v1/auth/register", json={
        "email": "worker@example.com",
        "password": "Password123!",
        "full_name": "Task Worker"
    })
    assert reg_res.status_code == 201

    login_res = client.post("/api/v1/auth/login", data={
        "username": "worker@example.com",
        "password": "Password123!"
    })
    token = login_res.json()["data"]["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 3. Check task eligibility
    elig_res = client.get(f"/api/v1/tasks/{sample_task.id}/eligibility", headers=headers)
    assert elig_res.status_code == 200
    assert elig_res.json()["data"]["eligible"] is True

    # 4. Create submission with explicit consent
    sub_res = client.post("/api/v1/submissions", json={
        "task_id": sample_task.id,
        "consent_agreed": True,
        "policy_version": "1.0"
    }, headers=headers)
    assert sub_res.status_code == 201
    sub_data = sub_res.json()["data"]
    assert sub_data["status"] == "DRAFT"
    assert "episode_id" in sub_data
    submission_id = sub_data["id"]

    # 5. Request direct S3 upload session
    upload_res = client.post(f"/api/v1/submissions/{submission_id}/uploads", json={
        "file_name": "demonstration.mp4",
        "file_size_bytes": 10485760,
        "mime_type": "video/mp4"
    }, headers=headers)
    assert upload_res.status_code == 200
    upload_data = upload_res.json()["data"]
    assert "upload_url" in upload_data
    assert upload_data["submission_id"] == submission_id
    assert "s3_key" in upload_data
    upload_id = upload_data["upload_id"]

    # 6. Complete upload notification
    complete_res = client.post(f"/api/v1/submissions/uploads/{upload_id}/complete", json={
        "checksum_sha256": "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    }, headers=headers)
    assert complete_res.status_code == 200
    assert complete_res.json()["data"]["status"] == "PROCESSING"
