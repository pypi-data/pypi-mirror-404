import asyncio
import base64
from pathlib import Path
from typing import Literal, Tuple

import aiohttp
from openreward.api.sandboxes.http import request_retryable, resumable_sse
from openreward.api.sandboxes.ping import ErrorResponse, get_ping_manager
from openreward.api.sandboxes.types import PodTerminatedError, SandboxSettings


def _decode_output(output: str) -> str:
    """Output from the terminal is base64 encoded, as it can arbitrary binary data."""
    return base64.b64decode(output.encode('utf-8')).decode('utf-8', 'surrogateescape').rstrip()


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


class AsyncSandboxesAPI:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        settings: SandboxSettings,
        creation_timeout: int = 60 * 30,
        ping_start_method: Literal["fork"] | None = None
    ) -> None:
        self.base_url = base_url
        self.api_key = api_key
        self.settings = settings
        self.creation_timeout = creation_timeout

        # Deferred initialization - created in start()
        self.connector: aiohttp.TCPConnector | None = None
        self.client: aiohttp.ClientSession | None = None
        self.client_id: str | None = None

        self._ping_manager = get_ping_manager(start_method=ping_start_method)
        self._ping_id = id(self)
        self._dead = asyncio.Event()
        self._dead_exception: BaseException | None = None

    def _ensure_alive(self):
        if self._dead_exception is not None:
            raise self._dead_exception

    def _ensure_started(self):
        if self.client is None:
            raise RuntimeError("Sandbox not started. Call start() or use as context manager.")

    def _mark_dead(self, exc: ErrorResponse):
        if self._dead_exception is None:
            self._dead_exception = PodTerminatedError(exc.message, client_id=self.client_id)
            self._dead.set()

    async def run(
        self,
        cmd: str,
        timeout: float | None = 300,
        max_bytes: int | None = 10_000_000,
    ) -> Tuple[str, int]:
        """Run a command in the container."""
        self._ensure_alive()
        self._ensure_started()

        assert self.client is not None
        run_task = asyncio.create_task(resumable_sse(
            self.client,
            "/run",
            token=self.api_key,
            json={
                "cmd": cmd,
                "timeout_s": timeout,
                "max_bytes": max_bytes,
                "shell": "/bin/bash",
            },
            client_id=self.client_id,
            max_retries=5,
        ))
        dead_task = asyncio.create_task(self._dead.wait())

        done, pending = await asyncio.wait(
            [run_task, dead_task],
            return_when=asyncio.FIRST_COMPLETED,
        )

        if dead_task in done:
            run_task.cancel()
            try:
                await run_task
            except asyncio.CancelledError:
                pass
            raise self._dead_exception or PodTerminatedError("Pod died", client_id=self.client_id)

        dead_task.cancel()
        try:
            res = await run_task
        finally:
            try:
                await dead_task
            except asyncio.CancelledError:
                pass

        return_code = res["return_code"]
        output = _decode_output(res["output"])
        return output, return_code

    async def check_run(
        self,
        cmd: str,
        timeout: float | None = 300,
        max_bytes: int | None = 10_000_000,
    ) -> str:
        """Run a command in the container and raise an error if it fails."""
        self._ensure_alive()
        output, exit_code = await self.run(cmd, timeout=timeout, max_bytes=max_bytes)
        if exit_code != 0:
            raise RuntimeError(f"Command failed: {cmd}\n{output}")
        return output

    async def upload(self, local_path: str | Path, container_path: str) -> None:
        """Upload a single file from local filesystem to the container."""
        self._ensure_alive()
        local_path = Path(local_path)
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        max_size = 10 * 1024 * 1024
        if local_path.stat().st_size > max_size:
            raise ValueError(f"File is too large: {local_path.stat().st_size} bytes > {max_size} bytes")

        file_content = local_path.read_bytes()
        encoded_content = base64.b64encode(file_content).decode('ascii')

        cmd = f"echo '{encoded_content}' | base64 -d > {container_path}"
        await self.check_run(cmd, max_bytes=max_size)

    async def download(self, container_path: str) -> bytes:
        """Download a single file from the container."""
        self._ensure_alive()
        cmd = f"base64 {container_path}"
        output = await self.check_run(cmd, max_bytes=None)

        try:
            file_content = base64.b64decode(output.encode('ascii'))
            return file_content
        except Exception as e:
            raise RuntimeError(f"Failed to decode and write file: {e}")

    async def start(self) -> None:
        # Create aiohttp client (requires running event loop)
        self.connector = aiohttp.TCPConnector(limit=1_000_000)
        self.client = aiohttp.ClientSession(base_url=self.base_url, connector=self.connector)

        # Get client id
        res = await resumable_sse(
            self.client,
            "/create",
            token=self.api_key,
            json={
                "creation_request": self.settings.model_dump(),
            },
            max_retries=3,
            timeout=self.creation_timeout,
        )
        self.client_id = res["client_id"]

        # Register with ping manager
        assert self.client_id is not None
        await self._ping_manager.start_ping(
            task_id=str(self._ping_id),
            url=f"{self.base_url}/ping",
            client_id=self.client_id,
            api_key=self.api_key,
            sleep_time=10,
            on_error=self._mark_dead,
        )

    async def stop(self) -> None:
        # Stop ping
        try:
            await self._ping_manager.stop_ping(str(self._ping_id))
        except:
            pass

        # Delete pod
        if self.client is not None:
            try:
                await request_retryable(
                    self.client,
                    "POST",
                    "/delete",
                    expect_json=True,
                    token=self.api_key,
                    client_id=self.client_id,
                )
            except:
                pass

            # Close client
            if not self.client.closed:
                await self.client.close()

    async def __aenter__(self):
        await self.start()
        return self

    async def __aexit__(self, *_):
        await self.stop()

    def __del__(self):
        if self.client is not None:
            _finalize_session(self.client)


