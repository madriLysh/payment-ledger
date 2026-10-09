import pytest

from tests.helper import run_alembic
from sqlalchemy import text

def test_migration(fresh_db, admin_engine):
    url= fresh_db
    run_alembic("ledger", url, "head")

    with admin_engine.connect() as conn:
        conn.execute(
            text(f"INSERT INTO ACCOUNTS(owner_type, owner_id, currency) VALUES(merchant, 123, USD)")
        )
        result = conn.execute(
            text("SELECT * FROM ACCOUNTS")
        )

        assert result
