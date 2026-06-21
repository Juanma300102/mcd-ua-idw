from datetime import datetime
from typing import Any, Dict, TYPE_CHECKING

from sqlalchemy import ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from mcd_ua_idw.db.base import Base

if TYPE_CHECKING:
    from mcd_ua_idw.db.models.script_version import ScriptVersion


class ScriptRun(Base):
    __tablename__ = "ScriptRuns"

    run_at: Mapped[datetime] = mapped_column()
    finished_at: Mapped[datetime] = mapped_column()
    results: Mapped[Dict[str, Any]] = mapped_column(JSONB)
    script_version_id: Mapped[int] = mapped_column(
        ForeignKey(column="ScriptVersions.id")
    )

    script_version: Mapped["ScriptVersion"] = relationship(back_populates="script_runs")
