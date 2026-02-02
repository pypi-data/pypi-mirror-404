from collections.abc import AsyncGenerator

from sqlalchemy import event, text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from hearth_controller.config import settings
from hearth_controller.db.models import Base

engine = create_async_engine(
    settings.database_url,
    echo=False,
    connect_args={
        "timeout": 30,
    },
)


@event.listens_for(engine.sync_engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """Configure SQLite for better concurrency and durability."""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()


async_session_maker = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def _migrate_schema(conn) -> None:
    """
    Lightweight schema migration for SQLite.

    SQLAlchemy's create_all() won't add columns to existing tables,
    so we need to manually ALTER TABLE for new columns.
    """
    migrations = [
        ("users", "password_hash", "TEXT", None),
        ("users", "password_changed_at", "DATETIME", None),
        ("users", "failed_login_count", "INTEGER", "0"),
        ("users", "locked_until", "DATETIME", None),
        ("api_tokens", "kind", "TEXT", "'api'"),
        ("api_tokens", "session_id", "TEXT", None),
        ("host_identities", "machine_id", "TEXT", None),
        ("host_identities", "dmi_uuid", "TEXT", None),
        ("host_identities", "hostname", "TEXT", None),
        ("host_identities", "hw_fingerprint", "TEXT", None),
        ("runs", "accepted_at", "DATETIME", None),
        ("runs", "current_attempt_id", "TEXT", None),
        ("runs", "cancel_requested_at", "DATETIME", None),
        ("hosts", "capabilities", "TEXT", None),
        ("runs", "client_request_id", "TEXT", None),
        ("runs", "idempotency_fingerprint", "TEXT", None),
        ("host_metrics_latest", "observed_remote_addr", "VARCHAR(64)", None),
        ("host_metrics_latest", "observed_remote_port", "INTEGER", None),
        ("host_metrics_latest", "observed_remote_at", "DATETIME", None),
    ]

    for table, column, col_type, default in migrations:
        # Check if column exists
        result = await conn.execute(text(f"PRAGMA table_info({table})"))
        columns = [row[1] for row in result.fetchall()]

        if column not in columns:
            # Add column with default value
            if default is not None:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type} DEFAULT {default}"
            else:
                sql = f"ALTER TABLE {table} ADD COLUMN {column} {col_type}"
            await conn.execute(text(sql))

    # Create unique index for idempotency (partial index: only where client_request_id is not null)
    try:
        await conn.execute(
            text(
                "CREATE UNIQUE INDEX IF NOT EXISTS idx_runs_owner_client_request_id "
                "ON runs(owner_user_id, client_request_id) "
                "WHERE client_request_id IS NOT NULL"
            )
        )
    except Exception:
        pass  # Index might already exist


async def init_db() -> None:
    """Initialize database schema and run migrations."""
    async with engine.begin() as conn:
        # Create tables that don't exist
        await conn.run_sync(Base.metadata.create_all)
        # Run migrations for new columns on existing tables
        await _migrate_schema(conn)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
