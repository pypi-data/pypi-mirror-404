"""Unit tests for TriggerServer API endpoints using in-memory testing."""

import os
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from pydantic import BaseModel

from langchain_triggers import TriggerServer


async def mock_auth_handler(request_body, headers):
    """Mock authentication handler for testing."""
    auth_header = headers.get("authorization", "")
    if not auth_header:
        return None
    # Extract user ID from Bearer token for testing
    token = auth_header.replace("Bearer ", "")
    return {
        "identity": f"test_user_{token}",
        "tenant_id": f"test_tenant_{token}",
    }


class TestRegistration(BaseModel):
    """Simple registration model for testing."""

    name: str


async def dummy_trigger_handler(request, database):
    """Dummy trigger handler for test triggers."""
    return {"ok": True}


# Mock database class
class MockDatabase:
    """Mock database for testing."""

    def __init__(self):
        self.registrations = []
        self.agent_links = []

    async def create_trigger_registration(
        self, user_id, tenant_id, template_id, resource, metadata
    ):
        registration = {
            "id": f"reg_{len(self.registrations)}",
            "user_id": user_id,
            "tenant_id": tenant_id,
            "template_id": template_id,
            "resource": resource,
            "metadata": metadata,
            "created_at": "2025-01-01T00:00:00Z",
            "linked_agent_ids": [],
        }
        self.registrations.append(registration)
        return registration

    async def get_user_trigger_registrations_with_agents(self, user_id, tenant_id):
        return [
            {
                **reg,
                "linked_agent_ids": reg.get("linked_agent_ids", []),
            }
            for reg in self.registrations
            if reg["user_id"] == user_id and reg["tenant_id"] == tenant_id
        ]

    async def get_trigger_registration(self, registration_id, user_id, tenant_id):
        for reg in self.registrations:
            if reg["id"] == registration_id:
                if reg["user_id"] == user_id and reg["tenant_id"] == tenant_id:
                    return reg
        return None

    async def find_user_registration_by_resource(
        self, user_id, tenant_id, template_id, resource_data
    ):
        return None  # No duplicates for testing

    async def delete_trigger_registration(self, registration_id, user_id, tenant_id):
        from fastapi import HTTPException

        initial_count = len(self.registrations)
        self.registrations = [
            reg
            for reg in self.registrations
            if not (
                reg["id"] == registration_id
                and reg["user_id"] == user_id
                and reg["tenant_id"] == tenant_id
            )
        ]
        deleted = len(self.registrations) < initial_count
        if not deleted:
            raise HTTPException(status_code=404, detail="Registration not found")
        return deleted

    async def link_agent_to_trigger(
        self, agent_id, registration_id, created_by, field_selection=None
    ):
        link = {
            "agent_id": agent_id,
            "registration_id": registration_id,
            "created_by": created_by,
            "field_selection": field_selection,
        }
        self.agent_links.append(link)
        # Update registration
        for reg in self.registrations:
            if reg["id"] == registration_id:
                if "linked_agent_ids" not in reg:
                    reg["linked_agent_ids"] = []
                reg["linked_agent_ids"].append(agent_id)
        return True

    async def unlink_agent_from_trigger(self, agent_id, registration_id):
        self.agent_links = [
            link
            for link in self.agent_links
            if not (
                link["agent_id"] == agent_id
                and link["registration_id"] == registration_id
            )
        ]
        # Update registration
        for reg in self.registrations:
            if reg["id"] == registration_id:
                if "linked_agent_ids" in reg and agent_id in reg["linked_agent_ids"]:
                    reg["linked_agent_ids"].remove(agent_id)
        return True

    async def get_agents_for_trigger(self, registration_id):
        return [
            link["agent_id"]
            for link in self.agent_links
            if link["registration_id"] == registration_id
        ]

    async def get_all_registrations(self, template_id):
        return [reg for reg in self.registrations if reg["template_id"] == template_id]

    async def get_registrations_for_agent(self, agent_id, tenant_id):
        return [
            reg
            for reg in self.registrations
            if reg["tenant_id"] == tenant_id
            and agent_id in reg.get("linked_agent_ids", [])
        ]


