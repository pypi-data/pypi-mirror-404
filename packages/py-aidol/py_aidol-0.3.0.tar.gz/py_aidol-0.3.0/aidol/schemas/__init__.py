"""
AIdol Pydantic schemas
"""

from aidol.schemas.aidol import (
    AIdol,
    AIdolBase,
    AIdolCreate,
    AIdolPublic,
    AIdolUpdate,
    ImageGenerationData,
    ImageGenerationRequest,
    ImageGenerationResponse,
)
from aidol.schemas.aidol_lead import AIdolLead, AIdolLeadBase, AIdolLeadCreate
from aidol.schemas.companion import (
    Companion,
    CompanionBase,
    CompanionCreate,
    CompanionPublic,
    CompanionStats,
    CompanionUpdate,
    Gender,
    Grade,
    Position,
)

__all__ = [
    "AIdol",
    "AIdolBase",
    "AIdolCreate",
    "AIdolPublic",
    "AIdolUpdate",
    "ImageGenerationData",
    "ImageGenerationRequest",
    "ImageGenerationResponse",
    "AIdolLead",
    "AIdolLeadBase",
    "AIdolLeadCreate",
    "Companion",
    "CompanionBase",
    "CompanionCreate",
    "CompanionPublic",
    "CompanionStats",
    "CompanionUpdate",
    "Gender",
    "Grade",
    "Position",
]
