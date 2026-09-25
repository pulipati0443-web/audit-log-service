from concurrent.futures import ThreadPoolExecutor
from app.persistence.database import (
    archive_audit_event,
    create_audit_event,
    get_audit_events,
    get_connection,
    initialize_database,
)

def test_initialize_database_creates_audit_events_table(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    with get_connection(database_path) as connection:
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


def test_audit_events_schema_contains_expected_columns(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    with get_connection(database_path) as connection:
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
                "archived",
                "archived_at",
        ]

        assert column_names == expected_columns


def test_get_audit_events_returns_records_in_record_id_order(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    with get_connection(database_path) as connection:
        connection.execute(
            """
            INSERT INTO audit_events (
                event_type,
                actor_id,
                resource_type,
                resource_id,
                payload,
                timestamp,
                content_hash,
                previous_hash,
                record_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ACCOUNT_VIEW",
                "actor-123",
                "ACCOUNT",
                "account-456",
                '{"action":"view"}',
                "2026-09-24T19:00:00+00:00",
                "content-hash-1",
                "genesis",
                "record-hash-1",
            ),
        )

        connection.execute(
            """
            INSERT INTO audit_events (
                event_type,
                actor_id,
                resource_type,
                resource_id,
                payload,
                timestamp,
                content_hash,
                previous_hash,
                record_hash
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                "ACCOUNT_UPDATE",
                "actor-123",
                "ACCOUNT",
                "account-456",
                '{"action":"update"}',
                "2026-09-24T19:01:00+00:00",
                "content-hash-2",
                "record-hash-1",
                "record-hash-2",
            ),
        )

    records = get_audit_events(database_path)

    assert len(records) == 2
    assert records[0]["record_id"] < records[1]["record_id"]
    assert records[0]["event_type"] == "ACCOUNT_VIEW"
    assert records[1]["event_type"] == "ACCOUNT_UPDATE"


def test_create_audit_event_creates_first_record_with_genesis_hash(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    record = create_audit_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        database_path=database_path,
    )

    assert record["record_id"] == 1
    assert record["event_type"] == "ACCOUNT_VIEW"
    assert record["actor_id"] == "actor-123"
    assert record["resource_type"] == "ACCOUNT"
    assert record["resource_id"] == "account-456"
    assert record["payload"] == {"action": "view"}
    assert record["previous_hash"] == "0" * 64
    assert len(record["content_hash"]) == 64
    assert len(record["record_hash"]) == 64
    assert record["timestamp"]


def test_archive_audit_event_preserves_record_and_chain(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    first = create_audit_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        database_path=database_path,
    )

    second = create_audit_event(
        event_type="ACCOUNT_UPDATE",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "update"},
        database_path=database_path,
    )

    archived = archive_audit_event(
        record_id=first["record_id"],
        database_path=database_path,
    )

    assert archived is not None
    assert archived["record_id"] == first["record_id"]
    assert archived["archived"] is True
    assert archived["archived_at"] is not None

    records = get_audit_events(database_path)

    assert len(records) == 2
    assert records[0]["archived"] is True
    assert records[1]["archived"] is False
    assert records[1]["previous_hash"] == first["record_hash"]

    from app.integrity.verification import verify_chain

    verification = verify_chain(records)

    assert verification["intact"] is True
    assert verification["first_invalid_record_id"] is None
    assert verification["violation"] is None

def test_concurrent_writes_preserve_chain_order(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    def create_event(index):
        return create_audit_event(
            event_type="ACCOUNT_VIEW",
            actor_id=f"actor-{index}",
            resource_type="ACCOUNT",
            resource_id=f"account-{index}",
            payload={"index": index},
            database_path=database_path,
        )

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [
            executor.submit(create_event, index)
            for index in range(10)
        ]

        records = [future.result() for future in futures]

    records.sort(key=lambda record: record["record_id"])

    assert [record["record_id"] for record in records] == list(
        range(1, 11)
    )

    stored_records = get_audit_events(database_path)

    assert len(stored_records) == 10

    from app.integrity.verification import verify_chain

    verification = verify_chain(stored_records)

    assert verification["intact"] is True
    assert verification["first_invalid_record_id"] is None
    assert verification["violation"] is None

    for index in range(1, len(stored_records)):
        assert (
            stored_records[index]["previous_hash"]
            == stored_records[index - 1]["record_hash"]
        )