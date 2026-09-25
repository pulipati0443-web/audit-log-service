\# Scenario A - Core Audit Log Service



\## Objective



Implement a tamper-evident append-only audit log that records audit events and

detects unauthorized modification of previously stored records.



\## Requirement Decomposition



\### Write



The service accepts:



\- `eventType`

\- `actorId`

\- `resourceType`

\- `resourceId`

\- `payload`



The server assigns the authoritative timestamp when the event is accepted.



\### Append-Only Behavior



The public API does not provide update or delete operations for audit-event

content.



Once an event is created, its event content and integrity hashes are treated as

immutable.



\### Query



The service supports filtering by:



\- actor ID

\- resource type

\- resource ID

\- event type

\- timestamp range



Pagination is supported using `record\_id` as the stable ordering field.



\### Integrity



Each record contains:



\- `content\_hash`

\- `previous\_hash`

\- `record\_hash`



The content hash covers the canonical audit-event representation.



The record hash incorporates both the previous record hash and the current

canonical representation.



The first record uses a fixed genesis hash.



\## Chain Ordering Decision



`record\_id` is the authoritative chain sequence.



The server-assigned timestamp represents the event recording time but is not

used to determine chain order.



This avoids ambiguity if timestamps are equal or if event timing does not

strictly correspond to persistence order.



\## Verification



`GET /audit/verify` processes records in ascending `record\_id` order.



For each record it verifies:



1\. Genesis linkage for the first record.

2\. Previous-hash linkage for subsequent records.

3\. Recalculated content hash.

4\. Recalculated record hash.



Verification stops at the first detected inconsistency and reports the affected

record and violation type.



\## Validation



The integrity workflow was validated by:



1\. Creating an audit event.

2\. Verifying the chain while intact.

3\. Directly modifying the stored payload in SQLite.

4\. Running chain verification again.



The resulting verification response was:



```json

{

&#x20; "intact": false,

&#x20; "first\_invalid\_record\_id": 1,

&#x20; "violation": "CONTENT\_HASH\_MISMATCH"

}
