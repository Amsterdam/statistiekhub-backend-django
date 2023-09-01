def convert_str(value: str, to: str = "float"):
    """Convert string-value to format 'to'"""
    if "float" == to:
        try:
            value = float(value)
        finally:
            return value
    else:
        return value
