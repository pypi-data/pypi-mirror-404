"""
AIdol Lead repository

Implements BaseRepository pattern for BaseCrudRouter compatibility.
"""

from datetime import timezone

from aioia_core.repositories import BaseRepository
from sqlalchemy.orm import Session

from aidol.models import DBAIdolLead
from aidol.protocols import AIdolLeadRepositoryProtocol, NoUpdate
from aidol.schemas import AIdolLead, AIdolLeadCreate


def _convert_db_aidol_lead_to_model(db_lead: DBAIdolLead) -> AIdolLead:
    """Convert DB AIdolLead to Pydantic model."""
    return AIdolLead(
        id=db_lead.id,
        aidol_id=db_lead.aidol_id,
        email=db_lead.email,
        created_at=db_lead.created_at.replace(tzinfo=timezone.utc),
        updated_at=db_lead.updated_at.replace(tzinfo=timezone.utc),
    )


def _convert_aidol_lead_create_to_db(schema: AIdolLeadCreate) -> dict:
    """Convert AIdolLeadCreate schema to DB model data dict."""
    return schema.model_dump(exclude_unset=True)


class AIdolLeadRepository(
    BaseRepository[AIdolLead, DBAIdolLead, AIdolLeadCreate, NoUpdate],
    AIdolLeadRepositoryProtocol,
):
    """
    Database-backed AIdolLead repository.

    Extends BaseRepository for CRUD operations compatible with BaseCrudRouter.
    """

    def __init__(self, db_session: Session):
        super().__init__(
            db_session=db_session,
            db_model=DBAIdolLead,
            convert_to_model=_convert_db_aidol_lead_to_model,
            convert_to_db_model=_convert_aidol_lead_create_to_db,
        )
