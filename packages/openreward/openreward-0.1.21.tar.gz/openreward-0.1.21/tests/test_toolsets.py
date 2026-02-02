"""Tests for toolset composition system."""

import pytest
from typing import Any
from pydantic import BaseModel, Field

from openreward.environments import Environment, Toolset, tool, ToolOutput, TextBlock
from openreward.environments.types import Blocks, JSONObject


# ===== Test Toolsets =====

class SimpleParams(BaseModel):
    message: str = Field(..., description="Test message")


class SimpleToolset:
    """Simple toolset without sandbox requirement"""

    @tool
    async def simple_tool(self, params: SimpleParams) -> ToolOutput:
        """A simple test tool"""
        return ToolOutput(
            blocks=[TextBlock(text=f"Simple: {params.message}")],
            reward=0.0,
            finished=False,
        )


class MockSandbox:
    """Mock sandbox for testing"""
    async def run(self, cmd: str) -> tuple[str, int]:
        return f"Executed: {cmd}", 0


class SandboxToolset(Toolset):
    """Toolset that requires sandbox"""

    @tool
    async def sandbox_tool(self, params: SimpleParams) -> ToolOutput:
        """Tool that uses sandbox"""
        output, code = await self.sandbox.run("test command")
        return ToolOutput(
            blocks=[TextBlock(text=f"Sandbox: {params.message}, output={output}")],
            reward=0.0,
            finished=False,
        )


class AnotherToolset:
    """Another simple toolset for testing multiple toolsets"""

    @tool
    async def another_tool(self) -> ToolOutput:
        """Another test tool without parameters"""
        return ToolOutput(
            blocks=[TextBlock(text="Another toolset")],
            reward=0.5,
            finished=False,
        )


# ===== Test Environments =====

class EnvWithSimpleToolset(Environment):
    """Environment with a simple toolset"""
    toolsets = [SimpleToolset]

    @classmethod
    def list_splits(cls) -> list[str]:
        return ["train"]

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        return [{"id": "1"}]

    def get_prompt(self) -> Blocks:
        return [TextBlock(text="Test prompt")]

    @tool
    async def env_tool(self) -> ToolOutput:
        """Tool defined on environment itself"""
        return ToolOutput(
            blocks=[TextBlock(text="From environment")],
            reward=1.0,
            finished=True,
        )


class EnvWithSandboxToolset(Environment):
    """Environment with sandbox toolset"""
    toolsets = [SandboxToolset]

    def __init__(self, task_spec: JSONObject = {}, secrets: dict[str, str] = {}):
        super().__init__(task_spec, secrets)
        self.sandbox = MockSandbox()

    @classmethod
    def list_splits(cls) -> list[str]:
        return ["train"]

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        return [{"id": "1"}]

    def get_prompt(self) -> Blocks:
        return [TextBlock(text="Test prompt with sandbox")]


class EnvWithMultipleToolsets(Environment):
    """Environment with multiple toolsets"""
    toolsets = [SimpleToolset, AnotherToolset]

    @classmethod
    def list_splits(cls) -> list[str]:
        return ["train"]

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        return [{"id": "1"}]

    def get_prompt(self) -> Blocks:
        return [TextBlock(text="Test prompt")]


class EnvWithCustomSandboxAttr(Environment):
    """Environment with custom sandbox attribute name"""

    class CustomSandboxToolset(Toolset):
        def __init__(self, env: Any, sandbox_attr: str = "custom_sandbox"):
            super().__init__(env, sandbox_attr)

        @tool
        async def custom_sandbox_tool(self) -> ToolOutput:
            """Tool that uses custom sandbox attribute"""
            output, code = await self.sandbox.run("custom command")
            return ToolOutput(
                blocks=[TextBlock(text=f"Custom sandbox: {output}")],
                reward=0.0,
                finished=False,
            )

    toolsets = [CustomSandboxToolset]

    def __init__(self, task_spec: JSONObject = {}, secrets: dict[str, str] = {}):
        super().__init__(task_spec, secrets)
        self.custom_sandbox = MockSandbox()

    @classmethod
    def list_splits(cls) -> list[str]:
        return ["train"]

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        return [{"id": "1"}]

    def get_prompt(self) -> Blocks:
        return [TextBlock(text="Test prompt")]


