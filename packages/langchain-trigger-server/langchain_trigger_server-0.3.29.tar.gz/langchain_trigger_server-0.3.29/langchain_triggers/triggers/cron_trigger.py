"""Cron-based trigger for scheduled agent execution."""

import logging
import uuid
from datetime import datetime
from typing import Any

from croniter import croniter
from fastapi import Request
from langgraph_sdk import get_client
from pydantic import Field

from langchain_triggers.core import (
    TriggerRegistrationModel,
    TriggerRegistrationResult,
    TriggerType,
)
from langchain_triggers.decorators import TriggerTemplate
from langchain_triggers.util import (
    create_service_auth_headers,
    get_langgraph_url,
    get_org_config_with_service_auth,
    is_assistant_triggers_paused,
)

logger = logging.getLogger(__name__)

# Global constant for cron trigger ID (UUID format to match database schema)
CRON_TRIGGER_ID = "c809e66e-0000-4000-8000-000000000001"


class CronRegistration(TriggerRegistrationModel):
    """Registration model for cron triggers - just a crontab pattern."""

    crontab: str = Field(
        ...,
        description="Cron pattern (e.g., '0 9 * * MON-FRI', '*/15 * * * *')",
        examples=["0 9 * * MON-FRI", "*/15 * * * *", "0 2 * * SUN"],
    )


async def cron_registration_handler(
    request: Request, user_id: str, registration: CronRegistration
) -> TriggerRegistrationResult:
    """Handle cron trigger registration - validates cron pattern and prepares for scheduling."""
    logger.info(f"Cron registration request: {registration}")

    cron_pattern = registration.crontab.strip()
    cron_parts = cron_pattern.split()

    # Validate cron pattern
    try:
        if not croniter.is_valid(cron_pattern) or len(cron_parts) != 5:
            return TriggerRegistrationResult(
                create_registration=False,
                response_body={
                    "success": False,
                    "error": "invalid_cron_pattern",
                    "message": f"Invalid cron pattern: '{cron_pattern}'",
                },
                status_code=400,
            )
    except Exception as e:
        return TriggerRegistrationResult(
            create_registration=False,
            response_body={
                "success": False,
                "error": "cron_validation_failed",
                "message": f"Failed to validate cron pattern: {str(e)}",
            },
            status_code=400,
        )

    logger.info(f"Successfully validated cron pattern: {cron_pattern}")
    return TriggerRegistrationResult(
        metadata={
            "cron_pattern": cron_pattern,
            "timezone": "UTC",
            "created_at": datetime.utcnow().isoformat(),
            "validated": True,
        }
    )


async def cron_poll_handler(
    registration: dict[str, Any],
    database,
) -> dict[str, Any]:
    """Polling handler for generic cron - invokes agents directly."""
    registration_id = registration["id"]
    user_id = str(registration["user_id"])
    tenant_id = str(registration.get("tenant_id", ""))
    organization_id = str(registration.get("organization_id", ""))
    langgraph_url = get_langgraph_url(registration)

    agent_links = await database.get_agents_for_trigger(registration_id)

    if not agent_links:
        logger.info(f"cron_no_linked_agents registration_id={registration_id}")
        return {"success": True, "message": "No linked agents", "agents_invoked": 0}

    client = get_client(url=langgraph_url, api_key=None)
    headers = create_service_auth_headers(user_id, tenant_id, organization_id)

    try:
        org_config = await get_org_config_with_service_auth(
            user_id=user_id,
            tenant_id=tenant_id,
            organization_id=organization_id,
        )
        agent_builder_enabled = org_config.get("agent_builder_enabled", True)
        status = "active" if agent_builder_enabled else "paused"
        logger.info(f"Setting trigger registration ID {registration_id} to {status}")
        await database.update_trigger_registration(
            registration_id=registration_id,
            user_id=user_id,
            tenant_id=tenant_id,
            status=status,
        )
        if not agent_builder_enabled:
            return {"success": True, "agents_invoked": 0}
    except Exception as e:
        logger.warning(
            f"cron_org_config_error registration_id={registration_id} error={str(e)}"
        )

    current_time = datetime.utcnow()
    current_time_str = current_time.strftime("%A, %B %d, %Y at %H:%M UTC")

    agents_invoked = 0
    for agent_link in agent_links:
        agent_id = str(
            agent_link if isinstance(agent_link, str) else agent_link.get("agent_id")
        )

        paused = await is_assistant_triggers_paused(client, agent_id, headers)
        if paused:
            logger.info(
                f"cron_triggers_paused_skip agent_id={agent_id} registration_id={registration_id}"
            )
            continue

        try:
            thread_id = str(uuid.uuid4())

            try:
                thread_result = await client.threads.create(
                    thread_id=thread_id,
                    if_exists="do_nothing",
                    metadata={
                        "triggered_by": "cron-trigger",
                        "user_id": user_id,
                        "tenant_id": tenant_id,
                        "registration_id": str(registration_id),
                    },
                    headers=headers,
                )
                logger.info(
                    f"cron_thread_create_success thread_id={thread_id} result={thread_result}"
                )
            except Exception as thread_err:
                logger.exception(
                    f"cron_thread_create_failed thread_id={thread_id} error={str(thread_err)}"
                )

            await client.runs.create(
                thread_id,
                agent_id,
                input={
                    "messages": [
                        {
                            "role": "human",
                            "content": f"Cron trigger fired at {current_time_str}",
                        }
                    ]
                },
                headers=headers,
                metadata={"source": "trigger"},
            )
            logger.info(
                f"cron_run_ok registration_id={registration_id} agent_id={agent_id} thread_id={thread_id}"
            )
            agents_invoked += 1
        except Exception as e:
            logger.exception(
                f"cron_run_err registration_id={registration_id} agent_id={agent_id} error={str(e)}"
            )

    return {"success": True, "agents_invoked": agents_invoked}


cron_trigger = TriggerTemplate(
    id=CRON_TRIGGER_ID,
    description="Triggers agents on a predetermined schedule",
    registration_model=CronRegistration,
    registration_handler=cron_registration_handler,
    trigger_type=TriggerType.POLLING,
    poll_handler=cron_poll_handler,
    display_name="Cron",
    integration=None,
)
