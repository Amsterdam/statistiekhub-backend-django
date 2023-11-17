import datetime

import pytest
from pandas import DataFrame
from tablib import Dataset

from src.statistiek_hub.utils.check_functions import (
    check_exists_in_model,
    check_missing_fields,
)

dataset = Dataset()
dataset.append(
    [
        "0363",
        "Gemeente",
        "20200101",
        "20170101",
        "Peildatum",
        "BEVTOTAAL",
        "876543",
        datetime.date(2020, 1, 1),
        datetime.datetime(2017, 1, 1, 0, 0),
    ]
)
dataset.append(
    [
        "N",
        "Stadsdeel",
        "20220324",
        "20180101",
        "Peildatum",
        "BEVMAN",
        "6876",
        datetime.date(2022, 3, 24),
        datetime.datetime(2018, 1, 1, 0, 0),
    ]
)

dataset.headers = [
    "spatial_code",
    "spatial_type",
    "spatial_date",
    "temporal_date",
    "temporal_type",
    "measure",
    "value",
    "source_date",
    "start_date",
]

testinput = [
    {
        "dataset": dataset,
        "dfmodel": DataFrame([[1, "BEVTOTAAL"], [2, "BEVMAN"]], columns=["id", "name"]),
        "column": ["measure"],
        "field": ["name"],
        "expected": False,
    },
    {
        "dataset": dataset,
        "dfmodel": DataFrame([[1, "TEST"], [2, "BEVMAN"]], columns=["id", "name"]),
        "column": ["measure"],
        "field": ["name"],
        "expected": "Niet terug",
    },
]


class TestCheck_functions:
    @pytest.mark.parametrize("test_input", testinput)
    def test_check_exists_in_model(self, test_input: dict):
        """check if values from import (dataset[column]) exists in a model field"""

        error = check_exists_in_model(
            test_input["dataset"],
            test_input["dfmodel"],
            test_input["column"],
            test_input["field"],
        )

        if type(error) != bool:
            error = error[0:10]

        assert error == test_input["expected"]


    @pytest.mark.parametrize("test_input, test_expected, test_result", [(dataset.headers, {"spatial_code", "spatial_type", "spatial_date",}, False)])
    def test_check_missing_fields(self, test_input, test_expected, test_result):
        """check all expected items exist in fields: return False"""
        assert  check_missing_fields(test_input, test_expected) == test_result

    @pytest.mark.parametrize("test_input, test_expected, test_result", [(dataset.headers, {"test_field", "spatial_type", "spatial_date",}, "Missing column(s) ['test_field'].")])
    def test_check_missing_fields_found(self, test_input, test_expected, test_result):
        """ check not all expected items exist in fields: return error with printed list with missing items 
        return error string message """

        result = check_missing_fields(test_input, test_expected)
        assert result[0:33] == test_result
