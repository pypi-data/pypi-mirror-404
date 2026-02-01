"""
AIdol repository protocols for type-safe dependency injection.

Defines the interface that AIdol Router expects from repositories.
Platform-specific integrators implement these protocols via adapters.
"""

# pylint: disable=unnecessary-ellipsis

from typing import Protocol

import PIL.Image
from aioia_core import CrudRepositoryProtocol
from pydantic import BaseModel
from sqlalchemy.orm import Session

from aidol.schemas import (
    AIdol,
    AIdolCreate,
    AIdolLead,
    AIdolLeadCreate,
    AIdolUpdate,
    Companion,
    CompanionCreate,
    CompanionUpdate,
)


class NoUpdate(BaseModel):
    """Placeholder for repositories without update support."""


class AIdolRepositoryProtocol(
    CrudRepositoryProtocol[AIdol, AIdolCreate, AIdolUpdate], Protocol
):
    """Protocol defining AIdol repository expectations.

    This protocol enables type-safe dependency injection by defining
    the exact interface that AIdolRouter uses. Inherits CRUD operations
    from CrudRepositoryProtocol.
    """


class AIdolRepositoryFactoryProtocol(Protocol):
    """Protocol for factory that creates AIdolRepositoryProtocol instances.

    Implementations:
        - aidol.factories.AIdolRepositoryFactory (standalone)
    """

    def create_repository(
        self, db_session: Session | None = None
    ) -> AIdolRepositoryProtocol:
        """Create a repository instance.

        Args:
            db_session: Optional database session.
        """
        ...


class CompanionRepositoryProtocol(
    CrudRepositoryProtocol[Companion, CompanionCreate, CompanionUpdate], Protocol
):
    """Protocol defining Companion repository expectations.

    This protocol enables type-safe dependency injection by defining
    the exact interface that CompanionRouter uses. Inherits CRUD operations
    from CrudRepositoryProtocol.
    """


class CompanionRepositoryFactoryProtocol(Protocol):
    """Protocol for factory that creates CompanionRepositoryProtocol instances.

    Implementations:
        - aidol.factories.CompanionRepositoryFactory (standalone)
    """

    def create_repository(
        self, db_session: Session | None = None
    ) -> CompanionRepositoryProtocol:
        """Create a repository instance.

        Args:
            db_session: Optional database session.
        """
        ...


class ImageStorageProtocol(Protocol):
    """Protocol for image storage operations.

    Enables dependency injection of storage implementations.
    Platform-specific adapters implement this protocol.

    Implementations:
        - ImageStorageAdapter (platform integration via StorageService)
    """

    def upload_image(self, image: PIL.Image.Image) -> str:
        """Upload an image and return the permanent URL.

        Args:
            image: PIL Image object to upload.
        """
        ...


class AIdolLeadRepositoryProtocol(
    CrudRepositoryProtocol[AIdolLead, AIdolLeadCreate, NoUpdate], Protocol
):
    """Protocol defining AIdolLead repository expectations.

    Inherits CRUD operations from CrudRepositoryProtocol.
    """


class AIdolLeadRepositoryFactoryProtocol(Protocol):
    """Protocol for factory that creates AIdolLeadRepositoryProtocol instances."""

    def create_repository(
        self, db_session: Session | None = None
    ) -> AIdolLeadRepositoryProtocol:
        """Create a repository instance."""
        ...
