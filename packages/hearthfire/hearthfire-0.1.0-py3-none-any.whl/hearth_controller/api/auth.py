"""
Authentication API endpoints for Hearth Controller.

Provides:
- POST /auth/login - Password-based login
- POST /auth/logout - Revoke current session
- POST /auth/refresh - Refresh access token
- PUT /auth/password - Change password
- POST /auth/bootstrap - First-time admin setup
- GET /auth/me - Current user info
- CRUD for API tokens (/auth/tokens)
"""

from datetime import datetime, timedelta, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy import select

from hearth_controller.api.deps import CurrentUser, DBSession
from hearth_controller.config import settings
from hearth_controller.db.models import APIToken, User
from hearth_controller.services import auth as auth_service

router = APIRouter()


# =============================================================================
# Request/Response Models
# =============================================================================


class LoginRequest(BaseModel):
    """Login request with username and password."""

    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=1)


class LoginResponse(BaseModel):
    """Login response with tokens and user info."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int  # seconds
    user: dict


class RefreshRequest(BaseModel):
    """Token refresh request."""

    refresh_token: str


class PasswordChangeRequest(BaseModel):
    """Password change request."""

    current_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)


class BootstrapRequest(BaseModel):
    """First-time admin setup request."""

    username: str = Field(..., min_length=1, max_length=64)
    password: str = Field(..., min_length=8)
    display_name: str | None = Field(None, max_length=128)


class TokenCreate(BaseModel):
    """API token creation request."""

    name: str = Field(..., min_length=1, max_length=128)
    expires_in_days: int | None = Field(None, ge=1, le=365)
    never_expires: bool = False


class TokenResponse(BaseModel):
    """API token info (without the raw token)."""

    id: str
    name: str
    prefix: str
    created_at: datetime
    expires_at: datetime | None


class TokenCreatedResponse(TokenResponse):
    """API token creation response (includes raw token)."""

    token: str  # Only returned on creation


class TokenListResponse(BaseModel):
    """List of API tokens."""

    tokens: list[TokenResponse]


class UserPublicResponse(BaseModel):
    """Public user information."""

    id: str
    username: str
    display_name: str | None
    role: str


# =============================================================================
# Authentication Endpoints
# =============================================================================


@router.post("/login", response_model=LoginResponse)
async def login(db: DBSession, body: LoginRequest) -> LoginResponse:
    """
    Authenticate with username and password.

    Returns access and refresh tokens for session-based authentication.
    Access tokens expire in 15 minutes, refresh tokens in 7 days.
    """
    # Find user by username
    user = await auth_service.get_user_by_username(db, body.username)

    if not user:
        # Use same error message to prevent username enumeration
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # Check if account is locked
    if auth_service.is_account_locked(user):
        raise HTTPException(
            status_code=status.HTTP_423_LOCKED,
            detail="账户已被锁定，请稍后再试",
        )

    # Check if user has a password set
    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="此账户未设置密码，请使用 API Token 登录",
        )

    # Verify password
    if not auth_service.verify_password(body.password, user.password_hash):
        # Record failed attempt
        is_locked = await auth_service.record_failed_login(db, user)
        if is_locked:
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail=f"登录失败次数过多，账户已锁定 {settings.lockout_minutes} 分钟",
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )

    # Check user status
    if user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="账户已被禁用",
        )

    # Reset failed login counter on success
    await auth_service.reset_failed_logins(db, user)

    # Create session tokens
    access_token, refresh_token, session_id, expires_at = await auth_service.create_session_tokens(
        db, user
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.session_access_minutes * 60,
        user={
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
        },
    )


_bearer_scheme = HTTPBearer(auto_error=True)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    db: DBSession,
    credentials: HTTPAuthorizationCredentials = Depends(_bearer_scheme),
) -> None:
    """
    Logout and revoke the current session.

    Revokes only the current session's tokens (access + refresh with same session_id).
    PATs (Personal Access Tokens) cannot be revoked via logout - use the token management API.
    """
    raw_token = credentials.credentials

    # Hash token and look up the APIToken record
    token_hash = auth_service.hash_token(raw_token)
    result = await db.execute(
        select(APIToken)
        .where(APIToken.token_hash == token_hash)
        .where(APIToken.revoked_at.is_(None))
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Only session_access tokens can be used to logout
    if token.kind != "session_access":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有 session token 可以通过 logout 撤销，PAT 请使用 token 管理 API",
        )

    # Revoke only this session (access + refresh tokens with same session_id)
    await auth_service.revoke_session(db, token.session_id)


@router.post("/refresh", response_model=LoginResponse)
async def refresh_token(db: DBSession, body: RefreshRequest) -> LoginResponse:
    """
    Refresh an access token using a refresh token.

    The old tokens are revoked and new ones are issued (token rotation).
    """
    # Verify refresh token
    token = await auth_service.verify_refresh_token(db, body.refresh_token)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效或已过期的刷新令牌",
        )

    # Get user
    user = await auth_service.get_user_by_id(db, token.user_id)

    if not user or user.status != "active":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户不存在或已被禁用",
        )

    # Revoke old session
    if token.session_id:
        await auth_service.revoke_session(db, token.session_id)

    # Create new session tokens
    access_token, refresh_token, session_id, expires_at = await auth_service.create_session_tokens(
        db, user
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.session_access_minutes * 60,
        user={
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
        },
    )


@router.put("/password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    db: DBSession,
    current_user: CurrentUser,
    body: PasswordChangeRequest,
) -> None:
    """
    Change the current user's password.

    Requires the current password for verification.
    All existing sessions will be revoked after password change.
    """
    # Verify current password
    if not current_user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="此账户未设置密码",
        )

    if not auth_service.verify_password(body.current_password, current_user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="当前密码错误",
        )

    # Validate new password
    if len(body.new_password) < settings.min_password_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"新密码至少需要 {settings.min_password_length} 个字符",
        )

    # Update password
    current_user.password_hash = auth_service.hash_password(body.new_password)
    current_user.password_changed_at = datetime.now(timezone.utc)

    # Revoke all existing sessions (force re-login)
    await auth_service.revoke_all_user_sessions(db, current_user.id)

    await db.commit()


@router.post("/bootstrap", response_model=LoginResponse)
async def bootstrap(db: DBSession, body: BootstrapRequest) -> LoginResponse:
    """
    First-time admin setup.

    Creates the initial admin user. Only works when no users exist in the system.
    Returns tokens for immediate login.
    """
    # Check if any users exist
    user_count = await auth_service.get_user_count(db)

    if user_count > 0:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="系统已初始化，无法再次执行 bootstrap",
        )

    # Validate password
    if len(body.password) < settings.min_password_length:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"密码至少需要 {settings.min_password_length} 个字符",
        )

    # Create admin user
    now = datetime.now(timezone.utc)
    user = User(
        id=uuid4().hex[:32],
        username=body.username,
        display_name=body.display_name or "Administrator",
        role="admin",
        status="active",
        password_hash=auth_service.hash_password(body.password),
        password_changed_at=now,
        created_at=now,
    )
    db.add(user)
    await db.flush()

    # Create session tokens for immediate login
    access_token, refresh_token, session_id, expires_at = await auth_service.create_session_tokens(
        db, user
    )

    return LoginResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=settings.session_access_minutes * 60,
        user={
            "id": user.id,
            "username": user.username,
            "display_name": user.display_name,
            "role": user.role,
        },
    )


@router.get("/me", response_model=UserPublicResponse)
async def get_current_user_info(current_user: CurrentUser) -> UserPublicResponse:
    """Get the current user's information."""
    return UserPublicResponse(
        id=current_user.id,
        username=current_user.username,
        display_name=current_user.display_name,
        role=current_user.role,
    )


