from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.submission import Submission, SubmissionStatus
from app.models.task import Task
from app.models.annotation import Annotation, AnnotationSource
from app.models.review import QualityReview, ReviewDecision
from app.models.user import User, UserRole
from app.schemas.review import (
    AnnotationCreate,
    ReviewSubmitRequest,
    ReviewQueueItem
)
from app.schemas.submission import AnnotationResponse, QualityReviewResponse
from app.schemas.common import ApiResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter()


@router.get("/queue", response_model=ApiResponse[List[ReviewQueueItem]])
def get_review_queue(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN))
) -> Any:
    """Fetch submissions pending human quality verification (Status: IN_REVIEW)."""
    submissions = db.query(Submission).filter(
        Submission.status.in_([SubmissionStatus.IN_REVIEW, SubmissionStatus.PROCESSING])
    ).order_by(Submission.created_at.asc()).all()

    items = []
    for s in submissions:
        task = db.query(Task).filter(Task.id == s.task_id).first()
        anno_count = db.query(Annotation).filter(Annotation.submission_id == s.id).count()
        items.append(
            ReviewQueueItem(
                submission_id=s.id,
                episode_id=s.episode_id,
                task_id=s.task_id,
                task_title=task.title if task else "Unknown Task",
                category=task.category if task else "general",
                status=s.status.value,
                created_at=s.created_at,
                annotation_count=anno_count
            )
        )
    return ApiResponse(data=items)


@router.get("/submissions/{submission_id}/annotations", response_model=ApiResponse[List[AnnotationResponse]])
def get_submission_annotations(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """View all AI and human-verified annotations for a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    annotations = db.query(Annotation).filter(
        Annotation.submission_id == submission_id
    ).order_by(Annotation.start_time_ms.asc()).all()

    return ApiResponse(data=annotations)


@router.post("/submissions/{submission_id}/annotations", response_model=ApiResponse[AnnotationResponse], status_code=status.HTTP_201_CREATED)
def add_human_verified_annotation(
    submission_id: str,
    anno_in: AnnotationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN))
) -> Any:
    """
    Add or correct an action annotation during review.
    Guarantees source is marked as HUMAN_VERIFIED with reviewer attribution.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    # Get latest revision number
    latest_anno = db.query(Annotation).filter(
        Annotation.submission_id == submission_id
    ).order_by(Annotation.revision.desc()).first()
    next_rev = (latest_anno.revision + 1) if latest_anno else 1

    annotation = Annotation(
        submission_id=submission.id,
        label=anno_in.label,
        start_time_ms=anno_in.start_time_ms,
        end_time_ms=anno_in.end_time_ms,
        confidence=1.0,  # Human verified ground truth
        source=AnnotationSource.HUMAN_VERIFIED,
        model_name=f"reviewer:{current_user.id[:8]}",
        model_version="manual-correction",
        revision=next_rev
    )
    db.add(annotation)
    db.commit()
    db.refresh(annotation)
    return ApiResponse(data=annotation)


@router.post("/submissions/{submission_id}/reviews", response_model=ApiResponse[QualityReviewResponse])
def submit_quality_decision(
    submission_id: str,
    review_in: ReviewSubmitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.REVIEWER, UserRole.ADMIN))
) -> Any:
    """
    Submit final quality decision (APPROVED or REJECTED) on a submission.
    Transitions submission status and records audit decision.
    """
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    review = QualityReview(
        submission_id=submission.id,
        reviewer_id=current_user.id,
        decision=review_in.decision,
        rejection_reason=review_in.rejection_reason,
        feedback_notes=review_in.feedback_notes
    )
    db.add(review)

    if review_in.decision == ReviewDecision.APPROVED:
        submission.status = SubmissionStatus.APPROVED
    elif review_in.decision == ReviewDecision.REJECTED:
        submission.status = SubmissionStatus.REJECTED
        submission.rejection_reason = review_in.rejection_reason

    db.commit()
    db.refresh(review)
    return ApiResponse(data=review)


@router.get("/submissions/{submission_id}/reviews", response_model=ApiResponse[List[QualityReviewResponse]])
def get_submission_reviews(
    submission_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """View permitted review decisions and feedback notes for a submission."""
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if not submission:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Submission not found")

    if submission.user_id != current_user.id and current_user.role not in [UserRole.REVIEWER, UserRole.ADMIN]:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    reviews = db.query(QualityReview).filter(QualityReview.submission_id == submission_id).all()
    return ApiResponse(data=reviews)

