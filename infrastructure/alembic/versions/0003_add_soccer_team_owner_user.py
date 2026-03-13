from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0003"
down_revision: Union[str, None] = "0002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("soccer_team", sa.Column("owner_user_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "fk_soccer_team_owner_user_id_app_user",
        "soccer_team",
        "app_user",
        ["owner_user_id"],
        ["id"],
    )

    # Backfill team owner from existing match ownership when available.
    op.execute(
        """
        UPDATE soccer_team AS team
        SET owner_user_id = match.starwars_user_id
        FROM soccer_match AS match
        WHERE team.id = match.starwars_team_id
          AND team.owner_user_id IS NULL
        """
    )
    op.execute(
        """
        UPDATE soccer_team AS team
        SET owner_user_id = match.pokemon_user_id
        FROM soccer_match AS match
        WHERE team.id = match.pokemon_team_id
          AND team.owner_user_id IS NULL
        """
    )

    # If teams exist without a match link, assign the first user as a fallback.
    op.execute(
        """
        UPDATE soccer_team
        SET owner_user_id = (
            SELECT id FROM app_user ORDER BY id LIMIT 1
        )
        WHERE owner_user_id IS NULL
          AND EXISTS (SELECT 1 FROM app_user)
        """
    )

    op.alter_column("soccer_team", "owner_user_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("fk_soccer_team_owner_user_id_app_user", "soccer_team", type_="foreignkey")
    op.drop_column("soccer_team", "owner_user_id")
