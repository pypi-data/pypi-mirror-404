"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

HTTP handlers for the MCP Proxy Adapter API.
Provides JSON-RPC handling and health/commands endpoints.
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, List, Optional

from fastapi import Request

from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.core.errors import (
    MicroserviceError,
    InvalidRequestError,
    MethodNotFoundError,
    InternalError,
    ValidationError,
    TimeoutError,
)
from mcp_proxy_adapter.core.logging import get_global_logger, RequestLogger


async def _poll_job_status(
    queue_manager: Any,
    job_id: str,
    command_name: str,
    poll_interval: float,
    max_wait_time: Optional[float],
    logger: Any,
) -> Dict[str, Any]:
    """
    Automatically poll job status until completion or timeout.

    This function uses asyncio.sleep (non-blocking) to poll job status
    at specified intervals. It works for all protocols (HTTP, HTTPS, mTLS)
    since it's server-side and doesn't depend on client protocol.

    Args:
        queue_manager: Queue manager instance
        job_id: Job identifier to poll
        command_name: Command name for logging
        poll_interval: Interval in seconds between status checks
        max_wait_time: Maximum time to wait in seconds (None = no limit)
        logger: Logger instance

    Returns:
        Final job result dictionary

    Raises:
        TimeoutError: If max_wait_time is exceeded
        InternalError: If job is not found or other error occurs
    """
    from mcp_proxy_adapter.integrations.queuemgr_integration import (
        QueueJobStatus,
        QueueJobError,
    )

    start_time = time.time()
    last_progress = -1
    last_status = None

    while True:
        # Check timeout
        elapsed = time.time() - start_time
        if max_wait_time is not None and elapsed >= max_wait_time:
            raise TimeoutError(
                f"Polling timeout after {max_wait_time} seconds for job {job_id}",
                data={
                    "job_id": job_id,
                    "command": command_name,
                    "elapsed": elapsed,
                    "max_wait_time": max_wait_time,
                },
            )

        try:
            # Get job status (non-blocking async call)
            job_result = await queue_manager.get_job_status(job_id)
        except QueueJobError as e:
            # Job not found or other queue error
            raise InternalError(
                f"Failed to get job status for {job_id}: {str(e)}",
                data={"job_id": job_id, "command": command_name},
            )

        current_status = job_result.status
        current_progress = job_result.progress

        # Log status changes and progress updates
        if current_status != last_status:
            logger.info(
                "Job %s (command=%s) status changed: %s -> %s",
                job_id,
                command_name,
                last_status or "unknown",
                current_status,
            )
            last_status = current_status

        if current_progress != last_progress:
            logger.debug(
                "Job %s (command=%s) progress: %d%% - %s",
                job_id,
                command_name,
                current_progress,
                job_result.description or "",
            )
            last_progress = current_progress

        # Check if job is in terminal state
        if current_status in (
            QueueJobStatus.COMPLETED,
            QueueJobStatus.FAILED,
            QueueJobStatus.STOPPED,
        ):
            # Return final result
            if current_status == QueueJobStatus.COMPLETED:
                # Return success result with job data
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": current_status,
                    "result": job_result.result or {},
                    "progress": current_progress,
                    "description": job_result.description,
                    "message": f"Command '{command_name}' completed successfully",
                }
            elif current_status == QueueJobStatus.FAILED:
                # Return error result
                return {
                    "success": False,
                    "job_id": job_id,
                    "status": current_status,
                    "error": job_result.error or "Job failed",
                    "result": job_result.result or {},
                    "progress": current_progress,
                    "description": job_result.description,
                    "message": f"Command '{command_name}' failed",
                }
            else:  # STOPPED
                # Return stopped result
                return {
                    "success": False,
                    "job_id": job_id,
                    "status": current_status,
                    "result": job_result.result or {},
                    "progress": current_progress,
                    "description": job_result.description,
                    "message": f"Command '{command_name}' was stopped",
                }

        # Wait before next check (non-blocking async sleep)
        # This works for all protocols since it's server-side
        await asyncio.sleep(poll_interval)


