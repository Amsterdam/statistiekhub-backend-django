# # validation of the input data
import re

from django.core.exceptions import ObjectDoesNotExist, ValidationError


# field filter validation
def check_filter_rule(rule: str) -> ValidationError:
    """ TODO check rule
    - validate syntax: spaces, OR AND and brackets
    - validate measure: bv is measure een aantal (met percentages als basis is raar?)
    - validate at leas 1 observation of rule measure:
    """
    isinstance(rule, str) # added ivm linting



def validate_calculation_string(string: str) -> ValidationError:
    ''' check if string has format that can be used by database function
    publicatie_tabellen.db_functions.function_calculate_observations '''
    
    open_brackets = re.findall(r'\(', string)
    close_brackets = re.findall(r'\)', string)

    if not len(open_brackets) == len(close_brackets):
        raise ValidationError(
            f'Invalid format. The string {string} should have equal open and closing brackets'
        )

    strip_brackets = string.replace('(', '').replace(')', '')
    pattern =  r'^\s*\$\w+\s*[\+\-\*/]\s*\$\w+(\s*[\+\-\*/]\s*(\$\w+|\d+))*\s*$'

    if not re.fullmatch(pattern, strip_brackets):
        raise ValidationError(
            f'Invalid format. The string should be of the form like: ( $VAR1 [+-*/] $VAR2 ) [+-*/] 1000'
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
