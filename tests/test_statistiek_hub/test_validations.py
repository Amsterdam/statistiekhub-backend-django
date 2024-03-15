import pytest
from model_bakery import baker

from statistiek_hub.models.measure import Measure
from statistiek_hub.validations import (
    check_code_in_name,
    check_value_context,
    get_instance,
)


class TestValidations:

    @pytest.mark.django_db
    def test_get_instance_notexists(self):
        result = get_instance(Measure, field="name", row={"measure": "test"}, column="measure")
        assert str(result[1]) == 'Provided measure=test does not exist.'

    @pytest.mark.django_db
    def test_get_instance_exists(self):
        var = "BEVTOT"
        testmeasure = baker.make(Measure, name=var)
        result = get_instance(Measure, field="name", row={"measure": var}, column="measure")
        assert result[0].name == testmeasure.name

    @pytest.mark.parametrize(
        "test_code, test_name, expected",
        [
            ("P", "Test_", "['This field needs to be containing _P']"),
            ("R", "Test_R", "None"),
            ("R", "Test__R", "None"),
        ],
    )
    def test_check_code_in_name(self, test_code, test_name, expected):
        result = check_code_in_name(code=test_code, name=test_name)
        assert str(result) == expected

    @pytest.mark.parametrize(
        "test_code, test_value, expected",
        [
            ("P", 300, "['Percentage is more than 200']"),
            ("P", 50, "None"),
            ("R", 11, "['Rapportcijfer is more than 10']"),
            ("R", 7, "None"),
            ("R", -1, "['Rapportcijfer is negative']"),
        ],
    )
    def test_check_value_context(self, test_code, test_value, expected):
        result = check_value_context(unit_code=test_code, value=test_value)
        assert str(result) == expected

