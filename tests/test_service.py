from datetime import datetime, timezone

from app.persistence.database import initialize_database
from app.services.audit_service import (
    create_event,
    query_events,
    verify_audit_chain,
)


def test_create_event_and_verify_chain(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    first = create_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        database_path=database_path,
    )

    second = create_event(
        event_type="ACCOUNT_UPDATE",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "update"},
        database_path=database_path,
    )

    assert first["record_id"] == 1
    assert second["record_id"] == 2
    assert second["previous_hash"] == first["record_hash"]

    result = verify_audit_chain(database_path)

    assert result["intact"] is True
    assert result["first_invalid_record_id"] is None
    assert result["violation"] is None


def test_query_events_filters_by_actor(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    create_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-1",
        payload={"action": "view"},
        database_path=database_path,
    )

    create_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-456",
        resource_type="ACCOUNT",
        resource_id="account-2",
        payload={"action": "view"},
        database_path=database_path,
    )

    results = query_events(
        actor_id="actor-123",
        database_path=database_path,
    )

    assert len(results) == 1
    assert results[0]["actor_id"] == "actor-123"


def test_query_events_filters_by_resource_and_event_type(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    create_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-1",
        payload={"action": "view"},
        database_path=database_path,
    )

    create_event(
        event_type="ACCOUNT_UPDATE",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-1",
        payload={"action": "update"},
        database_path=database_path,
    )

    create_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="CUSTOMER",
        resource_id="customer-1",
        payload={"action": "view"},
        database_path=database_path,
    )

    results = query_events(
        resource_type="ACCOUNT",
        resource_id="account-1",
        event_type="ACCOUNT_UPDATE",
        database_path=database_path,
    )

    assert len(results) == 1
    assert results[0]["event_type"] == "ACCOUNT_UPDATE"


def test_query_events_supports_pagination(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    for index in range(5):
        create_event(
            event_type="ACCOUNT_VIEW",
            actor_id="actor-123",
            resource_type="ACCOUNT",
            resource_id=f"account-{index}",
            payload={"index": index},
            database_path=database_path,
        )

    first_page = query_events(
        limit=2,
        database_path=database_path,
    )

    assert [record["record_id"] for record in first_page] == [1, 2]

    second_page = query_events(
        after_id=2,
        limit=2,
        database_path=database_path,
    )

    assert [record["record_id"] for record in second_page] == [3, 4]


def test_query_events_supports_timestamp_range(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    first = create_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-1",
        payload={"index": 1},
        database_path=database_path,
    )

    second = create_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-2",
        payload={"index": 2},
        database_path=database_path,
    )

    first_timestamp = datetime.fromisoformat(first["timestamp"])
    second_timestamp = datetime.fromisoformat(second["timestamp"])

    results = query_events(
        from_timestamp=first_timestamp,
        to_timestamp=second_timestamp,
        database_path=database_path,
    )

    assert len(results) == 2
    assert results[0]["record_id"] == 1
    assert results[1]["record_id"] == 2