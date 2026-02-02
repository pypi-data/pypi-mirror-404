import pytest
import asyncio
import uvicorn
import aiohttp
from threading import Thread
from typing import Generator
from openreward import OpenReward
from openreward.environments import Environment, Server, tool, ToolOutput
from openreward.environments.types import Blocks, TextBlock, JSONObject


class Foo(Environment):
    def setup(self):
        pass

    def teardown(self):
        pass

    def get_prompt(self) -> Blocks:
        return [TextBlock(text=str(self.task_spec["foo"]))]

    @classmethod
    def list_splits(cls) -> list[str]:
        return ["train"]

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        assert split == "train"
        return [{"foo": "bar"}]

    @tool
    async def submit(self) -> ToolOutput:
        return ToolOutput(blocks=[TextBlock(text="foo_result")], reward=1.0, finished=True)


class Bar(Environment):
    def setup(self):
        pass

    def teardown(self):
        pass

    def get_prompt(self) -> Blocks:
        return [TextBlock(text=str(self.task_spec["bar"]))]

    @classmethod
    def list_splits(cls) -> list[str]:
        return ["test"]

    @classmethod
    def list_tasks(cls, split: str) -> list[JSONObject]:
        assert split == "test"
        return [{"bar": "baz"}]

    @tool
    async def submit(self) -> ToolOutput:
        return ToolOutput(blocks=[TextBlock(text="bar_result")], reward=0.5, finished=True)


async def wait_for_server(base_url: str, timeout: float = 5.0):
    """Wait for server to be ready using aiohttp."""
    import time
    start = time.monotonic()
    async with aiohttp.ClientSession() as session:
        while time.monotonic() - start < timeout:
            try:
                async with session.get(f"{base_url}/health", timeout=aiohttp.ClientTimeout(total=0.5)) as resp:
                    if resp.status == 200:
                        return
            except Exception:
                pass
            await asyncio.sleep(0.1)
    pytest.fail("Server failed to start")


@pytest.fixture(scope="module")
def server() -> Generator[str, None, None]:
    """Start the server in a background thread and yield the base URL."""
    import os
    os.environ["OPENREWARD_LOCAL"] = "1"
    
    host = "localhost"
    port = 8080
    app = Server(environments=[Foo, Bar]).app
    config = uvicorn.Config(app, host=host, port=port, log_level="warning")
    server_instance = uvicorn.Server(config)
    
    thread = Thread(target=server_instance.run, daemon=True)
    thread.start()
    
    base_url = f"http://{host}:{port}"
    asyncio.run(wait_for_server(base_url))
    
    yield base_url
    server_instance.should_exit = True


@pytest.fixture
def client(server: str) -> OpenReward:
    return OpenReward(base_url=server, api_key="test")


# =============================================================================
# Tests for default environment (no variant specified, uses first env)
# =============================================================================

@pytest.mark.asyncio
async def test_default_variant_splits(client: OpenReward):
    """Test that default variant works - redirects to first environment."""
    environment = client.environments.get("foo")  # No variant specified
    splits = await environment.list_splits()
    assert splits == ["train"]


@pytest.mark.asyncio
async def test_default_variant_tools(client: OpenReward):
    """Test listing tools with default variant."""
    environment = client.environments.get("foo")
    tools = await environment.list_tools()
    tool_names = [t.name for t in tools]
    assert "submit" in tool_names


@pytest.mark.asyncio
async def test_default_variant_list_tasks(client: OpenReward):
    """Test listing tasks with default variant."""
    environment = client.environments.get("foo")
    tasks = await environment.list_tasks(split="train")
    assert len(tasks) == 1
    assert tasks[0].task_spec == {"foo": "bar"}


@pytest.mark.asyncio
async def test_default_variant_call_tool(client: OpenReward):
    """Test calling tool with default variant."""
    environment = client.environments.get("foo")
    tasks = await environment.list_tasks(split="train")
    async with environment.session(tasks[0]) as session:
        res = await session.call_tool("submit")
        assert res.reward == 1.0
        assert res.finished is True
        assert len(res.blocks) == 1
        assert res.blocks[0].type == "text"
        assert res.blocks[0].text == "foo_result"


# =============================================================================
# Tests for explicit variants
# =============================================================================

