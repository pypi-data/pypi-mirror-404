#!/usr/bin/env python3
"""
Tests for handle_json_rpc job_id compatibility (embed_job_status / queue_get_job_status).

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Reproduces bug: job status command called without job_id causes validation error.
Verifies: top-level job_id is copied into params; missing job_id returns clear error.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from mcp_proxy_adapter.api.handlers import handle_json_rpc


@pytest.mark.asyncio
async def test_embed_job_status_without_job_id_returns_error() -> None:
    """Reproduce: call embed_job_status with empty params -> must return error, not call backend."""
    request_data = {"command": "embed_job_status", "params": {}, "id": 1}
    with patch(
        "mcp_proxy_adapter.api.handlers.execute_command", new_callable=AsyncMock
    ) as mock_exec:
        response = await handle_json_rpc(request_data, request_id=None, request=None)

    assert "error" in response
    assert response.get("jsonrpc") == "2.0"
    assert response["error"]["message"] == (
        "Parameter 'job_id' is required. Send params: "
        '{"job_id": "<job_id from chunk response>"}'
    )
    mock_exec.assert_not_called()


@pytest.mark.asyncio
async def test_queue_get_job_status_without_job_id_returns_error() -> None:
    """Reproduce: call queue_get_job_status with empty params -> must return error."""
    request_data = {"command": "queue_get_job_status", "params": {}, "id": 2}
    with patch(
        "mcp_proxy_adapter.api.handlers.execute_command", new_callable=AsyncMock
    ) as mock_exec:
        response = await handle_json_rpc(request_data, request_id=None, request=None)

    assert "error" in response
    assert response["error"]["message"] == (
        "Parameter 'job_id' is required. Send params: "
        '{"job_id": "<job_id from chunk response>"}'
    )
    mock_exec.assert_not_called()


@pytest.mark.asyncio
async def test_embed_job_status_with_job_id_in_params_calls_execute() -> None:
    """Correct usage: job_id in params -> execute_command called with params containing job_id."""
    job_id = "abc-123-uuid"
    request_data = {
        "command": "embed_job_status",
        "params": {"job_id": job_id},
        "id": 3,
    }
    with patch(
        "mcp_proxy_adapter.api.handlers.execute_command", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = {"success": True, "status": "completed"}
        response = await handle_json_rpc(request_data, request_id=None, request=None)

    mock_exec.assert_called_once()
    call_args = mock_exec.call_args
    assert call_args[0][0] == "embed_job_status"
    assert call_args[0][1].get("job_id") == job_id
    assert "result" in response
    assert response["result"]["success"] is True


@pytest.mark.asyncio
async def test_embed_job_status_with_job_id_at_top_level_injected_into_params() -> None:
    """Compatibility: job_id at request top level (not in params) -> copied into params."""
    job_id = "top-level-uuid-456"
    request_data = {
        "command": "embed_job_status",
        "params": {},
        "job_id": job_id,
        "id": 4,
    }
    with patch(
        "mcp_proxy_adapter.api.handlers.execute_command", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = {"success": True, "status": "running"}
        response = await handle_json_rpc(request_data, request_id=None, request=None)

    mock_exec.assert_called_once()
    call_args = mock_exec.call_args
    assert call_args[0][0] == "embed_job_status"
    assert call_args[0][1].get("job_id") == job_id
    assert "result" in response


@pytest.mark.asyncio
async def test_queue_get_job_status_jsonrpc_form_top_level_job_id() -> None:
    """JSON-RPC 2.0 form: method + params empty, job_id at top level -> injected into params."""
    job_id = "jsonrpc-top-level-789"
    request_data = {
        "jsonrpc": "2.0",
        "method": "queue_get_job_status",
        "params": {},
        "job_id": job_id,
        "id": 5,
    }
    with patch(
        "mcp_proxy_adapter.api.handlers.execute_command", new_callable=AsyncMock
    ) as mock_exec:
        mock_exec.return_value = {"success": True, "data": {"status": "completed"}}
        await handle_json_rpc(request_data, request_id=None, request=None)

    mock_exec.assert_called_once()
    call_args = mock_exec.call_args
    assert call_args[0][0] == "queue_get_job_status"
    assert call_args[0][1].get("job_id") == job_id
