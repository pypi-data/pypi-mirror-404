from functools import wraps
from typing import Callable, Iterable, Tuple

from pandas import Series

from .exceptions import ContractViolation


def feature_contract(name: str, depends_on: Iterable[str], output_range: Tuple[float, float]) -> Callable:
    """Validate feature outputs for downstream contracts."""

    def decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def wrapper(*args, **kwargs) -> Series:
            output = fn(*args, **kwargs)
            if not isinstance(output, Series):
                raise ContractViolation(f"{name} must return a pandas Series")

            lower, upper = output_range
            if output.min() < lower or output.max() > upper:
                raise ContractViolation(f"{name} out of range {output_range}")

            present_keys = set(kwargs)
            if not set(depends_on).issubset(present_keys):
                missing = set(depends_on) - present_keys
                raise ContractViolation(f"{name} missing deps: {sorted(missing)}")

            return output

        return wrapper

    return decorator
