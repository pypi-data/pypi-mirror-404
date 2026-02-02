import asyncio
import base64
import os
import uuid
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator, Coroutine, overload

import aiohttp
from .http import request_retryable, resumable_sse
from .ping import ErrorResponse, PingManager, get_ping_manager
from .types import (
    ImageBlock,
    JSONObject,
    JSONValue,
    Provider,
    Server,
    Task,
    TextBlock,
    ToolCallError,
    ToolOutput,
    ToolSpec,
    Literal,
    Mapping,
)

GOOGLE_UNSUPPORTED_SCHEMA_KEYS = {
    "additionalProperties",      # JSON Schema
    "additional_properties",     # sometimes appears already converted
    "title",                     # you already strip, but keep it here too
    "default",                   # often unsupported in function schemas
    "examples",
    "example",
    "patternProperties",
    "oneOf",
    "allOf",
    "anyOf",
    "not",
}

def _sanitize_google_schema(x: Any) -> Any:
    """Recursively remove schema keys that Gemini/Google function calling rejects."""
    if isinstance(x, dict):
        out = {}
        for k, v in x.items():
            if k in GOOGLE_UNSUPPORTED_SCHEMA_KEYS:
                continue
            # If your schemas ever include JSON-Schema $ref/$defs, Gemini expects ref/defs (no $)
            if k == "$ref":
                k = "ref"
            elif k == "$defs":
                k = "defs"
            out[k] = _sanitize_google_schema(v)
        return out
    if isinstance(x, list):
        return [_sanitize_google_schema(i) for i in x]
    return x

def _strip_titles(value: Any) -> Any:
    """Recursively remove JSON schema `title` keys."""
    if isinstance(value, dict):
        return {
            k: _strip_titles(v)
            for k, v in value.items()
            if k != "title"
        }
    if isinstance(value, list):
        return [_strip_titles(item) for item in value]
    return value

@overload
def convert_tool_response(res: Mapping[str, Any], format: None = None) -> list[ToolSpec]: ...

@overload
def convert_tool_response(res: Mapping[str, Any], format: Provider = ...) -> list[dict[str, Any]]: ...

def convert_tool_response(
    res: Mapping[str, Any],
    format: Provider | None = None,
) -> list[ToolSpec] | list[dict[str, Any]]:
    if format is not None:
        if format == "openai":
            return [
                {
                    "type": "function",
                    **{
                        k: _strip_titles(v)
                        for k, v in tool.items()
                        if k not in {"input_schema", "title"}
                    },
                    "parameters": _strip_titles(tool["input_schema"]) if tool.get("input_schema") else None
                }
                for tool in res["tools"]
            ]
        elif format == "openrouter":
            return [
                {
                    "type": "function",
                    "function": {
                        k: _strip_titles(v)
                        for k, v in tool.items()
                        if k not in {"input_schema", "title"}
                    },
                    "parameters": _strip_titles(tool["input_schema"]) if tool.get("input_schema") else None
                }
                for tool in res["tools"]
            ]
        elif format == "anthropic":
            return [
                {
                    "type": "custom",
                    **{
                        k: _strip_titles(v)
                        for k, v in tool.items()
                        if k not in {"input_schema", "title"}
                    },
                    "input_schema": _strip_titles(tool["input_schema"]) if tool.get("input_schema") else None
                }
                for tool in res["tools"]
            ]
        elif format == "google":
            return [
                {
                    **{
                        k: _strip_titles(v)
                        for k, v in tool.items()
                        if k not in {"input_schema", "title"}
                    },
                    "parameters": (
                        _sanitize_google_schema(_strip_titles(tool["input_schema"]))
                        if tool.get("input_schema")
                        else None
                    ),
                }
                for tool in res["tools"]
            ]
        else:
            raise ValueError(f"Invalid format: {format!r}")

    return [ToolSpec(**tool) for tool in res["tools"]]

@asynccontextmanager
async def matrix_sid_provider(client: aiohttp.ClientSession, server_name: str, token: str | None) -> AsyncGenerator[str, None]:
    sid = await request_retryable(client, "POST", "/create_session", expect_json=True, deployment=server_name, token=token)
    try:
        yield sid["sid"]
    finally:
        await request_retryable(client, "POST", "/delete_session", sid=sid["sid"], expect_json=False, deployment=server_name, token=token)

def _finalize_session(session: aiohttp.ClientSession):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        try:
            asyncio.run(session.close())
        except RuntimeError:
            loop = asyncio.new_event_loop()
            loop.run_until_complete(session.close())
            loop.close()
    else:
        if not session.closed:
            loop.create_task(session.close())

