import pytest
from sqlalchemy import create_engine, NullPool, text
from testcontainers.postgres import PostgresContainer
from uuid import uuid4

@pytest.fixture(scope="session")
def pf_container():
    with PostgresContainer("postgres:16") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def admin_engine(pg_container):
    engine = create_engine(pg_container.get_connection_url(), poolclass=NullPool)

    try:
        yield engine
    finally:
        engine.dispose()

@pytest.fixture
def fresh_db(admin_engine):
    db_name = f"payledger_test_{uuid4().hex[:12]}" 

    with admin_engine.connect() as conn:
        conn = conn.execution_options(isolation_level="AUTOCOMMIT")
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))

        url = str(admin_engine.url.set(database=db_name))
        try:
            yield url
        finally:
            with admin_engine.connect() as conn:
                conn = conn.execution_options(isolation_level="AUTOCOMMIT")
                conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))

