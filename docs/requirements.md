# Audit Log Service - Requirements

## 1. Objective

Build a tamper-evident audit log service that records an append-only
history of events and detects unauthorized modification of previously
stored records.

## 2. Scenario A - Core Audit Log Service

### 2.1 Audit Event

The service shall accept an audit event containing:

- `eventType` - identifies what happened.
- `actorId` - identifies the actor that caused the event.
- `resourceType` - identifies the type of affected resource.
- `resourceId` - identifies the affected resource.
- `payload` - structured event-specific data.
- `timestamp` - assigned by the server when the event is accepted.

### 2.2 Timestamp Decision

The service will use a server-assigned timestamp as the authoritative
timestamp for the stored audit record.

This avoids relying on the caller to provide the authoritative recording
time and provides a consistent service-side timestamp for audit records.

### 2.3 Append-Only Behavior

Audit records shall be append-only.

The public API shall provide no operation for updating or deleting an
existing audit record.

### 2.4 Query

The service shall provide an API to retrieve audit records using
combinations of:

- `actorId`
- `resourceType`
- `resourceId`
- `eventType`
- `from`
- `to`

The query API shall support pagination for large result sets.

### 2.5 Tamper Evidence

Each stored audit record shall contain:

- A hash representing its own canonical record content.
- A hash reference to the immediately preceding record.

The first record shall reference a defined genesis value.

Together, these values shall form a hash chain.

### 2.6 Chain Verification

The service shall expose a verification endpoint that walks the audit
chain and reports:

- Whether the chain is intact.
- The first inconsistent record when the chain is broken.
- The type of detected inconsistency.

### 2.7 Tamper Detection Validation

The system shall be validated by:

1. Creating audit records through the write API.
2. Verifying that the chain is intact.
3. Modifying a stored record directly in the data store.
4. Running chain verification again.
5. Confirming that the modification is detected.

## 3. Initial Acceptance Criteria

The Scenario A implementation will be considered complete when:

- An audit event can be successfully written.
- Stored records contain the required event information.
- Timestamps are assigned by the server.
- Existing records cannot be updated or deleted through the public API.
- Audit records can be queried using the required filters.
- Query results support pagination.
- Records form a verifiable hash chain.
- The verification endpoint identifies an intact chain.
- The verification endpoint detects a modified historical record.
- Automated tests cover the core behavior.