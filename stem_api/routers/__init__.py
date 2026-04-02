from .assets import router as assets_router
from .effects import router as effects_router
from .jobs import router as jobs_router
from .separation import router as separation_router
from .system import router as system_router

__all__ = [
    "assets_router",
    "effects_router",
    "jobs_router",
    "separation_router",
    "system_router",
]
