"""Textual application for running project scripts with managed DB sessions."""

import re
from dataclasses import dataclass

from mcd_ua_idw.db import dispose_engine
from mcd_ua_idw.script_runner.discovery import ScriptDefinition, discover_scripts
from mcd_ua_idw.script_runner.runner import ScriptRunOutcome, execute_script
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static, Tree

_ETAPA_PREFIX_RE = re.compile(r"^e(?P<number>\d+)_")
_GENERIC_PREFIX_RE = re.compile(r"^(?P<prefix>[a-zA-Z0-9]+)_")
_KNOWN_PREFIX_LABELS = {
    "util": "Utilidades",
}


@dataclass(frozen=True)
class _ScriptGroup:
    """Display grouping information for a script tree branch."""

    label: str
    sort_key: tuple[int, int, str]


class ScriptRunnerApp(App[None]):
    """TUI that discovers scripts and runs the selected one."""

    TITLE = "MCD UA IDW Script Runner"
    BINDINGS = [("q", "quit", "Quit")]

    def __init__(self, scripts: list[ScriptDefinition] | None = None) -> None:
        super().__init__()
        self.scripts = scripts if scripts is not None else discover_scripts()

    def compose(self) -> ComposeResult:
        yield Header()
        if self.scripts:
            yield _build_script_tree(self.scripts)
        else:
            yield Static("No runnable scripts found.", id="script-list-empty")
        yield Static(
            "Toggle a group, select a script, and press Enter to run it.", id="status"
        )
        yield Footer()

    @on(Tree.NodeSelected, "#script-tree")
    def on_script_selected(self, event: Tree.NodeSelected) -> None:
        script = event.node.data
        if not isinstance(script, ScriptDefinition):
            return
        self.run_worker(self._run_script(script), exclusive=True)

    async def _run_script(self, script: ScriptDefinition) -> None:
        status = self.query_one("#status", Static)
        status.update(f"Running {script.name} v{script.version}...")
        try:
            outcome = await execute_script(script)
        finally:
            await dispose_engine()
        status.update(_format_outcome(outcome))


def _format_outcome(outcome: ScriptRunOutcome) -> str:
    if outcome.succeeded:
        return f"✅ {outcome.script.name} completed: {outcome.output or {}}"

    error = outcome.error or {}
    error_type = error.get("type", "Error")
    message = error.get("message", "Unknown failure")
    return f"❌ {outcome.script.name} failed: {error_type}: {message}"


def _build_script_tree(
    scripts: list[ScriptDefinition],
) -> Tree[ScriptDefinition | None]:
    """Build the grouped script tree displayed by the TUI."""
    tree: Tree[ScriptDefinition | None] = Tree("Scripts", id="script-tree")
    tree.show_root = False

    groups: dict[_ScriptGroup, list[ScriptDefinition]] = {}
    for script in scripts:
        groups.setdefault(_group_for_script(script), []).append(script)

    for group in sorted(groups, key=lambda item: item.sort_key):
        group_node = tree.root.add(group.label, data=None, expand=False)
        for script in sorted(
            groups[group], key=lambda item: (item.name.lower(), item.slug.lower())
        ):
            group_node.add_leaf(_format_script_label(script), data=script)

    if tree.root.children:
        tree.move_cursor(tree.root.children[0])

    return tree


def _group_for_script(script: ScriptDefinition) -> _ScriptGroup:
    """Return the friendly tree group for a script definition."""
    slug = script.slug
    etapa_match = _ETAPA_PREFIX_RE.match(slug)
    if etapa_match is not None:
        etapa_number = int(etapa_match.group("number"))
        return _ScriptGroup(
            label=f"Etapa {etapa_number}",
            sort_key=(0, etapa_number, ""),
        )

    prefix_match = _GENERIC_PREFIX_RE.match(slug)
    if prefix_match is not None:
        prefix = prefix_match.group("prefix").lower()
        label = _KNOWN_PREFIX_LABELS.get(prefix, prefix.title())
        return _ScriptGroup(
            label=label,
            sort_key=(1, 0, label.lower()),
        )

    return _ScriptGroup(label="Otros", sort_key=(2, 0, ""))


def _format_script_label(script: ScriptDefinition) -> str:
    """Return the display label for a runnable script leaf."""
    return f"{script.name}  v{script.version}  ({script.slug})"


def main() -> None:
    """Console-script boundary for the Textual app."""
    ScriptRunnerApp().run()


if __name__ == "__main__":
    main()
