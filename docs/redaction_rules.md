# Redaction Rules

LogService redacts sensitive data before returning or exporting logs.

## Default Behavior
- Redaction is enabled by default.
- It runs on log lines in query responses and exports.

## Default Patterns (Summary)
- Authorization/token/password key-value pairs
- Bearer tokens
- JWTs
- AWS access keys and secret key fields

## Custom Rules
Create a JSON file and point to it with `LOGSERVICE_REDACTION_PATH` or place it at:
```
~/.logservice/redaction.json
```

### Example
```json
{
  "patterns": [
    {
      "pattern": "(?i)authorization\\s*[:=]\\s*([A-Za-z0-9\\-_.~+/=]+)",
      "replace": "authorization=***",
      "ignore_case": true
    }
  ]
}
```

## Disable Redaction
Set:
```
LOGSERVICE_REDACT=false
```

