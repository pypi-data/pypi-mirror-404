"""
Companion database model

Uses aioia_core.models.BaseModel which provides:
- id: Mapped[str] (primary key, UUID default)
- created_at: Mapped[datetime]
- updated_at: Mapped[datetime]
"""

from aioia_core.models import BaseModel
from sqlalchemy import ForeignKey, Index, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column


class DBCompanion(BaseModel):
    """Companion (member) database model"""

    __tablename__ = "companions"

    # id, created_at, updated_at inherited from BaseModel
    aidol_id: Mapped[str | None] = mapped_column(ForeignKey("aidols.id"), nullable=True)
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    grade: Mapped[str | None] = mapped_column(String, nullable=True)
    biography: Mapped[str | None] = mapped_column(Text, nullable=True)
    profile_picture_url: Mapped[str | None] = mapped_column(String, nullable=True)
    system_prompt: Mapped[str | None] = mapped_column(Text, nullable=True)

    # MBTI scores (1-10 scale)
    mbti_energy: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mbti_perception: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mbti_judgment: Mapped[int | None] = mapped_column(Integer, nullable=True)
    mbti_lifestyle: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Stats (0-100 scale)
    vocal: Mapped[int | None] = mapped_column(Integer, nullable=True)
    dance: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rap: Mapped[int | None] = mapped_column(Integer, nullable=True)
    visual: Mapped[int | None] = mapped_column(Integer, nullable=True)
    stamina: Mapped[int | None] = mapped_column(Integer, nullable=True)
    charm: Mapped[int | None] = mapped_column(Integer, nullable=True)

    position: Mapped[str | None] = mapped_column(String, nullable=True)

    __table_args__ = (Index("ix_companions_aidol_id", "aidol_id"),)