# =============================================================================
# API Token Management
# =============================================================================


@router.post("/tokens", response_model=TokenCreatedResponse, status_code=status.HTTP_201_CREATED)
async def create_token(
    db: DBSession,
    current_user: CurrentUser,
    body: TokenCreate,
) -> TokenCreatedResponse:
    """
    Create a new API token for programmatic access.

    API tokens are long-lived (default 90 days) and meant for CLI/scripts.
    Admin users can create never-expiring tokens with never_expires=True.
    """
    # Mutual exclusion: never_expires and expires_in_days cannot both be set
    if body.never_expires and body.expires_in_days is not None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="不能同时设置 never_expires 和 expires_in_days",
        )

    # Permission check: only admin can create never-expiring tokens
    if body.never_expires and current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="只有管理员可以创建永不过期的 token",
        )

    raw_token, token_hash, prefix = auth_service.generate_token()

    # Determine expiration
    expires_at = None
    if body.never_expires:
        expires_at = None  # Never expires
    elif body.expires_in_days:
        expires_at = datetime.now(timezone.utc) + timedelta(days=body.expires_in_days)
    else:
        expires_at = datetime.now(timezone.utc) + timedelta(days=settings.token_default_expiry_days)

    token = APIToken(
        id=uuid4().hex[:32],
        user_id=current_user.id,
        name=body.name,
        token_hash=token_hash,
        prefix=prefix,
        kind="api",  # Explicitly mark as API token
        expires_at=expires_at,
    )
    db.add(token)
    await db.flush()

    return TokenCreatedResponse(
        id=token.id,
        name=token.name,
        prefix=prefix,
        token=raw_token,
        created_at=token.created_at,
        expires_at=expires_at,
    )


@router.get("/tokens", response_model=TokenListResponse)
async def list_tokens(
    db: DBSession,
    current_user: CurrentUser,
) -> TokenListResponse:
    """
    List all API tokens for the current user.

    Only shows API tokens (not session tokens).
    """
    result = await db.execute(
        select(APIToken)
        .where(APIToken.user_id == current_user.id)
        .where(APIToken.kind == "api")  # Only show API tokens
        .where(APIToken.revoked_at.is_(None))
        .order_by(APIToken.created_at.desc())
    )
    tokens = result.scalars().all()

    return TokenListResponse(
        tokens=[
            TokenResponse(
                id=t.id,
                name=t.name,
                prefix=t.prefix,
                created_at=t.created_at,
                expires_at=t.expires_at,
            )
            for t in tokens
        ]
    )


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    db: DBSession,
    current_user: CurrentUser,
    token_id: str,
) -> None:
    """Revoke an API token."""
    result = await db.execute(
        select(APIToken)
        .where(APIToken.id == token_id)
        .where(APIToken.user_id == current_user.id)
        .where(APIToken.revoked_at.is_(None))
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Token not found",
        )

    token.revoked_at = datetime.now(timezone.utc)
