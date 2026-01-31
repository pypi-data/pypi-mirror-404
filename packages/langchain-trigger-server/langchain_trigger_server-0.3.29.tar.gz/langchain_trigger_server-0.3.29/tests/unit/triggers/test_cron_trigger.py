from unittest.mock import MagicMock

import pytest

from langchain_triggers.triggers.cron_trigger import (
    CronRegistration,
    cron_registration_handler,
)


@pytest.mark.asyncio
async def test_cron_registration_handler_valid_pattern():
    """Test cron_registration_handler with a valid cron pattern."""
    # set up test
    mock_request = MagicMock()
    user_id = "test_user"
    valid_crontab = "0 9 * * MON-FRI"
    registration = CronRegistration(crontab=valid_crontab)

    # call method / assertions
    result = await cron_registration_handler(mock_request, user_id, registration)

    assert result.create_registration is True
    assert "cron_pattern" in result.metadata
    assert result.metadata["cron_pattern"] == valid_crontab
    assert "timezone" in result.metadata
    assert result.metadata["timezone"] == "UTC"
    assert "created_at" in result.metadata
    assert result.metadata["validated"] is True


@pytest.mark.asyncio
async def test_cron_registration_handler_invalid_pattern():
    """Test cron_registration_handler with an invalid cron pattern."""
    # set up test
    mock_request = MagicMock()
    user_id = "test_user"

    # call method / assertions
    invalid_crontab = "invalid cron string"
    registration = CronRegistration(crontab=invalid_crontab)

    result = await cron_registration_handler(mock_request, user_id, registration)

    assert result.create_registration is False
    assert result.status_code == 400
    assert "error" in result.response_body
    assert result.response_body["error"] == "invalid_cron_pattern"

    # call method / assertions
    too_many_parts_crontab = "* * * * * *"

    registration = CronRegistration(crontab=too_many_parts_crontab)
    result = await cron_registration_handler(mock_request, user_id, registration)

    assert result.create_registration is False
    assert result.status_code == 400
    assert "error" in result.response_body
    assert result.response_body["error"] == "invalid_cron_pattern"
