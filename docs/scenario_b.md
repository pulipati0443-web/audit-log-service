\# Scenario B - Retention, Archive, Redaction, and Export



\## Archive / Retention



The prototype implements logical archival rather than physically deleting

audit records.



Archived records retain:



\- original event content

\- original timestamp

\- content hash

\- previous hash

\- record hash



Additional lifecycle metadata records the archive state:



\- `archived`

\- `archived\_at`



This preserves archived records as part of the verification chain.



The archive operation therefore changes lifecycle metadata rather than changing

the immutable audit-event content.



\## Verification of Archived Records



Chain verification reads the complete audit history, including archived

records.



Archival therefore does not break the chain or remove historical evidence from

verification.



\## Structured Redaction



Redaction is performed on an output representation rather than modifying the

stored audit event.



The redaction service accepts a list of payload fields and replaces matching

values with:



```text

\[REDACTED]
