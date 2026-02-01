"""
AIdol database model

Uses aioia_core.models.BaseModel which provides:
- id: Mapped[str] (primary key, UUID default)
- created_at: Mapped[datetime]
- updated_at: Mapped[datetime]
"""

from aioia_core.models import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class DBAIdol(BaseModel):
    """AIdol (group) database model"""

    __tablename__ = "aidols"

    # id, created_at, updated_at inherited from BaseModel
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    concept: Mapped[str | None] = mapped_column(String, nullable=True)
    profile_image_url: Mapped[str | None] = mapped_column(String, nullable=True)
    claim_token: Mapped[str | None] = mapped_column(String(36), nullable=True)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    greeting: Mapped[str | None] = mapped_column(String, nullable=True)
