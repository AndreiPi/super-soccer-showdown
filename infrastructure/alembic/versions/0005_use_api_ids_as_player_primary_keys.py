from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0005"
down_revision: Union[str, None] = "0004"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _has_column(table_name: str, column_name: str) -> bool:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    return any(column["name"] == column_name for column in inspector.get_columns(table_name))


def upgrade() -> None:
    # Simplify migration: remove existing generated data instead of rewriting references.
    op.execute("TRUNCATE TABLE soccer_match, pokemon_team_composition, starwars_team_composition, soccer_team RESTART IDENTITY CASCADE")

    op.execute("ALTER TABLE pokemon_team_composition DROP CONSTRAINT IF EXISTS pokemon_team_composition_player_id_fkey")
    op.execute("ALTER TABLE starwars_team_composition DROP CONSTRAINT IF EXISTS starwars_team_composition_player_id_fkey")

    if _has_column("pokemon_data", "id"):
        op.execute("ALTER TABLE pokemon_data DROP CONSTRAINT IF EXISTS pokemon_data_pkey")
        op.execute("ALTER TABLE pokemon_data DROP CONSTRAINT IF EXISTS pokemon_data_pokeapi_id_key")
        op.execute("ALTER TABLE pokemon_data ADD PRIMARY KEY (pokeapi_id)")
        op.execute("ALTER TABLE pokemon_data DROP COLUMN id")

    if _has_column("starwars_data", "id"):
        op.execute("ALTER TABLE starwars_data DROP CONSTRAINT IF EXISTS starwars_data_pkey")
        op.execute("ALTER TABLE starwars_data DROP CONSTRAINT IF EXISTS starwars_data_swapi_id_key")
        op.execute("ALTER TABLE starwars_data ADD PRIMARY KEY (swapi_id)")
        op.execute("ALTER TABLE starwars_data DROP COLUMN id")

    op.execute(
        "ALTER TABLE pokemon_team_composition ADD CONSTRAINT pokemon_team_composition_player_id_fkey FOREIGN KEY (player_id) REFERENCES pokemon_data (pokeapi_id)"
    )
    op.execute(
        "ALTER TABLE starwars_team_composition ADD CONSTRAINT starwars_team_composition_player_id_fkey FOREIGN KEY (player_id) REFERENCES starwars_data (swapi_id)"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE pokemon_team_composition DROP CONSTRAINT IF EXISTS pokemon_team_composition_player_id_fkey")
    op.execute("ALTER TABLE starwars_team_composition DROP CONSTRAINT IF EXISTS starwars_team_composition_player_id_fkey")

    op.execute("ALTER TABLE pokemon_data DROP CONSTRAINT IF EXISTS pokemon_data_pkey")
    op.execute("ALTER TABLE starwars_data DROP CONSTRAINT IF EXISTS starwars_data_pkey")

    if not _has_column("pokemon_data", "id"):
        op.execute("ALTER TABLE pokemon_data ADD COLUMN id INTEGER")
    if not _has_column("starwars_data", "id"):
        op.execute("ALTER TABLE starwars_data ADD COLUMN id INTEGER")

    op.execute("UPDATE pokemon_data SET id = pokeapi_id")
    op.execute("UPDATE starwars_data SET id = swapi_id")

    op.execute("ALTER TABLE pokemon_data ALTER COLUMN id SET NOT NULL")
    op.execute("ALTER TABLE starwars_data ALTER COLUMN id SET NOT NULL")

    op.execute("ALTER TABLE pokemon_data ADD PRIMARY KEY (id)")
    op.execute("ALTER TABLE starwars_data ADD PRIMARY KEY (id)")

    op.execute("ALTER TABLE pokemon_data ADD CONSTRAINT pokemon_data_pokeapi_id_key UNIQUE (pokeapi_id)")
    op.execute("ALTER TABLE starwars_data ADD CONSTRAINT starwars_data_swapi_id_key UNIQUE (swapi_id)")

    op.execute(
        "ALTER TABLE pokemon_team_composition ADD CONSTRAINT pokemon_team_composition_player_id_fkey FOREIGN KEY (player_id) REFERENCES pokemon_data (id)"
    )
    op.execute(
        "ALTER TABLE starwars_team_composition ADD CONSTRAINT starwars_team_composition_player_id_fkey FOREIGN KEY (player_id) REFERENCES starwars_data (id)"
    )
