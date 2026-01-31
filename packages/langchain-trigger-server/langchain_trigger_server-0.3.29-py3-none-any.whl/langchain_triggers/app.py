"""FastAPI application for trigger server."""

from __future__ import annotations

import logging
import os
from collections.abc import Callable
from contextlib import asynccontextmanager
from datetime import UTC, datetime, timedelta
from typing import Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request
from langchain_auth.client import Client
from langgraph_sdk import get_client
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
from starlette.types import Lifespan

from .core import TriggerType
from .cron_manager import CronTriggerManager
from .database import TriggerDatabaseInterface
from .decorators import TriggerTemplate

logger = logging.getLogger(__name__)


def get_x_service_jwt_token(
    payload: dict[str, Any] | None = None, expiration_seconds: int = 60 * 60
) -> str:
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


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """Middleware to handle authentication for API endpoints."""

    def __init__(self, app, auth_handler: Callable):
        super().__init__(app)
        self.auth_handler = auth_handler

    async def dispatch(self, request: Request, call_next):
        # Skip auth for webhooks, health/root endpoints, and OPTIONS requests
        if (
            request.url.path.startswith("/v1/triggers/webhooks/")
            or request.url.path in ["/", "/health"]
            or request.method == "OPTIONS"
        ):
            return await call_next(request)

        try:
            identity = await self.auth_handler({}, dict(request.headers))
            if (
                not identity
                or not identity.get("identity")
                or not identity.get("tenant_id")
            ):
                logger.error(
                    f"Authentication failed: missing required fields (identity={bool(identity.get('identity') if identity else None)}, tenant_id={bool(identity.get('tenant_id') if identity else None)})"
                )
                return Response(
                    content='{"detail": "Authentication required - identity and tenant_id must be provided"}',
                    status_code=401,
                    media_type="application/json",
                )
            request.state.current_user = identity

        except Exception as e:
            logger.error(f"Authentication middleware error: {e}")
            return Response(
                content='{"detail": "Authentication failed"}',
                status_code=401,
                media_type="application/json",
            )

        return await call_next(request)


def get_current_user(request: Request) -> dict[str, Any]:
    """FastAPI dependency to get the current authenticated user."""
    if not hasattr(request.state, "current_user"):
        raise HTTPException(status_code=401, detail="Authentication required")
    return request.state.current_user


