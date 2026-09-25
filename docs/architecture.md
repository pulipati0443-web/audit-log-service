# Audit Log Service - Architecture

## 1. Architecture Overview

The Audit Log Service is a Python-based REST service that records audit
events as an append-only sequence and provides integrity verification of
the stored audit history.

The prototype uses:

- FastAPI for the REST API.
- SQLite for persistent storage.
- SHA-256 for cryptographic hashing.
- Deterministic JSON serialization for canonical record representation.

The core integrity mechanism is a hash chain. Each audit record contains
a reference to the hash of the immediately preceding record. Verification
recomputes the expected hashes and identifies the first detected
inconsistency.

The design separates API concerns, persistence, hashing, and verification
logic so that the integrity mechanism can be tested independently from
the HTTP layer.

---

## 2. High-Level Components

The service will contain the following logical components.

### API Layer

Responsible for:

- Accepting audit-event requests.
- Validating request data.
- Providing query and verification endpoints.
- Translating service errors into appropriate HTTP responses.

### Service Layer

Responsible for:

- Applying audit-log business rules.
- Creating immutable audit records.
- Obtaining the previous chain record.
- Coordinating record creation and verification.
- Enforcing append-only behavior at the application layer.

### Persistence Layer

Responsible for:

- Creating and reading audit records from SQLite.
- Maintaining the database schema.
- Providing ordered access to records.
- Supporting controlled datastore modification during tamper-detection
  validation.

### Integrity Layer

Responsible for:

- Creating the canonical representation of an audit event.
- Calculating content hashes.
- Calculating chain hashes.
- Verifying record content and chain relationships.

---

## 3. Data Model

Each audit record will contain:

| Field | Purpose |
|---|---|
| record_id | Monotonically increasing database-generated chain sequence |
| event_type | Type of audit event |
| actor_id | Identity associated with the event |
| resource_type | Type of resource affected |
| resource_id | Identifier of the affected resource |
| payload | JSON object containing structured event details |
| timestamp | Server-assigned event recording timestamp |
| content_hash | SHA-256 hash of canonical audit-event content |
| previous_hash | Hash of the immediately preceding record |
| record_hash | Hash representing the current record and chain linkage |

The `record_id` determines chain order.

The `timestamp` records when the service accepted the event and does not
determine chain order.

---

## 4. Canonical Record Representation

The following audit-event fields will be used to construct the canonical
representation for hashing:

- eventType
- actorId
- resourceType
- resourceId
- payload
- timestamp

The representation will use deterministic JSON serialization so that the
same logical record produces the same serialized representation and hash.

The `payload` field will be a JSON object so that event details can be
represented structurally and serialized deterministically for hashing.

Hashing will not depend on JSON object field insertion order or
non-deterministic serialization behavior.

---

## 5. Hash Chain

For each audit record:

    content_hash = SHA256(canonical_record)

    chain_input = canonical representation of:
        - previous_hash
        - canonical_record

    record_hash = SHA256(chain_input)

The first record uses a fixed genesis value as its `previous_hash`.

For every subsequent record:

    current.previous_hash = previous.record_hash

The `chain_input` representation will use deterministic serialization so
that the same previous hash and canonical record always produce the same
record hash.

This creates a sequential dependency between records.

Changing the content of an earlier record causes its calculated hash to
differ. That difference also invalidates the previous-hash relationship
stored by the next record.

The chain therefore provides tamper evidence rather than independent
per-record hashing.

---

## 6. Record Creation Flow

A successful write follows this logical sequence:

1. Validate the incoming audit event.
2. Assign the server timestamp.
3. Begin a database transaction.
4. Obtain the current last record in chain order.
5. Determine the `previous_hash`.
6. Construct the canonical representation.
7. Calculate `content_hash`.
8. Calculate `record_hash`.
9. Insert the new record.
10. Commit the transaction.
11. Return the created record information.

The database transaction is required so that obtaining the previous chain
record and inserting the new record are treated as one atomic operation.

The implementation must prevent concurrent writers from creating
conflicting chain links.

---

## 7. Verification Flow

The verification operation processes records in ascending `record_id`
order.

For each record, verification checks:

1. The first record references the fixed genesis value.
2. Each subsequent record references the immediately preceding
   record's `record_hash`.
