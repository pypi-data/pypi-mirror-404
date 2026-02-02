"""
Admin commands for Hearth CLI.

These commands require direct local SQLite database access and are
intended to be run only on the controller machine.
"""

import secrets
import sqlite3
from pathlib import Path

import typer

from argon2 import PasswordHasher

app = typer.Typer(no_args_is_help=True)

# Default DB path (same as controller config)
DEFAULT_DB_PATH = Path.home() / ".hearth" / "controller" / "hearth.db"

# Password hasher matching controller's auth.py
_password_hasher = PasswordHasher()


def _parse_db_path(db_path: str | None) -> Path:
    """
    Parse and validate database path.

    Args:
        db_path: Database path or SQLite URL

    Returns:
        Path to SQLite database file

    Raises:
        typer.Exit: If path is remote or invalid
    """
    if db_path is None:
        return DEFAULT_DB_PATH

    # Check for remote database URLs
    if db_path.startswith(("postgres://", "postgresql://", "mysql://", "mysql+", "mariadb://")):
        typer.secho(
            "Error: Admin password reset requires local SQLite database access.\n"
            "For remote databases, use direct database access.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    # Handle SQLite URL formats
    if db_path.startswith("sqlite:///"):
        db_path = db_path[len("sqlite:///") :]
    elif db_path.startswith("sqlite+aiosqlite:///"):
        db_path = db_path[len("sqlite+aiosqlite:///") :]

    return Path(db_path).expanduser()


@app.command("reset-password")
def reset_password(
    username: str = typer.Option(..., "--username", "-u", help="Username to reset password for"),
    db_path: str | None = typer.Option(
        None,
        "--db-path",
        "-d",
        help=f"Path to SQLite database file (default: {DEFAULT_DB_PATH})",
    ),
) -> None:
    """
    Reset password for a user.

    This command requires direct access to the local SQLite database and
    should only be run on the controller machine. It generates a new random
    password and updates the database directly.

    The new password is printed to stdout (NOT logged) for security.
    """
    # Parse and validate DB path
    db_file = _parse_db_path(db_path)

    # Check file exists
    if not db_file.exists():
        typer.secho(
            f"Error: Database file not found: {db_file}\n"
            "Make sure the controller has been started at least once.",
            fg=typer.colors.RED,
        )
        raise typer.Exit(1)

    # Check file is writable
    if not db_file.is_file():
        typer.secho(f"Error: {db_file} is not a file", fg=typer.colors.RED)
        raise typer.Exit(1)

    try:
        # Connect to SQLite database
        conn = sqlite3.connect(str(db_file))
        cursor = conn.cursor()

        # Check user exists
        cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        row = cursor.fetchone()

        if not row:
            typer.secho(f"Error: User '{username}' not found", fg=typer.colors.RED)
            conn.close()
            raise typer.Exit(1)

        # Generate new password
        password = secrets.token_urlsafe(16)
        password_hash = _password_hasher.hash(password)

        # Update user: password_hash, failed_login_count=0, locked_until=NULL
        cursor.execute(
            """
            UPDATE users
            SET password_hash = ?,
                failed_login_count = 0,
                locked_until = NULL
            WHERE username = ?
            """,
            (password_hash, username),
        )

        conn.commit()
        conn.close()

        # Print to stdout (NOT logger!) for security
        print(f"Password reset for {username}. New password: {password}")

    except sqlite3.Error as e:
        typer.secho(f"Error: Database error: {e}", fg=typer.colors.RED)
        raise typer.Exit(1)
