import pytest

from helper import run_alembic, make_engine
from sqlalchemy import text

def test_migration(fresh_db):
    url= fresh_db
    run_alembic("ledger", url, "head")
    engine = make_engine(url)
    
    with engine.connect() as conn:
        conn.execute(
            text("INSERT INTO ACCOUNTS(owner_type, owner_id, currency) VALUES(:ot, :oi, :cur)"),{"ot": "merchant", "oi": "123", "cur": "USD"}
        )
        result = conn.execute(
            text("SELECT * FROM ACCOUNTS")
        )

        assert result.scalar_one() == 1
