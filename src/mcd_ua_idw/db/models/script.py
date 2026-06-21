from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from mcd_ua_idw.db.base import Base

if TYPE_CHECKING:
    from mcd_ua_idw.db.models.script_version import ScriptVersion


class Script(Base):
    __tablename__ = "Scripts"

    name: Mapped[str] = mapped_column(String())

    script_versions: Mapped[list["ScriptVersion"]] = relationship(
        back_populates="script"
    )