async def execute_command(
    command_name: str,
    params: Optional[Dict[str, Any]],
    request_id: Optional[str] = None,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Execute a registered command by name with parameters.

    If command has use_queue=True, command will be executed via queue and job_id will be returned.
    Otherwise, command will be executed synchronously and result will be returned.

    Raises MethodNotFoundError if command is not found.
    Wraps unexpected exceptions into InternalError.
    """
    logger = RequestLogger(__name__, request_id) if request_id else get_global_logger()

    try:
        logger.info(f"Executing command: {command_name}")

        # Resolve command
        try:
            command_class = registry.get_command(command_name)
        except Exception:
            raise MethodNotFoundError(f"Method not found: {command_name}")

        # Build context (user info if middleware set state)
        context: Dict[str, Any] = {}
        if request is not None and hasattr(request, "state"):
            user_id = getattr(request.state, "user_id", None)
            user_role = getattr(request.state, "user_role", None)
            user_roles = getattr(request.state, "user_roles", None)
            if user_id or user_role or user_roles:
                context["user"] = {
                    "id": user_id,
                    "role": user_role,
                    "roles": user_roles or [],
                }

        # Check if command should be executed via queue
        use_queue = getattr(command_class, "use_queue", False)

        if use_queue:
            # Execute via queue - enqueue quickly and offload heavy work to worker process.
            # HTTP/JSON-RPC layer should only:
            #   1) validate params
            #   2) enqueue CommandExecutionJob
            #   3) return job_id to client as fast as possible (or poll if poll_interval specified)
            #
            # All heavy processing must happen inside the queue worker process so that
            # long-running pipelines do not block the initial HTTP request or hit
            # fixed 30s timeouts in queuemgr start_job / HTTP client.
            try:
                from mcp_proxy_adapter.integrations.queuemgr_integration import (
                    get_global_queue_manager,
                )
                from mcp_proxy_adapter.commands.queue.jobs import CommandExecutionJob
                from mcp_proxy_adapter.commands.hooks import hooks
                import uuid

                # Check for automatic polling parameters
                # First check command parameters, then fall back to config defaults
                poll_interval = params.get("poll_interval") if params else None
                max_wait_time = params.get("max_wait_time") if params else None

                # If not specified in params, try to get from config
                if poll_interval is None:
                    try:
                        from mcp_proxy_adapter.config import get_config

                        config = get_config()
                        if hasattr(config, "model") and hasattr(
                            config.model, "queue_manager"
                        ):
                            queue_config = config.model.queue_manager
                            poll_interval = queue_config.default_poll_interval
                    except Exception:
                        # Config might not be available, use default 0.0
                        poll_interval = 0.0

                if max_wait_time is None:
                    try:
                        from mcp_proxy_adapter.config import get_config

                        config = get_config()
                        if hasattr(config, "model") and hasattr(
                            config.model, "queue_manager"
                        ):
                            queue_config = config.model.queue_manager
                            max_wait_time = queue_config.default_max_wait_time
                    except Exception:
                        # Config might not be available, ignore
                        pass

                # Validate poll_interval: must be >= 0 (0 means no polling)
                if poll_interval is not None:
                    if not isinstance(poll_interval, (int, float)) or poll_interval < 0:
                        raise ValidationError(
                            "poll_interval must be >= 0 (0 means no polling, > 0 enables automatic polling)",
                            data={"poll_interval": poll_interval},
                        )

                # Validate max_wait_time if specified: must be > 0
                if max_wait_time is not None:
                    if (
                        not isinstance(max_wait_time, (int, float))
                        or max_wait_time <= 0
                    ):
                        raise ValidationError(
                            "max_wait_time must be a positive number > 0",
                            data={"max_wait_time": max_wait_time},
                        )

                queue_manager = await get_global_queue_manager()
                job_id = str(uuid.uuid4())

                # Get list of modules to import in child process
                # This ensures commands are available in spawn mode
                auto_import_modules = hooks.get_auto_import_modules()

                # Prepare job parameters - remove poll_interval and max_wait_time before queuing
                # These are handler-level parameters, not command parameters
                command_params = (params or {}).copy()
                command_params.pop("poll_interval", None)
                command_params.pop("max_wait_time", None)

                # Prepare job parameters - heavy processing happens in CommandExecutionJob.run()
                job_params = {
                    "command": command_name,
                    "params": command_params,
                    "context": context,
                    "auto_import_modules": auto_import_modules,  # Pass modules to child process
                }

                # Add job to queue (fast, no heavy work here)
                await queue_manager.add_job(CommandExecutionJob, job_id, job_params)

                # Start job in background to avoid blocking HTTP request on queuemgr timeouts
                async def _start_job_background() -> None:
                    try:
                        await queue_manager.start_job(job_id)
                        logger.info(
                            "Background start for job %s (command=%s) completed",
                            job_id,
                            command_name,
                        )
                    except Exception as start_exc:
                        # Important: do not fail the original HTTP request if queuemgr
                        # reports a timeout or IPC error. The job may still transition
                        # to a terminal state and be observable via queue_get_job_status.
                        logger.warning(
                            "Background start for job %s (command=%s) failed: %s",
                            job_id,
                            command_name,
                            start_exc,
                        )

                asyncio.create_task(_start_job_background())

                # If poll_interval > 0, automatically poll for job completion
                # If poll_interval == 0 or None, return job_id immediately (no polling)
                if poll_interval is not None and poll_interval > 0:
                    return await _poll_job_status(
                        queue_manager=queue_manager,
                        job_id=job_id,
                        command_name=command_name,
                        poll_interval=poll_interval,
                        max_wait_time=max_wait_time,
                        logger=logger,
                    )

                # Return job_id immediately (always returned, even with polling).
                # If poll_interval > 0, additional data (result, status, progress) will be included.
                # Client code can use job_id to track progress or get status later.
                return {
                    "success": True,
                    "job_id": job_id,
                    "status": "pending",
                    "message": f"Command '{command_name}' has been queued for execution",
                }

            except MicroserviceError:
                # Re-raise domain-specific errors (ValidationError, etc.) so that JSON-RPC layer can format them properly
                raise
            except Exception as exc:
                logger.exception(f"Failed to queue command '{command_name}': {exc}")
                raise InternalError(f"Failed to queue command: {str(exc)}")

        # Execute synchronously (default behavior)
        # Ensure params is a dict, not None
        if params is None:
            params = {}
        started_at = time.time()
        try:
            result_obj = await asyncio.wait_for(
                command_class.run(**params, context=context), timeout=30.0
            )
        except asyncio.TimeoutError:
            elapsed = time.time() - started_at
            raise InternalError(f"Command timed out after {elapsed:.2f}s")

        elapsed = time.time() - started_at
        logger.info(f"Command '{command_name}' executed in {elapsed:.3f}s")
        return result_obj.to_dict()

    except MicroserviceError:
        # Re-raise domain-specific errors so that JSON-RPC layer can format them properly.
        raise
    except Exception as exc:
        logger.exception(f"Unhandled error in command '{command_name}': {exc}")
        raise InternalError("Internal error", data={"error": str(exc)})


async def handle_batch_json_rpc(
    batch_requests: List[Dict[str, Any]], request: Optional[Request] = None
) -> List[Dict[str, Any]]:
    """Handle batch JSON-RPC requests."""
    responses: List[Dict[str, Any]] = []
    request_id = getattr(request.state, "request_id", None) if request else None
    for item in batch_requests:
        responses.append(await handle_json_rpc(item, request_id, request))
    return responses


async def handle_json_rpc(
    request_data: Dict[str, Any],
    request_id: Optional[str] = None,
    request: Optional[Request] = None,
) -> Dict[str, Any]:
    """Handle a single JSON-RPC request with strict 2.0 compatibility.

    Also supports simplified form: {"command": "echo", "params": {...}}.
    """
    # Keep handler logic very thin – all heavy work is delegated to execute_command().
    method: Optional[str]
    params: Dict[str, Any]
    json_rpc_id: Any

    if "jsonrpc" in request_data:
        if request_data.get("jsonrpc") != "2.0":
            return _error_response(
                InvalidRequestError("Invalid Request: jsonrpc must be '2.0'"),
                request_data.get("id"),
            )
        method = request_data.get("method")
        params = request_data.get("params") or {}
        json_rpc_id = request_data.get("id")
        if not method:
            return _error_response(
                InvalidRequestError("Invalid Request: method is required"), json_rpc_id
            )
    else:
        # Simplified
        method = request_data.get("command")
        params = request_data.get("params") or {}
        json_rpc_id = request_data.get("id", 1)
        if not method:
            return _error_response(
                InvalidRequestError("Invalid Request: command is required"), json_rpc_id
            )

    # Compatibility: some clients send job_id at request top level instead of in params.
    # Ensure job status commands receive job_id so backend validation does not fail.
    if method in ("embed_job_status", "queue_get_job_status"):
        if not params.get("job_id") and request_data.get("job_id"):
            params = {**params, "job_id": request_data["job_id"]}
        if not params.get("job_id"):
            return _error_response(
                InvalidRequestError(
                    'Parameter \'job_id\' is required. Send params: {"job_id": "<job_id from chunk response>"}'
                ),
                json_rpc_id,
            )

    result = await execute_command(method, params, request_id, request)
    return {"jsonrpc": "2.0", "result": result, "id": json_rpc_id}


def _error_response(error: MicroserviceError, request_id: Any) -> Dict[str, Any]:
    """
    Create JSON-RPC error response.

    Args:
        error: Microservice error instance
        request_id: Request ID from original request

    Returns:
        Dictionary with JSON-RPC error response format
    """
    return {"jsonrpc": "2.0", "error": error.to_dict(), "id": request_id}


async def get_server_health() -> Dict[str, Any]:
    """Return server health info."""
    import os
    import platform
    import sys
    import psutil  # type: ignore[import-untyped]
    from datetime import datetime

    process = psutil.Process(os.getpid())
    start_time = datetime.fromtimestamp(process.create_time())
    uptime_seconds = (datetime.now() - start_time).total_seconds()
    mem = process.memory_info().rss / (1024 * 1024)

    from mcp_proxy_adapter.core.proxy_registration import get_proxy_registration_status

    return {
        "status": "ok",
        "model": "mcp-proxy-adapter",
        "version": "1.0.0",
        "uptime": uptime_seconds,
        "components": {
            "system": {
                "python_version": sys.version,
                "platform": platform.platform(),
                "cpu_count": os.cpu_count(),
            },
            "process": {
                "pid": os.getpid(),
                "memory_usage_mb": mem,
                "start_time": start_time.isoformat(),
            },
            "commands": {"registered_count": len(registry.get_all_commands())},
            "proxy_registration": get_proxy_registration_status(),
        },
    }


async def get_commands_list() -> Dict[str, Dict[str, Any]]:
    """Return list of registered commands with schemas."""
    result: Dict[str, Dict[str, Any]] = {}
    for name, cls in registry.get_all_commands().items():
        schema = cls.get_schema()
        result[name] = {
            "name": name,
            "schema": schema,
            "description": schema.get("description", ""),
        }
    return result


async def handle_heartbeat() -> Dict[str, Any]:
    """Handle heartbeat request from proxy.

    This endpoint is used by the proxy to check if the server is alive.
    Returns server status and metadata.
    """
    logger = get_global_logger()
    logger.debug("💓 Heartbeat request received")

    # Get server info from config if available
    server_name = "mcp-proxy-adapter"
    server_url = "http://localhost:8080"

    try:
        from mcp_proxy_adapter.config import get_config

        cfg = get_config()
        if hasattr(cfg, "model") and hasattr(cfg.model, "server"):
            server_config = cfg.model.server
            if hasattr(server_config, "name"):
                server_name = server_config.name or server_name
            if hasattr(server_config, "host") and hasattr(server_config, "port"):
                protocol = (
                    "https"
                    if (
                        hasattr(server_config, "ssl")
                        and server_config.ssl
                        and server_config.ssl.enabled
                    )
                    else "http"
                )
                host = server_config.host or "localhost"
                port = server_config.port or 8080
                server_url = f"{protocol}://{host}:{port}"
    except Exception:
        pass  # Use defaults if config is not available

    return {
        "status": "ok",
        "server_name": server_name,
        "server_url": server_url,
        "timestamp": time.time(),
    }
