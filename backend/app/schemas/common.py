from typing import Generic, Optional, TypeVar, Any
from pydantic import BaseModel, Field
import uuid

T = TypeVar("T")


class ApiError(BaseModel):
    code: str
    message: str
    details: Optional[Any] = None


class ApiResponse(BaseModel, Generic[T]):
    success: bool = True
    data: Optional[T] = None
    error: Optional[ApiError] = None
    request_id: str = Field(default_factory=lambda: f"req_{uuid.uuid4().hex[:12]}")

