"""
Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com

Echo command for testing purposes.
"""

import asyncio
from typing import Any, Dict, Optional

from mcp_proxy_adapter.commands.base import Command, CommandResult


class EchoCommandResult(CommandResult):
    """Result for echo command."""

    def __init__(self, message: str, timestamp: Optional[str] = None):
        """
        Initialize echo command result.

        Args:
            message: Echo message
            timestamp: Optional timestamp
        """
        data = {"message": message}
        if timestamp:
            data["timestamp"] = timestamp
        super().__init__(success=True, data=data, error="")

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """Get JSON schema for result."""
        return {
            "type": "object",
            "properties": {
                "success": {"type": "boolean", "const": True},
                "data": {
                    "type": "object",
                    "properties": {
                        "message": {"type": "string"},
                        "timestamp": {"type": "string"},
                    },
                    "required": ["message"],
                },
            },
            "required": ["success", "data"],
        }


class EchoCommand(Command):
    """Echo command for testing purposes."""

    name = "echo"
    version = "1.0.0"
    descr = "Echo command for testing"
    category = "testing"
    author = "Vasiliy Zdanovskiy"
    email = "vasilyvz@gmail.com"
    result_class = EchoCommandResult

    @classmethod
    def get_schema(cls) -> Dict[str, Any]:
        """
        Return JSON Schema for command parameters.

        Note:
            The framework validates incoming JSON-RPC params against this schema.
            Without an explicit schema, commands implemented with ``**kwargs`` may
            appear to accept no parameters and get rejected.
            
            Built-in commands allow additionalProperties to support proxy systems
            that may add metadata or routing parameters.
        """
        return {
            "type": "object",
            "properties": {
                "message": {
                    "type": "string",
                    "description": "Echo message",
                },
                "timestamp": {
                    "type": "string",
                    "description": "Optional timestamp",
                },
            },
            "additionalProperties": False,  # Strict validation - no additional parameters allowed
        }

    async def execute(self, **kwargs: Any) -> CommandResult:
        """Execute echo command."""
        message = kwargs.get("message", "Hello, World!")
        timestamp = kwargs.get("timestamp")

        # Simulate some processing time
        await asyncio.sleep(0.001)

        return EchoCommandResult(message=message, timestamp=timestamp)
