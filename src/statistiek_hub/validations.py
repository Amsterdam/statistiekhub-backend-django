# # validation of the input data
import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError


def _check_open_closing_brackets(string: str):
    open_brackets = re.findall(r"\(", string)
    close_brackets = re.findall(r"\)", string)

    if not len(open_brackets) == len(close_brackets):
        raise ValidationError(
            f"Invalid format. The string {string} should have equal open and closing brackets"
        )


def validate_filter_rule(string: str) -> ValidationError:
    """check rule format"""
    _check_open_closing_brackets(string)

    strip_brackets = string.replace("(", "").replace(")", "")

    matches = re.findall(r"\b(AND|OR)\b", strip_brackets)
    count_and_or = len(matches)

    strip_and_or = strip_brackets.replace("AND", "").replace("OR", "")
    pattern = rf"^(?:\s*\$\w+\s+[!=<>]+\s+\d+\s*){{{count_and_or + 1}}}$"

    if not re.fullmatch(pattern, strip_and_or):
        raise ValidationError(
            f"Invalid format. The string should be of the form like: ( $VAR1 [!=<>] getal ) AND | OR etc"
        )


def validate_calculation_string(string: str) -> ValidationError:
    """check if string has format that can be used by database function
    publicatie_tabellen.db_functions.function_calculate_observations"""

    _check_open_closing_brackets(string)

    strip_brackets = string.replace("(", "").replace(")", "")
    pattern = (
        r"^\s*\$(\w+|\[[0-9]{4}-[0-9]{4}\]\|\w+)(\|(\[[0-9]{4}-[0-9]{4}\]\|\w+|))*"
        r"\s*[\+\-\*\/]\s*\$(\w+|\[[0-9]{4}-[0-9]{4}\]\|\w+)(\|(\[[0-9]{4}-[0-9]{4}\]\|\w+|))*"
        r"(\s*[\+\-\*\/]\s*(\$\w+|\d+))*\s*$"
    )

    if not re.fullmatch(pattern, strip_brackets):
        raise ValidationError(
            f"Invalid format. The string should be of the form like: ( $VAR1 [+-*/] $VAR2 ) [+-*/] 1000"
        )


def check_value_context(unit_code: str, value: float) -> ValidationError:
    """check if value is valid given the unit_code

    Params
    ------------
    value: float

    Return
    -----------
    ValidationError()
    """

    if unit_code == "P":
        if value > 200:
            return ValidationError(f"Percentage is more than 200")
    elif unit_code == "R":
        if value > 10:
            return ValidationError(f"Rapportcijfer is more than 10")
        elif value < 0:
            return ValidationError(f"Rapportcijfer is negative")


# model validation
def check_code_in_name(code: str, name: str) -> ValidationError:
    """check if code is containt in the name

    Params
    ------------
    dimension_code: str
        code from the dimension table
    name: str
        name of a table that needs to contain '_'code

    Return
    -----------
    ValidationError() if name doesn't contain '_'code
    """

    name_split = name.split("_")
    if code not in name_split:
        return ValidationError(f"This field needs to be containing _{code}")


def get_instance(model, field, row, column):
    try:
        instance = model.objects.get(**{f"{field}__iexact": row[column]})
        error = False
    except model.DoesNotExist:
        instance = None
        error = ObjectDoesNotExist(f"Provided {column}={row[column]} does not exist.")
    return (instance, error)
