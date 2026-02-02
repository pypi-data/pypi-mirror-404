# ml-contracts
Design-by-Contract for ML: Enforce data/features/models pre-deployment.

## Install
```
pip install ml-contracts
```

## Quickstart
```python
from ml_contracts import DataContract
contract = DataContract(
    name="input-data",
    schema={"age": int},
    ranges={"age": (18, 75)},
    distribution={"age": "norm"}
)
```

Fits production pipelines—lightweight, no infra.
