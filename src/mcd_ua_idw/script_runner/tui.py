"""Textual application for running project scripts with managed DB sessions."""

from mcd_ua_idw.db import dispose_engine
from mcd_ua_idw.script_runner.discovery import ScriptDefinition, discover_scripts
from mcd_ua_idw.script_runner.runner import ScriptRunOutcome, execute_script
from textual import on
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Label, ListItem, ListView, Static


class ScriptListItem(ListItem):
    """List item carrying its script definition."""

    def __init__(self, script: ScriptDefinition) -> None:
        self.script = script
        super().__init__(Label(f"{script.name}  v{script.version}  ({script.slug})"))


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
            yield ListView(
                *(ScriptListItem(script) for script in self.scripts),
                id="script-list",
            )
        else:
            yield Static("No runnable scripts found.", id="script-list-empty")
        yield Static("Select a script and press Enter to run it.", id="status")
        yield Footer()

    @on(ListView.Selected, "#script-list")
    def on_script_selected(self, event: ListView.Selected) -> None:
        item = event.item
        if not isinstance(item, ScriptListItem):
            return
        self.run_worker(self._run_script(item.script), exclusive=True)

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


def main() -> None:
    """Console-script boundary for the Textual app."""
    ScriptRunnerApp().run()


if __name__ == "__main__":
    main()
