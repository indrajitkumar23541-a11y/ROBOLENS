from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from app.models.task import TaskStatus


class TaskBase(BaseModel):
    title: str
    description: str
    instructions_md: str
    category: str
    expected_duration_min: int
    expected_duration_max: int
    reward_amount: float
    max_submissions: int = 1000


class TaskCreate(TaskBase):
    pass


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    title: str
    description: str
    category: str
    expected_duration_min: int
    expected_duration_max: int
    reward_amount: float
    status: TaskStatus
    version: int
    created_at: datetime


class TaskDetail(TaskResponse):
    instructions_md: str
    max_submissions: int


class TaskEligibility(BaseModel):
    task_id: str
    eligible: bool
    reason: Optional[str] = None
    remaining_submissions: int
