"""Tests for controlled script execution and DQM tracking."""

from typing import Any

import pytest

from mcd_ua_idw.db.models import Script, ScriptRun, ScriptVersion
from mcd_ua_idw.script_runner.discovery import ScriptDefinition
from mcd_ua_idw.script_runner.runner import execute_script


class FakeSession:
    def __init__(self, scalar_results: list[Any] | None = None) -> None:
        self.added: list[Any] = []
        self.next_id = 1
        self.scalar_results = scalar_results or []

    async def scalar(self, statement: Any) -> Any:
        if self.scalar_results:
            return self.scalar_results.pop(0)
        return None

    def add(self, model: Any) -> None:
        if getattr(model, "id", None) is None:
            model.id = self.next_id
            self.next_id += 1
        self.added.append(model)

    async def flush(self) -> None:
        return None


class FakeTransaction:
    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.exc_type: type[BaseException] | None = None

    async def __aenter__(self) -> FakeSession:
        return self.session

    async def __aexit__(self, exc_type, exc, traceback) -> bool:
        self.exc_type = exc_type
        return False


class FakeSessionFactory:
    def __init__(self, session: FakeSession) -> None:
        self.session = session
        self.transactions: list[FakeTransaction] = []

    def begin(self) -> FakeTransaction:
        transaction = FakeTransaction(self.session)
        self.transactions.append(transaction)
        return transaction


def existing_script(name: str, script_id: int = 7) -> Script:
    script = Script(name=name)
    script.id = script_id
    return script


def existing_script_version(
    script_id: int = 7,
    version_number: int = 2,
    script_version_id: int = 9,
) -> ScriptVersion:
    version = ScriptVersion(script_id=script_id, version_number=version_number)
    version.id = script_version_id
    return version


@pytest.mark.asyncio
async def test_execute_script_registers_before_execution_and_tracks_success() -> None:
    script_session = FakeSession()
    tracking_session = FakeSession()
    script_factory = FakeSessionFactory(script_session)
    tracking_factory = FakeSessionFactory(tracking_session)
    seen_sessions: list[FakeSession] = []

    async def run(session: FakeSession) -> dict[str, Any]:
        assert [type(model) for model in tracking_session.added] == [
            Script,
            ScriptVersion,
        ]
        seen_sessions.append(session)
        return {"rows_inserted": 2}

    script = ScriptDefinition("tests.load_people", "Load people", 2, run)

    outcome = await execute_script(
        script,
        session_factory=script_factory,  # type: ignore[arg-type]
        tracking_session_factory=tracking_factory,  # type: ignore[arg-type]
    )

    assert outcome.succeeded is True
    assert outcome.output == {"rows_inserted": 2}
    assert seen_sessions == [script_session]
    assert script_factory.transactions[0].exc_type is None
    assert len(tracking_factory.transactions) == 2
    assert [type(model) for model in tracking_session.added] == [
        Script,
        ScriptVersion,
        ScriptRun,
    ]
    registered_script = tracking_session.added[0]
    assert registered_script.name == "load_people"
    script_run = tracking_session.added[-1]
    assert script_run.script_version_id == tracking_session.added[1].id
    assert script_run.results == {
        "status": "success",
        "output": {"rows_inserted": 2},
    }


@pytest.mark.asyncio
async def test_execute_script_registers_first_run_failure() -> None:
    script_session = FakeSession()
    tracking_session = FakeSession()
    script_factory = FakeSessionFactory(script_session)
    tracking_factory = FakeSessionFactory(tracking_session)

    async def run(session: FakeSession) -> dict[str, Any]:
        raise RuntimeError("csv file missing")

    script = ScriptDefinition("tests.load_people", "Load people", 2, run)

    outcome = await execute_script(
        script,
        session_factory=script_factory,  # type: ignore[arg-type]
        tracking_session_factory=tracking_factory,  # type: ignore[arg-type]
    )

    assert outcome.succeeded is False
    assert outcome.error == {"type": "RuntimeError", "message": "csv file missing"}
    assert script_factory.transactions[0].exc_type is RuntimeError
    assert len(tracking_factory.transactions) == 2
    assert [type(model) for model in tracking_session.added] == [
        Script,
        ScriptVersion,
        ScriptRun,
    ]
    script_run = tracking_session.added[-1]
    assert script_run.script_version_id == tracking_session.added[1].id
    assert script_run.results == {
        "status": "failed",
        "error": {"type": "RuntimeError", "message": "csv file missing"},
    }


@pytest.mark.asyncio
async def test_execute_script_reuses_existing_script_and_version() -> None:
    script_model = existing_script("load_people")
    version_model = existing_script_version(script_id=script_model.id)
    tracking_session = FakeSession([script_model, version_model])

    async def run(session: FakeSession) -> dict[str, Any]:
        return {"rows_inserted": 1}

    script = ScriptDefinition("tests.load_people", "Renamed display", 2, run)

    await execute_script(
        script,
        session_factory=FakeSessionFactory(FakeSession()),  # type: ignore[arg-type]
        tracking_session_factory=FakeSessionFactory(tracking_session),  # type: ignore[arg-type]
    )

    assert [type(model) for model in tracking_session.added] == [ScriptRun]
    assert tracking_session.added[0].script_version_id == version_model.id


@pytest.mark.asyncio
async def test_execute_script_creates_new_version_for_existing_script() -> None:
    script_model = existing_script("load_people")
    tracking_session = FakeSession([script_model, None])

    async def run(session: FakeSession) -> dict[str, Any]:
        return {"rows_inserted": 1}

    script = ScriptDefinition("tests.load_people", "Load people", 3, run)

    await execute_script(
        script,
        session_factory=FakeSessionFactory(FakeSession()),  # type: ignore[arg-type]
        tracking_session_factory=FakeSessionFactory(tracking_session),  # type: ignore[arg-type]
    )

    assert [type(model) for model in tracking_session.added] == [
        ScriptVersion,
        ScriptRun,
    ]
    version_model = tracking_session.added[0]
    assert version_model.script_id == script_model.id
    assert version_model.version_number == 3
    assert tracking_session.added[1].script_version_id == version_model.id


@pytest.mark.asyncio
async def test_execute_script_rejects_non_dict_output() -> None:
    tracking_session = FakeSession()

    async def run(session: FakeSession) -> list[str]:
        return ["not", "a", "dict"]

    script = ScriptDefinition("tests.bad", "Bad", 1, run)  # type: ignore[arg-type]

    outcome = await execute_script(
        script,
        session_factory=FakeSessionFactory(FakeSession()),  # type: ignore[arg-type]
        tracking_session_factory=FakeSessionFactory(tracking_session),  # type: ignore[arg-type]
    )

    assert outcome.succeeded is False
    assert outcome.error is not None
    assert outcome.error["type"] == "TypeError"
    assert "must return dict" in outcome.error["message"]
    assert [type(model) for model in tracking_session.added] == [
        Script,
        ScriptVersion,
        ScriptRun,
    ]
