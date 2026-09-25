from app.persistence.database import create_audit_event, initialize_database
from app.services.export import export_events


def test_export_by_resource_id(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    create_audit_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-1",
        resource_type="ACCOUNT",
        resource_id="account-1",
        payload={"action": "view"},
        database_path=database_path,
    )

    create_audit_event(
        event_type="ACCOUNT_UPDATE",
        actor_id="actor-2",
        resource_type="ACCOUNT",
        resource_id="account-2",
        payload={"action": "update"},
        database_path=database_path,
    )

    bundle = export_events(
        resource_id="account-1",
        database_path=database_path,
    )

    assert bundle["format"] == "audit-log-export"
    assert bundle["version"] == "1.0"
    assert bundle["record_count"] == 1
    assert bundle["records"][0]["resource_id"] == "account-1"
    assert bundle["records"][0]["record_hash"]
    assert bundle["records"][0]["previous_hash"]


def test_export_by_actor_id(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    create_audit_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-1",
        resource_type="ACCOUNT",
        resource_id="account-1",
        payload={"action": "view"},
        database_path=database_path,
    )

    create_audit_event(
        event_type="ACCOUNT_UPDATE",
        actor_id="actor-1",
        resource_type="ACCOUNT",
        resource_id="account-2",
        payload={"action": "update"},
        database_path=database_path,
    )

    create_audit_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-2",
        resource_type="ACCOUNT",
        resource_id="account-3",
        payload={"action": "view"},
        database_path=database_path,
    )

    bundle = export_events(
        actor_id="actor-1",
        database_path=database_path,
    )

    assert bundle["record_count"] == 2
    assert all(
        record["actor_id"] == "actor-1"
        for record in bundle["records"]
    )


def test_export_supports_redaction(tmp_path):
    database_path = tmp_path / "audit.db"

    initialize_database(database_path)

    create_audit_event(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-1",
        resource_type="ACCOUNT",
        resource_id="account-1",
        payload={
            "accountNumber": "123456789",
            "action": "view",
        },
        database_path=database_path,
    )

    bundle = export_events(
        resource_id="account-1",
        redact_fields=["accountNumber"],
        database_path=database_path,
    )

    exported_payload = bundle["records"][0]["payload"]

    assert exported_payload["accountNumber"] == "[REDACTED]"
    assert exported_payload["action"] == "view"