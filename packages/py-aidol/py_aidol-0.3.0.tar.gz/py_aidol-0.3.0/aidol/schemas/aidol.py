"""
AIdol (group) schemas

Schema hierarchy:
- AIdolBase: Mutable fields (used in Create/Update)
- AIdolCreate: Base + optional claim_token
- AIdolUpdate: Base fields only
- AIdol: Response with all fields including claim_token (internal use)
- AIdolPublic: Response without sensitive fields (API use)
"""

from datetime import datetime

from humps import camelize
from pydantic import BaseModel, ConfigDict, Field


class AIdolBase(BaseModel):
    """Base AIdol model with mutable fields.

    Contains only fields that can be modified after creation.
    Excludes claim_token (immutable, set at creation only).
    """

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    name: str | None = Field(default=None, description="AIdol group name")
    email: str | None = Field(default=None, description="Creator email")
    greeting: str | None = Field(default=None, description="Greeting message")
    concept: str | None = Field(default=None, description="Group concept or theme")
    profile_image_url: str | None = Field(default=None, description="Profile image URL")


class AIdolCreate(AIdolBase):
    """Schema for creating an AIdol group (no id).

    claim_token is required for ownership verification.
    """

    claim_token: str = Field(
        ...,
        description="Client-generated UUID for ownership verification",
    )


class AIdolUpdate(BaseModel):
    """Schema for updating an AIdol group (all fields optional)."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    name: str | None = Field(default=None, description="AIdol group name")
    email: str | None = Field(default=None, description="Creator email")
    greeting: str | None = Field(default=None, description="Greeting message")
    concept: str | None = Field(default=None, description="Group concept or theme")
    profile_image_url: str | None = Field(default=None, description="Profile image URL")


class AIdol(AIdolBase):
    """AIdol response schema with id and timestamps.

    Includes optional claim_token for ownership verification.
    Use AIdolPublic for API responses to exclude sensitive fields.
    """

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, alias_generator=camelize
    )

    id: str = Field(..., description="AIdol group ID")
    claim_token: str | None = Field(
        default=None, description="Optional ownership token (sensitive, internal use)"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


class AIdolPublic(AIdolBase):
    """Public AIdol response schema without sensitive fields.

    Excludes claim_token for API responses.
    """

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, alias_generator=camelize
    )

    id: str = Field(..., description="AIdol group ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")


# ---------------------------------------------------------------------------
# Image Generation
# ---------------------------------------------------------------------------


class ImageGenerationRequest(BaseModel):
    """Request schema for image generation."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    prompt: str = Field(
        ...,
        max_length=200,
        description="Text description for image generation (max 200 chars)",
    )


class ImageGenerationData(BaseModel):
    """Image generation result data."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    image_url: str = Field(..., description="Generated image URL")
    width: int = Field(..., description="Image width in pixels")
    height: int = Field(..., description="Image height in pixels")
    format: str = Field(..., description="Image format (e.g., png, jpg)")


class ImageGenerationResponse(BaseModel):
    """Response schema for image generation."""

    data: ImageGenerationData
