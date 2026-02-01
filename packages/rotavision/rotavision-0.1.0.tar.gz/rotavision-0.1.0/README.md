# Rotavision Python SDK

Official Python client for [Rotavision](https://rotavision.com) AI Trust Infrastructure.

## Installation

```bash
pip install rotavision
```

## Quick Start

```python
from rotavision import Rotavision

client = Rotavision(api_key="rv_...")

# Analyze for bias (Vishwas)
result = client.vishwas.analyze(
    text="Loan application response...",
    demographics=["caste", "gender", "region"]
)
print(result.bias_score)

# Monitor AI output (Guardian)
result = client.guardian.monitor(
    prompt="What is the RBI repo rate?",
    response="The RBI repo rate is 6.5%...",
    checks=["hallucination", "factuality"]
)
print(result.status)

# Extract from documents (Dastavez)
result = client.dastavez.extract(
    document=document_bytes,
    document_type="aadhaar",
    mask_pii=True
)
print(result.fields)
```

## Products

| Product | Description |
|---------|-------------|
| **Vishwas** | Trust, Fairness & Explainability |
| **Guardian** | AI Reliability Monitoring |
| **Dastavez** | Document AI + Browser Agents |
| **Sankalp** | Sovereign AI Gateway |
| **Orchestrate** | Multi-Agent Platform |
| **Gati** | Fleet & Mobility Intelligence |

## Documentation

- [API Reference](https://rotavision.com/docs/api/)
- [SDK Documentation](https://rotavision.com/docs/sdks/)
- [Integration Guides](https://rotavision.com/integrations/)

## Requirements

- Python 3.8+
- API key from [Rotavision](https://rotavision.com/contact/)

## License

Apache 2.0 - See [LICENSE](LICENSE) for details.
