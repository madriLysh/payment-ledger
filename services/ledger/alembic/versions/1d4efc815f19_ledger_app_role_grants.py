"""ledger app role grants

Revision ID: 1d4efc815f19
Revises: 9bde7b365b9c
Create Date: 2026-10-07 22:54:30.195473

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1d4efc815f19'
down_revision: Union[str, Sequence[str], None] = '9bde7b365b9c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

APP_ROLE = "ledger_app"

def upgrade() -> None:
    op.execute(f"CREATE ROLE {APP_ROLE} LOGIN PASSWORD 'ledger_dev_password'")
    op.execute(f"GRANT USAGE ON SCHEMA public TO {APP_ROLE}")
    # SELECT for reading balances/history; INSERT for appending
    op.execute(f"GRANT SELECT, INSERT ON transactions, entries TO {APP_ROLE}")
    op.execute(f"GRANT SELECT, INSERT ON processed_events, accounts TO {APP_ROLE}")
    op.execute(f"GRANT USAGE ON SEQUENCE entries_id_seq TO {APP_ROLE}")
    # The immutability guarantee: no UPDATE, no DELETE, ever.
    op.execute(f"REVOKE UPDATE, DELETE ON transactions, entries FROM {APP_ROLE}")


def downgrade() -> None:
    op.execute(f"REVOKE ALL ON transactions, entries, processed_events, accounts FROM {APP_ROLE}")
    op.execute(f"DROP ROLE {APP_ROLE}")
