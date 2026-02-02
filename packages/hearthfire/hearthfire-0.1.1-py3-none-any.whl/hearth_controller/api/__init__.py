from fastapi import APIRouter

from hearth_controller.api.artifacts import router as artifacts_router
from hearth_controller.api.auth import router as auth_router
from hearth_controller.api.hosts import router as hosts_router
from hearth_controller.api.runs import router as runs_router
from hearth_controller.api.snapshots import router as snapshots_router
from hearth_controller.api.storage import router as storage_router
from hearth_controller.api.users import router as users_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth", tags=["auth"])
router.include_router(users_router, prefix="/users", tags=["users"])
router.include_router(hosts_router, prefix="/hosts", tags=["hosts"])
router.include_router(runs_router, prefix="/runs", tags=["runs"])
router.include_router(artifacts_router, prefix="/runs", tags=["artifacts"])
router.include_router(snapshots_router, prefix="/snapshots", tags=["snapshots"])
router.include_router(storage_router, prefix="/storage", tags=["storage"])
