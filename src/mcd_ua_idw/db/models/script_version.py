from typing import List

from sqlalchemy import Integer
from sqlalchemy.orm import Mapped, relationship, mapped_column

from mcd_ua_idw.db import Base
from mcd_ua_idw.db.models import Script, ScriptRun


class ScriptVersion(Base):
    __tablename__ = "ScriptVersions"
    script: Mapped[Script] = relationship(back_populates="script_versions")
    version_number: Mapped[int] = mapped_column(Integer)
    script_runs: Mapped[List[ScriptRun]] = relationship(back_populates="script_version")
