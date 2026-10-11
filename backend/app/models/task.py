import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Integer, Float, DateTime, Enum as SQLEnum
from sqlalchemy.orm import relationship
import enum
from app.core.database import Base


class TaskStatus(str, enum.Enum):
    DRAFT = "DRAFT"
    ACTIVE = "ACTIVE"
    PAUSED = "PAUSED"
    ARCHIVED = "ARCHIVED"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    instructions_md = Column(Text, nullable=False)
    category = Column(String(100), index=True, nullable=False)
    expected_duration_min = Column(Integer, default=5, nullable=False)  # seconds
    expected_duration_max = Column(Integer, default=180, nullable=False)  # seconds
    reward_amount = Column(Float, default=0.0, nullable=False)
    status = Column(SQLEnum(TaskStatus), default=TaskStatus.ACTIVE, nullable=False)
    version = Column(Integer, default=1, nullable=False)
    max_submissions = Column(Integer, default=1000, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc), nullable=False)

    submissions = relationship("Submission", back_populates="task", cascade="all, delete-orphan")
