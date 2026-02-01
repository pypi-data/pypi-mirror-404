# SpinDynamics Python SDK

Official Python SDK for the SpinDynamics inference routing platform.

## Installation

```bash
pip install spindynamics
```

## Quick Start

```python
from spindynamics import Cortex

client = Cortex(api_key="sd_live_...")

deployment = client.deploy(
    model="llama-3.1-70b",
    strategy="adaptive",
    regions=["us-east-1", "eu-west-1"],
)

response = client.infer(
    deployment_id=deployment.id,
    prompt="Explain quantum computing",
    max_tokens=512,
)

print(response.text)
```

## Documentation

Full documentation at [spindynamics.net/docs](https://spindynamics.net/docs).
