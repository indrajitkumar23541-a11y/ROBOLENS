from typing import Any, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.task import Task, TaskStatus
from app.models.submission import Submission
from app.models.user import User, UserRole
from app.schemas.task import TaskResponse, TaskDetail, TaskEligibility, TaskCreate
from app.schemas.common import ApiResponse
from app.api.deps import get_current_active_user, require_role

router = APIRouter()


@router.get("", response_model=ApiResponse[List[TaskResponse]])
def list_tasks(
    category: str = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """List all active tasks available for contribution."""
    query = db.query(Task).filter(Task.status == TaskStatus.ACTIVE)
    if category:
        query = query.filter(Task.category == category)
    tasks = query.offset(skip).limit(limit).all()
    return ApiResponse(data=tasks)


@router.get("/{task_id}", response_model=ApiResponse[TaskDetail])
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Get complete task details including markdown instructions."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    return ApiResponse(data=task)


@router.get("/{task_id}/eligibility", response_model=ApiResponse[TaskEligibility])
def check_task_eligibility(
    task_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
) -> Any:
    """Check whether current authenticated contributor is eligible to record this task."""
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    if task.status != TaskStatus.ACTIVE:
        return ApiResponse(
            data=TaskEligibility(
                task_id=task.id,
                eligible=False,
                reason="Task is no longer active",
                remaining_submissions=0
            )
        )
    
    # Check total submissions count
    current_count = db.query(Submission).filter(Submission.task_id == task_id).count()
    remaining = max(0, task.max_submissions - current_count)
    if remaining <= 0:
        return ApiResponse(
            data=TaskEligibility(
                task_id=task.id,
                eligible=False,
                reason="Task has reached its submission quota",
                remaining_submissions=0
            )
        )

    return ApiResponse(
        data=TaskEligibility(
            task_id=task.id,
            eligible=True,
            reason=None,
            remaining_submissions=remaining
        )
    )


@router.post("", response_model=ApiResponse[TaskDetail], status_code=status.HTTP_201_CREATED)
def create_task(
    task_in: TaskCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(require_role(UserRole.ADMIN))
) -> Any:
    """Create a new data collection task (Admin only)."""
    task = Task(
        title=task_in.title,
        description=task_in.description,
        instructions_md=task_in.instructions_md,
        category=task_in.category,
        expected_duration_min=task_in.expected_duration_min,
        expected_duration_max=task_in.expected_duration_max,
        reward_amount=task_in.reward_amount,
        max_submissions=task_in.max_submissions,
        status=TaskStatus.ACTIVE,
        version=1
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return ApiResponse(data=task)
