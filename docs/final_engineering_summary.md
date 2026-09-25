# Final Engineering Summary

## 1. Overview

This project implements a prototype tamper-evident append-only audit log
service using Python, FastAPI, and SQLite.

The service records audit events, maintains a hash chain across records,
supports filtered queries and pagination, verifies chain integrity, provides
logical archival, supports structured output redaction, and produces filtered
export bundles.

The implementation was developed incrementally with AI-assisted engineering
support while keeping implementation decisions, validation, and final
acceptance engineer-led.

## 2. Architecture

The application is divided into four primary responsibilities:

```text
Client
  |
  v
FastAPI API Layer
  |
  v
Audit Service Layer
  |
  +--------------------+
  |                    |
  v                    v
Persistence Layer   Integrity Layer
  |                    |
  v                    v
SQLite              SHA-256 /
                    Chain Verification
```

### API Layer

FastAPI exposes the audit-event creation, query, verification, archival, and
export operations.

### Service Layer

The service layer coordinates validation, filtering, verification, and export
behavior while keeping API handling separate from persistence and integrity
logic.

### Persistence Layer

SQLite provides persistent relational storage for the prototype. The
persistence layer manages database initialization, transactions, audit-event
storage, retrieval, and logical archival metadata.

### Integrity Layer

The integrity layer provides deterministic record canonicalization, SHA-256
hashing, hash-chain construction, and chain verification.

## 3. Implementation Completed

### Scenario A - Core Audit Log

Implemented:

- audit-event creation
- server-assigned authoritative timestamps
- append-only public event API
- filtered event queries
- pagination using `record_id` as the stable sequence position
- deterministic canonical record representation
- SHA-256 content hashing
- previous-record hash chaining
- genesis hash for the first record
- chain verification
- direct datastore tamper validation

### Scenario B - Retention, Archive, Redaction, and Export

Implemented:

- logical archival using `archived` and `archived_at` lifecycle metadata
- verification including archived records
- output-only payload redaction
- bulk export filtered by `resourceId` or `actorId`
- export metadata and record count
- exported content, previous, and record hashes
- chain anchor for the first exported record
- redaction during export without modifying the stored audit event

### Scenario C - Ambiguous Requirement Analysis

The ambiguous requirement concerning regulatory auditing of client account
data was normalized into an implementable requirement covering:

- actor identification
- resource identification
- access event type
- server-assigned timestamp
- relevant event metadata
- authorized querying and verification
- verifiable exports

Regulatory-specific requirements, authorization policies, retention periods,
and other production controls remain assumptions or open questions rather than
being presented as implemented functionality.

## 4. Data and Integrity Model

Each audit record contains:

- `record_id`
- `event_type`
- `actor_id`
- `resource_type`
- `resource_id`
- `payload`
- `timestamp`
- `content_hash`
- `previous_hash`
- `record_hash`
- archive metadata

The canonical audit-event representation includes the event type, actor,
resource type, resource ID, payload, and timestamp.

The content hash is calculated as:

```text
content_hash = SHA256(canonical_record)
```

The record hash binds the previous hash to the canonical current record:

```text
record_hash = SHA256(canonical JSON containing previous_hash and record)
```

The first record references a fixed genesis hash.

`record_id` provides deterministic chain ordering. The timestamp represents
service acceptance time and does not determine chain order.

## 5. API Surface

The prototype exposes:

| Method | Endpoint | Purpose |
|---|---|---|
| POST | `/audit/events` | Create an audit event |
| GET | `/audit/events` | Query audit events |
| GET | `/audit/verify` | Verify the complete audit chain |
| POST | `/audit/events/{record_id}/archive` | Logically archive an event |
| GET | `/audit/export` | Export events filtered by resource or actor |

No public update or delete endpoint exists for audit-event content.

## 6. Engineering Decisions

### SHA-256

SHA-256 was selected because it is a standard cryptographic hash function,
deterministic, available through the Python standard library, and appropriate
for tamper detection in the prototype.

MD5 and SHA-1 were not selected because of known collision weaknesses.
SHA-512 was not selected because its additional digest size does not provide a
material benefit for this prototype.

### Deterministic JSON

Audit-event fields are serialized into deterministic JSON before hashing.
Sorted keys and deterministic separators ensure that the same logical record
produces the same canonical representation.

