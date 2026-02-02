"""
Authentication service for Hearth Controller.

Provides:
- Password hashing and verification (Argon2id)
- API token generation and validation
- Session token management (access + refresh tokens)
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from hearth_controller.config import settings
from hearth_controller.db.models import APIToken, User

# Argon2id password hasher with secure defaults
_password_hasher = PasswordHasher()

# Token kind type for type safety
TokenKind = Literal["api", "session_access", "session_refresh"]


# =============================================================================
# Password Hashing (Argon2id)
# =============================================================================


def hash_password(password: str) -> str:
    """
    Hash a password using Argon2id algorithm.

    Args:
        password: Plain text password

    Returns:
        Argon2id hash string (includes salt and parameters)
    """
    return _password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """
    Verify a password against its Argon2id hash.

    Args:
        password: Plain text password to verify
        password_hash: Stored Argon2id hash

    Returns:
        True if password matches, False otherwise
    """
    try:
        _password_hasher.verify(password_hash, password)
        return True
    except VerifyMismatchError:
        return False


def password_needs_rehash(password_hash: str) -> bool:
    """
    Check if a password hash needs to be rehashed (parameters outdated).

    Args:
        password_hash: Stored Argon2id hash

    Returns:
        True if rehashing is recommended
    """
    return _password_hasher.check_needs_rehash(password_hash)


# =============================================================================
# Token Generation
# =============================================================================


def generate_token() -> tuple[str, str, str]:
    """
    Generate a new API token.

    Returns:
        Tuple of (raw_token, token_hash, prefix)
    """
    raw_token = f"{settings.token_prefix}{secrets.token_urlsafe(settings.token_bytes)}"
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    prefix = raw_token[:8]
    return raw_token, token_hash, prefix


def hash_token(raw_token: str) -> str:
    """Hash a raw token using SHA256."""
    return hashlib.sha256(raw_token.strip().encode()).hexdigest()


def generate_session_id() -> str:
    """Generate a unique session identifier."""
    return secrets.token_urlsafe(16)


# =============================================================================
# Session Token Creation
# =============================================================================


async def create_session_tokens(
    db: AsyncSession,
    user: User,
) -> tuple[str, str, str, datetime]:
    """
    Create a new session token pair (access + refresh) for password login.

    Args:
        db: Database session
        user: Authenticated user

    Returns:
        Tuple of (access_token, refresh_token, session_id, access_expires_at)
    """
    session_id = generate_session_id()
    now = datetime.now(timezone.utc)

    # Create access token (short-lived)
    access_token, access_hash, access_prefix = generate_token()
    access_expires = now + timedelta(minutes=settings.session_access_minutes)

    access_token_obj = APIToken(
        id=secrets.token_urlsafe(16),
        user_id=user.id,
        name="Session Access Token",
        token_hash=access_hash,
        prefix=access_prefix,
        kind="session_access",
        session_id=session_id,
        created_at=now,
        expires_at=access_expires,
    )
    db.add(access_token_obj)

    # Create refresh token (longer-lived)
    refresh_token, refresh_hash, refresh_prefix = generate_token()
    refresh_expires = now + timedelta(days=settings.session_refresh_days)

    refresh_token_obj = APIToken(
        id=secrets.token_urlsafe(16),
        user_id=user.id,
        name="Session Refresh Token",
        token_hash=refresh_hash,
        prefix=refresh_prefix,
        kind="session_refresh",
        session_id=session_id,
        created_at=now,
        expires_at=refresh_expires,
    )
    db.add(refresh_token_obj)

    await db.commit()

    return access_token, refresh_token, session_id, access_expires


# =============================================================================
# Token Verification
# =============================================================================


async def verify_token(
    db: AsyncSession,
    raw_token: str,
    allowed_kinds: tuple[TokenKind, ...] = ("api", "session_access"),
) -> User | None:
    """
    Verify an API or session token and return the associated user.

    Args:
        db: Database session
        raw_token: Raw token string (e.g., "hth_xxx...")
        allowed_kinds: Token kinds that are accepted for this verification

    Returns:
        User if token is valid, None otherwise
    """
    token_hash = hash_token(raw_token)

    result = await db.execute(
        select(APIToken)
        .where(APIToken.token_hash == token_hash)
        .where(APIToken.revoked_at.is_(None))
        .where(APIToken.kind.in_(allowed_kinds))
    )
    token = result.scalar_one_or_none()

    if not token:
        return None

    # Check expiration
    if token.expires_at:
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None

    # Update last used timestamp
    token.last_used_at = datetime.now(timezone.utc)

    # Get and validate user
    result = await db.execute(
        select(User).where(User.id == token.user_id).where(User.status == "active")
    )
    user = result.scalar_one_or_none()

    if user:
        user.last_seen_at = datetime.now(timezone.utc)

    return user


async def verify_refresh_token(db: AsyncSession, raw_token: str) -> APIToken | None:
    """
    Verify a refresh token and return the token object.

    Args:
        db: Database session
        raw_token: Raw refresh token string

    Returns:
        APIToken if valid, None otherwise
    """
    token_hash = hash_token(raw_token)

    result = await db.execute(
        select(APIToken)
        .where(APIToken.token_hash == token_hash)
        .where(APIToken.revoked_at.is_(None))
        .where(APIToken.kind == "session_refresh")
    )
    token = result.scalar_one_or_none()

    if not token:
        return None

    # Check expiration
    if token.expires_at:
        expires_at = token.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        if expires_at < datetime.now(timezone.utc):
            return None

    return token


# =============================================================================
# Session Management
# =============================================================================


async def revoke_session(db: AsyncSession, session_id: str) -> int:
    """
    Revoke all tokens associated with a session.

    Args:
        db: Database session
        session_id: Session identifier

    Returns:
        Number of tokens revoked
    """
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(APIToken)
        .where(APIToken.session_id == session_id)
        .where(APIToken.revoked_at.is_(None))
    )
    tokens = result.scalars().all()

    for token in tokens:
        token.revoked_at = now

    await db.commit()
    return len(tokens)


async def revoke_all_user_sessions(db: AsyncSession, user_id: str) -> int:
    """
    Revoke all session tokens for a user (e.g., after password change).

    Args:
        db: Database session
        user_id: User identifier

    Returns:
        Number of tokens revoked
    """
    now = datetime.now(timezone.utc)

    result = await db.execute(
        select(APIToken)
        .where(APIToken.user_id == user_id)
        .where(APIToken.kind.in_(("session_access", "session_refresh")))
        .where(APIToken.revoked_at.is_(None))
    )
    tokens = result.scalars().all()

    for token in tokens:
        token.revoked_at = now

    await db.commit()
    return len(tokens)


# =============================================================================
# User Queries
# =============================================================================


async def get_user_by_id(db: AsyncSession, user_id: str) -> User | None:
    """Get a user by their ID."""
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    """Get a user by their username."""
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def get_user_count(db: AsyncSession) -> int:
    """Get total number of users in the system."""
    from sqlalchemy import func

    result = await db.execute(select(func.count(User.id)))
    return result.scalar_one()


# =============================================================================
# Login Attempt Tracking
# =============================================================================


async def record_failed_login(db: AsyncSession, user: User) -> bool:
    """
    Record a failed login attempt and check if account should be locked.

    Args:
        db: Database session
        user: User who failed login

    Returns:
        True if account is now locked
    """
    user.failed_login_count = (user.failed_login_count or 0) + 1

    if user.failed_login_count >= settings.max_failed_logins:
        user.locked_until = datetime.now(timezone.utc) + timedelta(minutes=settings.lockout_minutes)
        await db.commit()
        return True

    await db.commit()
    return False


async def reset_failed_logins(db: AsyncSession, user: User) -> None:
    """Reset failed login counter after successful login."""
    user.failed_login_count = 0
    user.locked_until = None
    await db.commit()


def is_account_locked(user: User) -> bool:
    """Check if a user account is currently locked."""
    if not user.locked_until:
        return False

    locked_until = user.locked_until
    if locked_until.tzinfo is None:
        locked_until = locked_until.replace(tzinfo=timezone.utc)

    return locked_until > datetime.now(timezone.utc)


# =============================================================================
# Admin Bootstrap
# =============================================================================


async def bootstrap_admin(db: AsyncSession) -> None:
    """
    Bootstrap admin user on first startup if none exists.

    Creates an admin user with a random password and prints it to stdout.
    This is idempotent: does nothing if admin already exists.

    SECURITY: Password is printed to stdout, NOT logged, to prevent
    leakage to centralized log collection systems.

    Args:
        db: Database session
    """
    # Check if admin user exists
    existing = await get_user_by_username(db, "admin")
    if existing:
        return  # Admin exists, nothing to do

    # Generate random password
    password = secrets.token_urlsafe(16)
    password_hash_value = hash_password(password)

    # Create admin user
    user = User(
        id=secrets.token_urlsafe(16),
        username="admin",
        display_name="Administrator",
        role="admin",
        status="active",
        password_hash=password_hash_value,
        password_changed_at=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()

    # Print to stdout (NOT logger!) to prevent password leakage to log systems
    print("\n" + "=" * 60)
    print("[BOOTSTRAP] Admin user created on first startup")
    print("=" * 60)
    print(f"Username: admin")
    print(f"Password: {password}")
    print("=" * 60)
    print("SAVE THIS PASSWORD - it will NOT be shown again!")
    print("=" * 60 + "\n")
