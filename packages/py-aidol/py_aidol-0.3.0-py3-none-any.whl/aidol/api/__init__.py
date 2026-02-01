"""
AIdol API routers
"""

from aidol.api.aidol import AIdolRouter, create_aidol_router
from aidol.api.companion import CompanionRouter, create_companion_router

__all__ = [
    "AIdolRouter",
    "CompanionRouter",
    "create_aidol_router",
    "create_companion_router",
]
