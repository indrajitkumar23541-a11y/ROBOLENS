from typing import Any, Dict
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.core.database import get_db
from app.core.config import settings
from app.schemas.common import ApiResponse
import redis
import urllib.request

router = APIRouter()


@router.get("", response_model=ApiResponse[Dict[str, Any]])
def health_check(db: Session = Depends(get_db)) -> Any:
    """Check API and dependent service health (PostgreSQL, Redis, S3)."""
    health_status = {
        "status": "HEALTHY",
        "services": {
            "api": "UP",
            "database": "UNKNOWN",
            "redis": "UNKNOWN",
            "object_storage": "UNKNOWN"
        }
    }

    # 1. Database Check
    try:
        db.execute(text("SELECT 1"))
        health_status["services"]["database"] = "UP"
    except Exception as e:
        health_status["services"]["database"] = f"DOWN: {str(e)}"
        health_status["status"] = "DEGRADED"

    # 2. Redis Check
    try:
        r = redis.from_url(settings.REDIS_URL, socket_connect_timeout=0.5)
        r.ping()
        health_status["services"]["redis"] = "UP"
    except Exception as e:
        health_status["services"]["redis"] = f"DOWN: {str(e)}"
        health_status["status"] = "DEGRADED"

    # 3. S3 / MinIO Check (Fast HTTP Probe)
    try:
        req = urllib.request.Request(f"{settings.S3_ENDPOINT_URL}/minio/health/live")
        with urllib.request.urlopen(req, timeout=0.5) as resp:
            if resp.status == 200:
                health_status["services"]["object_storage"] = "UP"
            else:
                health_status["services"]["object_storage"] = f"STATUS_{resp.status}"
    except Exception as e:
        health_status["services"]["object_storage"] = "OFFLINE"
        health_status["status"] = "DEGRADED"

    return ApiResponse(data=health_status)
