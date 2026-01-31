"""Utility functions for trigger handlers."""

import logging
import os
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
from cachetools import TTLCache
from langgraph_sdk.client import LangGraphClient

logger = logging.getLogger(__name__)

_DEFAULT_ORG_CONFIG_TTL_SECONDS = 8 * 60 * 60

# leaving this in case we want to change it based on env variable
_ORG_CONFIG_TTL_SECONDS = float(
    os.getenv("ORG_CONFIG_CACHE_TTL_SECONDS", str(_DEFAULT_ORG_CONFIG_TTL_SECONDS))
)
_ORG_CONFIG_CACHE: TTLCache[str, dict] = TTLCache(
    maxsize=1024, ttl=_ORG_CONFIG_TTL_SECONDS
)


def get_x_service_jwt_token(
    payload: dict[str, Any] | None = None, expiration_seconds: int = 60 * 60
) -> str:
    """Create X-Service-Key JWT token for service-to-service authentication.

    Args:
        payload: Optional payload to include in JWT
        expiration_seconds: Token expiration time in seconds (default 1 hour)

    Returns:
        JWT token string
    """
    exp_datetime = datetime.now(tz=UTC) + timedelta(seconds=expiration_seconds)
    exp = int(exp_datetime.timestamp())

    payload = payload or {}
    payload = {
        "sub": "unspecified",
        "exp": exp,
        **payload,
    }

    secret = os.environ["X_SERVICE_AUTH_JWT_SECRET"]

    return jwt.encode(
        payload,
        secret,
        algorithm="HS256",
    )


def create_service_auth_headers(
    user_id: str,
    tenant_id: str,
    organization_id: str,
) -> dict[str, str]:
    """Create authentication headers with X-Service-Key JWT token.

    Args:
        user_id: User ID for the request
        tenant_id: Tenant ID for the request

    Returns:
        Dictionary of authentication headers
    """
    headers = {
        "x-api-key": "",
        "x-auth-scheme": "langsmith-agent",
        "x-user-id": user_id,
        "x-tenant-id": tenant_id,
        "x-organization-id": organization_id,
        "x-service-key": get_x_service_jwt_token(
            payload={
                "user_id": user_id,
                "tenant_id": tenant_id,
                "organization_id": organization_id,
            }
        ),
    }

    return headers


def get_langgraph_url(registration: dict[str, Any]) -> str:
    """Get the LangGraph API URL for a given registration
    by comparing the registration's organization ID to the
    LANGCHAIN_ORGANIZATION_ID setting."""
    reg_organization_id = str(registration.get("organization_id"))

    langgraph_api_url = os.getenv("LANGGRAPH_API_URL", "http://localhost:2024")
    langgraph_api_url_public = os.getenv(
        "LANGGRAPH_API_URL_PUBLIC", "http://localhost:2024"
    )
    langchain_organization_id = os.getenv(
        "LANGCHAIN_ORGANIZATION_ID", "f5c798a2-2155-4999-ad27-6d466bd26e1c"
    )

    return (
        langgraph_api_url
        if reg_organization_id == langchain_organization_id
        else langgraph_api_url_public
    )


async def is_assistant_triggers_paused(
    client: LangGraphClient, agent_id: str, headers: dict[str, str] | None = None
) -> bool:
    """Check if triggers are paused for the given assistant.

    Looks for a boolean `triggers_paused` under `assistant.config.configurable`.
    If the assistant cannot be fetched or the field is absent, returns False.
    """
    try:
        assistant = await client.assistants.get(agent_id, headers=headers)
        if not assistant:
            logger.warning(
                f"assistant_triggers_paused_check_failed agent_id={agent_id} error=assistant_not_found"
            )
            return False
        config = assistant.get("config") or {}
        configurable = config.get("configurable") or {}
        paused = bool(configurable.get("triggers_paused", False))
        if paused:
            logger.debug(f"assistant_triggers_paused agent_id={agent_id} paused=True")
        return paused
    except Exception as e:
        logger.warning(
            f"assistant_triggers_paused_check_failed agent_id={agent_id} error={str(e)}"
        )
        return False


async def _get_with_client(url: str, headers: dict[str, str]) -> httpx.Response:
    client = httpx.AsyncClient()
    try:
        resp = await client.get(url, headers=headers)
        return resp
    finally:
        await client.aclose()


async def get_org_config_with_service_auth(
    user_id: str,
    tenant_id: str,
    organization_id: str,
    base_url: str | None = None,
) -> dict:
    base = base_url or os.getenv("SMITH_BACKEND_ENDPOINT") or ""

    if not base:
        logger.warning("SMITH_BACKEND_ENDPOINT not set; cannot fetch org config")
        return {}

    # Cache key should always be the org ID
    cache_key = str(organization_id)

    cached = _ORG_CONFIG_CACHE.get(cache_key)
    if cached is not None:
        return cached

    headers = {
        "x-api-key": "",
        "x-auth-scheme": "langsmith-agent",
        "x-user-id": user_id,
        "x-tenant-id": tenant_id,
        "x-organization-id": organization_id,
        "x-service-key": get_x_service_jwt_token(
            payload={
                "user_id": user_id,
                "tenant_id": tenant_id,
                "organization_id": organization_id,
            },
            expiration_seconds=60 * 5,
        ),
    }

    try:
        info_resp = await _get_with_client(f"{base}/orgs/current/info", headers=headers)
        info_resp.raise_for_status()
        info_json = info_resp.json() or {}
        config = info_json.get("config") or {}
        _ORG_CONFIG_CACHE[cache_key] = config
        return config
    except Exception as e:
        logger.warning(
            f"org_config_fetch_failed tenant_id={tenant_id} org_id={organization_id} error={str(e)}"
        )
        return {}
