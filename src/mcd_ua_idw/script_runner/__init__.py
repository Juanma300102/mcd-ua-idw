"""Script discovery and controlled execution primitives."""

from mcd_ua_idw.script_runner.discovery import ScriptDefinition, discover_scripts
from mcd_ua_idw.script_runner.runner import ScriptRunOutcome, execute_script

__all__ = [
    "ScriptDefinition",
    "ScriptRunOutcome",
    "discover_scripts",
    "execute_script",
]
