"""Run scripts behind one controlled async SQLAlchemy session boundary."""

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal
import json

from mcd_ua_idw.db import AsyncSessionFactory, get_session_factory
from mcd_ua_idw.db.models import Script, ScriptRun, ScriptVersion
from mcd_ua_idw.script_runner.discovery import ScriptDefinition
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

RunStatus = Literal["success", "failed"]


@dataclass(frozen=True)
class ScriptRegistration:
    """Database identity for the script/version being executed."""

    script_id: int
    script_version_id: int


@dataclass(frozen=True)
class ScriptRunOutcome:
    """Result of executing one discovered script."""

    script: ScriptDefinition
    status: RunStatus
    started_at: datetime
    finished_at: datetime
    output: dict[str, Any] | None = None
    error: dict[str, str] | None = None

    @property
    def succeeded(self) -> bool:
        return self.status == "success"

    def tracking_payload(self) -> dict[str, Any]:
        if self.succeeded:
            return {"status": self.status, "output": self.output or {}}
        return {"status": self.status, "error": self.error or {}}


async def execute_script(
    script: ScriptDefinition,
    *,
    session_factory: AsyncSessionFactory | None = None,
    tracking_session_factory: AsyncSessionFactory | None = None,
) -> ScriptRunOutcome:
    """Register, execute, and track one script run."""
    script_session_factory = session_factory or get_session_factory()
    dqm_session_factory = tracking_session_factory or script_session_factory

    registration = await register_script_version(script, dqm_session_factory)
    started_at = _now()
    try:
        async with script_session_factory.begin() as session:
            output = await script.run(session)
            _require_json_object(output, script)
    except Exception as error:  # noqa: BLE001 - failures are converted into DQM facts.
        outcome = ScriptRunOutcome(
            script=script,
            status="failed",
            started_at=started_at,
            finished_at=_now(),
            error={"type": type(error).__name__, "message": str(error)},
        )
        await record_script_run(outcome, dqm_session_factory, registration)
        return outcome

    outcome = ScriptRunOutcome(
        script=script,
        status="success",
        started_at=started_at,
        finished_at=_now(),
        output=output,
    )
    await record_script_run(outcome, dqm_session_factory, registration)
    return outcome


async def register_script_version(
    script: ScriptDefinition,
    session_factory: AsyncSessionFactory,
) -> ScriptRegistration:
    """Ensure the script and its version exist before script execution."""
    async with session_factory.begin() as session:
        script_version = await _get_or_create_script_version(
            session,
            script_name=script.slug,
            version_number=script.version,
        )
        return ScriptRegistration(
            script_id=script_version.script_id,
            script_version_id=script_version.id,
        )


async def record_script_run(
    outcome: ScriptRunOutcome,
    session_factory: AsyncSessionFactory,
    registration: ScriptRegistration,
) -> None:
    """Persist one DQM tracking row in its own transaction."""
    async with session_factory.begin() as session:
        session.add(
            ScriptRun(
                run_at=outcome.started_at,
                finished_at=outcome.finished_at,
                results=outcome.tracking_payload(),
                script_version_id=registration.script_version_id,
            )
        )


async def _get_or_create_script_version(
    session: AsyncSession,
    *,
    script_name: str,
    version_number: int,
) -> ScriptVersion:
    script = await session.scalar(select(Script).where(Script.name == script_name))
    if script is None:
        script = Script(name=script_name)
        session.add(script)
        await session.flush()

    script_version = await session.scalar(
        select(ScriptVersion).where(
            ScriptVersion.script_id == script.id,
            ScriptVersion.version_number == version_number,
        )
    )
    if script_version is None:
        script_version = ScriptVersion(
            script=script,
            script_id=script.id,
            version_number=version_number,
        )
        session.add(script_version)
        await session.flush()

    return script_version


def _require_json_object(output: Any, script: ScriptDefinition) -> None:
    if not isinstance(output, dict):
        raise TypeError(f"{script.module_name}.run() must return dict[str, Any]")
    try:
        json.dumps(output)
    except TypeError as error:
        raise TypeError(
            f"{script.module_name}.run() returned a non JSON-serializable dict"
        ) from error


def _now() -> datetime:
    """Return a UTC timestamp compatible with the existing naive DateTime columns."""
    return datetime.now(UTC).replace(tzinfo=None)
