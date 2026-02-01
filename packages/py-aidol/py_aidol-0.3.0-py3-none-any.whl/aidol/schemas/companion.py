"""
Companion (member) schemas

Schema hierarchy:
- CompanionStats: Nested stats object for request/response
- CompanionBase: Mutable fields (used in Create/Update)
- CompanionCreate: Base + system_prompt (mutable, but sensitive)
- CompanionUpdate: All fields optional for partial updates
- Companion: Response with all fields including system_prompt (internal use)
- CompanionPublic: Response without sensitive fields (API use)
"""

from datetime import datetime
from enum import Enum

from humps import camelize
from pydantic import BaseModel, ConfigDict, Field

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class Gender(str, Enum):
    """Gender options for companions."""

    MALE = "male"
    FEMALE = "female"


class Grade(str, Enum):
    """Grade levels for companions."""

    A = "A"
    B = "B"
    C = "C"
    F = "F"


class Position(str, Enum):
    """Position roles in the group."""

    LEADER = "leader"
    MAIN_VOCAL = "mainVocal"
    SUB_VOCAL = "subVocal"
    MAIN_DANCER = "mainDancer"
    SUB_DANCER = "subDancer"
    MAIN_RAPPER = "mainRapper"
    SUB_RAPPER = "subRapper"
    VISUAL = "visual"
    MAKNAE = "maknae"


# ---------------------------------------------------------------------------
# Nested Objects
# ---------------------------------------------------------------------------


class CompanionStats(BaseModel):
    """Nested stats object for API request/response."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    vocal: int = Field(default=0, ge=0, le=100, description="Vocal skill")
    dance: int = Field(default=0, ge=0, le=100, description="Dance skill")
    rap: int = Field(default=0, ge=0, le=100, description="Rap skill")
    visual: int = Field(default=0, ge=0, le=100, description="Visual score")
    stamina: int = Field(default=0, ge=0, le=100, description="Stamina")
    charm: int = Field(default=0, ge=0, le=100, description="Charm score")


# ---------------------------------------------------------------------------
# Request Schemas
# ---------------------------------------------------------------------------


class CompanionBase(BaseModel):
    """Base companion model with common mutable fields.

    Contains fields that can be modified after creation.
    Excludes system_prompt (sensitive, requires explicit inclusion).
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    aidol_id: str | None = Field(default=None, description="AIdol group ID")
    name: str | None = Field(default=None, description="Companion name")
    gender: Gender | None = Field(default=None, description="Gender")
    grade: Grade | None = Field(default=None, description="Grade level")
    biography: str | None = Field(default=None, description="Companion biography")
    profile_picture_url: str | None = Field(
        default=None, description="Profile picture URL"
    )
    position: Position | None = Field(default=None, description="Position in group")

    # MBTI scores (1-10)
    mbti_energy: int | None = Field(default=None, ge=1, le=10, description="E↔I (1-10)")
    mbti_perception: int | None = Field(
        default=None, ge=1, le=10, description="S↔N (1-10)"
    )
    mbti_judgment: int | None = Field(
        default=None, ge=1, le=10, description="T↔F (1-10)"
    )
    mbti_lifestyle: int | None = Field(
        default=None, ge=1, le=10, description="J↔P (1-10)"
    )

    # Stats (nested object)
    stats: CompanionStats = Field(
        default_factory=CompanionStats, description="Ability stats"
    )


class CompanionCreate(CompanionBase):
    """Schema for creating a companion (no id).

    Includes system_prompt for creation (excluded from response for security).
    """

    system_prompt: str | None = Field(
        default=None, description="AI system prompt (not exposed in responses)"
    )


class CompanionUpdate(BaseModel):
    """Schema for updating a companion (all fields optional)."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    aidol_id: str | None = Field(default=None, description="AIdol group ID")
    name: str | None = Field(default=None, description="Companion name")
    gender: Gender | None = Field(default=None, description="Gender")
    grade: Grade | None = Field(default=None, description="Grade level")
    biography: str | None = Field(default=None, description="Companion biography")
    profile_picture_url: str | None = Field(
        default=None, description="Profile picture URL"
    )
    position: Position | None = Field(default=None, description="Position in group")
    system_prompt: str | None = Field(
        default=None, description="AI system prompt (not exposed in responses)"
    )

    # MBTI scores (1-10)
    mbti_energy: int | None = Field(default=None, ge=1, le=10, description="E↔I (1-10)")
    mbti_perception: int | None = Field(
        default=None, ge=1, le=10, description="S↔N (1-10)"
    )
    mbti_judgment: int | None = Field(
        default=None, ge=1, le=10, description="T↔F (1-10)"
    )
    mbti_lifestyle: int | None = Field(
        default=None, ge=1, le=10, description="J↔P (1-10)"
    )

    # Stats (nested object, optional for updates)
    stats: CompanionStats | None = Field(default=None, description="Ability stats")


# ---------------------------------------------------------------------------
# Response Schemas
# ---------------------------------------------------------------------------


class Companion(CompanionBase):
    """Companion response schema with id and timestamps.

    Includes system_prompt for internal use (Service layer).
    Use CompanionPublic for API responses to exclude sensitive fields.
    """

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, alias_generator=camelize
    )

    id: str = Field(..., description="Companion ID")
    system_prompt: str | None = Field(
        default=None, description="AI system prompt (sensitive, internal use only)"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class CompanionPublic(BaseModel):
    """Public companion response schema for frontend.

    - Excludes system_prompt for security
    - Uses nested stats object
    - Includes calculated mbti string
    """

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, alias_generator=camelize
    )

    id: str = Field(..., description="Companion ID")
    aidol_id: str | None = Field(default=None, description="AIdol group ID")
    name: str | None = Field(default=None, description="Companion name")
    gender: Gender | None = Field(default=None, description="Gender")
    grade: Grade | None = Field(default=None, description="Grade level")
    biography: str | None = Field(default=None, description="Companion biography")
    profile_picture_url: str | None = Field(
        default=None, description="Profile picture URL"
    )
    position: Position | None = Field(default=None, description="Position in group")
    mbti: str | None = Field(default=None, description="Calculated MBTI (e.g., ENFP)")
    stats: CompanionStats = Field(
        default_factory=CompanionStats, description="Ability stats"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
