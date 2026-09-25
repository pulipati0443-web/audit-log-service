from copy import deepcopy
from typing import Any


REDACTED_VALUE = "[REDACTED]"


def redact_payload(
    payload: dict[str, Any],
    fields: list[str],
) -> dict[str, Any]:
    redacted_payload = deepcopy(payload)

    for field in fields:
        if field in redacted_payload:
            redacted_payload[field] = REDACTED_VALUE

    return redacted_payload