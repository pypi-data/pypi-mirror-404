"""
Test suite for help command schema and metadata exposure.

This test verifies that the builtin help command properly exposes
its input schema with the cmdname parameter and examples, preventing
clients from having to guess parameters.

Author: Vasiliy Zdanovskiy
email: vasilyvz@gmail.com
"""

import pytest

from mcp_proxy_adapter.commands.help_command import HelpCommand
from mcp_proxy_adapter.commands.command_registry import registry


class TestHelpCommandSchema:
    """Test help command schema and metadata exposure."""

    def test_help_command_has_schema_method(self):
        """Test that HelpCommand has get_schema class method."""
        assert hasattr(HelpCommand, "get_schema")
        assert callable(HelpCommand.get_schema)

    def test_help_command_schema_structure(self):
        """Test that help command schema has correct structure."""
        schema = HelpCommand.get_schema()

        # Basic schema structure
        assert isinstance(schema, dict)
        assert schema.get("type") == "object"
        assert "properties" in schema
        assert "description" in schema

    def test_help_command_schema_includes_cmdname(self):
        """Test that help command schema includes cmdname parameter."""
        schema = HelpCommand.get_schema()

        properties = schema.get("properties", {})
        assert "cmdname" in properties

        cmdname_schema = properties["cmdname"]
        assert cmdname_schema.get("type") == "string"
        assert "description" in cmdname_schema
        assert len(cmdname_schema["description"]) > 0

        # Verify description is informative
        description = cmdname_schema["description"]
        assert "command" in description.lower()

    def test_help_command_schema_includes_examples(self):
        """Test that help command schema includes usage examples."""
        schema = HelpCommand.get_schema()

        assert "examples" in schema
        examples = schema["examples"]
        assert isinstance(examples, list)
        assert len(examples) >= 2  # At least two examples

        # Check first example (list all commands)
        example1 = examples[0]
        assert "command" in example1
        assert example1["command"] == "help"
        assert "params" in example1
        assert isinstance(example1["params"], dict)
        assert "description" in example1

        # Check second example (get specific command help)
        example2 = examples[1]
        assert "command" in example2
        assert example2["command"] == "help"
        assert "params" in example2
        assert "cmdname" in example2["params"]
        assert "description" in example2

    def test_help_command_schema_no_required_params(self):
        """Test that help command has no required parameters."""
        schema = HelpCommand.get_schema()

        # cmdname should be optional
        required = schema.get("required", [])
        assert "cmdname" not in required

    def test_help_command_schema_additional_properties(self):
        """Test that help command schema declares additionalProperties (True for proxy metadata)."""
        schema = HelpCommand.get_schema()

        # Schema must declare additionalProperties (implementation uses True for proxy/routing params)
        assert "additionalProperties" in schema
        assert isinstance(schema["additionalProperties"], bool)

    @pytest.mark.asyncio
    async def test_help_command_execution_without_cmdname(self):
        """Test that help command executes correctly without cmdname parameter."""
        # Register help command
        registry.register(HelpCommand, "builtin")

        command = HelpCommand()
        result = await command.execute()

        result_dict = result.to_dict()
        assert result_dict.get("success") is True
        assert "data" in result_dict

    @pytest.mark.asyncio
    async def test_help_command_execution_with_cmdname(self):
        """Test that help command executes correctly with cmdname parameter."""
        # Register help command
        registry.register(HelpCommand, "builtin")

        command = HelpCommand()
        result = await command.execute(cmdname="help")

        result_dict = result.to_dict()
        assert result_dict.get("success") is True
        assert "data" in result_dict

    def test_help_command_introspection_via_registry(self):
        """Test that help command schema is accessible via registry."""
        # Register help command
        registry.register(HelpCommand, "builtin")

        # Get command info from registry
        command_info = registry.get_command_info("help")

        assert command_info is not None
        assert "schema" in command_info

        schema = command_info["schema"]
        assert "properties" in schema
        assert "cmdname" in schema["properties"]
        assert "examples" in schema

    def test_help_command_examples_are_complete(self):
        """Test that help command examples are complete and don't encourage guessing."""
        schema = HelpCommand.get_schema()
        examples = schema.get("examples", [])

        for example in examples:
            # Each example must have command, params, and description
            assert "command" in example, f"Example missing 'command': {example}"
            assert "params" in example, f"Example missing 'params': {example}"
            assert "description" in example, f"Example missing 'description': {example}"

            # Description should be informative
            assert (
                len(example["description"]) > 10
            ), f"Example description too short: {example['description']}"

            # Params must be a dict
            assert isinstance(
                example["params"], dict
            ), f"Example params must be dict: {example['params']}"


