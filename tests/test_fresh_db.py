import pytest
from sqlalchemy import text
def test_fresh_db_exists(fresh_db, admin_engine):
    db_name = fresh_db.rsplit("/", 1)[-1] 

    with admin_engine.connect() as conn:
        exists = conn.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :name"),{"name": db_name}
        ).scalar()

    assert exists == 1 
    