@pytest.fixture
def mock_env():
    """Set up mock environment variables."""
    with patch.dict(
        os.environ,
        {
            "LANGGRAPH_API_URL": "http://localhost:8000",
            "LANGCHAIN_API_KEY": "test_api_key",
        },
    ):
        yield


@pytest_asyncio.fixture
async def trigger_server(mock_env):
    """Create a TriggerServer instance for testing."""
    mock_db = MockDatabase()

    # Mock the cron manager to avoid scheduler startup
    with patch("langchain_triggers.app.CronTriggerManager") as mock_cron_class:
        mock_cron_instance = AsyncMock()
        mock_cron_instance.start = AsyncMock()
        mock_cron_instance.shutdown = AsyncMock()
        mock_cron_instance.reload_from_database = AsyncMock()
        mock_cron_class.return_value = mock_cron_instance

        server = TriggerServer(
            auth_handler=mock_auth_handler,
            database=mock_db,
        )
        server.cron_manager = mock_cron_instance

        # Trigger startup event
        await server.app.router.startup()

        yield server

        # Trigger shutdown event
        await server.app.router.shutdown()


@pytest.mark.asyncio
async def test_root_endpoint(trigger_server):
    """Test the root endpoint returns server info."""
    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert data["message"] == "Triggers Server"
        assert data["version"] == "0.1.0"


@pytest.mark.asyncio
async def test_health_endpoint(trigger_server):
    """Test the health endpoint."""
    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"


