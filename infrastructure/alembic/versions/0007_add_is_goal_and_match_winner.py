from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0007"
down_revision: Union[str, None] = "0006"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "showdown_action",
        sa.Column("is_goal", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )
    op.alter_column("showdown_action", "is_goal", server_default=None)

    op.add_column("soccer_match", sa.Column("winner_team_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_soccer_match_winner_team_id_soccer_team",
        "soccer_match",
        "soccer_team",
        ["winner_team_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint("fk_soccer_match_winner_team_id_soccer_team", "soccer_match", type_="foreignkey")
    op.drop_column("soccer_match", "winner_team_id")
    op.drop_column("showdown_action", "is_goal")
