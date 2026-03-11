from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "app_user",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("username"),
    )

    op.create_table(
        "starwars_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("swapi_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("height_cm", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("power", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("swapi_id"),
    )

    op.create_table(
        "pokemon_data",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("pokeapi_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("height_cm", sa.Integer(), nullable=False),
        sa.Column("weight_kg", sa.Float(), nullable=False),
        sa.Column("power", sa.Float(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("pokeapi_id"),
    )

    op.create_table(
        "soccer_team",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("universe", sa.Enum("starwars", "pokemon", name="universeenum"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "soccer_match",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("starwars_team_id", sa.Integer(), nullable=False),
        sa.Column("pokemon_team_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("starwars_user_id", sa.Integer(), nullable=False),
        sa.Column("pokemon_user_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["pokemon_team_id"], ["soccer_team.id"]),
        sa.ForeignKeyConstraint(["pokemon_user_id"], ["app_user.id"]),
        sa.ForeignKeyConstraint(["starwars_team_id"], ["soccer_team.id"]),
        sa.ForeignKeyConstraint(["starwars_user_id"], ["app_user.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "starwars_team_composition",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Enum("Goalie", "Defence", "Offence", name="positionenum"), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["starwars_data.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["soccer_team.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "pokemon_team_composition",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("team_id", sa.Integer(), nullable=False),
        sa.Column("player_id", sa.Integer(), nullable=False),
        sa.Column("position", sa.Enum("Goalie", "Defence", "Offence", name="positionenum"), nullable=False),
        sa.ForeignKeyConstraint(["player_id"], ["pokemon_data.id"]),
        sa.ForeignKeyConstraint(["team_id"], ["soccer_team.id"]),
        sa.PrimaryKeyConstraint("id"),
    )


def downgrade() -> None:
    op.drop_table("pokemon_team_composition")
    op.drop_table("starwars_team_composition")
    op.drop_table("soccer_match")
    op.drop_table("soccer_team")
    op.drop_table("pokemon_data")
    op.drop_table("starwars_data")
    op.drop_table("app_user")
    op.execute("DROP TYPE IF EXISTS universeenum")
    op.execute("DROP TYPE IF EXISTS positionenum")
