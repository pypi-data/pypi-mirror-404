"""Database interface for trigger operations."""

from abc import ABC, abstractmethod
from typing import Any


class TriggerDatabaseInterface(ABC):
    """Abstract interface for trigger database operations."""

    # ========== Trigger Registrations ==========

    @abstractmethod
    async def create_trigger_registration(
        self,
        user_id: str,
        tenant_id: str,
        template_id: str,
        resource: dict,
        metadata: dict = None,
    ) -> dict[str, Any] | None:
        """Create a new trigger registration for a user."""
        pass

    @abstractmethod
    async def get_user_trigger_registrations(
        self, user_id: str, tenant_id: str
    ) -> list[dict[str, Any]]:
        """Get all trigger registrations for a user within a tenant."""
        pass

    @abstractmethod
    async def get_user_trigger_registrations_with_agents(
        self, user_id: str, tenant_id: str
    ) -> list[dict[str, Any]]:
        """Get all trigger registrations for a user with linked agents in a single query within a tenant."""
        pass

    @abstractmethod
    async def get_trigger_registration(
        self, registration_id: str, user_id: str, tenant_id: str
    ) -> dict[str, Any] | None:
        """Get a specific trigger registration."""
        pass

    @abstractmethod
    async def find_registration_by_resource(
        self, template_id: str, resource_data: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Find trigger registration by matching resource data."""
        pass

    @abstractmethod
    async def find_user_registration_by_resource(
        self,
        user_id: str,
        tenant_id: str,
        template_id: str,
        resource_data: dict[str, Any],
    ) -> dict[str, Any] | None:
        """Find trigger registration by matching resource data for a specific user within a tenant."""
        pass

    @abstractmethod
    async def get_all_registrations(self, template_id: str) -> list[dict[str, Any]]:
        """Get all registrations for a specific trigger template."""
        pass

    @abstractmethod
    async def delete_trigger_registration(
        self, registration_id: str, user_id: str, tenant_id: str
    ) -> bool:
        """Delete a trigger registration."""
        pass

    @abstractmethod
    async def update_trigger_registration(
        self, registration_id: str, user_id: str, tenant_id: str, status: str
    ) -> dict[str, Any] | None:
        """Update a trigger registration (currently supports status field) and return the updated record."""
        pass

    # ========== Agent-Trigger Links ==========

    @abstractmethod
    async def link_agent_to_trigger(
        self,
        agent_id: str,
        registration_id: str,
        created_by: str,
        field_selection: dict[str, bool] | None = None,
    ) -> bool:
        """Link an agent to a trigger registration with optional field selection."""
        pass

    @abstractmethod
    async def unlink_agent_from_trigger(
        self, agent_id: str, registration_id: str
    ) -> bool:
        """Unlink an agent from a trigger registration."""
        pass

    @abstractmethod
    async def get_agents_for_trigger(
        self, registration_id: str
    ) -> list[dict[str, Any]]:
        """Get all agent links for a trigger registration with field_selection."""
        pass

    @abstractmethod
    async def get_registrations_for_agent(
        self, agent_id: str, tenant_id: str
    ) -> list[dict[str, Any]]:
        """Get all trigger registrations linked to a specific agent within a tenant."""
        pass
