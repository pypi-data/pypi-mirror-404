"""
AIdol Leads database model

Uses aioia_core.models.BaseModel which provides:
- id: Mapped[str] (primary key, UUID default)
- created_at: Mapped[datetime]
- updated_at: Mapped[datetime]
"""

from aioia_core.models import BaseModel
from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column


class DBAIdolLead(BaseModel):
    """AIdol Lead (viewer email) database model"""

    __tablename__ = "aidol_leads"

    # id, created_at, updated_at inherited from BaseModel
    aidol_id: Mapped[str] = mapped_column(String, nullable=False)
    email: Mapped[str] = mapped_column(String, nullable=False)
