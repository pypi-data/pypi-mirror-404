# pylint: disable=duplicate-code
# TODO: Extract common AIdol converters to shared module
#       (duplicated in managers/database_aidol_manager.py)
"""
AIdol repository

Implements BaseRepository pattern for BaseCrudRouter compatibility.
"""

from datetime import timezone

from aioia_core.repositories import BaseRepository
from sqlalchemy.orm import Session

from aidol.models import DBAIdol
from aidol.schemas import AIdol, AIdolCreate, AIdolUpdate


def _convert_db_aidol_to_model(db_aidol: DBAIdol) -> AIdol:
    """Convert DB AIdol to Pydantic model.

    Includes claim_token for internal use (Service layer).
    Router should convert to AIdolPublic for API responses.
    """
    return AIdol(
        id=db_aidol.id,
        name=db_aidol.name,
        email=db_aidol.email,
        greeting=db_aidol.greeting,
        concept=db_aidol.concept,
        profile_image_url=db_aidol.profile_image_url,
        claim_token=db_aidol.claim_token,
        created_at=db_aidol.created_at.replace(tzinfo=timezone.utc),
        updated_at=db_aidol.updated_at.replace(tzinfo=timezone.utc),
    )


def _convert_aidol_create_to_db(schema: AIdolCreate) -> dict:
    """Convert AIdolCreate schema to DB model data dict.

    Includes claim_token for ownership verification.
    """
    return schema.model_dump(exclude_unset=True)


class AIdolRepository(BaseRepository[AIdol, DBAIdol, AIdolCreate, AIdolUpdate]):
    """
    Database-backed AIdol repository.

    Extends BaseRepository for CRUD operations compatible with BaseCrudRouter.
    """

    def __init__(self, db_session: Session):
        super().__init__(
            db_session=db_session,
            db_model=DBAIdol,
            convert_to_model=_convert_db_aidol_to_model,
            convert_to_db_model=_convert_aidol_create_to_db,
        )
