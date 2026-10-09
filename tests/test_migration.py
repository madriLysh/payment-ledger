import pytest

from helper import run_alembic, list_tables

def test_ledger_migrations_create_schema(fresh_db):
    run_alembic("ledger", fresh_db, "head")

    tables = list_tables(fresh_db)

    assert {"accounts", "transactions", "entries", "processed_events"} <= tables
    assert "alembic_version_ledger" in tables