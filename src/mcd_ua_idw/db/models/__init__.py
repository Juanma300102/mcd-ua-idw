"""ORM model registry imported by Alembic.

Import every mapped model module here when models are introduced.
"""

from mcd_ua_idw.db.models.script_version import ScriptVersion
from mcd_ua_idw.db.models.script import Script
from mcd_ua_idw.db.models.script_run import ScriptRun
from mcd_ua_idw.db.base import Base

__all__ = ["ScriptVersion", "Script", "ScriptRun", "Base"]
