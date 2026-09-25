import hashlib
import json


GENESIS_HASH = "0" * 64


def calculate_sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def calculate_record_hash(previous_hash: str, canonical_record: str) -> str:
    chain_input = json.dumps(
        {
            "previous_hash": previous_hash,
            "record": canonical_record,
        },
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )

    return calculate_sha256(chain_input)


def canonicalize_record(
    event_type: str,
    actor_id: str,
    resource_type: str,
    resource_id: str,
    payload: dict,
    timestamp: str,
) -> str:
    record = {
        "eventType": event_type,
        "actorId": actor_id,
        "resourceType": resource_type,
        "resourceId": resource_id,
        "payload": payload,
        "timestamp": timestamp,
    }

    return json.dumps(
        record,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )