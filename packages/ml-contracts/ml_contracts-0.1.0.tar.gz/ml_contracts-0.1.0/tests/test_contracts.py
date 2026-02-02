import pandas as pd
import pytest

from ml_contracts import DataContract, ContractViolation


def test_data_contract_out_of_range():
    contract = DataContract(
        name="test",
        schema={"age": int},
        ranges={"age": (18, 75)},
        distribution={"age": "norm"},
    )
    df = pd.DataFrame({"age": [20, 80]})
    with pytest.raises(ContractViolation):
        contract.enforce(df)
