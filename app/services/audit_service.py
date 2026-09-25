from datetime import datetime
from typing import Optional

from app.integrity.verification import verify_chain
from app.persistence.database import (
    create_audit_event,
    get_audit_events,
)


def create_event(
    event_type: str,
    actor_id: str,
    resource_type: str,
    resource_id: str,
    payload: dict,
    database_path=None,
):
    if database_path is None:
        return create_audit_event(
            event_type=event_type,
            actor_id=actor_id,
            resource_type=resource_type,
            resource_id=resource_id,
            payload=payload,
        )

    return create_audit_event(
        event_type=event_type,
        actor_id=actor_id,
        resource_type=resource_type,
        resource_id=resource_id,
        payload=payload,
        database_path=database_path,
    )


def query_events(
    actor_id: Optional[str] = None,
    resource_type: Optional[str] = None,
    resource_id: Optional[str] = None,
    event_type: Optional[str] = None,
    from_timestamp: Optional[datetime] = None,
    to_timestamp: Optional[datetime] = None,
    after_id: Optional[int] = None,
    limit: int = 50,
    database_path=None,
):
    if database_path is None:
        records = get_audit_events()
    else:
        records = get_audit_events(database_path)

    filtered_records = []

    for record in records:
        if actor_id is not None and record["actor_id"] != actor_id:
            continue

        if (
            resource_type is not None
            and record["resource_type"] != resource_type
        ):
            continue

        if resource_id is not None and record["resource_id"] != resource_id:
            continue

        if event_type is not None and record["event_type"] != event_type:
            continue

        record_timestamp = datetime.fromisoformat(record["timestamp"])

        if from_timestamp is not None and record_timestamp < from_timestamp:
            continue

        if to_timestamp is not None and record_timestamp > to_timestamp:
            continue

        if after_id is not None and record["record_id"] <= after_id:
            continue

        filtered_records.append(record)

        if len(filtered_records) >= limit:
            break

    return filtered_records


def verify_audit_chain(database_path=None):
    if database_path is None:
        records = get_audit_events()
    else:
        records = get_audit_events(database_path)

    return verify_chain(records)