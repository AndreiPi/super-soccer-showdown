from typing import Sequence, Union

from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Convert existing naive timestamps to UTC-aware timestamps.
    op.execute(
        """
        ALTER TABLE app_user
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE app_user
        ALTER COLUMN updated_at TYPE TIMESTAMP WITH TIME ZONE
        USING updated_at AT TIME ZONE 'UTC'
        """
    )
    op.execute(
        """
        ALTER TABLE soccer_match
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE soccer_match
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        """
    )
    op.execute(
        """
        ALTER TABLE app_user
        ALTER COLUMN updated_at TYPE TIMESTAMP WITHOUT TIME ZONE
        """
    )
    op.execute(
        """
        ALTER TABLE app_user
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        """
    )
