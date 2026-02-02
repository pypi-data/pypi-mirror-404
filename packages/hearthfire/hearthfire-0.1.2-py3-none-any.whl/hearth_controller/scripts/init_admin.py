"""
Initialize admin user and token for first-time setup.

This script supports two modes:
1. Create admin user with password (for web login)
2. Create admin user with API token only (for programmatic access)

Usage:
    # With password (recommended for web UI)
    python -m hearth_controller.scripts.init_admin --password

    # With API token only
    python -m hearth_controller.scripts.init_admin
"""

import argparse
import asyncio
import getpass
import secrets
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from uuid import uuid4

from sqlalchemy import select

from hearth_controller.config import settings
from hearth_controller.db.models import APIToken, User
from hearth_controller.db.session import async_session_maker, init_db
from hearth_controller.services.auth import hash_password


def generate_token() -> tuple[str, str, str]:
    """Generate a new API token.

    Returns:
        Tuple of (raw_token, token_hash, prefix)
    """
    raw_token = f"{settings.token_prefix}{secrets.token_urlsafe(settings.token_bytes)}"
    token_hash = sha256(raw_token.encode()).hexdigest()
    prefix = raw_token[:8]
    return raw_token, token_hash, prefix


async def create_admin_user(
    with_password: bool = False,
    password: str | None = None,
    username: str = "admin",
) -> None:
    """Create admin user with optional password and API token.

    Args:
        with_password: If True, prompt for password or use provided one
        password: Pre-provided password (for non-interactive use)
        username: Admin username (default: "admin")
    """
    await init_db()

    async with async_session_maker() as session:
        # Check if admin user exists
        result = await session.execute(select(User).where(User.username == username))
        existing_user = result.scalar_one_or_none()

        if existing_user:
            print(f"Admin user already exists: {existing_user.username}")

            # Update password if requested
            if with_password:
                if not password:
                    password = getpass.getpass("Enter new password for admin: ")
                    confirm = getpass.getpass("Confirm password: ")
                    if password != confirm:
                        print("Error: Passwords do not match")
                        return

                if len(password) < settings.min_password_length:
                    print(
                        f"Error: Password must be at least {settings.min_password_length} characters"
                    )
                    return

                existing_user.password_hash = hash_password(password)
                existing_user.password_changed_at = datetime.now(timezone.utc)
                await session.commit()
                print("Password updated successfully!")

            # Check if there's a valid token
            token_result = await session.execute(
                select(APIToken).where(
                    APIToken.user_id == existing_user.id,
                    APIToken.kind == "api",
                    APIToken.revoked_at.is_(None),
                )
            )
            existing_token = token_result.scalar_one_or_none()

            if existing_token:
                print(f"Existing API token prefix: {existing_token.prefix}...")
                print("To create a new token, revoke existing ones first.")
                return
            else:
                # Create new API token
                await _create_api_token(session, existing_user)
        else:
            # Get password if requested
            password_hash = None
            if with_password:
                if not password:
                    password = getpass.getpass("Enter password for admin: ")
                    confirm = getpass.getpass("Confirm password: ")
                    if password != confirm:
                        print("Error: Passwords do not match")
                        return

                if len(password) < settings.min_password_length:
                    print(
                        f"Error: Password must be at least {settings.min_password_length} characters"
                    )
                    return

                password_hash = hash_password(password)

            # Create admin user
            user = User(
                id=uuid4().hex[:32],
                username=username,
                display_name="Administrator",
                role="admin",
                status="active",
                password_hash=password_hash,
                password_changed_at=datetime.now(timezone.utc) if password_hash else None,
            )
            session.add(user)
            await session.flush()
            print(f"Created admin user: {user.username}")

            if password_hash:
                print("Password set successfully!")

            # Create API token
            await _create_api_token(session, user)


async def _create_api_token(session, user: User) -> None:
    """Create an API token for the user."""
    raw_token, token_hash, prefix = generate_token()
    expires_at = datetime.now(timezone.utc) + timedelta(days=settings.token_default_expiry_days)

    token = APIToken(
        id=uuid4().hex[:32],
        user_id=user.id,
        name="Initial Admin Token",
        token_hash=token_hash,
        prefix=prefix,
        kind="api",
        expires_at=expires_at,
    )
    session.add(token)
    await session.commit()

    print("\n" + "=" * 60)
    print("ADMIN SETUP COMPLETED")
    print("=" * 60)
    print(f"\nAPI Token (SAVE THIS - shown only once):\n{raw_token}")
    print(f"\nExpires: {expires_at.isoformat()}")
    print("\nUse this token for API access:")
    print(f"  Authorization: Bearer {raw_token}")
    print("=" * 60)


def main() -> None:
    """Entry point."""
    parser = argparse.ArgumentParser(description="Initialize admin user for Hearth Controller")
    parser.add_argument(
        "--password",
        "-p",
        action="store_true",
        help="Set password for web login (interactive prompt)",
    )
    parser.add_argument(
        "--username",
        "-u",
        default="admin",
        help="Admin username (default: admin)",
    )
    parser.add_argument(
        "--set-password",
        metavar="PASSWORD",
        help="Set password non-interactively (for scripts)",
    )

    args = parser.parse_args()

    with_password = args.password or args.set_password is not None
    asyncio.run(
        create_admin_user(
            with_password=with_password,
            password=args.set_password,
            username=args.username,
        )
    )


if __name__ == "__main__":
    main()