class SandboxesAPI:
    """Synchronous wrapper around AsyncSandboxesAPI."""

    def __init__(
        self,
        base_url: str,
        api_key: str,
        settings: SandboxSettings,
        creation_timeout: int = 60 * 30,
    ) -> None:
        self._loop = asyncio.new_event_loop()
        self._base_url = base_url
        self._api_key = api_key
        self._settings = settings
        self._creation_timeout = creation_timeout
        self._async: AsyncSandboxesAPI | None = None

    @property
    def client_id(self) -> str | None:
        return self._async.client_id if self._async else None

    def run(
        self,
        cmd: str,
        timeout: float | None = 300,
        max_bytes: int | None = 10_000_000,
    ) -> Tuple[str, int]:
        """Run a command in the container."""
        if self._async is None:
            raise RuntimeError("Sandbox not started. Call start() or use as context manager.")
        return self._loop.run_until_complete(
            self._async.run(cmd, timeout=timeout, max_bytes=max_bytes)
        )

    def check_run(
        self,
        cmd: str,
        timeout: float | None = 300,
        max_bytes: int | None = 10_000_000,
    ) -> str:
        """Run a command in the container and raise an error if it fails."""
        if self._async is None:
            raise RuntimeError("Sandbox not started. Call start() or use as context manager.")
        return self._loop.run_until_complete(
            self._async.check_run(cmd, timeout=timeout, max_bytes=max_bytes)
        )

    def upload(self, local_path: str | Path, container_path: str) -> None:
        """Upload a single file from local filesystem to the container."""
        if self._async is None:
            raise RuntimeError("Sandbox not started. Call start() or use as context manager.")
        self._loop.run_until_complete(
            self._async.upload(local_path, container_path)
        )

    def download(self, container_path: str) -> bytes:
        """Download a single file from the container."""
        if self._async is None:
            raise RuntimeError("Sandbox not started. Call start() or use as context manager.")
        return self._loop.run_until_complete(
            self._async.download(container_path)
        )

    def start(self) -> None:
        # Create async client inside the event loop
        self._async = AsyncSandboxesAPI(
            base_url=self._base_url,
            api_key=self._api_key,
            settings=self._settings,
            creation_timeout=self._creation_timeout,
            ping_start_method="fork"
        )
        self._loop.run_until_complete(self._async.start())

    def stop(self) -> None:
        if self._async is not None:
            self._loop.run_until_complete(self._async.stop())

    def close(self):
        """Clean up resources."""
        self.stop()
        self._loop.run_until_complete(self._loop.shutdown_asyncgens())
        self._loop.close()

    def __enter__(self) -> "SandboxesAPI":
        self.start()
        return self

    def __exit__(self, *exc):
        self.close()

    def __del__(self):
        if not self._loop.is_closed():
            self.close()