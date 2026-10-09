import pytest
from sqlalchemy import text
def test_fresh_db_exists(fresh_db, admin_engine):
    with admin_engine.connect() as conn:
        result = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = : name"),
            {"name": fresh_db.rsplit("/", 1)[-1]},
        ).scalar()
    assert result == 1 
    