class SessionTerminatedError(RuntimeError):
    def __init__(self, reason: str, *, sid: str | None):
        super().__init__(f"Session terminated (sid={sid!r}): {reason}")
        self.reason = reason
        self.sid = sid

class AsyncSession:
    
    def __init__(
        self, 
        env: "AsyncEnvironment", 
        task: Task, 
        secrets: dict[str, str] | None = None, 
        api_key: str | None = None
    ):
        self.client = env.client
        self.task = task
        self.api_key = api_key
        self.base_url = str(env.client._base_url)
        self._sid_cm = None
        self.sid: str | None = None

        self.secrets = {**(secrets or {}), **{"api_key": api_key}}
        
        self._ping_manager = env.ping_manager
        self._ping_id = uuid.uuid4().hex
        self._dead = asyncio.Event()
        self._dead_exception: SessionTerminatedError | None = None

    def _mark_dead(self, exc: ErrorResponse):
        if self._dead_exception is None:
            self._dead_exception = SessionTerminatedError(exc.message, sid=self.sid)
            self._dead.set()

    async def _run_task(self, coro: Coroutine[Any, Any, Any]):
        """Run a coroutine until completion or until the session dies."""
        if self._dead_exception is not None:
            raise self._dead_exception

        task = asyncio.create_task(coro)
        stopper = asyncio.create_task(self._dead.wait())
        try:
            done, pending = await asyncio.wait(
                {task, stopper},
                return_when=asyncio.FIRST_COMPLETED,
            )

            # If session died first
            if self._dead.is_set() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
                if self._dead_exception:
                    raise self._dead_exception

            return await task  # return result (or raise from task)

        finally:
            stopper.cancel()
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def __aenter__(self) -> "AsyncSession":
        self._sid_cm = matrix_sid_provider(self.client, self.task.deployment_name, self.api_key)
        self.sid = await self._sid_cm.__aenter__()
        await request_retryable(
            self.client,
            "POST",
            "/create",
            expect_json=True,
            sid=self.sid,
            deployment=self.task.deployment_name,
            json={
                "env_name": self.task.environment_name,
                "task_spec": self.task.task_spec,
                "secrets": self.secrets
            },
            token=self.api_key
        )

        # register with ping manager
        await self._ping_manager.start_ping(
            task_id=str(self._ping_id),
            url=f"{self.base_url}/ping",
            deployment=self.task.deployment_name,
            session_id=self.sid,
            api_key=self.api_key,
            sleep_time=10,
            on_error=self._mark_dead,
        )

        return self

    async def __aexit__(self, *exc):
        try:
            await self._ping_manager.stop_ping(str(self._ping_id))
        except:
            pass
        
        try:
            await request_retryable(
                self.client,
                "POST",
                "/delete",
                expect_json=False,
                sid=self.sid,
                deployment=self.task.deployment_name,
                token=self.api_key
            )
        except:
            pass
        await self._sid_cm.__aexit__(*exc) # type: ignore
        self._sid_cm = None

    async def get_prompt(self) -> list[TextBlock | ImageBlock]:
        res = await self._run_task(
            request_retryable(
                self.client,
                "GET",
                f"/{self.task.environment_name}/prompt",
                expect_json=True,
                sid=self.sid,
                deployment=self.task.deployment_name,
                token=self.api_key,
            )
        )
        blocks: list[TextBlock | ImageBlock] = []
        for block in res:
            if block["type"] == "text":
                blocks.append(TextBlock(text=block["text"], detail=block["detail"]))
            elif block["type"] == "image":
                blocks.append(ImageBlock(mimeType=block["mimeType"], detail=block["detail"], data=block["data"]))
        return blocks

    @overload
    async def list_tools(self, format: None = None) -> list[ToolSpec]: ...

    @overload
    async def list_tools(self, format: Provider) -> list[dict]: ...

    async def list_tools(self, format: Provider | None = None) -> list[ToolSpec] | list[dict]:
        res = await self._run_task(
            request_retryable(
                self.client,
                "GET",
                f"/{self.task.environment_name}/tools",
                expect_json=True,
                sid=self.sid,
                deployment=self.task.deployment_name,
                token=self.api_key,
            )
        )
        return convert_tool_response(res, format=format)

    async def call_tool(self, tool_name: str, input: JSONObject = {}) -> ToolOutput:
        if not isinstance(input, Mapping):
            raise ToolCallError(f"Tool input must be a dictionary, got {type(input).__name__}")

        if not all(isinstance(k, str) for k in input.keys()):
            non_string_keys = [k for k in input.keys() if not isinstance(k, str)]
            raise ToolCallError(f"All keys in tool input must be strings. Found non-string keys: {non_string_keys}")

        res = await self._run_task(
            resumable_sse(
                self.client,
                f"/{self.task.environment_name}/call",
                sid=self.sid,
                deployment=self.task.deployment_name,
                token=self.api_key,
                json={"name": tool_name, "input": input},
                max_retries=5,
            )
        )

        if res["ok"]:
            blocks: list[TextBlock | ImageBlock] = []
            for block in res["output"]["blocks"]:
                if block["type"] == "text":
                    blocks.append(TextBlock(
                        text=block["text"],
                        detail=block["detail"]
                    ))
                elif block["type"] == "image":
                    blocks.append(ImageBlock(
                        mimeType=block["mimeType"],
                        detail=block["detail"],
                        data=block["data"]
                    ))
            return ToolOutput(
                blocks=blocks,
                metadata=res["output"]["metadata"],
                reward=res["output"]["reward"],
                finished=res["output"]["finished"]
            )
        else:
            raise ToolCallError(res["error"])
        