### Record ID Ordering

The database-generated `record_id` is used as the authoritative chain
sequence. This avoids using timestamps as ordering information when multiple
events may be accepted close together.

### Server Timestamp

The service assigns the authoritative timestamp when the event is accepted.
This provides consistent service-side recording time.

### SQLite

SQLite was selected for the prototype because it provides persistent
relational storage without requiring separate database infrastructure and
allows the required direct-datastore tamper validation.

### Logical Archival

Archival is implemented as lifecycle metadata rather than physical deletion.
Archived records remain available to chain verification.

### Output-Only Redaction

Redaction operates on exported/output representations rather than modifying
the immutable stored event. This preserves the original event and its
integrity hashes.

## 7. Concurrency

Audit-event creation uses a database transaction with `BEGIN IMMEDIATE` so
that concurrent writers do not independently construct conflicting chain
links.

Concurrent write behavior is covered by automated testing.

## 8. Validation

The implementation was validated through automated tests and direct
tamper-detection testing.

The automated test suite contains coverage for:

- database persistence
- concurrent writes
- hashing and canonicalization
- chain verification
- service-layer behavior
- redaction
- export
- API behavior

The final validation result was:

```text
35 passed, 1 warning
```

The warning is related to the test client's HTTPX/Starlette deprecation
notice and does not represent a failing test.

### Tamper Validation

The required tamper scenario was validated by:

1. creating an audit event
2. verifying the chain while the stored data was intact
3. directly modifying the SQLite datastore
4. running chain verification again

The modified record was detected with:

```text
CONTENT_HASH_MISMATCH
```

The verification response identified the affected record as the first invalid
record.

## 9. Export and Redaction Validation

The export implementation was validated through API tests covering:

- resource-based export filtering
- record count
- export format and version
- redacted payload output
- `content_hash`
- `previous_hash`
- `record_hash`
- `chain_anchor`

The stored audit event is not modified when redaction is requested.

A filtered export represents only a subset of the global audit chain. The
export therefore preserves the chain boundary through `chain_anchor`, but a
recipient cannot reconstruct the entire global history from a filtered subset
without preceding records or a trusted external anchor.

## 10. Security and Production Considerations

The prototype intentionally leaves several production concerns outside its
scope:

- enterprise authentication and authorization
- encryption and key management
- regulatory retention configuration
- production database scaling and high availability
- monitoring and alerting infrastructure
- backup and recovery
- deployment hardening
- external cryptographic signing or trust services for export bundles

The prototype demonstrates the audit-log integrity and workflow concepts but
should not be interpreted as a production-ready regulatory compliance system.

## 11. Known Limitations

### SQLite Prototype

SQLite is appropriate for the prototype but does not provide the distributed
scaling and availability characteristics expected from a production
multi-instance service.

### Query Execution

The current prototype retrieves audit events in deterministic `record_id`
order and applies filters and pagination in the service layer.

A production implementation should push filtering and pagination into
parameterized database queries and use appropriate indexes.

### Redaction Scope

Redaction currently applies only to top-level payload fields. Nested payload
structures are not recursively redacted.

### Export Verification

Exported records contain the hashes and chain anchor needed to validate the
relationships represented within the exported sequence. The prototype does
not provide external signing or a separate cryptographic trust service for
exports.

### Authentication and Authorization

API authentication and authorization are outside the prototype scope.

## 12. AI-Assisted Engineering

AI was used as an engineering support tool during requirements decomposition,
design exploration, implementation review, debugging, test planning, and
documentation review.

Engineering decisions were reviewed and accepted, modified, or rejected by
the engineer based on the requirements and validation results.

The detailed AI interaction and decision traceability is maintained in
`AI_USAGE_LOG.md`.

## 13. Engineering Outcome

The resulting prototype provides a working tamper-evident audit log service
with:

- append-only audit-event creation
- deterministic hash-chain integrity
- chain verification and first-failure reporting
- filtered queries and pagination
- logical archival
- output-only redaction
- filtered export bundles
- ambiguous-requirement analysis
- automated test coverage
- direct datastore tamper validation
- documented engineering decisions and limitations

The implementation and documentation are structured so that the design,
validation approach, tradeoffs, and remaining production considerations can
be explained and defended independently.