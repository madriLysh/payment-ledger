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

def run_alembic(service: str, url: str, revision: str) -> None:
    ini_path, _, _ = SERVICES[service]
    print("INI: ", ini_path, " exists: ", ini_path.exists())
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
    engine = create_engine(url, poolclass=NullPool)
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

    