# Audit Log Service

A Python/FastAPI prototype implementing a tamper-evident append-only audit
logging service.

## Features

- Append-only audit events
- Server-assigned timestamps
- SHA-256 content hashing
- Hash-chain integrity
- Genesis hash
- Chain verification
- Tamper detection
- Query filters
- Cursor-style pagination
- Logical archival
- Structured payload redaction
- Filtered export bundles
- Concurrent-write validation
- Automated test suite

## Project Structure

```text
audit-log-service/
├── app/
│   ├── api/
│   ├── integrity/
│   ├── persistence/
│   └── services/
├── docs/
├── scripts/
├── tests/
├── data/
├── requirements.txt
├── ATTESTATION.md
├── AI_USAGE_LOG.md
└── README.md
```

## Requirements

- Python 3.11+
- Git
- A Python virtual environment

The prototype uses SQLite, so no separate database server is required.

## Setup

Clone the repository and create a virtual environment:

```powershell
git clone <repository-url>
cd audit-log-service
python -m venv venv
```

Activate the virtual environment on Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

## Run the Application

Start the FastAPI application with:

```powershell
uvicorn app.main:app --reload
```

The API is available at:

```text
http://127.0.0.1:8000
```

FastAPI interactive documentation is available at:

```text
http://127.0.0.1:8000/docs
```

## API Endpoints

### Create an Audit Event

```text
POST /audit/events
```

Creates a new audit event.

The service assigns the authoritative timestamp when the event is accepted.

### Query Audit Events

```text
GET /audit/events
```

Supports filtering by:

- `actorId`
- `resourceType`
- `resourceId`
- `eventType`
- `from`
- `to`

Pagination is supported using the record sequence.

### Verify the Audit Chain

```text
GET /audit/verify
```

Verifies the complete audit chain and reports whether the chain is intact.

If an inconsistency is detected, the response identifies the first invalid
record and the violation type.

### Archive an Audit Event

```text
POST /audit/events/{record_id}/archive
```

Logically archives an audit event without physically deleting it.

Archived records remain part of chain verification.

### Export Audit Events

```text
GET /audit/export
```

Supports export filtered by:

- `resourceId`
- `actorId`

The export includes audit records, integrity hashes, export metadata, and a
chain anchor for the first exported record.

Payload redaction can be applied to the exported representation without
modifying the stored audit event.

## Testing

Run the test suite from the repository root:

```powershell
$env:PYTHONPATH="."
pytest -q
```

The final validation result for the prototype was:

```text
35 passed, 1 warning
```

The warning is related to the HTTPX/Starlette test-client deprecation notice
and does not represent a failing test.

The test suite covers:

- database persistence
- concurrent writes
- hashing and canonicalization
- chain verification
- service behavior
- redaction
- export
- API behavior

## Tamper Detection Validation

The required tamper-detection scenario was validated by:

1. creating an audit event
2. verifying the chain while the data was intact
3. directly modifying the SQLite datastore
4. running chain verification again

The modified record was detected with:

```text
CONTENT_HASH_MISMATCH
```

The verification response identified the affected record as the first invalid
record.

## Design Documentation

Detailed engineering decisions and requirement analysis are documented in:

- `docs/requirements.md`
- `docs/assumptions.md`
- `docs/architecture.md`
- `docs/scenario_a.md`
- `docs/scenario_b.md`
- `docs/scenario_c.md`
- `docs/final_engineering_summary.md`

Scenario C documents the ambiguity analysis for the requirement concerning
regulatory auditing of client account data.

## AI-Assisted Development

AI was used as an engineering support tool for:

- requirements decomposition
- design exploration
- implementation review
- debugging
- test planning
- documentation review

Engineering decisions remained engineer-led and were validated against the
requirements and test results.

The detailed AI interaction and decision traceability is documented in:

```text
AI_USAGE_LOG.md
```

## Prototype Boundary

This repository demonstrates the audit-log integrity and workflow concepts as
a prototype.

The following production concerns remain outside the prototype scope:

- enterprise authentication and authorization
- encryption and key management
- regulatory retention configuration
- production database scaling and high availability
- monitoring and alerting infrastructure
- backup and recovery
- deployment hardening
- external cryptographic signing or trust services for export bundles

The prototype should not be interpreted as a production-ready regulatory
compliance system.

## Attestation

The individual-work and AI-use attestation is provided in:

```text
ATTESTATION.md
```