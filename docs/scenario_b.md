# Scenario B - Retention, Archive, Redaction, and Export

## Archive / Retention

The prototype implements logical archival rather than physically deleting
audit records.

Archived records retain:

- original event content
- original timestamp
- content hash
- previous hash
- record hash

Additional lifecycle metadata records the archive state:

- `archived`
- `archived_at`

This preserves archived records as part of the verification chain.

The archive operation therefore changes lifecycle metadata rather than changing
the immutable audit-event content.

## Verification of Archived Records

Chain verification reads the complete audit history, including archived
records.

Archival therefore does not break the chain or remove historical evidence from
verification.

## Structured Redaction

Redaction is performed on an output representation rather than modifying the
stored audit event.

The redaction service accepts a list of payload fields and replaces matching
values with:

```text
[REDACTED]
```

The original stored payload and its integrity hashes remain unchanged.

Redaction is currently applied only to top-level payload fields. Nested fields
are not recursively redacted by the prototype.

## Bulk Export

The prototype supports bulk export of audit records filtered by either
`resourceId` or `actorId`.

The export produces a bundle containing:

- export format and version
- export timestamp
- the filter used
- record count
- selected audit records
- a chain anchor for the first exported record

Each exported record retains its:

- `record_id`
- event fields
- timestamp
- `content_hash`
- `previous_hash`
- `record_hash`
- archive metadata

When redaction is requested, the exported payload is replaced with a
redacted representation without modifying the original stored audit event.

## Export Verification

The exported records include the hashes required to validate the integrity
relationships represented in the export.

The `chain_anchor` identifies the first exported record and its
`previous_hash`. A verifier can use this anchor together with the exported
records to validate the hash relationships within the exported sequence.

For an export containing the complete chain, the first record's
`previous_hash` is the genesis value. For a filtered export, the first
exported record may reference a record that is not included in the bundle;
the `chain_anchor` preserves that boundary information.

## Export Limitations

A filtered export is not necessarily the complete global audit chain.
Therefore, an independent verifier can validate the records and chain
relationships represented in the bundle, but cannot reconstruct the entire
global history from a subset alone without the preceding records or a
trusted external anchor.

The prototype also does not implement external signing or a separate
cryptographic trust service for exported bundles.
