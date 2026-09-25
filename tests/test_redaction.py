from app.services.redaction import redact_payload


def test_redact_payload_replaces_selected_fields():
    payload = {
        "clientName": "John Smith",
        "accountNumber": "123456789",
        "action": "view",
    }

    result = redact_payload(
        payload,
        ["clientName", "accountNumber"],
    )

    assert result == {
        "clientName": "[REDACTED]",
        "accountNumber": "[REDACTED]",
        "action": "view",
    }


def test_redaction_does_not_modify_original_payload():
    payload = {
        "clientName": "John Smith",
        "accountNumber": "123456789",
    }

    redact_payload(
        payload,
        ["accountNumber"],
    )

    assert payload == {
        "clientName": "John Smith",
        "accountNumber": "123456789",
    }


def test_redaction_ignores_missing_fields():
    payload = {
        "action": "view",
    }

    result = redact_payload(
        payload,
        ["accountNumber"],
    )

    assert result == {
        "action": "view",
    }