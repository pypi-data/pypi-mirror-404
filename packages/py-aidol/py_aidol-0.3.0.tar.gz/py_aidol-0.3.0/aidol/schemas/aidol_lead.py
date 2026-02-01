"""
AIdol Lead (viewer email) schemas

Schema hierarchy:
- AIdolLeadBase: Common fields
- AIdolLeadCreate: For creating a lead (no id)
- AIdolLead: Response with all fields
"""

from datetime import datetime

from humps import camelize
from pydantic import BaseModel, ConfigDict, Field


class AIdolLeadBase(BaseModel):
    """Base AIdol Lead model with common fields."""

    model_config = ConfigDict(populate_by_name=True, alias_generator=camelize)

    aidol_id: str = Field(..., description="AIdol group ID")
    email: str = Field(..., description="Viewer email")


class AIdolLeadCreate(AIdolLeadBase):
    """Schema for creating an AIdol lead (no id)."""


class AIdolLead(AIdolLeadBase):
    """AIdol Lead response schema with id and timestamps."""

    model_config = ConfigDict(
        populate_by_name=True, from_attributes=True, alias_generator=camelize
    )

    id: str = Field(..., description="Lead ID")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
