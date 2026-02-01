"""
Companion repository

Implements BaseRepository pattern for BaseCrudRouter compatibility.
"""

from datetime import timezone

from aioia_core.repositories import BaseRepository
from sqlalchemy.orm import Session

from aidol.models import DBCompanion
from aidol.schemas import (
    Companion,
    CompanionCreate,
    CompanionStats,
    CompanionUpdate,
    Gender,
    Grade,
    Position,
)


def _convert_db_companion_to_model(db_companion: DBCompanion) -> Companion:
    """Convert DB Companion to Pydantic model.

    Includes system_prompt for internal use (Service layer).
    Router should convert to CompanionPublic for API responses.
    """
    return Companion(
        id=db_companion.id,
        aidol_id=db_companion.aidol_id,
        name=db_companion.name,
        gender=Gender(db_companion.gender) if db_companion.gender else None,
        grade=Grade(db_companion.grade) if db_companion.grade else None,
        biography=db_companion.biography,
        profile_picture_url=db_companion.profile_picture_url,
        position=Position(db_companion.position) if db_companion.position else None,
        system_prompt=db_companion.system_prompt,
        mbti_energy=db_companion.mbti_energy,
        mbti_perception=db_companion.mbti_perception,
        mbti_judgment=db_companion.mbti_judgment,
        mbti_lifestyle=db_companion.mbti_lifestyle,
        stats=CompanionStats(
            vocal=db_companion.vocal or 0,
            dance=db_companion.dance or 0,
            rap=db_companion.rap or 0,
            visual=db_companion.visual or 0,
            stamina=db_companion.stamina or 0,
            charm=db_companion.charm or 0,
        ),
        created_at=db_companion.created_at.replace(tzinfo=timezone.utc),
        updated_at=db_companion.updated_at.replace(tzinfo=timezone.utc),
    )


def _convert_companion_schema_to_db(
    schema: CompanionCreate | CompanionUpdate,
) -> dict:
    """Convert CompanionCreate/Update schema to DB model data dict.

    Decomposes nested stats object into individual DB columns.
    Includes system_prompt for AI configuration.
    """
    data = schema.model_dump(exclude_unset=True, exclude={"stats"})

    # Decompose stats into individual columns
    if schema.stats is not None:
        stats_dict = schema.stats.model_dump()
        data.update(stats_dict)

    return data


class CompanionRepository(
    BaseRepository[Companion, DBCompanion, CompanionCreate, CompanionUpdate]
):
    """
    Database-backed Companion repository.

    Extends BaseRepository for CRUD operations compatible with BaseCrudRouter.
    """

    def __init__(self, db_session: Session):
        super().__init__(
            db_session=db_session,
            db_model=DBCompanion,
            convert_to_model=_convert_db_companion_to_model,
            convert_to_db_model=_convert_companion_schema_to_db,
        )
