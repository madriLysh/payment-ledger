"""my manual change

Revision ID: 93d7a7b03b49
Revises: 4cdde7d0b519
Create Date: 2026-10-06 11:45:47.661411

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '93d7a7b03b49'
down_revision: Union[str, Sequence[str], None] = '4cdde7d0b519'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("accounts", sa.Column("owner_email", sa.Text()),)
    op.execute("UPDATE accounts SET owner_email = 'unknown@platform.local'")
    op.execute("ALTER TABLE accounts ALTER COLUMN owner_email SET NOT NULL")

def downgrade() -> None:
    """Downgrade schema."""
    op.execute("ALTER TABLE accounts DROP COLUMN owner_email")
