"""make published_at timezone aware

Revision ID: 5f0fa9446420
Revises: c2105dcb17ca
Create Date: 2026-02-11 05:39:43.638424
"""

from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "5f0fa9446420"
down_revision: Union[str, Sequence[str], None] = "c2105dcb17ca"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 🔥 Convert columns to TIMESTAMP WITH TIME ZONE
    op.execute(
        """
        ALTER TABLE outbox_events
        ALTER COLUMN published_at TYPE TIMESTAMP WITH TIME ZONE
        USING published_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE outbox_events
        ALTER COLUMN occurred_at TYPE TIMESTAMP WITH TIME ZONE
        USING occurred_at AT TIME ZONE 'UTC'
        """
    )

    op.execute(
        """
        ALTER TABLE outbox_events
        ALTER COLUMN created_at TYPE TIMESTAMP WITH TIME ZONE
        USING created_at AT TIME ZONE 'UTC'
        """
    )


def downgrade() -> None:
    # Revert back to TIMESTAMP WITHOUT TIME ZONE
    op.execute(
        """
        ALTER TABLE outbox_events
        ALTER COLUMN published_at TYPE TIMESTAMP WITHOUT TIME ZONE
        """
    )

    op.execute(
        """
        ALTER TABLE outbox_events
        ALTER COLUMN occurred_at TYPE TIMESTAMP WITHOUT TIME ZONE
        """
    )

    op.execute(
        """
        ALTER TABLE outbox_events
        ALTER COLUMN created_at TYPE TIMESTAMP WITHOUT TIME ZONE
        """
    )

