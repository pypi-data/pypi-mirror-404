from typing import Any, Dict, Optional, Tuple

import pandas as pd
from pandas.api import types as ptypes
from scipy import stats

from .exceptions import ContractViolation


class DataContract:
    """Lightweight constraints for tabular inputs."""

    _TYPE_CHECKS: Dict[type, Any] = {
        int: ptypes.is_integer_dtype,
        float: ptypes.is_float_dtype,
        str: ptypes.is_string_dtype,
        bool: ptypes.is_bool_dtype,
    }

    def __init__(
        self,
        name: str,
        schema: Dict[str, type],
        ranges: Optional[Dict[str, Tuple[Any, Any]]] = None,
        distribution: Optional[Dict[str, str]] = None,
        required: bool = True,
    ) -> None:
        self.name = name
        self.schema = schema
        self.ranges = ranges or {}
        self.distribution = distribution or {}
        self.required = required

    def _check_type(self, series: pd.Series, expected: type, col: str) -> None:
        checker = self._TYPE_CHECKS.get(expected)
        if checker is None:
            return
        if not checker(series.dtype):
            raise ContractViolation(f"Column {col} type mismatch: expected {expected.__name__}")

    def enforce(self, df: pd.DataFrame) -> pd.DataFrame:
        missing = set(self.schema.keys()) - set(df.columns)
        if missing and self.required:
            raise ContractViolation(f"Missing columns: {sorted(missing)}")

        for col, expected_type in self.schema.items():
            if col not in df.columns:
                continue
            series = df[col]
            self._check_type(series, expected_type, col)

            if col in self.ranges:
                low, high = self.ranges[col]
                out_of_bounds = series[(series < low) | (series > high)]
                if not out_of_bounds.empty:
                    raise ContractViolation(
                        f"{col} out of range [{low}, {high}]: {len(out_of_bounds)} rows"
                    )

            if col in self.distribution:
                data = series.dropna()
                if len(data) > 10:
                    _, p_value = stats.kstest(data, self.distribution[col])
                    if p_value < 0.05:
                        raise ContractViolation(
                            f"{col} distribution mismatch (p={p_value:.3f})"
                        )

        return df


class ModelContract:
    """Minimal runtime checks for model predict functions."""

    def __init__(
        self,
        max_latency_ms: float = 50.0,
        allowed_null_output: bool = False,
        monotonicity: Optional[Dict[str, str]] = None,
        stability_threshold: float = 0.02,
    ) -> None:
        self.max_latency_ms = max_latency_ms
        self.allowed_null_output = allowed_null_output
        self.monotonicity = monotonicity or {}
        self.stability_threshold = stability_threshold

    def enforce(self, predict_fn, sample_inputs: pd.DataFrame, **kwargs) -> None:
        import time

        start = time.time()
        outputs = predict_fn(sample_inputs, **kwargs)
        latency = (time.time() - start) * 1000
        if latency > self.max_latency_ms:
            raise ContractViolation(f"Latency exceeded: {latency:.1f}ms")

        if not self.allowed_null_output and getattr(outputs, "isnull", None):
            if outputs.isnull().any():
                raise ContractViolation("Null outputs detected")

        # Monotonicity and stability checks can be expanded in future iterations.
