"""
Integration test for help command schema exposure via JSON-RPC API.

This test verifies that the help command schema is properly exposed
through the JSON-RPC API and that clients can discover the cmdname
parameter and examples without guessing.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest

from fastapi.testclient import TestClient
from mcp_proxy_adapter.api.app import create_app


@pytest.fixture
def test_app():
    """Create test FastAPI application."""
    app = create_app(
        title="Test App",
        description="Test application for help command",
        version="1.0.0",
    )
    return app


@pytest.fixture
def client(test_app):
    """Create test client."""
    return TestClient(test_app)


class TestHelpCommandIntegration:
    """Integration tests for help command via JSON-RPC API."""

    def test_help_command_via_jsonrpc_list_all(self, client):
        """Test calling help command via JSON-RPC without parameters."""
        response = client.post(
            "/api/jsonrpc",
            json={"jsonrpc": "2.0", "method": "help", "params": {}, "id": 1},
        )

        assert response.status_code == 200
        data = response.json()

        assert "jsonrpc" in data
        assert data["jsonrpc"] == "2.0"
        assert "result" in data
        assert data["id"] == 1

        result = data["result"]
        assert result.get("success") is True
        assert "data" in result

        # Should contain list of commands
        result_data = result["data"]
        assert "commands" in result_data

    def test_help_command_via_jsonrpc_specific_command(self, client):
        """Test calling help command via JSON-RPC with cmdname parameter."""
        response = client.post(
            "/api/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "help",
                "params": {"cmdname": "help"},
                "id": 2,
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert "result" in data
        result = data["result"]
        assert result.get("success") is True
        assert "data" in result

    def test_help_schema_via_jsonrpc(self, client):
        """Test that help command schema can be retrieved via JSON-RPC."""
        # Call help with cmdname="help" to get help's own schema
        response = client.post(
            "/api/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "help",
                "params": {"cmdname": "help"},
                "id": 1,
            },
        )

        assert response.status_code == 200
        data = response.json()

        result = data["result"]["data"]
        schema = result.get("schema", {})

        # Verify schema includes cmdname parameter
        assert "properties" in schema
        assert "cmdname" in schema["properties"]

        # Verify schema includes examples
        assert "examples" in schema
        assert len(schema["examples"]) >= 2

    def test_help_command_returns_own_schema(self, client):
        """Test that help command returns its own complete schema."""
        # Call help for help command
        response = client.post(
            "/api/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "help",
                "params": {"cmdname": "help"},
                "id": 3,
            },
        )

        assert response.status_code == 200
        data = response.json()

        result = data["result"]
        assert result.get("success") is True

        # Get the schema for help command
        result_data = result["data"]
        assert "schema" in result_data

        schema = result_data["schema"]
        assert "properties" in schema
        assert "cmdname" in schema["properties"]

        # Verify cmdname has description
        cmdname_schema = schema["properties"]["cmdname"]
        assert "description" in cmdname_schema
        assert len(cmdname_schema["description"]) > 0

        # Verify examples are present
        assert "examples" in schema
        examples = schema["examples"]
        assert len(examples) >= 2

    def test_help_command_examples_are_executable(self, client):
        """Test that help command examples can actually be executed."""
        # Get help command schema
        response = client.post(
            "/api/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": "help",
                "params": {"cmdname": "help"},
                "id": 4,
            },
        )

        assert response.status_code == 200
        schema = response.json()["result"]["data"]["schema"]
        examples = schema["examples"]

        # Try to execute each example
        for i, example in enumerate(examples):
            command = example["command"]
            params = example["params"]

            exec_response = client.post(
                "/api/jsonrpc",
                json={
                    "jsonrpc": "2.0",
                    "method": command,
                    "params": params,
                    "id": 100 + i,
                },
            )

            assert (
                exec_response.status_code == 200
            ), f"Example {i} failed to execute: {example}"

            exec_data = exec_response.json()
            assert "result" in exec_data, f"Example {i} returned error: {exec_data}"


class TestHelpCommandDiscovery:
    """Test that help command can be discovered without prior knowledge."""

    def test_discover_help_via_jsonrpc(self, client):
        """Test discovering help command via JSON-RPC help."""
        # Client calls help without params to discover commands
        response = client.post(
            "/api/jsonrpc",
            json={"jsonrpc": "2.0", "method": "help", "params": {}, "id": 1},
        )

        assert response.status_code == 200
        data = response.json()

        result = data["result"]["data"]
        commands = result.get("commands", {})

        # Discover help command
        assert "help" in commands
        help_info = commands["help"]

        # Learn about parameters from schema
        schema = help_info.get("schema", {})
        properties = schema.get("properties", {})

        assert "cmdname" in properties, "Client cannot discover cmdname parameter"

        cmdname_info = properties["cmdname"]
        assert "description" in cmdname_info, "Client cannot learn what cmdname does"

    def test_discover_help_usage_from_help_result(self, client):
        """Test that help result teaches correct usage without guessing."""
        # Get all commands
        response = client.post(
            "/api/jsonrpc",
            json={"jsonrpc": "2.0", "method": "help", "params": {}, "id": 1},
        )

        data = response.json()
        result = data["result"]["data"]

        # Check help_usage section has examples
        help_usage = result.get("help_usage", {})
        assert "examples" in help_usage

        examples = help_usage["examples"]
        assert len(examples) >= 2

        # Find example with cmdname
        example_with_params = None
        for example in examples:
            if "params" in example and "cmdname" in example["params"]:
                example_with_params = example
                break

        assert (
            example_with_params is not None
        ), "No example shows how to use cmdname parameter"


def test_bug_fix_integration():
    """
    Integration test for the bug fix:
    Verify that help command metadata is accessible through the API
    and clients don't need to guess parameters.
    """
    # Create test app
    app = create_app(
        title="Bug Fix Test",
        description="Testing help command metadata exposure",
        version="1.0.0",
    )
    client = TestClient(app)

    # Step 1: Client calls help to discover commands
    response = client.post(
        "/api/jsonrpc", json={"jsonrpc": "2.0", "method": "help", "params": {}, "id": 1}
    )
    assert response.status_code == 200
    data = response.json()
    result = data["result"]["data"]
    commands = result.get("commands", {})

    # Step 2: Client finds help command
    assert "help" in commands

    # Step 3: Client inspects help command schema
    help_schema = commands["help"]["schema"]

    # Step 4: Client discovers cmdname parameter (NO GUESSING)
    assert "properties" in help_schema
    assert "cmdname" in help_schema["properties"]

    # Step 5: Client reads cmdname description
    cmdname_info = help_schema["properties"]["cmdname"]
    assert "description" in cmdname_info

    # Step 6: Client learns usage from examples (NO GUESSING)
    assert "examples" in help_schema
    examples = help_schema["examples"]
    assert len(examples) >= 2

    # Step 7: Client uses examples to make correct calls
    for example in examples:
        response = client.post(
            "/api/jsonrpc",
            json={
                "jsonrpc": "2.0",
                "method": example["command"],
                "params": example["params"],
                "id": 1,
            },
        )
        assert response.status_code == 200

    print(
        "✅ Integration test passed: Clients can discover help command usage without guessing"
    )


if __name__ == "__main__":
    test_bug_fix_integration()
    print("\n✅ Bug fix integration test completed successfully!")
