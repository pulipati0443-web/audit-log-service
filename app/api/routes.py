from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from app.persistence.database import archive_audit_event
from app.services.audit_service import (
    create_event,
    query_events,
    verify_audit_chain,
)
from app.services.export import export_events


router = APIRouter(prefix="/audit", tags=["audit"])


class AuditEventCreate(BaseModel):
    eventType: str = Field(min_length=1)
    actorId: str = Field(min_length=1)
    resourceType: str = Field(min_length=1)
    resourceId: str = Field(min_length=1)
    payload: dict[str, Any]


class AuditEventResponse(BaseModel):
    record_id: int
    event_type: str
    actor_id: str
    resource_type: str
    resource_id: str
    payload: dict[str, Any]
    timestamp: str
    content_hash: str
    previous_hash: str
    record_hash: str
    archived: bool
    archived_at: Optional[str]


@router.post(
    "/events",
    response_model=AuditEventResponse,
    status_code=201,
)
def create_audit_event(event: AuditEventCreate):
    try:
        return create_event(
            event_type=event.eventType,
            actor_id=event.actorId,
            resource_type=event.resourceType,
            resource_id=event.resourceId,
            payload=event.payload,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Unable to create audit event",
        ) from exc


@router.get("/events")
def get_audit_events(
    actorId: Optional[str] = None,
    resourceType: Optional[str] = None,
    resourceId: Optional[str] = None,
    eventType: Optional[str] = None,
    from_: Optional[datetime] = Query(default=None, alias="from"),
    to: Optional[datetime] = None,
    afterId: Optional[int] = Query(default=None, ge=0),
    limit: int = Query(default=50, ge=1, le=100),
):
    return query_events(
        actor_id=actorId,
        resource_type=resourceType,
        resource_id=resourceId,
        event_type=eventType,
        from_timestamp=from_,
        to_timestamp=to,
        after_id=afterId,
        limit=limit,
    )


@router.get("/verify")
def verify_audit_events():
    return verify_audit_chain()


@router.post("/events/{record_id}/archive")
def archive_event(record_id: int):
    record = archive_audit_event(record_id)

    if record is None:
        raise HTTPException(
            status_code=404,
            detail="Audit event not found",
        )

    return record


@router.get("/export")
def export_audit_events(
    resourceId: Optional[str] = None,
    actorId: Optional[str] = None,
    redact: Optional[str] = None,
):
    if resourceId is None and actorId is None:
        raise HTTPException(
            status_code=400,
            detail="resourceId or actorId is required",
        )

    redact_fields = None

    if redact:
        redact_fields = [
            field.strip()
            for field in redact.split(",")
            if field.strip()
        ]

    try:
        return export_events(
            resource_id=resourceId,
            actor_id=actorId,
            redact_fields=redact_fields,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc