import pytest
from django.contrib.auth.models import Group
from django.core.exceptions import ValidationError
from model_bakery import baker

from referentie_tabellen.models import Theme
from statistiek_hub.models.measure import Measure
from statistiek_hub.validations import (
    check_code_in_name,
    check_value_context,
    get_instance,
    validate_calculation_string,
    validate_filter_rule,
)


class TestValidations:
    @pytest.mark.django_db
    def test_get_instance_notexists(self):
        result = get_instance(Measure, field="name", row={"measure": "test"}, column="measure")
        assert str(result[1]) == "Provided measure=test does not exist."

    @pytest.mark.django_db
    def test_get_instance_exists(self):
        var = "BEVTOT"
        testmeasure = baker.make(Measure, name=var, theme=baker.make(Theme, group=baker.make(Group)))
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
            ("P", 1001, "['Percentage is more than 1000']"),
            ("P", 50, "None"),
            ("R", 11, "['Rapportcijfer is more than 10']"),
            ("R", 7, "None"),
            ("R", -1, "['Rapportcijfer is negative']"),
        ],
    )
    def test_check_value_context(self, test_code, test_value, expected):
        result = check_value_context(unit_code=test_code, value=test_value)
        assert str(result) == expected

    def test_validate_calculation_string_valid(self):
        valid_strings = [
            "( $A / ( $B ) ) * 1000",
            "( $VAR1 + $VAR2 ) - 500",
            "( $A * $B ) / 2",
            "( ( $VAR1 - $VAR2 ) / ( $VAR3 ) ) * 1",
            "( $A / ( $[2015-2017]|B|[2018-2999]|C ) ) * 100",
            "( ( $[2015-2017]|A) / ( $[2018-2999]|C ) )",
            "( $A / ( $[2018-2999]|B ) ) * 100",
        ]
        for string in valid_strings:
            validate_calculation_string(string)

    def test_validate_calculation_string_invalid(self):
        invalid_strings = [
            "$A / ( $B ) ) * 1000",  # Missing opening parenthesis
            "( $VAR1 + + $VAR2 ) - 500",  # double operator
            "( $A * ( B ) ) / 2",  # Missing $ before B
            "( $A / ( $[2015-2017] ) ) * 100",  # No var after year-period
            "( $A / ( $[2015 -- 2017]|B",  # Double separator
            "( $A + $[218-299]|C ) * 100",  # No years
        ]
        for string in invalid_strings:
            with pytest.raises(ValidationError):
                validate_calculation_string(string)

    def test_validate_filter_rule_valid(self):
        valid_strings = [
            "( $VAR < 11 )",
            "( $VAR > 11 )",
            "( $VAR >= 11 )",
            "( $VAR != 11 )",
            "( $VAR =! 11 )",
            "( $VAR = 11 )",
            "( $VAR1 = 0 AND $VAR1 < 5 )",
            "( ( ( $VAR1 != 0 ) AND ( $VAR1 < 5 ) ) OR ( $VAR2 < 11 ) )",
        ]
        for string in valid_strings:
            validate_filter_rule(string)

    def test_validate_filter_rule_invalid(self):
        invalid_strings = [
            " $VAR < 11 )",  # Missing opening parenthesis
            "( VAR > 11 )",  # Missing $ before VAR
            "( $VAR >= 11 + 10 )",  # double operator
            "( ( ( $VAR1 != 0 $VAR1 < 5 ) ) OR ( $VAR2 < 11 ) )",  # missing operator
        ]
        for string in invalid_strings:
            with pytest.raises(ValidationError):
                validate_filter_rule(string)
