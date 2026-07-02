"""Tests for the Textual script runner app."""

from datetime import datetime
from typing import Any

import pytest
from textual.widgets import Tree

from mcd_ua_idw.script_runner.discovery import ScriptDefinition
from mcd_ua_idw.script_runner.runner import ScriptRunOutcome
from mcd_ua_idw.script_runner import tui


async def _run_ok(session: Any) -> dict[str, Any]:
    return {"ok": True}


def _label_text(node: Any) -> str:
    return node.label.plain


@pytest.mark.asyncio
async def test_tui_runs_selected_script(monkeypatch: pytest.MonkeyPatch) -> None:
    script = ScriptDefinition("tests.e1_p01_example", "Example", 1, _run_ok)
    calls: list[ScriptDefinition] = []

    async def fake_execute_script(
        selected_script: ScriptDefinition,
    ) -> ScriptRunOutcome:
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
        tree = app.query_one("#script-tree", Tree)
        tree.select_node(tree.root.children[0].children[0])
        await pilot.pause()

    assert calls == [script]


def test_script_tree_groups_scripts_by_prefix() -> None:
    scripts = [
        ScriptDefinition("tests.util_db_check", "DB Check", 1, _run_ok),
        ScriptDefinition("tests.e2_p01_two", "Two", 1, _run_ok),
        ScriptDefinition("tests.ops_healthcheck", "Ops", 1, _run_ok),
        ScriptDefinition("tests.noprefix", "Other", 1, _run_ok),
        ScriptDefinition("tests.e10_p01_ten", "Ten", 1, _run_ok),
        ScriptDefinition("tests.e1_p02_alpha", "Alpha", 1, _run_ok),
    ]

    tree = tui._build_script_tree(scripts)

    group_labels = [_label_text(node) for node in tree.root.children]
    assert group_labels == [
        "Etapa 1",
        "Etapa 2",
        "Etapa 10",
        "Ops",
        "Utilidades",
        "Otros",
    ]
    assert [_label_text(node) for node in tree.root.children[0].children] == [
        "Alpha  v1  (e1_p02_alpha)"
    ]
    assert [_label_text(node) for node in tree.root.children[4].children] == [
        "DB Check  v1  (util_db_check)"
    ]
    assert all(not node.is_expanded for node in tree.root.children)


@pytest.mark.asyncio
async def test_tui_ignores_group_node_selection(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    script = ScriptDefinition("tests.e1_p01_example", "Example", 1, _run_ok)
    calls: list[ScriptDefinition] = []

    async def fake_execute_script(
        selected_script: ScriptDefinition,
    ) -> ScriptRunOutcome:
        calls.append(selected_script)
        return ScriptRunOutcome(
            script=selected_script,
            status="success",
            started_at=datetime(2026, 1, 1),
            finished_at=datetime(2026, 1, 1),
            output={"ok": True},
        )

    monkeypatch.setattr(tui, "execute_script", fake_execute_script)

    app = tui.ScriptRunnerApp(scripts=[script])
    async with app.run_test() as pilot:
        tree = app.query_one("#script-tree", Tree)
        assert not tree.root.children[0].is_expanded
        await pilot.press("enter")
        await pilot.pause()
        assert tree.root.children[0].is_expanded

    assert calls == []
