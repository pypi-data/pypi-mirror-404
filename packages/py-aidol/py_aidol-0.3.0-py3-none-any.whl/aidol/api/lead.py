"""
Lead API router

Public endpoints for collecting leads (emails).
"""

from typing import Annotated

from aioia_core.fastapi import BaseCrudRouter
from aioia_core.settings import JWTSettings
from fastapi import APIRouter, Depends, Header, status
from pydantic import BaseModel
from sqlalchemy.orm import Session, sessionmaker

from aidol.protocols import (
    AIdolLeadRepositoryFactoryProtocol,
    AIdolLeadRepositoryProtocol,
    AIdolRepositoryFactoryProtocol,
    NoUpdate,
)
from aidol.schemas import AIdolLead, AIdolLeadCreate, AIdolUpdate


class LeadResponse(BaseModel):
    """Response for lead creation."""

    email: str


class LeadRouter(
    BaseCrudRouter[AIdolLead, AIdolLeadCreate, NoUpdate, AIdolLeadRepositoryProtocol]
):
    """
    Lead router.

    Handles email collection.
    """

    def __init__(
        self,
        aidol_repository_factory: AIdolRepositoryFactoryProtocol,
        **kwargs,
    ):
        super().__init__(**kwargs)
        self.aidol_repository_factory = aidol_repository_factory

    def _register_routes(self) -> None:
        """Register routes."""
        self._register_create_lead_route()

    def _register_create_lead_route(self) -> None:
        """POST /leads - Collect email"""

        @self.router.post(
            f"/{self.resource_name}",
            response_model=LeadResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Collect Lead",
            description="Collect email. Associates with AIdol if ClaimToken is valid.",
        )
        async def create_lead(
            request: AIdolLeadCreate,
            claim_token: Annotated[str | None, Header(alias="ClaimToken")] = None,
            db_session: Session = Depends(self.get_db_dep),
            lead_repository: AIdolLeadRepositoryProtocol = Depends(
                self.get_repository_dep
            ),
        ):
            """Collect email."""
            email_saved = False

            # 1. Try to associate with AIdol if token is present
            if claim_token:
                # Reuse session from dependency
                aidol_repo = self.aidol_repository_factory.create_repository(db_session)

                # Find AIdol by claim_token
                # Assuming get_all supports filters
                items, _ = aidol_repo.get_all(
                    filters=[
                        {
                            "field": "claim_token",
                            "operator": "eq",
                            "value": claim_token,
                        }
                    ]
                )

                if items:
                    aidol = items[0]
                    # Update AIdol email
                    aidol_repo.update(aidol.id, AIdolUpdate(email=request.email))
                    email_saved = True

            # 2. If not saved as AIdol email, create Lead
            if not email_saved:
                lead_repository.create(request)

            return LeadResponse(email=request.email)


def create_lead_router(
    db_session_factory: sessionmaker,
    aidol_repository_factory: AIdolRepositoryFactoryProtocol,
    lead_repository_factory: AIdolLeadRepositoryFactoryProtocol,
    jwt_settings: JWTSettings | None = None,
    resource_name: str = "leads",
    tags: list[str] | None = None,
) -> APIRouter:
    """Create Lead router."""
    router = LeadRouter(
        model_class=AIdolLead,
        create_schema=AIdolLeadCreate,
        update_schema=NoUpdate,  # Update not supported
        db_session_factory=db_session_factory,
        repository_factory=lead_repository_factory,
        aidol_repository_factory=aidol_repository_factory,
        user_info_provider=None,  # No auth required for lead collection
        jwt_secret_key=jwt_settings.secret_key if jwt_settings else None,
        resource_name=resource_name,
        tags=tags or ["Lead"],
    )
    return router.get_router()
