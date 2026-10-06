from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base
from sqlalchemy.exc import SQLAlchemyError
from typing import Generator
from config import Config

from functools import lru_cache
Base = declarative_base()

@lru_cache
def get_engine():
    return create_engine(
    Config.DATABASE_URL,
    pool_pre_ping=True,
    pool_size=Config.DB_POOL_SIZE,
    max_overflow=Config.DB_MAX_OVERFLOW,
    pool_timeout=Config.DB_POOL_TIMEOUT,
    echo=Config.DB_ECHO,
    connect_args={
        "connect_timeout": 10, 
        "options": " -c statement_timeout=30000"
    }
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=get_engine()
)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try: 
        yield db
    except SQLAlchemyError:
        db.rollback()
        raise
    finally:
        db.close()