@pytest.mark.asyncio
async def test_list_triggers_endpoint(trigger_server):
    """Test listing trigger templates from in-memory registry."""
    from langchain_triggers import (
        TriggerRegistrationResult,
        TriggerTemplate,
    )

    # Create a test trigger registration handler
    async def test_registration_handler(request, user_id, registration):
        return TriggerRegistrationResult()

    # Add a trigger template to the in-memory registry
    test_trigger = TriggerTemplate(
        id="test_trigger",
        display_name="Test Trigger",
        description="A test trigger",
        registration_model=TestRegistration,
        registration_handler=test_registration_handler,
        trigger_handler=dummy_trigger_handler,
    )
    trigger_server.add_trigger(test_trigger)

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get(
            "/v1/triggers", headers={"Authorization": "Bearer token1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == "test_trigger"
        assert data["data"][0]["displayName"] == "Test Trigger"


@pytest.mark.asyncio
async def test_list_triggers_requires_auth(trigger_server):
    """Test that listing triggers requires authentication."""
    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # No Authorization header
        response = await client.get("/v1/triggers")

        assert response.status_code == 401


@pytest.mark.asyncio
async def test_list_registrations_for_user(trigger_server):
    """Test listing registrations for a specific user."""
    # Create a registration
    await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        tenant_id="test_tenant_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={"test": "value"},
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer token1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert len(data["data"]) == 1
        assert data["data"][0]["user_id"] == "test_user_token1"
        assert data["data"][0]["template_id"] == "test_trigger"


@pytest.mark.asyncio
async def test_link_agent_to_trigger(trigger_server):
    """Test linking an agent to a trigger registration."""
    # Create a registration first
    reg = await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        tenant_id="test_tenant_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={},
    )
    registration_id = reg["id"]

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.post(
            f"/v1/triggers/registrations/{registration_id}/agents/agent_123",
            headers={"Authorization": "Bearer token1"},
            json={},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["data"]["agent_id"] == "agent_123"
        assert data["data"]["registration_id"] == registration_id


@pytest.mark.asyncio
async def test_unlink_agent_from_trigger(trigger_server):
    """Test unlinking an agent from a trigger registration."""
    # Create a registration and link an agent
    reg = await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        tenant_id="test_tenant_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={},
    )
    registration_id = reg["id"]
    await trigger_server.database.link_agent_to_trigger(
        agent_id="agent_123",
        registration_id=registration_id,
        created_by="test_user_token1",
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.delete(
            f"/v1/triggers/registrations/{registration_id}/agents/agent_123",
            headers={"Authorization": "Bearer token1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_user_isolation(trigger_server):
    """Test that users can only see their own registrations."""
    # Create registrations for two different users
    await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        tenant_id="test_tenant_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={},
    )
    await trigger_server.database.create_trigger_registration(
        user_id="test_user_token2",
        tenant_id="test_tenant_token2",
        template_id="test_trigger",
        resource={"url": "https://other.com"},
        metadata={},
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        # User 1 should only see their registration
        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer token1"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["user_id"] == "test_user_token1"

        # User 2 should only see their registration
        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer token2"}
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["user_id"] == "test_user_token2"


@pytest.mark.asyncio
async def test_metadata_storage(trigger_server):
    """Test that handler metadata is properly stored."""
    from langchain_triggers import TriggerRegistrationResult, TriggerTemplate

    async def test_registration_handler(request, user_id, registration):
        return TriggerRegistrationResult(metadata={"handler_data": "from_handler"})

    test_trigger = TriggerTemplate(
        id="test_metadata_trigger",
        description="Tests metadata storage",
        registration_model=TestRegistration,
        registration_handler=test_registration_handler,
        trigger_handler=dummy_trigger_handler,
    )
    trigger_server.add_trigger(test_trigger)

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.post(
            "/v1/triggers/registrations",
            headers={"Authorization": "Bearer token1"},
            json={
                "type": "test_metadata_trigger",
                "name": "test",
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

        # Verify metadata in API response
        registration_id = data["data"]["id"]
        metadata = data["data"]["metadata"]
        assert metadata["handler_data"] == "from_handler"

        # Verify metadata persisted in database
        db_registration = await trigger_server.database.get_trigger_registration(
            registration_id, user_id="test_user_token1", tenant_id="test_tenant_token1"
        )
        assert db_registration is not None
        db_metadata = db_registration["metadata"]
        assert db_metadata["handler_data"] == "from_handler"


@pytest.mark.asyncio
async def test_tenant_isolation(trigger_server):
    """Test strict tenant isolation across all APIs."""
    tenant_a_reg = await trigger_server.database.create_trigger_registration(
        user_id="test_user_tenant_a",
        tenant_id="test_tenant_tenant_a",
        template_id="test_trigger",
        resource={"url": "https://tenant-a.com"},
        metadata={},
    )
    tenant_b_reg = await trigger_server.database.create_trigger_registration(
        user_id="test_user_tenant_b",
        tenant_id="test_tenant_tenant_b",
        template_id="test_trigger",
        resource={"url": "https://tenant-b.com"},
        metadata={},
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer tenant_a"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == tenant_a_reg["id"]

        response = await client.get(
            "/v1/triggers/registrations", headers={"Authorization": "Bearer tenant_b"}
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == tenant_b_reg["id"]

        response = await client.post(
            f"/v1/triggers/registrations/{tenant_a_reg['id']}/agents/agent_x",
            headers={"Authorization": "Bearer tenant_b"},
            json={},
        )
        assert response.status_code == 404

        response = await client.delete(
            f"/v1/triggers/registrations/{tenant_a_reg['id']}",
            headers={"Authorization": "Bearer tenant_b"},
        )
        assert response.status_code == 404

        response = await client.delete(
            f"/v1/triggers/registrations/{tenant_a_reg['id']}",
            headers={"Authorization": "Bearer tenant_a"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


@pytest.mark.asyncio
async def test_get_registrations_for_agent(trigger_server):
    """Test getting trigger registrations linked to a specific agent."""
    # Create a registration and link an agent
    reg = await trigger_server.database.create_trigger_registration(
        user_id="test_user_token1",
        tenant_id="test_tenant_token1",
        template_id="test_trigger",
        resource={"url": "https://example.com"},
        metadata={},
    )
    await trigger_server.database.link_agent_to_trigger(
        agent_id="agent_456",
        registration_id=reg["id"],
        created_by="test_user_token1",
    )

    transport = ASGITransport(app=trigger_server.app, raise_app_exceptions=True)
    async with AsyncClient(base_url="http://localhost", transport=transport) as client:
        response = await client.get(
            "/v1/triggers/agents/agent_456/registrations",
            headers={"Authorization": "Bearer token1"},
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 1
        assert data["data"][0]["id"] == reg["id"]
