from app.integrity.hashing import (
    GENESIS_HASH,
    calculate_record_hash,
    calculate_sha256,
    canonicalize_record,
)


def verify_chain(records):
    if not records:
        return {
            "intact": True,
            "first_invalid_record_id": None,
            "violation": None,
        }

    first_record = records[0]

    if first_record["previous_hash"] != GENESIS_HASH:
        return {
            "intact": False,
            "first_invalid_record_id": first_record["record_id"],
            "violation": "GENESIS_MISMATCH",
        }

    for index, current_record in enumerate(records):
        if index > 0:
            previous_record = records[index - 1]

            if current_record["previous_hash"] != previous_record["record_hash"]:
                return {
                    "intact": False,
                    "first_invalid_record_id": current_record["record_id"],
                    "violation": "PREVIOUS_HASH_MISMATCH",
                }

        canonical_record = canonicalize_record(
            event_type=current_record["event_type"],
            actor_id=current_record["actor_id"],
            resource_type=current_record["resource_type"],
            resource_id=current_record["resource_id"],
            payload=current_record["payload"],
            timestamp=current_record["timestamp"],
        )

        expected_content_hash = calculate_sha256(canonical_record)

        if current_record["content_hash"] != expected_content_hash:
            return {
                "intact": False,
                "first_invalid_record_id": current_record["record_id"],
                "violation": "CONTENT_HASH_MISMATCH",
            }

        expected_record_hash = calculate_record_hash(
            previous_hash=current_record["previous_hash"],
            canonical_record=canonical_record,
        )

        if current_record["record_hash"] != expected_record_hash:
            return {
                "intact": False,
                "first_invalid_record_id": current_record["record_id"],
                "violation": "RECORD_HASH_MISMATCH",
            }

    return {
        "intact": True,
        "first_invalid_record_id": None,
        "violation": None,
    }