class TriggerServer:
    """FastAPI application for trigger webhooks."""

    def __init__(
        self,
        auth_handler: Callable,
        database: TriggerDatabaseInterface,
        lifespan: Lifespan | None = None,
    ):
        # Configure uvicorn logging to use consistent formatting
        self._configure_uvicorn_logging()

        self.database = database
        self.auth_handler = auth_handler

        # LangGraph configuration
        self.langgraph_api_url = os.getenv("LANGGRAPH_API_URL")
        self.trigger_server_auth_api_url = os.getenv("TRIGGER_SERVER_HOST_API_URL")

        if not self.langgraph_api_url:
            raise ValueError("LANGGRAPH_API_URL environment variable is required")

        self.langgraph_api_url = self.langgraph_api_url.rstrip("/")

        # Initialize LangGraph SDK client
        self.langgraph_client = get_client(url=self.langgraph_api_url, api_key=None)
        logger.info(
            f"✓ LangGraph client initialized with URL: {self.langgraph_api_url}"
        )

        # Initialize LangChain auth client
        langchain_api_key = os.getenv("LANGCHAIN_API_KEY")
        if langchain_api_key:
            self.langchain_auth_client = Client(
                api_key=langchain_api_key, api_url=self.trigger_server_auth_api_url
            )
            logger.info("✓ LangChain auth client initialized")
        else:
            self.langchain_auth_client = None
            logger.warning(
                "LANGCHAIN_API_KEY not found - OAuth token injection disabled"
            )

        self.triggers: list[TriggerTemplate] = []

        # Initialize CronTriggerManager
        self.cron_manager = CronTriggerManager(self)

        # Create merged lifespan that includes cron manager lifecycle
        merged_lifespan = self._create_lifespan(lifespan)

        self.app = FastAPI(
            title="Triggers Server",
            description="Event-driven triggers framework",
            version="0.1.0",
            lifespan=merged_lifespan,
        )

        # Setup authentication middleware
        self.app.add_middleware(AuthenticationMiddleware, auth_handler=auth_handler)

        # Setup routes
        self._setup_routes()

    def _configure_uvicorn_logging(self) -> None:
        """Configure uvicorn loggers to use consistent formatting for production deployments."""
        formatter = logging.Formatter("%(levelname)s: %(name)s - %(message)s")

        # Configure uvicorn access logger
        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_access_logger.handlers.clear()
        access_handler = logging.StreamHandler()
        access_handler.setFormatter(formatter)
        uvicorn_access_logger.addHandler(access_handler)

        # Configure uvicorn error logger
        uvicorn_error_logger = logging.getLogger("uvicorn.error")
        uvicorn_error_logger.handlers.clear()
        error_handler = logging.StreamHandler()
        error_handler.setFormatter(formatter)
        uvicorn_error_logger.addHandler(error_handler)

        # Configure uvicorn main logger
        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_logger.handlers.clear()
        main_handler = logging.StreamHandler()
        main_handler.setFormatter(formatter)
        uvicorn_logger.addHandler(main_handler)

    def _create_lifespan(self, existing_lifespan: Lifespan | None) -> Lifespan:
        """Create a lifespan context manager that handles cron manager lifecycle."""
        cron_manager = self.cron_manager

        @asynccontextmanager
        async def lifespan(app: FastAPI):
            await cron_manager.start()
            if existing_lifespan:
                logger.info("Starting existing lifespan")
                async with existing_lifespan(app):
                    yield
            else:
                yield
            await cron_manager.shutdown()

        return lifespan

    def add_trigger(self, trigger: TriggerTemplate) -> None:
        """Add a trigger template to the app."""
        # Check for duplicate IDs
        if any(t.id == trigger.id for t in self.triggers):
            raise ValueError(f"Trigger with id '{trigger.id}' already exists")

        self.triggers.append(trigger)

        if trigger.trigger_handler:

            async def handler_endpoint(request: Request) -> dict[str, Any]:
                return await self._handle_request(trigger, request)

            handler_path = f"/v1/triggers/webhooks/{trigger.id}"
            self.app.post(handler_path)(handler_endpoint)
            logger.info(f"Added handler route: POST {handler_path}")

        logger.info(
            f"Registered trigger template in memory: {trigger.display_name} ({trigger.id})"
        )

    def add_triggers(self, triggers: list[TriggerTemplate]) -> None:
        """Add multiple triggers."""
        for trigger in triggers:
            self.add_trigger(trigger)

    def _setup_routes(self) -> None:
        """Setup built-in API routes."""

        @self.app.get("/")
        async def root() -> dict[str, str]:
            return {"message": "Triggers Server", "version": "0.1.0"}

        @self.app.get("/health")
        async def health() -> dict[str, str]:
            return {"status": "healthy"}

        @self.app.get("/v1/triggers")
        async def api_list_triggers() -> dict[str, Any]:
            """List available trigger templates from in-memory registry."""
            trigger_list = []
            for trigger in self.triggers:
                trigger_list.append(
                    {
                        "id": trigger.id,
                        "displayName": trigger.display_name,
                        "description": trigger.description,
                        "path": "/v1/triggers/registrations",
                        "method": "POST",
                        "payloadSchema": trigger.registration_model.model_json_schema(),
                        "integration": trigger.integration,
                        "authProvider": trigger.auth_provider,
                        "scopes": trigger.scopes,
                    }
                )

            return {"success": True, "data": trigger_list}

        @self.app.get("/v1/triggers/registrations")
        async def api_list_registrations(
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """List user's trigger registrations (user and tenant-scoped)."""
            try:
                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]

                # Get user's trigger registrations with linked agents in a single query
                user_registrations = (
                    await self.database.get_user_trigger_registrations_with_agents(
                        user_id, tenant_id
                    )
                )

                # Format response to match expected structure
                registrations = []
                for reg in user_registrations:
                    registrations.append(
                        {
                            "id": reg["id"],
                            "user_id": reg["user_id"],
                            "template_id": reg.get("template_id"),
                            "resource": reg["resource"],
                            "linked_agent_ids": reg.get("linked_agent_ids", []),
                            "created_at": reg["created_at"],
                        }
                    )

                return {"success": True, "data": registrations}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error listing registrations: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.patch("/v1/triggers/registrations/{registration_id}")
        async def api_update_registration(
            registration_id: str,
            request: Request,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Update a trigger registration (currently supports status field: active/paused)."""
            try:
                try:
                    body = await request.json()
                except Exception:
                    raise HTTPException(status_code=400, detail="Invalid JSON body")

                # Currently only supports status field updates
                status = (body or {}).get("status")
                if status not in {"active", "paused"}:
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid status. Must be 'active' or 'paused'",
                    )

                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]

                updated = await self.database.update_trigger_registration(
                    registration_id=registration_id,
                    user_id=user_id,
                    tenant_id=tenant_id,
                    status=status,
                )
                if not updated:
                    raise HTTPException(
                        status_code=404,
                        detail="Registration not found or access denied",
                    )

                return {"success": True, "data": updated}

            except HTTPException as e:
                logger.error(
                    f"Error updating registration {registration_id}: {e.status_code} - {e.detail}"
                )
                raise
            except Exception as e:
                logger.error(f"Error updating registration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/triggers/registrations")
        async def api_create_registration(
            request: Request, current_user: dict[str, Any] = Depends(get_current_user)
        ) -> dict[str, Any]:
            """Create a new trigger registration."""
            try:
                payload = await request.json()
                logger.info(f"Registration payload received: {payload}")

                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]
                trigger_id = payload.get("type")
                if not trigger_id:
                    raise HTTPException(
                        status_code=400, detail="Missing required field: type"
                    )

                trigger = next((t for t in self.triggers if t.id == trigger_id), None)
                if not trigger:
                    raise HTTPException(
                        status_code=400, detail=f"Unknown trigger type: {trigger_id}"
                    )

                # Parse payload into registration model first
                try:
                    registration_instance = trigger.registration_model(**payload)
                except Exception as e:
                    raise HTTPException(
                        status_code=400, detail=f"Invalid payload for trigger: {str(e)}"
                    )

                # Check for duplicate registration based on resource data within this user's tenant scope
                resource_dict = registration_instance.model_dump()
                existing_registration = (
                    await self.database.find_user_registration_by_resource(
                        user_id=user_id,
                        tenant_id=tenant_id,
                        template_id=trigger.id,
                        resource_data=resource_dict,
                    )
                )

                if existing_registration:
                    raise HTTPException(
                        status_code=400,
                        detail=f"You already have a registration with this configuration for trigger type '{trigger.id}'. Registration ID: {existing_registration.get('id')}",
                    )
                result = await trigger.registration_handler(
                    request, user_id, registration_instance
                )

                # Check if handler requested to skip registration (e.g., for OAuth or URL verification)
                if not result.create_registration:
                    logger.info(
                        "Registration handler requested to skip database creation"
                    )
                    import json

                    from fastapi import Response

                    return Response(
                        content=json.dumps(result.response_body),
                        status_code=result.status_code,
                        media_type="application/json",
                    )

                resource_dict = registration_instance.model_dump()
                resource_dict.update(result.resource)

                registration = await self.database.create_trigger_registration(
                    user_id=user_id,
                    tenant_id=tenant_id,
                    template_id=trigger.id,
                    resource=resource_dict,
                    metadata=result.metadata,
                )

                if not registration:
                    raise HTTPException(
                        status_code=500, detail="Failed to create trigger registration"
                    )

                # Reload cron manager to pick up any new cron registrations
                await self.cron_manager.reload_from_database()

                # Return registration result
                return {
                    "success": True,
                    "data": registration,
                    "metadata": result.metadata,
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.exception(f"Error creating trigger registration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete("/v1/triggers/registrations/{registration_id}")
        async def api_delete_registration(
            registration_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Delete a trigger registration."""
            try:
                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]
                success = await self.database.delete_trigger_registration(
                    registration_id, user_id, tenant_id
                )
                if not success:
                    raise HTTPException(
                        status_code=500, detail="Failed to delete trigger registration"
                    )
                return {"success": True}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error deleting trigger registration: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/v1/triggers/registrations/{registration_id}/agents")
        async def api_list_registration_agents(
            registration_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """List agents linked to this registration."""
            try:
                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]

                # Get the specific trigger registration
                trigger = await self.database.get_trigger_registration(
                    registration_id, user_id, tenant_id
                )
                if not trigger:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Return the linked agent IDs
                return {
                    "success": True,
                    "data": trigger.get("linked_assistant_ids", []),
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting registration agents: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/triggers/registrations/{registration_id}/agents/{agent_id}")
        async def api_add_agent_to_trigger(
            registration_id: str,
            agent_id: str,
            request: Request,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Add an agent to a trigger registration."""
            try:
                # Parse request body for field selection
                try:
                    body = await request.json()
                    field_selection = body.get("field_selection")
                except:
                    field_selection = None

                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]

                # Verify the trigger registration exists and belongs to the user
                registration = await self.database.get_trigger_registration(
                    registration_id, user_id, tenant_id
                )
                if not registration:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Link the agent to the trigger
                success = await self.database.link_agent_to_trigger(
                    agent_id=agent_id,
                    registration_id=registration_id,
                    created_by=user_id,
                    field_selection=field_selection,
                )

                if not success:
                    raise HTTPException(
                        status_code=500, detail="Failed to link agent to trigger"
                    )

                return {
                    "success": True,
                    "message": f"Successfully linked agent {agent_id} to trigger {registration_id}",
                    "data": {"registration_id": registration_id, "agent_id": agent_id},
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error linking agent to trigger: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.delete(
            "/v1/triggers/registrations/{registration_id}/agents/{agent_id}"
        )
        async def api_remove_agent_from_trigger(
            registration_id: str,
            agent_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Remove an agent from a trigger registration."""
            try:
                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]

                # Verify the trigger registration exists and belongs to the user
                registration = await self.database.get_trigger_registration(
                    registration_id, user_id, tenant_id
                )
                if not registration:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Unlink the agent from the trigger
                success = await self.database.unlink_agent_from_trigger(
                    agent_id=agent_id, registration_id=registration_id
                )

                if not success:
                    raise HTTPException(
                        status_code=500, detail="Failed to unlink agent from trigger"
                    )

                return {
                    "success": True,
                    "message": f"Successfully unlinked agent {agent_id} from trigger {registration_id}",
                    "data": {"registration_id": registration_id, "agent_id": agent_id},
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error unlinking agent from trigger: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.get("/v1/triggers/agents/{agent_id}/registrations")
        async def api_get_agent_registrations(
            agent_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Get all trigger registrations linked to a specific agent."""
            try:
                tenant_id = current_user["tenant_id"]

                registrations = await self.database.get_registrations_for_agent(
                    agent_id, tenant_id
                )

                return {"data": registrations}

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error getting registrations for agent: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @self.app.post("/v1/triggers/registrations/{registration_id}/execute")
        async def api_execute_trigger_now(
            registration_id: str,
            current_user: dict[str, Any] = Depends(get_current_user),
        ) -> dict[str, Any]:
            """Manually execute a cron trigger registration immediately."""
            try:
                user_id = current_user["identity"]
                tenant_id = current_user["tenant_id"]

                # Verify the trigger registration exists and belongs to the user
                registration = await self.database.get_trigger_registration(
                    registration_id, user_id, tenant_id
                )
                if not registration:
                    raise HTTPException(
                        status_code=404,
                        detail="Trigger registration not found or access denied",
                    )

                # Get the template to check if it's a polling trigger
                template_id = registration.get("template_id")
                tmpl = (
                    next((t for t in self.triggers if t.id == template_id), None)
                    if template_id
                    else None
                )
                if not template_id or not tmpl:
                    error_reason = (
                        "missing_template_id"
                        if not template_id
                        else "template_not_found"
                    )
                    logger.error(
                        "manual_execute_error registration_id=%s template_id=%s error=%s",
                        registration_id,
                        template_id,
                        error_reason,
                        stack_info=True,
                    )
                    raise HTTPException(status_code=500, detail="Internal server error")
                if (
                    getattr(tmpl.trigger_type, "value", tmpl.trigger_type)
                    != TriggerType.POLLING.value
                ):
                    raise HTTPException(
                        status_code=400,
                        detail="Manual execution is only supported for polling triggers",
                    )

                # Execute the cron trigger using the cron manager
                agents_invoked = await self.cron_manager.execute_cron_job(registration)

                return {
                    "success": True,
                    "message": f"Manually executed cron trigger {registration_id}",
                    "agents_invoked": agents_invoked,
                }

            except HTTPException:
                raise
            except Exception as e:
                logger.error(f"Error executing trigger: {e}")
                raise HTTPException(status_code=500, detail=str(e))

    async def _handle_request(
        self, trigger: TriggerTemplate, request: Request
    ) -> dict[str, Any]:
        """Handle an incoming request with a handler function."""
        try:
            logger.info(
                "incoming_trigger_request method=%s path=%s trigger_id=%s content_type=%s",
                request.method,
                request.url.path,
                getattr(trigger, "id", "<unknown>"),
                request.headers.get("content-type", ""),
            )

            logger.info(
                "invoking_trigger_handler trigger_id=%s",
                getattr(trigger, "id", "<unknown>"),
            )
            response = await trigger.trigger_handler(request, self.database)
            logger.info(
                "trigger_handler_completed trigger_id=%s",
                getattr(trigger, "id", "<unknown>"),
            )
            return response

        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Error in trigger handler: {e}", exc_info=True)
            raise HTTPException(
                status_code=500, detail=f"Trigger processing failed: {str(e)}"
            )

    def get_app(self) -> FastAPI:
        """Get the FastAPI app instance."""
        return self.app
