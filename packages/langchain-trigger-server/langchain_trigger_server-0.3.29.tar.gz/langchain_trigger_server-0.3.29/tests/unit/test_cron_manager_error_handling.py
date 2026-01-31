"""Unit tests for CronTriggerManager error handling, including CancelledError."""

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from langchain_triggers.cron_manager import CronTriggerManager
from langchain_triggers.triggers import cron_trigger


class _FakeTriggerServer:
    def __init__(self, triggers):
        self.triggers = triggers
        self.database = None
        self.langchain_auth_client = None


class _FakeDatabase:
    async def get_agents_for_trigger(self, registration_id):
        return ["agent_1"]


@pytest.mark.asyncio
async def test_execute_cron_job_with_monitoring_handles_cancelled_error():
    """Test that CancelledError is caught and handled gracefully."""
    fake_server = _FakeTriggerServer([cron_trigger])
    fake_server.database = _FakeDatabase()
    mgr = CronTriggerManager(fake_server)

    registration = {
        "id": "test_reg_123",
        "template_id": cron_trigger.id,
        "resource": {"crontab": "* * * * *"},
    }

    # Mock execute_cron_job to raise CancelledError
    with patch.object(mgr, "execute_cron_job", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = asyncio.exceptions.CancelledError(
            "Request was cancelled"
        )

        # Execute the monitoring function
        await mgr._execute_cron_job_with_monitoring(registration)

        # Verify execute_cron_job was called
        mock_execute.assert_called_once_with(registration)

        # Verify execution was recorded with failed status
        assert len(mgr.execution_history) == 1
        execution = mgr.execution_history[0]
        assert execution.registration_id == "test_reg_123"
        assert execution.status == "failed"
        assert (
            execution.error_message == "Request was cancelled"
        )  # Uses the actual exception message
        assert execution.completion_time is not None


@pytest.mark.asyncio
async def test_execute_cron_job_with_monitoring_handles_regular_exception():
    """Test that regular exceptions are caught and handled."""
    fake_server = _FakeTriggerServer([cron_trigger])
    fake_server.database = _FakeDatabase()
    mgr = CronTriggerManager(fake_server)

    registration = {
        "id": "test_reg_456",
        "template_id": cron_trigger.id,
        "resource": {"crontab": "* * * * *"},
    }

    # Mock execute_cron_job to raise a regular exception
    with patch.object(mgr, "execute_cron_job", new_callable=AsyncMock) as mock_execute:
        mock_execute.side_effect = ValueError("Something went wrong")

        # Execute the monitoring function
        await mgr._execute_cron_job_with_monitoring(registration)

        # Verify execute_cron_job was called
        mock_execute.assert_called_once_with(registration)

        # Verify execution was recorded with failed status
        assert len(mgr.execution_history) == 1
        execution = mgr.execution_history[0]
        assert execution.registration_id == "test_reg_456"
        assert execution.status == "failed"
        assert execution.error_message == "Something went wrong"
        assert execution.completion_time is not None


@pytest.mark.asyncio
async def test_execute_cron_job_with_monitoring_handles_success():
    """Test that successful executions are recorded correctly."""
    fake_server = _FakeTriggerServer([cron_trigger])
    fake_server.database = _FakeDatabase()
    mgr = CronTriggerManager(fake_server)

    registration = {
        "id": "test_reg_789",
        "template_id": cron_trigger.id,
        "resource": {"crontab": "* * * * *"},
    }

    # Mock execute_cron_job to return successfully
    with patch.object(mgr, "execute_cron_job", new_callable=AsyncMock) as mock_execute:
        mock_execute.return_value = 2  # 2 agents invoked

        # Execute the monitoring function
        await mgr._execute_cron_job_with_monitoring(registration)

        # Verify execute_cron_job was called
        mock_execute.assert_called_once_with(registration)

        # Verify execution was recorded with completed status
        assert len(mgr.execution_history) == 1
        execution = mgr.execution_history[0]
        assert execution.registration_id == "test_reg_789"
        assert execution.status == "completed"
        assert execution.agents_invoked == 2
        assert execution.error_message is None
        assert execution.completion_time is not None
