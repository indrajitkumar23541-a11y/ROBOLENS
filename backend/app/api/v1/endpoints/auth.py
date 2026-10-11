from datetime import timedelta
from typing import Any
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_token
)
from app.models.user import User, UserRole
from app.schemas.auth import (
    UserRegister,
    TokenResponse,
    TokenRefresh,
    UserProfile,
    UserUpdate
)
from app.schemas.common import ApiResponse
from app.api.deps import get_current_active_user

router = APIRouter()


@router.post("/register", response_model=ApiResponse[UserProfile], status_code=status.HTTP_201_CREATED)
def register(user_in: UserRegister, db: Session = Depends(get_db)) -> Any:
    """Create a new contributor account."""
    existing_user = db.query(User).filter(User.email == user_in.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="A user with this email already exists."
        )
    
    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.CONTRIBUTOR,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return ApiResponse(data=user)


@router.post("/login", response_model=ApiResponse[TokenResponse])
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
) -> Any:
    """Authenticate a user using OAuth2 form data (or standard username/password)."""
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )
    
    access_token = create_access_token(user.id)
    refresh_token = create_refresh_token(user.id)
    return ApiResponse(
        data=TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/refresh", response_model=ApiResponse[TokenResponse])
def refresh_token(token_in: TokenRefresh, db: Session = Depends(get_db)) -> Any:
    """Renew an access token using a valid refresh token."""
    payload = decode_token(token_in.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    user_id = payload.get("sub")
    user = db.query(User).filter(User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    new_access_token = create_access_token(user.id)
    new_refresh_token = create_refresh_token(user.id)
    return ApiResponse(
        data=TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
    )


@router.post("/logout", response_model=ApiResponse[dict])
def logout(current_user: User = Depends(get_current_active_user)) -> Any:
    """Revoke the current session."""
    return ApiResponse(data={"message": "Logged out successfully"})


@router.get("/users/me", response_model=ApiResponse[UserProfile])
def get_current_user_profile(current_user: User = Depends(get_current_active_user)) -> Any:
    """Get profile of current authenticated user."""
    return ApiResponse(data=current_user)


@router.patch("/users/me", response_model=ApiResponse[UserProfile])
def update_current_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
) -> Any:
    """Update profile fields for the authenticated user."""
    if user_update.full_name is not None:
        current_user.full_name = user_update.full_name
    db.commit()
    db.refresh(current_user)
    return ApiResponse(data=current_user)
