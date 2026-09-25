from app.integrity.hashing import (
    GENESIS_HASH,
    calculate_record_hash,
    calculate_sha256,
    canonicalize_record,
)


def test_canonicalize_record_is_deterministic():
    payload_one = {
        "action": "view",
        "source": "customer-portal",
    }

    payload_two = {
        "source": "customer-portal",
        "action": "view",
    }

    canonical_one = canonicalize_record(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload=payload_one,
        timestamp="2026-09-24T19:00:00+00:00",
    )

    canonical_two = canonicalize_record(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload=payload_two,
        timestamp="2026-09-24T19:00:00+00:00",
    )

    assert canonical_one == canonical_two


def test_canonicalize_record_returns_json_string():
    canonical = canonicalize_record(
        event_type="ACCOUNT_VIEW",
        actor_id="actor-123",
        resource_type="ACCOUNT",
        resource_id="account-456",
        payload={"action": "view"},
        timestamp="2026-09-24T19:00:00+00:00",
    )

    assert isinstance(canonical, str)
    assert '"eventType":"ACCOUNT_VIEW"' in canonical
    assert '"actorId":"actor-123"' in canonical
    assert '"resourceId":"account-456"' in canonical


def test_calculate_sha256_is_deterministic():
    value = "audit-event"

    first_hash = calculate_sha256(value)
    second_hash = calculate_sha256(value)

    assert first_hash == second_hash


def test_calculate_sha256_changes_when_input_changes():
    first_hash = calculate_sha256("audit-event")
    second_hash = calculate_sha256("audit-event-modified")

    assert first_hash != second_hash


def test_calculate_record_hash_is_deterministic():
    canonical_record = '{"eventType":"ACCOUNT_VIEW","actorId":"actor-123"}'

    first_hash = calculate_record_hash(
        previous_hash=GENESIS_HASH,
        canonical_record=canonical_record,
    )

    second_hash = calculate_record_hash(
        previous_hash=GENESIS_HASH,
        canonical_record=canonical_record,
    )

    assert first_hash == second_hash


def test_calculate_record_hash_changes_when_previous_hash_changes():
    canonical_record = '{"eventType":"ACCOUNT_VIEW","actorId":"actor-123"}'

    first_hash = calculate_record_hash(
        previous_hash=GENESIS_HASH,
        canonical_record=canonical_record,
    )

    different_previous_hash = "1" * 64

    second_hash = calculate_record_hash(
        previous_hash=different_previous_hash,
        canonical_record=canonical_record,
    )

    assert first_hash != second_hash


def test_calculate_record_hash_changes_when_record_changes():
    first_hash = calculate_record_hash(
        previous_hash=GENESIS_HASH,
        canonical_record='{"eventType":"ACCOUNT_VIEW"}',
    )

    second_hash = calculate_record_hash(
        previous_hash=GENESIS_HASH,
        canonical_record='{"eventType":"ACCOUNT_UPDATE"}',
    )

    assert first_hash != second_hash