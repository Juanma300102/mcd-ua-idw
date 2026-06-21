"""Tests for the Textual script runner app."""

from datetime import datetime
from typing import Any

import pytest

from mcd_ua_idw.script_runner.discovery import ScriptDefinition
from mcd_ua_idw.script_runner.runner import ScriptRunOutcome
from mcd_ua_idw.script_runner import tui


@pytest.mark.asyncio
async def test_tui_runs_selected_script(monkeypatch: pytest.MonkeyPatch) -> None:
    async def run(session: Any) -> dict[str, Any]:
        return {"ok": True}

    script = ScriptDefinition("tests.example", "Example", 1, run)
    calls: list[ScriptDefinition] = []

    async def fake_execute_script(selected_script: ScriptDefinition) -> ScriptRunOutcome:
        calls.append(selected_script)
        return ScriptRunOutcome(
            script=selected_script,
            status="success",
            started_at=datetime(2026, 1, 1),
            finished_at=datetime(2026, 1, 1),
            output={"ok": True},
        )

    async def fake_dispose_engine() -> None:
        return None

    monkeypatch.setattr(tui, "execute_script", fake_execute_script)
    monkeypatch.setattr(tui, "dispose_engine", fake_dispose_engine)

    app = tui.ScriptRunnerApp(scripts=[script])
    async with app.run_test() as pilot:
        await pilot.press("enter")
        await pilot.pause()

    assert calls == [script]