@pytest.mark.asyncio
async def test_explicit_variant_foo_splits(client: OpenReward):
    """Test Foo environment with explicit variant."""
    environment = client.environments.get("foo", variant="foo")
    splits = await environment.list_splits()
    assert splits == ["train"]


@pytest.mark.asyncio
async def test_explicit_variant_bar_splits(client: OpenReward):
    """Test Bar environment with explicit variant."""
    environment = client.environments.get("bar", variant="bar")
    splits = await environment.list_splits()
    assert splits == ["test"]


@pytest.mark.asyncio
async def test_explicit_variant_bar_tools(client: OpenReward):
    """Test Bar environment tools with explicit variant."""
    environment = client.environments.get("bar", variant="bar")
    tools = await environment.list_tools()
    tool_names = [t.name for t in tools]
    assert "submit" in tool_names


@pytest.mark.asyncio
async def test_explicit_variant_bar_list_tasks(client: OpenReward):
    """Test Bar environment task listing with explicit variant."""
    environment = client.environments.get("bar", variant="bar")
    tasks = await environment.list_tasks(split="test")
    assert len(tasks) == 1
    assert tasks[0].task_spec == {"bar": "baz"}


@pytest.mark.asyncio
async def test_explicit_variant_bar_call_tool(client: OpenReward):
    """Test Bar environment tool call with explicit variant."""
    environment = client.environments.get("bar", variant="bar")
    tasks = await environment.list_tasks(split="test")
    async with environment.session(tasks[0]) as session:
        res = await session.call_tool("submit")
        assert res.reward == 0.5
        assert res.finished is True
        assert len(res.blocks) == 1
        assert res.blocks[0].type == "text"
        assert res.blocks[0].text == "bar_result"


# =============================================================================
# Tests for multiple variants interaction
# =============================================================================

@pytest.mark.asyncio
async def test_multiple_variants_different_splits(client: OpenReward):
    """Test that different variants return different splits."""
    foo_env = client.environments.get("foo", variant="foo")
    bar_env = client.environments.get("bar", variant="bar")
    
    foo_splits = await foo_env.list_splits()
    bar_splits = await bar_env.list_splits()
    
    assert foo_splits == ["train"]
    assert bar_splits == ["test"]
    assert foo_splits != bar_splits


@pytest.mark.asyncio
async def test_multiple_variants_different_tasks(client: OpenReward):
    """Test that different variants return different tasks."""
    foo_env = client.environments.get("foo", variant="foo")
    bar_env = client.environments.get("bar", variant="bar")
    
    foo_tasks = await foo_env.list_tasks(split="train")
    bar_tasks = await bar_env.list_tasks(split="test")
    
    assert foo_tasks[0].task_spec == {"foo": "bar"}
    assert bar_tasks[0].task_spec == {"bar": "baz"}


@pytest.mark.asyncio
async def test_multiple_variants_concurrent_sessions(client: OpenReward):
    """Test running sessions on multiple variants concurrently."""
    foo_env = client.environments.get("foo", variant="foo")
    bar_env = client.environments.get("bar", variant="bar")
    
    foo_tasks = await foo_env.list_tasks(split="train")
    bar_tasks = await bar_env.list_tasks(split="test")
    
    async with foo_env.session(foo_tasks[0]) as foo_session:
        async with bar_env.session(bar_tasks[0]) as bar_session:
            foo_res = await foo_session.call_tool("submit")
            bar_res = await bar_session.call_tool("submit")
            
            assert foo_res.reward == 1.0
            assert foo_res.blocks[0].text == "foo_result"
            
            assert bar_res.reward == 0.5
            assert bar_res.blocks[0].text == "bar_result"


@pytest.mark.asyncio
async def test_multiple_variants_prompt_isolation(client: OpenReward):
    """Test that prompts are correctly isolated between variants."""
    foo_env = client.environments.get("foo", variant="foo")
    bar_env = client.environments.get("bar", variant="bar")
    
    foo_tasks = await foo_env.list_tasks(split="train")
    bar_tasks = await bar_env.list_tasks(split="test")
    
    async with foo_env.session(foo_tasks[0]) as foo_session:
        foo_prompt = await foo_session.get_prompt()
        assert foo_prompt[0].text == "bar"  # from {"foo": "bar"}
    
    async with bar_env.session(bar_tasks[0]) as bar_session:
        bar_prompt = await bar_session.get_prompt()
        assert bar_prompt[0].text == "baz"  # from {"bar": "baz"}