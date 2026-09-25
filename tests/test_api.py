import sqlite3

import pytest
from fastapi.testclient import TestClient

import app.persistence.database as database
from app.main import app


@pytest.fixture
def test_database(tmp_path, monkeypatch):
    database_path = tmp_path / "audit.db"

    monkeypatch.setattr(
        database,
        "DATABASE_PATH",
        database_path,
    )

    database.initialize_database(database_path)

    return database_path


def test_create_event_and_verify_through_api(test_database):
    with TestClient(app) as client:
        response = client.post(
            "/audit/events",
            json={
                "eventType": "ACCOUNT_VIEW",
                "actorId": "actor-api",
                "resourceType": "ACCOUNT",
                "resourceId": "account-api-1",
                "payload": {
                    "action": "view",
                },
            },
        )

        assert response.status_code == 201

        created_record = response.json()

        assert created_record["record_id"] == 1
        assert created_record["event_type"] == "ACCOUNT_VIEW"
        assert created_record["actor_id"] == "actor-api"
        assert created_record["previous_hash"] == "0" * 64

        verify_response = client.get("/audit/verify")

        assert verify_response.status_code == 200
        assert verify_response.json() == {
            "intact": True,
            "first_invalid_record_id": None,
            "violation": None,
        }


def test_query_events_through_api(test_database):
    with TestClient(app) as client:
        client.post(
            "/audit/events",
            json={
                "eventType": "ACCOUNT_VIEW",
                "actorId": "actor-api",
                "resourceType": "ACCOUNT",
                "resourceId": "account-api-1",
                "payload": {
                    "action": "view",
                },
            },
        )

        client.post(
            "/audit/events",
            json={
                "eventType": "ACCOUNT_VIEW",
                "actorId": "actor-other",
                "resourceType": "ACCOUNT",
                "resourceId": "account-api-2",
                "payload": {
                    "action": "view",
                },
            },
        )

        response = client.get(
            "/audit/events",
            params={
                "actorId": "actor-api",
            },
        )

        assert response.status_code == 200

        records = response.json()

        assert len(records) == 1
        assert records[0]["actor_id"] == "actor-api"


def test_tampered_record_is_detected_through_api(test_database):
    with TestClient(app) as client:
        response = client.post(
            "/audit/events",
            json={
                "eventType": "ACCOUNT_UPDATE",
                "actorId": "actor-tamper",
                "resourceType": "ACCOUNT",
                "resourceId": "account-tamper-1",
                "payload": {
                    "action": "update",
                },
            },
        )

        assert response.status_code == 201

        record_id = response.json()["record_id"]

        connection = sqlite3.connect(test_database)

        connection.execute(
            """
            UPDATE audit_events
            SET payload = ?
            WHERE record_id = ?
            """,
            ('{"action":"TAMPERED"}', record_id),
        )

        connection.commit()
        connection.close()

        verify_response = client.get("/audit/verify")

        assert verify_response.status_code == 200

        verification = verify_response.json()

        assert verification["intact"] is False
        assert verification["first_invalid_record_id"] == record_id
        assert verification["violation"] == "CONTENT_HASH_MISMATCH"


def test_archive_event_through_api_preserves_chain(test_database):
    with TestClient(app) as client:
        create_response = client.post(
            "/audit/events",
            json={
                "eventType": "ACCOUNT_VIEW",
                "actorId": "actor-archive",
                "resourceType": "ACCOUNT",
                "resourceId": "account-archive-1",
                "payload": {
                    "action": "view",
                },
            },
        )

        assert create_response.status_code == 201

        record_id = create_response.json()["record_id"]

        archive_response = client.post(
            f"/audit/events/{record_id}/archive"
        )

        assert archive_response.status_code == 200
        assert archive_response.json()["archived"] is True
        assert archive_response.json()["archived_at"] is not None

        verify_response = client.get("/audit/verify")

        assert verify_response.status_code == 200
        assert verify_response.json()["intact"] is True

        events_response = client.get("/audit/events")

        assert events_response.status_code == 200

        records = events_response.json()

        assert len(records) == 1
        assert records[0]["record_id"] == record_id
        assert records[0]["archived"] is True


def test_export_event_through_api_with_redaction(test_database):
    with TestClient(app) as client:
        create_response = client.post(
            "/audit/events",
            json={
                "eventType": "ACCOUNT_VIEW",
                "actorId": "actor-export",
                "resourceType": "ACCOUNT",
                "resourceId": "account-export-1",
                "payload": {
                    "accountNumber": "123456789",
                    "clientName": "Example Client",
                    "action": "view",
                },
            },
        )

        assert create_response.status_code == 201

        export_response = client.get(
            "/audit/export",
            params={
                "resourceId": "account-export-1",
                "redact": "accountNumber,clientName",
            },
        )

        assert export_response.status_code == 200

        bundle = export_response.json()

        assert bundle["format"] == "audit-log-export"
        assert bundle["version"] == "1.0"
        assert bundle["record_count"] == 1

        exported_record = bundle["records"][0]

        assert exported_record["resource_id"] == "account-export-1"
        assert exported_record["payload"]["accountNumber"] == "[REDACTED]"
        assert exported_record["payload"]["clientName"] == "[REDACTED]"
        assert exported_record["payload"]["action"] == "view"

        assert exported_record["content_hash"]
        assert exported_record["previous_hash"]
        assert exported_record["record_hash"]

        assert bundle["chain_anchor"]["first_record_id"] == (
            exported_record["record_id"]
        )