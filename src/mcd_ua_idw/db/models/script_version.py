from typing import List, TYPE_CHECKING

from sqlalchemy import ForeignKey, Integer, UniqueConstraint
from sqlalchemy.orm import Mapped, relationship, mapped_column

from mcd_ua_idw.db.base import Base

if TYPE_CHECKING:
    from mcd_ua_idw.db.models.script import Script
    from mcd_ua_idw.db.models.script_run import ScriptRun


class ScriptVersion(Base):
    __tablename__ = "ScriptVersions"
    __table_args__ = (
        UniqueConstraint(
            "script_id",
            "version_number",
            name="uq_ScriptVersions_script_id_version_number",
        ),
    )
    version_number: Mapped[int] = mapped_column(Integer)
    script_id: Mapped[int] = mapped_column(ForeignKey(column="Scripts.id"))

    script: Mapped["Script"] = relationship(back_populates="script_versions")
    script_runs: Mapped[List["ScriptRun"]] = relationship(
        back_populates="script_version"
    )
