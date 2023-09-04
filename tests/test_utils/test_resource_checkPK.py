import datetime

import pytest
from pandas import DataFrame
from tablib import Dataset

from statistiek_hub.utils.resource_checkPK import check_exists_in_model

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


class TestCheckPK:
    @pytest.mark.parametrize("test_input", testinput)
    def test_resource_checkPK(self, test_input: dict):
        """Value with format in formats_allowed can be converted to datetime format"""

        error = check_exists_in_model(
            test_input["dataset"],
            test_input["dfmodel"],
            test_input["column"],
            test_input["field"],
        )

        if type(error) != bool:
            error = error[0:10]

        assert error == test_input["expected"]
