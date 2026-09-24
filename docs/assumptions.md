# Audit Log Service - Assumptions and Design Decisions

## 1. Purpose

This document records assumptions and design decisions made while
translating the assignment requirements into an implementable design.

## 2. Timestamp

### Decision

The service will assign the authoritative timestamp when an audit event
is accepted.

### Rationale

A server-assigned timestamp provides a consistent service-side record of
when the audit event was accepted and avoids relying on the caller to
provide the authoritative recording time.

The timestamp will be treated as part of the immutable audit record.

---

## 3. Persistence

### Decision

SQLite will be used as the datastore for the prototype.

### Rationale

SQLite provides persistent relational storage without requiring a
separate database server or additional infrastructure. It also allows
the required tamper-detection scenario to be demonstrated by directly
modifying stored data.

PostgreSQL is a viable production alternative, but the assignment does
not require external database infrastructure. SQLite keeps the prototype
focused on the audit-log behavior, integrity mechanism, testing, and
validation.

### Limitation

SQLite is intended for this prototype and does not represent the
scaling, availability, or multi-instance characteristics expected from a
production distributed deployment.

---

## 4. Hash Algorithm

### Decision

SHA-256 will be used for audit-record hashing.

### Rationale

SHA-256 is a standard cryptographic hash function that provides
deterministic output and strong change detection characteristics. It is
also available through the Python standard library, avoiding an
additional dependency.

MD5 and SHA-1 were not selected because they have known collision
weaknesses. SHA-512 was not selected because its additional digest size
does not provide a material benefit for this prototype.

---

## 5. Canonical Record Representation

### Decision

Audit-record content will be converted into a deterministic canonical
JSON representation before hashing.

### Rationale

Hash verification requires the same logical record to produce the same
hash each time it is calculated. A deterministic representation avoids
hash differences caused by variations in serialization or field order.

The canonical representation will include:

- eventType
- actorId
- resourceType
- resourceId
- payload
- timestamp

---

## 6. Hash Chain Design

Each stored audit record will contain:

- content_hash - SHA-256 hash of the canonical audit-event content.
- previous_hash - hash reference to the immediately preceding record.
- record_hash - SHA-256 hash calculated from the previous hash and the
  canonical current record content.

### First Record

The first record will use a fixed genesis value as its previous_hash.

### Rationale

Separating the content hash from the chain hash allows verification to
identify whether the current record content changed and whether the
record's chain linkage remains valid.

Conceptually:

    content_hash = SHA256(canonical_record)

    record_hash = SHA256(previous_hash + canonical_record)

A subsequent record stores the previous record's record_hash as its
previous_hash.

---

## 7. Record Ordering

### Decision

The audit chain will use a monotonically increasing database-generated
record ID as the authoritative chain sequence.

### Rationale

The record ID provides an unambiguous and deterministic ordering for
chain construction and verification.

The timestamp will represent when the service accepted the event, but it
will not determine chain order because multiple events may have the same
timestamp.

The resulting separation is:

- `record_id` - position in the audit chain.
- `timestamp` - service-assigned event recording time.
---

## 8. Append-Only API

The public API will expose operations for creating and reading audit
records.

No public update or delete endpoint will be provided for existing audit
records.

Direct datastore modification will only be used as a controlled
validation technique to demonstrate tamper detection.

---

## 9. Verification

Chain verification will process records in chain order and validate:

1. The expected previous-hash relationship.
2. The current record's content hash.
3. The current record's record hash.
4. The genesis relationship for the first record.

Verification will stop at the first detected inconsistency and report
the affected record and violation type.

---

## 10. Concurrency

The implementation must ensure that creation of audit records does not
produce conflicting chain links when multiple write requests are
processed concurrently.

The implementation approach will be finalized during the persistence
and service-layer design.

---

## 11. Scope Boundary

The initial implementation focuses on the requirements explicitly
defined in Scenario A.

Retention, redaction, bulk export, and the compliance-reporting scenario
will be addressed as subsequent assignment stages rather than being
mixed into the initial core implementation.
