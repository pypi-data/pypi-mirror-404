import fcntl
import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, WebSocket
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from starlette.staticfiles import StaticFiles

from hearth_controller.api import router as api_router
from hearth_controller.config import settings
from hearth_controller.db.session import async_session_maker, init_db
from hearth_controller.mcp import mcp_router
from hearth_controller.services.auth import bootstrap_admin
from hearth_controller.services.reconciler import get_reconciler
from hearth_controller.ws import websocket_handler
from hearth_controller.ws.client_gateway import client_websocket_handler

logger = logging.getLogger(__name__)


class ControllerLock:
    """File-based lock to ensure only one controller instance runs at a time."""

    def __init__(self, lock_path: Path):
        self.lock_path = lock_path
        self.fd = None

    def acquire(self) -> None:
        """Acquire exclusive lock. Raises RuntimeError if another instance is running."""
        self.lock_path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = open(self.lock_path, "w")
        try:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            self.fd.close()
            self.fd = None
            raise RuntimeError(
                "Another controller instance is running. "
                "Only one controller is supported with SQLite."
            )

    def release(self) -> None:
        """Release the lock."""
        if self.fd:
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            self.fd.close()
            self.fd = None


# Global lock instance
_controller_lock = ControllerLock(Path("./data/.hearth-controller.lock"))


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Acquire single-instance lock before any initialization
    _controller_lock.acquire()

    # Security warning: check if rsync/relay mode is enabled but worker_api_secret is not set
    if settings.storage_mode in ("rsync", "auto"):
        if not settings.worker_api_secret:
            logger.warning(
                "SECURITY WARNING: storage_mode=%s but HEARTH_WORKER_API_SECRET not set. "
                "Worker API is unauthenticated. Set HEARTH_WORKER_API_SECRET for production.",
                settings.storage_mode,
            )

    await init_db()

    # Bootstrap admin user on first startup (idempotent)
    async with async_session_maker() as db:
        await bootstrap_admin(db)

    # Start background services
    reconciler = get_reconciler()
    await reconciler.start()

    yield

    # Cleanup background services
    await reconciler.stop()

    # Release lock after cleanup
    _controller_lock.release()


app = FastAPI(
    title="Hearth Controller",
    description="Distributed GPU Task Scheduling System",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True if settings.cors_origins != ["*"] else False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
app.include_router(mcp_router, prefix="/api/v1", tags=["mcp"])


@app.get("/health")
async def health_check() -> dict[str, str]:
    return {"status": "healthy"}


@app.websocket("/ws/worker")
async def worker_websocket(websocket: WebSocket) -> None:
    await websocket_handler(websocket)


@app.websocket("/ws/client")
async def client_websocket(websocket: WebSocket) -> None:
    """WebSocket endpoint for frontend clients to receive real-time updates."""
    await client_websocket_handler(websocket)


# Static file serving for bundled WebUI
# The static directory is located at hearth_controller/static/ (after build)
_static_dir = Path(__file__).parent / "static"

if _static_dir.exists() and (_static_dir / "index.html").exists():
    # Mount /assets for JS, CSS, and other static files with hashed filenames
    _assets_dir = _static_dir / "assets"
    if _assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=_assets_dir), name="assets")

    # SPA fallback: any route not matched by API/WS/health returns index.html
    # This must be registered LAST to not interfere with other routes
    @app.api_route("/{full_path:path}", methods=["GET", "HEAD"])
    async def spa_fallback(request: Request, full_path: str) -> FileResponse:
        """Serve index.html for client-side routing (SPA fallback)."""
        # Exclude API, WebSocket, and health routes - they should be handled by their own handlers
        if full_path.startswith("api/") or full_path.startswith("ws/") or full_path == "health":
            # This shouldn't happen if routes are registered correctly, but just in case
            from fastapi import HTTPException

            raise HTTPException(status_code=404, detail="Not Found")
        return FileResponse(_static_dir / "index.html")

else:
    logger.info(
        "Static directory not found at %s. WebUI will not be served. "
        "Build WebUI and copy to static/ for embedded serving.",
        _static_dir,
    )


def main() -> None:
    import uvicorn

    uvicorn.run(
        "hearth_controller.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,  # reload=True causes port config issues
    )


if __name__ == "__main__":
    main()
