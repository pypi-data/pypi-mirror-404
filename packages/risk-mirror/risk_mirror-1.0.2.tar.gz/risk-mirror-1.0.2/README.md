# Risk Mirror SDK - Python

Deterministic AI Safety Toolkit for prompt security.

## Installation

```bash
pip install risk-mirror
```

## Quick Start

```python
from risk_mirror import RiskMirror

# Initialize client
client = RiskMirror(api_key="your-api-key")

# Scan for safety issues
result = client.scan("Check this text for PII and secrets")

print(result.verdict)  # SAFE, REVIEW, or HIGH_RISK
print(result.findings)  # List of findings
print(result.safe_output)  # Redacted text
```

## Features

- **PII Detection**: Email, phone, SSN, etc.
- **Secrets Detection**: API keys, tokens, passwords
- **Injection Detection**: Prompt injection attempts
- **Safe Share**: Burner-safe strings for sharing with AI
- **Zero Storage**: No content is stored
- **Deterministic**: Same input = same output

## Safe Share

```python
from risk_mirror import RiskMirror

client = RiskMirror(api_key="your-api-key")
result = client.safe_share("sk-ABCD1234-XYZ", mode="full")

print(result.safe_share_text)
print(result.audit_summary)
```

## License

MIT
