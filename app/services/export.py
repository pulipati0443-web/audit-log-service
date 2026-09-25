from datetime import datetime, timezone
from typing import Optional

from app.persistence.database import get_audit_events
from app.services.redaction import redact_payload


def export_events(
    resource_id: Optional[str] = None,
    actor_id: Optional[str] = None,
    redact_fields: Optional[list[str]] = None,
    database_path=None,
):
    if resource_id is None and actor_id is None:
        raise ValueError(
            "At least one export filter is required: resource_id or actor_id"
        )

    records = get_audit_events(database_path)

    selected_records = []

    for record in records:
        if resource_id is not None and record["resource_id"] != resource_id:
            continue

        if actor_id is not None and record["actor_id"] != actor_id:
            continue

        exported_record = dict(record)

        if redact_fields:
            exported_record["payload"] = redact_payload(
                record["payload"],
                redact_fields,
            )

        selected_records.append(exported_record)

    bundle = {
        "format": "audit-log-export",
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "filter": {
            "resource_id": resource_id,
            "actor_id": actor_id,
        },
        "record_count": len(selected_records),
        "records": selected_records,
    }

    if selected_records:
        bundle["chain_anchor"] = {
            "first_record_id": selected_records[0]["record_id"],
            "previous_hash": selected_records[0]["previous_hash"],
        }
    else:
        bundle["chain_anchor"] = None

    return bundle