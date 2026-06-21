"""Discover runnable project scripts by their async run(session) interface."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from importlib import import_module
from inspect import Parameter, iscoroutinefunction, signature
from pkgutil import iter_modules
from types import ModuleType
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

ScriptCallable = Callable[[AsyncSession], Any]


@dataclass(frozen=True)
class ScriptDefinition:
    """A runnable script module discovered from the scripts package."""

    module_name: str
    name: str
    version: int
    run: ScriptCallable

    @property
    def slug(self) -> str:
        """Return the stable module slug used as the DQM script identity."""
        return self.module_name.rsplit(".", maxsplit=1)[-1]


def discover_scripts(package_name: str = "mcd_ua_idw.scripts") -> list[ScriptDefinition]:
    """Return modules in ``package_name`` that expose ``async run(session)``."""
    package = import_module(package_name)
    package_paths: Sequence[str] | None = getattr(package, "__path__", None)
    if package_paths is None:
        raise ValueError(f"{package_name!r} is not a package")

    scripts: list[ScriptDefinition] = []
    for module_info in iter_modules(package_paths, prefix=f"{package_name}."):
        if module_info.ispkg:
            continue
        module = import_module(module_info.name)
        definition = script_definition_from_module(module)
        if definition is not None:
            scripts.append(definition)

    return sorted(scripts, key=lambda script: script.name.lower())


def script_definition_from_module(module: ModuleType) -> ScriptDefinition | None:
    """Build a script definition from a module or return ``None`` if invalid."""
    run = getattr(module, "run", None)
    if not iscoroutinefunction(run) or not _accepts_session_parameter(run):
        return None

    name = getattr(module, "NAME", None) or module.__name__.rsplit(".", maxsplit=1)[-1]
    if not hasattr(module, "VERSION"):
        raise ValueError(f"{module.__name__}.VERSION is required")
    version = getattr(module, "VERSION")
    if not isinstance(version, int) or version < 1:
        raise ValueError(f"{module.__name__}.VERSION must be a positive integer")

    return ScriptDefinition(
        module_name=module.__name__,
        name=str(name),
        version=version,
        run=run,
    )


def _accepts_session_parameter(run: Callable[..., Any]) -> bool:
    parameters = list(signature(run).parameters.values())
    positional_parameters = [
        parameter
        for parameter in parameters
        if parameter.kind
        in (Parameter.POSITIONAL_ONLY, Parameter.POSITIONAL_OR_KEYWORD)
    ]
    required_parameters = [
        parameter
        for parameter in positional_parameters
        if parameter.default is Parameter.empty
    ]

    return len(required_parameters) == 1 and required_parameters[0].name == "session"
