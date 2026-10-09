from alembic.config import Config as AlembicConfig
import alembic.command
from config import Config as AppConfig
from sqlalchemy import create_engine, NullPool
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

def run_alembic(service: str, url: str, revision: str) -> None:
    ini_path = REPO_ROOT / "services" / service / "alembic.ini"

    cfg = AlembicConfig(str(ini_path))
    cfg.set_main_option("sqlalchemy.url", url)

    AppConfig.DATABASE_URL = url

    if revision == "head":
        alembic.command.upgrade(cfg, "head")
    else:
        alembic.command.downgrade(cfg, revision)

def make_engine(url: str):
    return create_engine(url, poolclass=NullPool)

    