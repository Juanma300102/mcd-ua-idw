from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import TYPE_CHECKING

from mcd_ua_idw.db.base import Base

if TYPE_CHECKING:
    from mcd_ua_idw.db.models.script_version import ScriptVersion


class Script(Base):
    __tablename__ = "Scripts"
    __table_args__ = (UniqueConstraint("name", name="uq_Scripts_name"),)

    name: Mapped[str] = mapped_column(String())

    script_versions: Mapped[list["ScriptVersion"]] = relationship(
        back_populates="script"
    )
