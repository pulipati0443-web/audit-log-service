import sqlite3

from app.persistence.database import get_connection, initialize_database


def test_initialize_database_creates_audit_events_table():
    initialize_database()

    with get_connection() as connection:
        table = connection.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'audit_events'
            """
        ).fetchone()

        assert table is not None
        assert table["name"] == "audit_events"


def test_audit_events_schema_contains_expected_columns():
    initialize_database()

    with get_connection() as connection:
        columns = connection.execute(
            "PRAGMA table_info(audit_events)"
        ).fetchall()

        column_names = [column["name"] for column in columns]

        expected_columns = [
            "record_id",
            "event_type",
            "actor_id",
            "resource_type",
            "resource_id",
            "payload",
            "timestamp",
            "content_hash",
            "previous_hash",
            "record_hash",
        ]

        assert column_names == expected_columns