# ===== Tests =====

@pytest.mark.asyncio
async def test_list_tools_discovers_toolset_tools():
    """Test that list_tools() discovers tools from class-level toolsets"""
    tools_output = EnvWithSimpleToolset.list_tools()
    tool_names = [t.name for t in tools_output.tools]

    # Should have both environment tool and toolset tool
    assert "env_tool" in tool_names
    assert "simple_tool" in tool_names


@pytest.mark.asyncio
async def test_list_tools_with_multiple_toolsets():
    """Test that list_tools() discovers tools from multiple toolsets"""
    tools_output = EnvWithMultipleToolsets.list_tools()
    tool_names = [t.name for t in tools_output.tools]

    assert "simple_tool" in tool_names
    assert "another_tool" in tool_names


@pytest.mark.asyncio
async def test_call_toolset_tool():
    """Test calling a tool from a toolset"""
    env = EnvWithSimpleToolset(task_spec={"id": "1"})

    result = await env._call_tool("simple_tool", {"message": "Hello"})

    assert result.root.ok is True
    assert len(result.root.output.blocks) == 1
    assert result.root.output.blocks[0].text == "Simple: Hello"


@pytest.mark.asyncio
async def test_call_environment_tool():
    """Test calling a tool defined on environment itself"""
    env = EnvWithSimpleToolset(task_spec={"id": "1"})

    result = await env._call_tool("env_tool", {})

    assert result.root.ok is True
    assert len(result.root.output.blocks) == 1
    assert result.root.output.blocks[0].text == "From environment"
    assert result.root.output.reward == 1.0
    assert result.root.output.finished is True


@pytest.mark.asyncio
async def test_lazy_instantiation():
    """Test that toolsets are lazily instantiated on first tool call"""
    env = EnvWithSimpleToolset(task_spec={"id": "1"})

    # Before any tool call, toolset instances should be empty
    assert len(env._toolset_instances) == 0

    # Call a toolset tool
    await env._call_tool("simple_tool", {"message": "Test"})

    # Now toolset should be instantiated and cached
    assert len(env._toolset_instances) == 1
    assert SimpleToolset in env._toolset_instances


@pytest.mark.asyncio
async def test_toolset_caching():
    """Test that toolset instances are cached and reused"""
    env = EnvWithSimpleToolset(task_spec={"id": "1"})

    # First call instantiates
    await env._call_tool("simple_tool", {"message": "First"})
    first_instance = env._toolset_instances[SimpleToolset]

    # Second call reuses same instance
    await env._call_tool("simple_tool", {"message": "Second"})
    second_instance = env._toolset_instances[SimpleToolset]

    assert first_instance is second_instance


@pytest.mark.asyncio
async def test_toolset_with_sandbox():
    """Test toolset that requires sandbox access"""
    env = EnvWithSandboxToolset(task_spec={"id": "1"})

    result = await env._call_tool("sandbox_tool", {"message": "Test"})

    assert result.root.ok is True
    assert "Sandbox: Test" in result.root.output.blocks[0].text
    assert "Executed: test command" in result.root.output.blocks[0].text


@pytest.mark.asyncio
async def test_custom_sandbox_attribute():
    """Test toolset with custom sandbox attribute name"""
    env = EnvWithCustomSandboxAttr(task_spec={"id": "1"})

    result = await env._call_tool("custom_sandbox_tool", {})

    assert result.root.ok is True
    assert "Custom sandbox" in result.root.output.blocks[0].text


@pytest.mark.asyncio
async def test_tool_not_found():
    """Test calling a non-existent tool"""
    env = EnvWithSimpleToolset(task_spec={"id": "1"})

    result = await env._call_tool("nonexistent_tool", {})

    assert result.root.ok is False
    assert "not a valid tool" in result.root.error


