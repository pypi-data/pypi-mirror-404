# GridSeal

[![PyPI version](https://img.shields.io/pypi/v/gridseal.svg)](https://pypi.org/project/gridseal/)
[![Python](https://img.shields.io/pypi/pyversions/gridseal.svg)](https://pypi.org/project/gridseal/)
[![License](https://img.shields.io/badge/license-AGPL--3.0-blue.svg)](https://github.com/gridseal-ai/gridseal/blob/main/LICENSE)
[![Downloads](https://img.shields.io/pypi/dm/gridseal.svg)](https://pypi.org/project/gridseal/)

Verification and compliance-grade audit logging for LLM applications.

*A [Celestir](https://celestir.com) product.*

## Installation

```bash
pip install gridseal
```

## Quick Start

```python
from gridseal import GridSeal

gs = GridSeal()

@gs.verify
@gs.audit
def answer(query: str, context: list[str]) -> str:
    return your_llm.generate(query, context)

result = answer("Is this valid?", documents)
print(result.passed)      # True/False
print(result.response)    # The LLM output
print(result.audit_id)    # Audit record ID
```

## Features

- Hallucination detection via grounding checks
- Confidence and relevance scoring
- Citation verification with NLI
- Immutable audit trails with hash chain integrity
- Compliance-grade logging for FedRAMP, NIST AI RMF, EU AI Act

## Configuration

```python
from gridseal import GridSeal

gs = GridSeal(
    verification={
        "checks": ["grounding", "confidence", "relevance"],
        "threshold": 0.7,
        "on_fail": "flag",
    },
    audit={
        "backend": "sqlite",
        "path": "./audit.db",
    },
)
```

## CLI

```bash
gridseal verify --path ./audit.db    # Check integrity
gridseal export --format json        # Export records
gridseal stats                       # Show statistics
```

## License

AGPL-3.0-or-later - See [LICENSE](LICENSE)

## Copyright

Copyright (c) 2026 Celestir LLC
