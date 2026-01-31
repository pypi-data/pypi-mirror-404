"""Core types and interfaces for the triggers framework."""

from __future__ import annotations

import logging
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class TriggerType(str, Enum):
    """Type of trigger supported by the framework."""

    WEBHOOK = "webhook"
    POLLING = "polling"


class TriggerRegistrationResult(BaseModel):
    """Result returned by registration handlers."""

    create_registration: bool = Field(
        default=True,
        description="Whether to create database registration (False = return custom response)",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Metadata to store with the registration"
    )
    resource: dict[str, Any] = Field(
        default_factory=dict,
        description="Resource data to merge with user-provided registration data (backend-controlled fields)",
    )
    response_body: dict[str, Any] | None = Field(
        default=None,
        description="Custom HTTP response body (when create_registration=False)",
    )
    status_code: int | None = Field(
        default=None, description="HTTP status code (when create_registration=False)"
    )

    def model_post_init(self, __context) -> None:
        """Validate that required fields are provided based on create_registration."""
        if self.create_registration and not self.metadata:
            self.metadata = {}  # Allow empty metadata for create_registration=True

        if not self.create_registration and (
            not self.response_body or not self.status_code
        ):
            raise ValueError(
                "Both response_body and status_code are required when create_registration=False"
            )


class TriggerRegistrationModel(BaseModel):
    """Base class for trigger resource models that define how webhooks are matched to registrations."""

    pass