@pytest.mark.asyncio
async def test_multiple_toolsets_tool_calls():
    """Test calling tools from different toolsets"""
    env = EnvWithMultipleToolsets(task_spec={"id": "1"})

    # Call tool from first toolset
    result1 = await env._call_tool("simple_tool", {"message": "Test1"})
    assert result1.root.ok is True
    assert "Simple: Test1" in result1.root.output.blocks[0].text

    # Call tool from second toolset
    result2 = await env._call_tool("another_tool", {})
    assert result2.root.ok is True
    assert "Another toolset" in result2.root.output.blocks[0].text


@pytest.mark.asyncio
async def test_tool_validation_error():
    """Test that tool parameter validation works"""
    env = EnvWithSimpleToolset(task_spec={"id": "1"})

    # Call tool with missing required parameter
    result = await env._call_tool("simple_tool", {})

    assert result.root.ok is False
    assert "validation error" in result.root.error.lower()


@pytest.mark.asyncio
async def test_toolset_tool_schema():
    """Test that toolset tools have proper schema in list_tools()"""
    tools_output = EnvWithSimpleToolset.list_tools()

    simple_tool = next((t for t in tools_output.tools if t.name == "simple_tool"), None)

    assert simple_tool is not None
    assert simple_tool.description == "A simple test tool"
    assert simple_tool.input_schema is not None
    assert "message" in simple_tool.input_schema["properties"]


@pytest.mark.asyncio
async def test_toolset_without_sandbox():
    """Test that simple toolsets work without sandbox"""
    env = EnvWithSimpleToolset(task_spec={"id": "1"})

    # Should not have sandbox attribute
    assert not hasattr(env, 'sandbox')

    # But toolset tools should still work
    result = await env._call_tool("simple_tool", {"message": "No sandbox"})

    assert result.root.ok is True
    assert "Simple: No sandbox" in result.root.output.blocks[0].text


@pytest.mark.asyncio
async def test_tool_name_collision_detected_in_list_tools():
    """Test that list_tools() detects and raises error on tool name collisions"""

    class ToolsetWithSubmit:
        @tool
        async def submit(self) -> ToolOutput:
            return ToolOutput(
                blocks=[TextBlock(text="From toolset")],
                reward=0.0,
                finished=False,
            )

    class EnvWithConflictingTool(Environment):
        toolsets = [ToolsetWithSubmit]

        @classmethod
        def list_splits(cls) -> list[str]:
            return ["train"]

        @classmethod
        def list_tasks(cls, split: str) -> list[JSONObject]:
            return [{"id": "1"}]

        def get_prompt(self) -> Blocks:
            return [TextBlock(text="Test")]

        @tool
        async def submit(self) -> ToolOutput:
            return ToolOutput(
                blocks=[TextBlock(text="From environment")],
                reward=1.0,
                finished=True,
            )

    # list_tools() should raise ValueError on collision
    with pytest.raises(ValueError) as excinfo:
        EnvWithConflictingTool.list_tools()

    assert "Tool name collision" in str(excinfo.value)
    assert "'submit'" in str(excinfo.value)
    assert "ToolsetWithSubmit" in str(excinfo.value)


@pytest.mark.asyncio
async def test_tool_name_collision_detected_in_call_tool():
    """Test that _call_tool() detects and returns error on tool name collisions"""

    class ToolsetWithCollision:
        @tool
        async def my_tool(self) -> ToolOutput:
            return ToolOutput(
                blocks=[TextBlock(text="From toolset")],
                reward=0.0,
                finished=False,
            )

    class EnvWithCollision(Environment):
        toolsets = [ToolsetWithCollision]

        @classmethod
        def list_splits(cls) -> list[str]:
            return ["train"]

        @classmethod
        def list_tasks(cls, split: str) -> list[JSONObject]:
            return [{"id": "1"}]

        def get_prompt(self) -> Blocks:
            return [TextBlock(text="Test")]

        @tool
        async def my_tool(self) -> ToolOutput:
            return ToolOutput(
                blocks=[TextBlock(text="From environment")],
                reward=1.0,
                finished=True,
            )

    # Calling the tool should return an error about collision
    env = EnvWithCollision(task_spec={"id": "1"})
    result = await env._call_tool("my_tool", {})

    assert result.root.ok is False
    assert "Tool name collision" in result.root.error
    assert "'my_tool'" in result.root.error
    assert "ToolsetWithCollision" in result.root.error
