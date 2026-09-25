from app.integrity.hashing import (
    GENESIS_HASH,
    calculate_record_hash,
    calculate_sha256,
    canonicalize_record,
)
from app.integrity.verification import verify_chain


def test_empty_chain_is_intact():
    result = verify_chain([])

    assert result["intact"] is True
    assert result["first_invalid_record_id"] is None
    assert result["violation"] is None


def test_first_record_must_use_genesis_hash():
    record = {
        "record_id": 1,
        "event_type": "ACCOUNT_VIEW",
        "actor_id": "actor-123",
        "resource_type": "ACCOUNT",
        "resource_id": "account-456",
        "payload": {"action": "view"},
        "timestamp": "2026-09-24T19:00:00+00:00",
        "content_hash": "content-hash",
        "previous_hash": "wrong-hash",
        "record_hash": "record-hash",
    }

    result = verify_chain([record])

    assert result["intact"] is False
    assert result["first_invalid_record_id"] == 1
    assert result["violation"] == "GENESIS_MISMATCH"


def test_first_record_with_genesis_hash_is_valid():
    canonical_record = canonicalize_record(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        timestamp="2026-09-24T19:00:00+00:00",
    )

    valid_content_hash = calculate_sha256(canonical_record)

    valid_record_hash = calculate_record_hash(
        previous_hash=GENESIS_HASH,
        canonical_record=canonical_record,
    )

    record = {
        "record_id": 1,
        "event_type": "ACCOUNT_VIEW",
        "actor_id": "actor-123",
        "resource_type": "ACCOUNT",
        "resource_id": "account-456",
        "payload": {"action": "view"},
        "timestamp": "2026-09-24T19:00:00+00:00",
        "content_hash": valid_content_hash,
        "previous_hash": GENESIS_HASH,
        "record_hash": valid_record_hash,
    }

    result = verify_chain([record])

    assert result["intact"] is True
    assert result["first_invalid_record_id"] is None
    assert result["violation"] is None


def test_record_must_reference_previous_record_hash():
    first_canonical_record = canonicalize_record(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        timestamp="2026-09-24T19:00:00+00:00",
    )

    first_content_hash = calculate_sha256(first_canonical_record)

    first_record_hash = calculate_record_hash(
        previous_hash=GENESIS_HASH,
        canonical_record=first_canonical_record,
    )

    first_record = {
        "record_id": 1,
        "event_type": "ACCOUNT_VIEW",
        "actor_id": "actor-123",
        "resource_type": "ACCOUNT",
        "resource_id": "account-456",
        "payload": {"action": "view"},
        "timestamp": "2026-09-24T19:00:00+00:00",
        "content_hash": first_content_hash,
        "previous_hash": GENESIS_HASH,
        "record_hash": first_record_hash,
    }

    second_record = {
        "record_id": 2,
        "event_type": "ACCOUNT_UPDATE",
        "actor_id": "actor-123",
        "resource_type": "ACCOUNT",
        "resource_id": "account-456",
        "payload": {"action": "update"},
        "timestamp": "2026-09-24T19:01:00+00:00",
        "content_hash": "content-hash-2",
        "previous_hash": "wrong-previous-hash",
        "record_hash": "record-hash-2",
    }

    result = verify_chain([first_record, second_record])

    assert result["intact"] is False
    assert result["first_invalid_record_id"] == 2
    assert result["violation"] == "PREVIOUS_HASH_MISMATCH"


def test_modified_record_content_is_detected():
    canonical_record = canonicalize_record(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        timestamp="2026-09-24T19:00:00+00:00",
    )

    valid_content_hash = calculate_sha256(canonical_record)

    record = {
        "record_id": 1,
        "event_type": "ACCOUNT_UPDATE",
        "actor_id": "actor-123",
        "resource_type": "ACCOUNT",
        "resource_id": "account-456",
        "payload": {"action": "view"},
        "timestamp": "2026-09-24T19:00:00+00:00",
        "content_hash": valid_content_hash,
        "previous_hash": GENESIS_HASH,
        "record_hash": "record-hash",
    }

    result = verify_chain([record])

    assert result["intact"] is False
    assert result["first_invalid_record_id"] == 1
    assert result["violation"] == "CONTENT_HASH_MISMATCH"


def test_modified_record_hash_is_detected():
    canonical_record = canonicalize_record(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        timestamp="2026-09-24T19:00:00+00:00",
    )

    valid_content_hash = calculate_sha256(canonical_record)

    record = {
        "record_id": 1,
        "event_type": "ACCOUNT_VIEW",
        "actor_id": "actor-123",
        "resource_type": "ACCOUNT",
        "resource_id": "account-456",
        "payload": {"action": "view"},
        "timestamp": "2026-09-24T19:00:00+00:00",
        "content_hash": valid_content_hash,
        "previous_hash": GENESIS_HASH,
        "record_hash": "tampered-record-hash",
    }

    result = verify_chain([record])

    assert result["intact"] is False
    assert result["first_invalid_record_id"] == 1
    assert result["violation"] == "RECORD_HASH_MISMATCH"