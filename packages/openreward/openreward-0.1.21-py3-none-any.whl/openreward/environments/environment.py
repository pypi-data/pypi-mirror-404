import inspect
from abc import ABC, abstractmethod
from logging import getLogger
from typing import Any, Awaitable, Callable, Sequence, TypeVar, get_type_hints

from pydantic import BaseModel, ValidationError

from .types import (Blocks, JSONObject, ListToolsOutput, RunToolError,
                    RunToolOutput, RunToolSuccess, Split, ToolOutput, ToolSpec)
from .utils import maybe_await

T = TypeVar("T")

logger = getLogger(__file__)


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    setattr(fn, "_env_tool", True)
    return fn

class Environment(ABC):
    """
    An environment is an interface to computation that may be stateful. Clients interface with the
    environment through a persistent connection to perform actions. Environments have _tasks_, which
    are JSON objects describing a particular setup and goal state. For example, inside of an Ubuntu
    environment, a task could be to download a file from the internet and save its contents to a csv
    file.
    """
    def __init__(self, task_spec: JSONObject = {}, secrets: dict[str, str] = {}) -> None:
        self.task_spec = task_spec
        self._toolset_instances: dict[type, Any] = {}  # Cache for instantiated toolsets

    def setup(self) -> None | Awaitable[None]:
        """
        Setup the environment. This is called upon the first tool call by a connected client.
        """
        pass

    def teardown(self) -> None | Awaitable[None]:
        """
        Teardown the environment. This is called upon client disconnect.
        """
        pass

    @abstractmethod
    def get_prompt(self) -> Blocks | Awaitable[Blocks]:
        """
        Get a default prompt for the current task. For example, if the task is a question-answer pair,
        returning the question would be a sensible choice here.
        """

    @classmethod
    @abstractmethod
    def list_tasks(cls, split: str) -> Sequence[JSONObject]:
        """
        Get a list of tasks for the given split. Default is the empty list.
        """

    @classmethod
    @abstractmethod
    def list_splits(cls) -> Sequence[Split | str]:
        """
        Get a list of splits for the environment. Default is the empty list.
        """

    @staticmethod
    def _is_tool(fn: Callable[..., Any]) -> bool:
        if not callable(fn) or not getattr(fn, "_env_tool", False):
            return False
        real = inspect.unwrap(fn)
        hints = get_type_hints(real, include_extras=True)
        params = [p for p in inspect.signature(real).parameters.values() if p.name != "self"]
        ret = hints.get("return")
        if len(params) == 0:
            return ret == ToolOutput
        if len(params) == 1:
            pt = hints.get(params[0].name)
            return (
                pt is not None and ret is not None and inspect.isclass(pt)
                and issubclass(pt, BaseModel) and ret == ToolOutput
            )
        return False

    @classmethod
    def list_tools(cls) -> ListToolsOutput:
        out: list[ToolSpec] = []
        env_tool_names: set[str] = set()

        # Discover tools from the class itself (existing behavior)
        for name in dir(cls):
            fn = getattr(cls, name)
            if not cls._is_tool(fn):
                continue
            real = inspect.unwrap(fn)
            hints = get_type_hints(real, include_extras=True)
            params = [p for p in inspect.signature(real).parameters.values() if p.name != "self"]
            schema = None
            if params:
                mdl: type[BaseModel] = hints[params[0].name]  # type: ignore[assignment]
                schema = mdl.model_json_schema() if hasattr(mdl, "model_json_schema") else mdl.schema()  # type: ignore[attr-defined]
            out.append(ToolSpec(name=name, description=(fn.__doc__ or "").strip(), input_schema=schema))
            env_tool_names.add(name)

        # Discover tools from class-level declared toolsets and check for collisions
        if hasattr(cls, 'toolsets'):
            for toolset_cls in cls.toolsets:
                for name in dir(toolset_cls):
                    fn = getattr(toolset_cls, name)
                    if not cls._is_tool(fn):
                        continue

                    # Check for collision with environment tools
                    if name in env_tool_names:
                        raise ValueError(
                            f"Tool name collision: '{name}' is defined in both the environment "
                            f"and toolset '{toolset_cls.__name__}'. Please rename one of them to avoid conflicts."
                        )

                    real = inspect.unwrap(fn)
                    hints = get_type_hints(real, include_extras=True)
                    params = [p for p in inspect.signature(real).parameters.values() if p.name != "self"]
                    schema = None
                    if params:
                        mdl: type[BaseModel] = hints[params[0].name]  # type: ignore[assignment]
                        schema = mdl.model_json_schema() if hasattr(mdl, "model_json_schema") else mdl.schema()  # type: ignore[attr-defined]
                    out.append(ToolSpec(name=name, description=(fn.__doc__ or "").strip(), input_schema=schema))

        return ListToolsOutput(tools=out)

    async def _call_tool(self, name: str, input: JSONObject) -> RunToolOutput:
        # Check if tool exists on self (environment)
        env_fn = getattr(self, name, None)
        has_env_tool = env_fn is not None and self._is_tool(env_fn)

        # Check if tool exists in any toolset
        toolset_fn = None
        toolset_source = None

        if hasattr(self.__class__, 'toolsets'):
            for toolset_cls in self.__class__.toolsets:
                # Check if we've already instantiated this toolset
                if toolset_cls not in self._toolset_instances:
                    # Lazy instantiation: pass environment instance
                    try:
                        self._toolset_instances[toolset_cls] = toolset_cls(self)
                    except TypeError:
                        # If toolset doesn't accept env, try without args
                        try:
                            self._toolset_instances[toolset_cls] = toolset_cls()
                        except Exception as e:
                            logger.error(f"Failed to instantiate toolset {toolset_cls.__name__}: {e}")
                            continue

                toolset_instance = self._toolset_instances[toolset_cls]
                candidate = getattr(toolset_instance, name, None)

                if candidate is not None and self._is_tool(candidate):
                    toolset_fn = candidate
                    toolset_source = toolset_cls.__name__
                    break

        # Check for collision
        if has_env_tool and toolset_fn is not None:
            return RunToolOutput(RunToolError(
                error=f"Tool name collision: '{name}' is defined in both the environment "
                      f"and toolset '{toolset_source}'. Please rename one of them to avoid conflicts."
            ))

        # Determine which function to use
        if has_env_tool:
            fn = env_fn
        elif toolset_fn is not None:
            fn = toolset_fn
        else:
            return RunToolOutput(RunToolError(error=f"{name!r} is not a valid tool"))

        # Execute the tool (same logic as before)
        real = inspect.unwrap(fn)
        hints = get_type_hints(real, include_extras=True)
        params = [p for p in inspect.signature(real).parameters.values() if p.name != "self"]
        if not params:
            res = await maybe_await(fn())
        else:
            mdl: type[BaseModel] = hints[params[0].name]  # type: ignore[assignment]
            try:
                inp = mdl(**input)
            except ValidationError as e:
                return RunToolOutput(RunToolError(error=f"Tool input validation error: {str(e.errors())}"))
            res = await maybe_await(fn(inp))
        if not isinstance(res, ToolOutput):
            raise TypeError(f"{name!r} returned {type(res).__name__}; expected ToolOutput")
        return RunToolOutput(RunToolSuccess(output=res))

    @classmethod
    def name(cls) -> str:
        return cls.__name__