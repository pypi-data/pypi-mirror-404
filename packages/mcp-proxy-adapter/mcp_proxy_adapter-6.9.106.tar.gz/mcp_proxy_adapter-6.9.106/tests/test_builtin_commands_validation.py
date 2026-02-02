"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Test builtin commands parameter validation with additionalProperties: false
"""

import pytest
from mcp_proxy_adapter.commands.echo_command import EchoCommand
from mcp_proxy_adapter.commands.health_command import HealthCommand
from mcp_proxy_adapter.commands.command_registry import registry
from mcp_proxy_adapter.core.errors import ValidationError
from mcp_proxy_adapter.commands.result import ErrorResult


@pytest.fixture(autouse=True)
def register_commands():
    """Register commands for testing."""
    registry.register(EchoCommand, "builtin")
    registry.register(HealthCommand, "builtin")
    yield


@pytest.mark.asyncio
async def test_echo_command_with_valid_params():
    """Test echo command with valid parameters."""
    result = await EchoCommand.run(message="test")
    result_dict = result.to_dict()
    assert result_dict["success"] is True
    assert result_dict["data"]["message"] == "test"


@pytest.mark.asyncio
async def test_echo_command_without_params():
    """Test echo command without parameters (should use default)."""
    result = await EchoCommand.run()
    result_dict = result.to_dict()
    assert result_dict["success"] is True
    assert "message" in result_dict["data"]


@pytest.mark.asyncio
async def test_echo_command_with_invalid_param():
    """Test echo command with invalid parameter (should return ErrorResult)."""
    # Echo command has "additionalProperties": False
    # So passing unknown parameter should return ErrorResult
    result = await EchoCommand.run(message="test", unknown_param="value")
    
    assert isinstance(result, ErrorResult)
    result_dict = result.to_dict()
    assert result_dict["success"] is False
    assert "invalid_parameters" in result.details
    assert "unknown_param" in result.details["invalid_parameters"]


@pytest.mark.asyncio
async def test_health_command_without_params():
    """Test health command without parameters."""
    result = await HealthCommand.run()
    result_dict = result.to_dict()
    assert result_dict["success"] is True
    assert "status" in result_dict["data"]
    assert result_dict["data"]["status"] == "ok"


@pytest.mark.asyncio
async def test_health_command_with_invalid_param():
    """Test health command with invalid parameter (should return ErrorResult)."""
    # Health command has "additionalProperties": False
    # So passing any parameter should return ErrorResult
    result = await HealthCommand.run(unknown_param="value")
    
    assert isinstance(result, ErrorResult)
    result_dict = result.to_dict()
    assert result_dict["success"] is False
    assert "invalid_parameters" in result.details
    assert "unknown_param" in result.details["invalid_parameters"]


@pytest.mark.asyncio
async def test_echo_command_with_context():
    """Test echo command with context (context should be allowed)."""
    # Context is extracted before validation, so this should work
    result = await EchoCommand.run(
        message="test",
        context={"user": {"id": "123", "role": "admin"}}
    )
    result_dict = result.to_dict()
    assert result_dict["success"] is True
    assert result_dict["data"]["message"] == "test"


@pytest.mark.asyncio
async def test_builtin_commands_schema_has_additional_properties_false():
    """Verify builtin commands have additionalProperties: false in schema."""
    echo_schema = EchoCommand.get_schema()
    assert echo_schema.get("additionalProperties") is False
    
    health_schema = HealthCommand.get_schema()
    assert health_schema.get("additionalProperties") is False