class TestHelpCommandMetadataCompleteness:
    """Test that help command metadata is complete like man pages."""

    def test_help_command_schema_is_self_documenting(self):
        """Test that help command schema is complete enough to use without guessing."""
        schema = HelpCommand.get_schema()

        # Must have clear description
        assert "description" in schema
        assert len(schema["description"]) > 0

        # Must document all parameters
        properties = schema.get("properties", {})
        for param_name, param_schema in properties.items():
            assert (
                "description" in param_schema
            ), f"Parameter '{param_name}' missing description"
            assert (
                len(param_schema["description"]) > 0
            ), f"Parameter '{param_name}' has empty description"
            assert "type" in param_schema, f"Parameter '{param_name}' missing type"

        # Must have examples
        assert "examples" in schema
        assert len(schema["examples"]) > 0

    def test_help_command_schema_parameters_match_execute_signature(self):
        """Test that help command schema parameters match execute method signature."""
        import inspect

        # Get execute method signature
        sig = inspect.signature(HelpCommand.execute)
        params = sig.parameters

        # Get schema
        schema = HelpCommand.get_schema()
        schema_properties = schema.get("properties", {})

        # Check that cmdname is in both
        assert "cmdname" in params, "cmdname should be in execute signature"
        assert "cmdname" in schema_properties, "cmdname should be in schema"

        # Check that cmdname is optional in execute (has default)
        cmdname_param = params["cmdname"]
        assert (
            cmdname_param.default is not inspect.Parameter.empty
        ), "cmdname should have default value in execute signature"

    def test_help_command_examples_cover_all_use_cases(self):
        """Test that help command examples cover all major use cases."""
        schema = HelpCommand.get_schema()
        examples = schema.get("examples", [])

        # Should have example without params (list all commands)
        has_no_params_example = any(len(ex.get("params", {})) == 0 for ex in examples)
        assert (
            has_no_params_example
        ), "Missing example for listing all commands (no params)"

        # Should have example with cmdname (get specific command)
        has_cmdname_example = any("cmdname" in ex.get("params", {}) for ex in examples)
        assert (
            has_cmdname_example
        ), "Missing example for getting specific command help (with cmdname)"


def test_bug_report_scenario():
    """
    Test the exact scenario described in the bug report:
    - help command supports cmdname parameter
    - schema exposes cmdname parameter
    - examples are available
    - no guessing required
    """
    # Get schema
    schema = HelpCommand.get_schema()

    # Verify cmdname parameter is exposed
    assert "properties" in schema
    assert "cmdname" in schema["properties"]

    cmdname_def = schema["properties"]["cmdname"]
    assert cmdname_def.get("type") == "string"
    assert "description" in cmdname_def

    # Verify examples are present
    assert "examples" in schema
    examples = schema["examples"]
    assert len(examples) >= 2

    # Verify examples include both use cases
    example_without_cmdname = None
    example_with_cmdname = None

    for example in examples:
        params = example.get("params", {})
        if "cmdname" in params:
            example_with_cmdname = example
        elif len(params) == 0:
            example_without_cmdname = example

    assert example_without_cmdname is not None, "Missing example: help without cmdname"
    assert example_with_cmdname is not None, "Missing example: help with cmdname"

    # Verify examples have descriptions
    assert "description" in example_without_cmdname
    assert "description" in example_with_cmdname

    print("✅ Bug fix verified: help command metadata is complete")
    print("   - cmdname parameter exposed: ✓")
    print("   - cmdname has description: ✓")
    print(f"   - examples present: {len(examples)}")
    print("   - no guessing required: ✓")


if __name__ == "__main__":
    # Run quick validation
    test_bug_report_scenario()
    print("\n✅ All quick checks passed!")
