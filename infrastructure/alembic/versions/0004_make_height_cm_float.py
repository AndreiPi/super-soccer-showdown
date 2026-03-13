from typing import Sequence, Union

from alembic import op

revision: str = "0004"
down_revision: Union[str, None] = "0003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE pokemon_data
        ALTER COLUMN height_cm TYPE DOUBLE PRECISION
        USING height_cm::double precision
        """
    )
    op.execute(
        """
        ALTER TABLE starwars_data
        ALTER COLUMN height_cm TYPE DOUBLE PRECISION
        USING height_cm::double precision
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE starwars_data
        ALTER COLUMN height_cm TYPE INTEGER
        USING ROUND(height_cm)::integer
        """
    )
    op.execute(
        """
        ALTER TABLE pokemon_data
        ALTER COLUMN height_cm TYPE INTEGER
        USING ROUND(height_cm)::integer
        """
    )