3. The stored `content_hash` matches the recalculated content hash.
4. The stored `record_hash` matches the recalculated chain hash.

Verification stops at the first detected inconsistency.

The response identifies:

- whether the chain is intact;
- the affected record when an inconsistency is found;
- the type of integrity violation detected.

---

## 8. API Design

### Create Audit Event

`POST /audit/events`

Creates a new immutable audit record.

Request fields:

- eventType
- actorId
- resourceType
- resourceId
- payload

The server assigns the authoritative timestamp.

The `payload` field will be a JSON object so that event details can be
represented structurally and serialized deterministically for hashing.

No caller-facing update or delete operation is provided.

### Query Audit Events

`GET /audit/events`

Supported filters:

- actorId
- resourceType
- resourceId
- eventType
- from
- to

Pagination will be supported to avoid returning an unbounded number of
records in a single response.

### Verify Audit Chain

`GET /audit/verify`

Walks the audit chain and validates record content and chain linkage.

The endpoint reports either an intact chain or the first detected
integrity violation.

---

## 9. Pagination and Querying

For the current prototype, audit events are retrieved from the persistence
layer in deterministic `record_id` order, and the service layer applies the
requested filters and pagination.

This keeps the prototype implementation straightforward while preserving
deterministic ordering. For production scale, filtering and pagination should
be pushed into parameterized database queries with appropriate indexes to
avoid loading unnecessary records into application memory.

Pagination uses `record_id` as the stable ordering and cursor.

---

## 10. Append-Only Enforcement

The public API will not expose update or delete operations for audit
records.

The application treats stored audit records as immutable after creation.

For the prototype, direct database modification is intentionally possible
outside the application so that the assignment's tamper-detection
validation can demonstrate the difference between normal application
behavior and unauthorized datastore modification.

---

## 11. Concurrency Considerations

The integrity of a hash chain depends on each new record referencing the
correct immediately preceding record.

Therefore, concurrent writes cannot independently read the same previous
record and then commit conflicting chain links.

Record creation will use database transaction semantics to serialize the
critical sequence of:

- determining the current chain tail;
- calculating the new hashes;
- inserting the new record.

The exact SQLite transaction configuration will be implemented and tested
as part of the persistence layer.

---

## 12. Error Handling

The API will distinguish between:

- invalid client input;
- missing requested records;
- persistence failures;
- integrity verification failures.

Integrity verification failures are treated as audit-chain findings rather
than generic application errors.

Unexpected persistence or application failures will be handled separately
from a successfully completed verification that reports a broken chain.

---

## 13. Security Considerations

The prototype will follow these principles:

- No public update or delete endpoint.
- Server-controlled timestamps.
- Deterministic hashing of audit content.
- Integrity verification exposed through a dedicated endpoint.
- Structured request validation.
- No sensitive values included in application logs unnecessarily.
- Database access isolated behind the persistence layer.

The prototype does not claim to provide a complete production security
model. Authentication, authorization, key management, encrypted storage,
high availability, and operational controls would require additional
production design.

---

## 14. Prototype and Production Boundary

SQLite is appropriate for the prototype because it provides persistent
storage without requiring a separately managed database service.

A production implementation could use a database such as PostgreSQL and
would require additional consideration for:

- horizontal scaling;
- transaction and locking behavior across service instances;
- database availability;
- backup and recovery;
- access control;
- encryption;
- operational monitoring;
- retention and archival;
- key management and stronger trust-boundary controls.

These concerns are intentionally separated from the core prototype so that
the implementation remains focused on the assignment's audit-log
integrity requirements.

---

## 15. Validation Strategy

The implementation will be validated at multiple levels.

### Functional Validation

Verify that:

- audit events can be created;
- required fields are stored;
- timestamps are server assigned;
- query filters work;
- pagination works;
- verification reports an intact chain.

### Integrity Validation

1. Create multiple audit records.
2. Run chain verification.
3. Confirm the chain is intact.
4. Modify a stored record directly in SQLite.
5. Run verification again.
6. Confirm the modified record is identified as the first inconsistency.

### Automated Testing

Tests will cover:

- valid event creation;
- request validation;
- hash generation;
- genesis behavior;
- chain linkage;
- successful verification;
- detection of modified content;
- query filters;
- pagination;
- error handling;
- concurrent write behavior where applicable.