import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models.task import Task, TaskStatus
from app.models.user import User, UserRole
from app.models.submission import Submission, SubmissionStatus, MediaAsset, AssetType, AssetStatus
from app.models.annotation import Annotation, AnnotationSource
from app.models.review import QualityReview, ReviewDecision
from workers.worker import process_single_submission


def test_end_to_end_worker_processing_and_reviewer_flow(client: TestClient, db_session: Session):
    # 1. Setup Task
    task = Task(
        id="test_task_pick_place",
        title="Cup Pick & Place",
        category="tabletop_manipulation",
        description="Pick up cup and place into tray",
        instructions_md="Detailed instructions",
        expected_duration_min=5,
        expected_duration_max=45,
        reward_amount=50.0,
        status=TaskStatus.ACTIVE,
        version=1,
        max_submissions=100
    )
    db_session.add(task)

    # 2. Setup Contributor and Reviewer users
    contributor = User(
        id="user_contributor_1",
        email="contributor1@test.com",
        hashed_password="hashed_pw",
        role=UserRole.CONTRIBUTOR,
        is_active=True
    )
    reviewer = User(
        id="user_reviewer_1",
        email="reviewer1@test.com",
        hashed_password="hashed_pw",
        role=UserRole.REVIEWER,
        is_active=True
    )
    db_session.add(contributor)
    db_session.add(reviewer)
    db_session.commit()

    # 3. Create a Submission in PROCESSING status with MediaAsset
    submission = Submission(
        id="sub_test_worker_1",
        task_id=task.id,
        user_id=contributor.id,
        episode_id="ep_test_worker_1",
        status=SubmissionStatus.PROCESSING,
        task_version=1
    )
    db_session.add(submission)
    db_session.flush()

    media_asset = MediaAsset(
        submission_id=submission.id,
        asset_type=AssetType.RAW_VIDEO,
        s3_bucket="robolens-raw-media",
        s3_key=f"raw/{task.id}/{submission.episode_id}/video.mp4",
        file_size_bytes=1048576,
        mime_type="video/mp4",
        status=AssetStatus.UPLOADED
    )
    db_session.add(media_asset)
    db_session.commit()

    # 4. Execute Autonomous Worker Processing on this submission
    success = process_single_submission(
        submission_id=submission.id,
        scratch_dir="./scratch/test_worker_media",
        db_session=db_session
    )
    assert success is True

    # 5. Verify Database Records
    db_session.refresh(submission)
    assert submission.status in [SubmissionStatus.APPROVED, SubmissionStatus.IN_REVIEW]

    # Verify MediaAsset metadata updated
    db_session.refresh(media_asset)
    assert media_asset.status == AssetStatus.VERIFIED
    assert media_asset.duration_seconds is not None
    assert media_asset.duration_seconds > 0

    # Verify AI Annotations created with AI_GENERATED provenance
    annotations = db_session.query(Annotation).filter(
        Annotation.submission_id == submission.id
    ).all()
    assert len(annotations) > 0
    for a in annotations:
        assert a.source == AnnotationSource.AI_GENERATED
        assert a.confidence is not None
        assert a.start_time_ms < a.end_time_ms

    # Verify Quality Review record created
    q_review = db_session.query(QualityReview).filter(
        QualityReview.submission_id == submission.id
    ).first()
    assert q_review is not None
    assert q_review.decision in [ReviewDecision.PASS, ReviewDecision.NEEDS_REVIEW]