class AsyncEnvironment:

    def __init__(
        self,
        namespace: str | None,
        name: str,
        variant: str | None,
        client: aiohttp.ClientSession,
        api_key: str | None,
        ping_manager: PingManager
    ) -> None:

        self.server = name
        self.namespace = namespace
        self.name = name
        self.variant = variant
        self.client = client
        self.api_key = api_key
        self.ping_manager = ping_manager

    @property
    def deployment_name(self) -> str:
        if self.namespace is None:
            return self.name
        else:
            return f"{self.namespace}/{self.name}"
        
    async def list_splits(self) -> list[str]:
        async with matrix_sid_provider(self.client, self.deployment_name, self.api_key) as sid:
            path = "/splits" if self.variant is None else f"/{self.variant}/splits"
            res = await request_retryable(self.client, "GET", path, expect_json=True, sid=sid, deployment=self.deployment_name, token=self.api_key)
            return [s["name"] for s in res]

    async def list_tasks(self, split: str) -> list[Task]:
        async with matrix_sid_provider(self.client, self.deployment_name, self.api_key) as sid:
            path = "/tasks" if self.variant is None else f"/{self.variant}/tasks"
            res = await request_retryable(self.client, "POST", path, expect_json=True, sid=sid, deployment=self.deployment_name, json={"split": split}, token=self.api_key)
            return [Task(server_name=self.server, environment_name=res["env_name"], task_spec=task, namespace=self.namespace) for task in res["tasks"]]
        
    async def list_tools(self, format: Provider | None = None) -> list[ToolSpec] | list[dict]:
        path = "/tools" if self.variant is None else f"/{self.variant}/tools"
        async with matrix_sid_provider(self.client, self.deployment_name, self.api_key) as sid:
            res = await request_retryable(self.client, "GET", path, expect_json=True, sid=sid, deployment=self.deployment_name, token=self.api_key)
            return convert_tool_response(res, format=format)
        
    async def get_prompt(self, task: Task) -> str:
        async with matrix_sid_provider(self.client, task.deployment_name, self.api_key) as sid:
            path = "/prompt" if self.variant is None else f"/{self.variant}/prompt"
            res = await request_retryable(self.client, "GET", path, expect_json=True, sid=sid, deployment=task.deployment_name, token=self.api_key)
            return res
        
    def session(self, task: Task, secrets: dict[str, str] | None = None) -> AsyncSession:
        return AsyncSession(self, task, secrets, self.api_key)

