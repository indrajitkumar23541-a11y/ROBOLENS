import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.database import Base, engine
import app.models  # Ensures all models are registered
from app.api.v1.api import api_router

# Setup logging
logging.basicConfig(
    level=settings.LOG_LEVEL,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("robolens")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan event handler: initialize database tables in development."""
    logger.info("Initializing ROBOLENS API tables...")
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schema initialized successfully.")
    except Exception as e:
        logger.warning(f"Could not connect to database on startup (may be starting up): {e}")
    yield
    logger.info("Shutting down ROBOLENS API...")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="ROBOLENS Backend API — Mobile-first Robotics Training Data Infrastructure",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    docs_url=f"{settings.API_V1_STR}/docs",
    redoc_url=f"{settings.API_V1_STR}/redoc",
    lifespan=lifespan
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handler for HTTP Exceptions matching Api-Specification.md
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "success": False,
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail
            },
            "request_id": request.headers.get("X-Request-ID", "req_unknown")
        }
    )


# Global Exception Handler for Validation Errors
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request parameters",
                "details": exc.errors()
            },
            "request_id": request.headers.get("X-Request-ID", "req_unknown")
        }
    )


import os
from fastapi.responses import HTMLResponse, Response

# Include API v1 Router
app.include_router(api_router, prefix=settings.API_V1_STR)


@app.get("/assets/{filename}", tags=["Assets"])
def get_asset(filename: str):
    """Serve static branding and logo assets."""
    assets_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets"))
    file_path = os.path.join(assets_dir, filename)
    if os.path.exists(file_path):
        media_type = "image/png" if filename.endswith(".png") else "image/svg+xml"
        with open(file_path, "rb") as f:
            return Response(content=f.read(), media_type=media_type)
    return Response(status_code=404)


@app.get("/workbench", response_class=HTMLResponse, tags=["Workbench"])
def workbench():
    """ROBOLENS Physical AI Developer Console and Mobile Workbench UI."""
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse("<h1>ROBOLENS — Every Action Teaches AI</h1>")


@app.get("/", tags=["Root"])
def root(request: Request):
    """
    ROBOLENS Gateway:
    Returns product metadata JSON for explicit API consumers,
    or renders the full UI for all browsers.
    """
    accept = request.headers.get("accept", "")
    if accept == "application/json" and "text/html" not in accept:
        return {
            "product": "ROBOLENS",
            "tagline": "Every Action Teaches AI.",
            "version": settings.VERSION,
            "docs": f"{settings.API_V1_STR}/docs",
            "workbench": "/workbench"
        }

    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())

    return {
        "product": "ROBOLENS",
        "tagline": "Every Action Teaches AI.",
        "version": settings.VERSION,
        "docs": f"{settings.API_V1_STR}/docs",
        "workbench": "/workbench"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
