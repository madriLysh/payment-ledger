import pytest

from helper import SERVICES, list_tables, assert_schema_absent, assert_schema_present, ALL_TABLES, ALL_VERSION_TABLES

@pytest.mark.parametrize("service", list(SERVICES))
def test_migrations_roundtrip(service, fresh_db):
    assert_schema_present(service, fresh_db)
    assert_schema_absent(service, fresh_db)
    assert_schema_present(service, fresh_db)

def test_all_trees_coexist_on_one_database(fresh_db):
    for service in SERVICES:
        assert_schema_present(service, fresh_db)

    tables = list_tables(fresh_db)
    assert tables == ALL_TABLES | ALL_VERSION_TABLES

    for service in SERVICES:
        assert_schema_absent(service, fresh_db)

    assert list_tables(fresh_db) == set()