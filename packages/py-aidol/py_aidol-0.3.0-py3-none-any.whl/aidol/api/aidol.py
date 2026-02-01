# pylint: disable=duplicate-code
"""
AIdol API router

Public endpoints for AIdol group creation and retrieval.
Public access pattern: no authentication required.
"""

from aioia_core.auth import UserInfoProvider
from aioia_core.errors import ErrorResponse
from aioia_core.fastapi import BaseCrudRouter
from aioia_core.settings import JWTSettings
from fastapi import APIRouter, Depends, HTTPException, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import sessionmaker

from aidol.api.common import register_image_generation_route
from aidol.protocols import (
    AIdolRepositoryFactoryProtocol,
    AIdolRepositoryProtocol,
    ImageStorageProtocol,
)
from aidol.schemas import AIdol, AIdolCreate, AIdolPublic, AIdolUpdate


class AIdolCreateResponse(BaseModel):
    """Response for AIdol creation (only id)."""

    id: str


class AIdolRouter(
    BaseCrudRouter[AIdol, AIdolCreate, AIdolUpdate, AIdolRepositoryProtocol]
):
    """
    AIdol router with public endpoints.

    Public CRUD pattern: no authentication required.
    Returns AIdolPublic (excludes claim_token) for all responses.
    """

    def __init__(
        self,
        google_api_key: str | None,
        image_storage: ImageStorageProtocol,
        **kwargs,
    ):
        self.google_api_key = google_api_key
        self.image_storage = image_storage
        super().__init__(**kwargs)

    def _register_routes(self) -> None:
        """Register routes (public CRUD + image generation)"""
        # Register shared image generation route
        register_image_generation_route(
            router=self.router,
            resource_name=self.resource_name,
            google_api_key=self.google_api_key,
            image_storage=self.image_storage,
        )

        self._register_public_create_route()
        self._register_public_get_route()
        self._register_public_update_route()

    def _register_public_update_route(self) -> None:
        """PATCH /{resource_name}/{id} - Update AIdol group (public)"""

        @self.router.patch(
            f"/{self.resource_name}/{{item_id}}",
            response_model=AIdolPublic,
            status_code=status.HTTP_200_OK,
            summary="Update AIdol group",
            description="Update AIdol group by ID (public endpoint). Returns updated AIdol data directly.",
            responses={
                404: {"model": ErrorResponse, "description": "AIdol group not found"},
            },
        )
        async def update_aidol(
            item_id: str,
            data: AIdolUpdate,
            repository: AIdolRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """Update AIdol group."""
            # TODO: Verify ClaimToken if strict ownership is required (Sprint 1)
            updated = repository.update(item_id, data)
            if not updated:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="AIdol group not found",
                )

            # Return updated AIdol as public schema
            return AIdolPublic(**updated.model_dump())

    def _register_public_create_route(self) -> None:
        """POST /{resource_name} - Create an AIdol group (public)"""

        @self.router.post(
            f"/{self.resource_name}",
            response_model=AIdolCreateResponse,
            status_code=status.HTTP_201_CREATED,
            summary="Create AIdol group",
            description="Create a new AIdol group (public endpoint). Returns only the created id.",
        )
        async def create_aidol(
            request: AIdolCreate,
            response: Response,
            repository: AIdolRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """Create a new AIdol group."""
            created = repository.create(request)

            # Set ClaimToken header
            if created.claim_token:
                response.headers["ClaimToken"] = created.claim_token

            # Return only id
            return AIdolCreateResponse(id=created.id)

    def _register_public_get_route(self) -> None:
        """GET /{resource_name}/{id} - Get an AIdol group (public)"""

        @self.router.get(
            f"/{self.resource_name}/{{item_id}}",
            response_model=AIdolPublic,
            status_code=status.HTTP_200_OK,
            summary="Get AIdol group",
            description="Get AIdol group by ID (public endpoint). Returns AIdol data directly.",
            responses={
                404: {"model": ErrorResponse, "description": "AIdol group not found"},
            },
        )
        async def get_aidol(
            item_id: str,
            repository: AIdolRepositoryProtocol = Depends(self.get_repository_dep),
        ):
            """Get AIdol group by ID."""
            aidol = self._get_item_or_404(repository, item_id)
            # Return AIdol as public schema
            return AIdolPublic(**aidol.model_dump())


def create_aidol_router(
    google_api_key: str | None,
    db_session_factory: sessionmaker,
    repository_factory: AIdolRepositoryFactoryProtocol,
    image_storage: ImageStorageProtocol,
    jwt_settings: JWTSettings | None = None,
    user_info_provider: UserInfoProvider | None = None,
    resource_name: str = "aidols",
    tags: list[str] | None = None,
) -> APIRouter:
    """
    Create AIdol router with dependency injection.

    Args:
        google_api_key: Google API Key for image generation
        db_session_factory: Database session factory
        repository_factory: Factory implementing AIdolRepositoryFactoryProtocol
        image_storage: Image storage for permanent URLs
        jwt_settings: Optional JWT settings for authentication
        user_info_provider: Optional user info provider
        resource_name: Resource name for routes (default: "aidols")
        tags: Optional OpenAPI tags

    Returns:
        FastAPI APIRouter instance
    """
    router = AIdolRouter(
        google_api_key=google_api_key,
        image_storage=image_storage,
        model_class=AIdol,
        create_schema=AIdolCreate,
        update_schema=AIdolUpdate,
        db_session_factory=db_session_factory,
        repository_factory=repository_factory,
        user_info_provider=user_info_provider,
        jwt_secret_key=jwt_settings.secret_key if jwt_settings else None,
        resource_name=resource_name,
        tags=tags or ["AIdol"],
    )
    return router.get_router()
