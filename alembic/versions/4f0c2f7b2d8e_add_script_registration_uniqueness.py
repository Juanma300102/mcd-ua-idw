"""add script registration uniqueness

Revision ID: 4f0c2f7b2d8e
Revises: 9ea5f62ecfe7
Create Date: 2026-06-21 02:20:00.000000

"""
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "4f0c2f7b2d8e"
down_revision: Union[str, Sequence[str], None] = "9ea5f62ecfe7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint("uq_Scripts_name", "Scripts", ["name"])
    op.create_unique_constraint(
        "uq_ScriptVersions_script_id_version_number",
        "ScriptVersions",
        ["script_id", "version_number"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_ScriptVersions_script_id_version_number",
        "ScriptVersions",
        type_="unique",
    )
    op.drop_constraint("uq_Scripts_name", "Scripts", type_="unique")