class AsyncEnvironmentsAPI:

    def __init__(
        self,
        base_url: str,
        api_key: str,
        ping_start_method: Literal["fork"] | None
    ):
        self.api_key = api_key
        self.ping_manager = get_ping_manager(start_method=ping_start_method)

        self.base_url = base_url
        self.timeout = aiohttp.ClientTimeout(total=None)
        
        # Lazily initialized - connector requires a running event loop
        self._connector: aiohttp.TCPConnector | None = None
        self._clients: dict[str, aiohttp.ClientSession] = {}

    def _get_connector(self) -> aiohttp.TCPConnector:
        """Lazily create the connector when inside a running event loop."""
        if self._connector is None or self._connector.closed:
            self._connector = aiohttp.TCPConnector(limit=1_000_000)
        return self._connector

    def get(self, name: str, variant: str | None = None, base_url: str | None = None) -> AsyncEnvironment:

        parts = name.split("/", maxsplit=1)
        namespace = None
        if len(parts) == 1:
            env_name = parts[0]
        elif len(parts) == 2:
            namespace, env_name = parts
            pass
        else:
            raise RuntimeError("impossible")


        if namespace and self.api_key is None:
            raise ValueError(f"Expected api_key to be passed when accessing remote environment")

        if base_url is None:
            base_url = self.base_url

        if base_url not in self._clients:
            self._clients[base_url] = aiohttp.ClientSession(
                base_url=base_url,
                timeout=self.timeout,
                connector=self._get_connector()
            )
        client = self._clients[base_url]

        return AsyncEnvironment(
            namespace=namespace,
            name=env_name,
            variant=variant,
            client=client,
            api_key=self.api_key,
            ping_manager=self.ping_manager
        )

    def __del__(self):
        for client in self._clients.values():
            _finalize_session(client)
        # Note: ping_manager shutdown is handled by atexit in ping.py

class Session:
    """Synchronous wrapper around AsyncSession."""

    def __init__(self, async_session: AsyncSession, loop: asyncio.AbstractEventLoop):
        self._async = async_session
        self._loop = loop

    @property
    def sid(self) -> str | None:
        return self._async.sid

    @property
    def task(self) -> Task:
        return self._async.task

    def __enter__(self) -> "Session":
        self._loop.run_until_complete(self._async.__aenter__())
        return self

    def __exit__(self, *exc):
        self._loop.run_until_complete(self._async.__aexit__(*exc))

    def get_prompt(self) -> list[TextBlock | ImageBlock]:
        return self._loop.run_until_complete(self._async.get_prompt())

    @overload
    def list_tools(self, format: None = None) -> list[ToolSpec]: ...

    @overload
    def list_tools(self, format: Provider) -> list[dict]: ...

    def list_tools(self, format: Provider | None = None) -> list[ToolSpec] | list[dict]:
        return self._loop.run_until_complete(self._async.list_tools(format))

    def call_tool(self, tool_name: str, input: JSONObject = {}) -> ToolOutput:
        return self._loop.run_until_complete(self._async.call_tool(tool_name, input))


class Environment:
    """Synchronous wrapper around AsyncEnvironment."""

    def __init__(self, async_env: AsyncEnvironment, loop: asyncio.AbstractEventLoop):
        self._async = async_env
        self._loop = loop

    @property
    def server(self) -> str:
        return self._async.server

    @property
    def namespace(self) -> str | None:
        return self._async.namespace

    @property
    def name(self) -> str:
        return self._async.name

    @property
    def variant(self) -> str | None:
        return self._async.variant

    @property
    def deployment_name(self) -> str:
        return self._async.deployment_name

    def list_splits(self) -> list[str]:
        return self._loop.run_until_complete(self._async.list_splits())

    def list_tasks(self, split: str) -> list[Task]:
        return self._loop.run_until_complete(self._async.list_tasks(split))

    @overload
    def list_tools(self, format: None = None) -> list[ToolSpec]: ...

    @overload
    def list_tools(self, format: Provider) -> list[dict]: ...

    def list_tools(self, format: Provider | None = None) -> list[ToolSpec] | list[dict]:
        return self._loop.run_until_complete(self._async.list_tools(format))

    def get_prompt(self, task: Task) -> str:
        return self._loop.run_until_complete(self._async.get_prompt(task))

    def session(self, task: Task, secrets: dict[str, str] | None = None) -> Session:
        async_session = self._async.session(task, secrets)
        return Session(async_session, self._loop)


class EnvironmentsAPI:
    """Synchronous wrapper around AsyncEnvironmentsAPI."""

    def __init__(self, base_url: str, api_key: str):
        self._loop = asyncio.new_event_loop()
        self._async = AsyncEnvironmentsAPI(base_url, api_key, ping_start_method="fork")

    def get(self, name: str, variant: str | None = None, base_url: str | None = None) -> Environment:
        # Run inside the event loop so that lazy connector creation works
        async def _get():
            return self._async.get(name, variant, base_url)
        async_env = self._loop.run_until_complete(_get())
        return Environment(async_env, self._loop)

    def close(self):
        """Clean up resources."""
        async def _close_all():
            for client in self._async._clients.values():
                if not client.closed:
                    await client.close()
        self._loop.run_until_complete(_close_all())
        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        self._loop.close()

    def __enter__(self) -> "EnvironmentsAPI":
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        if not self._loop.is_closed():
            self.close()