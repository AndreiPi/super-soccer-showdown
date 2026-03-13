from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "0006"
down_revision: Union[str, None] = "0005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    universe_enum = postgresql.ENUM(name="universeenum", create_type=False)

    op.create_table(
        "showdown_action",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("soccer_match_id", sa.Integer(), nullable=False),
        sa.Column("action_number", sa.Integer(), nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("team_universe", universe_enum, nullable=False),
        sa.Column("scorer", sa.String(length=200), nullable=False),
        sa.Column("scorer_source_id", sa.Integer(), nullable=False),
        sa.Column("against", sa.String(length=200), nullable=False),
        sa.ForeignKeyConstraint(["soccer_match_id"], ["soccer_match.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["soccer_team.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("showdown_action")
