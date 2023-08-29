def convert(value: str, to: str = "float"):
    if "float" == to:
        try:
            value = float(value.replace(",", "."))
        finally:
            return value
