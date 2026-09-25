\# Audit Log Service



A Python/FastAPI prototype implementing a tamper-evident append-only audit

logging service.



\## Features



\- Append-only audit events

\- Server-assigned timestamps

\- SHA-256 hash chain

\- Genesis hash

\- Chain verification

\- Tamper detection

\- Query filters

\- Cursor-style pagination

\- Logical archival

\- Structured payload redaction

\- Verifiable export bundles

\- Concurrent-write validation

\- Automated test suite



\## Project Structure



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

├── AI\_USAGE\_LOG.md

└── README.md
