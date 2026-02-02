import secrets
from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select

from hearth_controller.api.deps import AdminUser, CurrentUser, DBSession
from hearth_controller.db.models import User
from hearth_controller.services.auth import hash_password, revoke_all_user_sessions

router = APIRouter()


class UserCreate(BaseModel):
    username: str = Field(..., min_length=1, max_length=64, pattern=r"^[a-zA-Z0-9_-]+$")
    display_name: str | None = Field(None, max_length=128)
    role: str = Field("user", pattern=r"^(user|admin)$")
    password: str | None = Field(None, min_length=1, max_length=128)


class UserUpdate(BaseModel):
    display_name: str | None = Field(None, max_length=128)
    role: str | None = Field(None, pattern=r"^(user|admin)$")
    status: str | None = Field(None, pattern=r"^(active|suspended)$")


class UserResponse(BaseModel):
    id: str
    username: str
    display_name: str | None
    role: str
    status: str
    created_at: datetime
    last_seen_at: datetime | None

    class Config:
        from_attributes = True


class UserListResponse(BaseModel):
    users: list[UserResponse]
    total: int


class ResetPasswordRequest(BaseModel):
    """Optional password for reset. If not provided, server generates one."""

    password: str | None = Field(None, min_length=8, max_length=128)


class ResetPasswordResponse(BaseModel):
    """One-time response containing the new password."""

    new_password: str
    message: str = "密码已重置。请妥善保存，此密码仅显示一次。"


@router.post("", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(
    db: DBSession,
    admin: AdminUser,
    body: UserCreate,
) -> UserResponse:
    """Create a new user (admin only)."""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == body.username))
    if result.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already exists",
        )

    user = User(
        id=uuid4().hex[:32],
        username=body.username,
        display_name=body.display_name,
        role=body.role,
        password_hash=hash_password(body.password) if body.password else None,
    )
    db.add(user)
    await db.flush()

    return UserResponse.model_validate(user)


@router.get("", response_model=UserListResponse)
async def list_users(
    db: DBSession,
    admin: AdminUser,
    limit: int = 50,
    offset: int = 0,
) -> UserListResponse:
    """List all users (admin only)."""
    result = await db.execute(
        select(User).order_by(User.created_at.desc()).limit(limit).offset(offset)
    )
    users = result.scalars().all()

    count_result = await db.execute(select(func.count(User.id)))
    total = count_result.scalar() or 0

    return UserListResponse(
        users=[UserResponse.model_validate(u) for u in users],
        total=total,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(
    db: DBSession,
    current_user: CurrentUser,
    user_id: str,
) -> UserResponse:
    """Get a user by ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse.model_validate(user)


@router.patch("/{user_id}", response_model=UserResponse)
async def update_user(
    db: DBSession,
    admin: AdminUser,
    user_id: str,
    body: UserUpdate,
) -> UserResponse:
    """Update a user (admin only)."""
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    if body.display_name is not None:
        user.display_name = body.display_name
    if body.role is not None:
        user.role = body.role
    if body.status is not None:
        user.status = body.status

    return UserResponse.model_validate(user)


@router.post("/{user_id}/reset-password", response_model=ResetPasswordResponse)
async def reset_password(
    db: DBSession,
    admin: AdminUser,
    user_id: str,
    body: ResetPasswordRequest | None = None,
) -> ResetPasswordResponse:
    """
    Reset a user's password (admin only).

    If password is not provided, a random password is generated.
    The new password is returned only once in this response.
    All session tokens for the user are revoked.
    """
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Generate or use provided password
    if body and body.password:
        new_password = body.password
    else:
        # Generate a secure random password (16 chars alphanumeric + symbols)
        new_password = secrets.token_urlsafe(12)  # ~16 chars

    # Update password hash
    user.password_hash = hash_password(new_password)
    user.password_changed_at = datetime.now(timezone.utc)

    # Clear lockout state
    user.failed_login_count = 0
    user.locked_until = None

    # Revoke all session tokens (but NOT PATs per plan)
    await revoke_all_user_sessions(db, user.id)

    await db.commit()

    return ResetPasswordResponse(new_password=new_password)
