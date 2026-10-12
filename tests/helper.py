from alembic.config import Config as AlembicConfig
import alembic.command
from config import Config as AppConfig
from sqlalchemy import create_engine, NullPool, text
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SERVICES = {
    "payment": (
        REPO_ROOT / "services" / "payment" / "alembic.ini",
        "alembic_version_payment",
        {"merchants", "idempotency_keys", "payments", "outbox"},
    ),
    "ledger": (
        REPO_ROOT / "services" / "ledger" / "alembic.ini",
        "alembic_version_ledger",
        {"accounts", "transactions", "entries", "processed_events"},
    ),
    "notifications": (
        REPO_ROOT / "services" / "notifications" / "alembic.ini",
        "alembic_version_notifications",
        {"webhook_deliveries"},
    ),
}

ALL_VERSION_TABLES = {info[1] for info in SERVICES.values()}
ALL_TABLES = {table for info in SERVICES.values() for table in info[2]}

def run_alembic(service: str, url: str, revision: str) -> None:
    ini_path, _, _ = SERVICES[service]

    cfg = AlembicConfig(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", url)

    AppConfig.DATABASE_URL = url

    if revision == "head":
        alembic.command.upgrade(cfg, "head")
    else:
        alembic.command.downgrade(cfg, revision)

def make_engine(url: str):
    return create_engine(url, poolclass=NullPool)

def list_tables(url: str) -> set[str]:
    engine = make_engine(url) 
    try:
        with engine.connect() as conn:
            rows = conn.execute(
                text(
                    "SELECT table_name FROM information_schema.tables "
                    "WHERE table_schema = 'public'"
                )
            )
            return {row[0] for row in rows}
    finally:
        engine.dispose()

def assert_schema_present(service: str, fresh_db):
    run_alembic(service, fresh_db, "head")
    _, version_table, expected_tables = SERVICES[service]
    tables = list_tables(fresh_db)
    assert expected_tables <= tables
    assert version_table in tables


def assert_schema_absent(service: str, fresh_db):
    run_alembic(service, fresh_db, "base")
    _, version_table, expected_tables = SERVICES[service]
    tables = list_tables(fresh_db)
    assert expected_tables.isdisjoint(tables)
    assert version_table not in tables
    leftover = tables & ALL_VERSION_TABLES
    assert not leftover, f"{service}: downgrade left bookkeeping behind: {leftover}"

    