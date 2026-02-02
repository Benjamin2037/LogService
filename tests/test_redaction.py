from backend.redaction import Redactor


def test_redacts_bearer_token():
    redactor = Redactor.default()
    text = "Authorization: Bearer abcdef123456"
    redacted = redactor.redact_text(text)
    assert "abcdef" not in redacted
    assert "***" in redacted


def test_redacts_jwt():
    redactor = Redactor.default()
    text = "token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.aaa.bbb"
    redacted = redactor.redact_text(text)
    assert "***JWT***" in redacted
