import pytest

from helper import assert_schema_present, make_engine
from sqlalchemy import text
from uuid_utils import uuid7

def test_unbalanced_transaction_is_detected_by_validation_query(fresh_db):
    assert_schema_present("ledger", fresh_db)
    ACCOUNT_DATAS = (
        {"id": uuid7(), "ot": "customer", "oi": "cust-1", "cur": "USD"},
        {"id": uuid7(), "ot": "merchant", "oi": "merch-1", "cur": "USD"},
        {"id": uuid7(), "ot": "platfrom", "oi": "pltform-1", "cur": "USD"}
    )
    engine = make_engine(fresh_db)
    with engine.connect() as conn:
        for data in ACCOUNT_DATAS:
            conn.execute(text("INSERT INTO ACCOUNTS(id, owner_type, owner_id, currency) VALUES(:id, :ot, :oi, :cur)"),data)

        conn.execute(text("INSERT INTO TRANSACTION(id, type, source_event_id) VALUES(:id, :t, :sei)"))