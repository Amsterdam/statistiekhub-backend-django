import pandas as pd
import pytest

from statistiek_hub.utils.converter import convert_str, set_stringfields_to_upper


class TestConverter:
    @pytest.mark.parametrize(
        "test_input, test_to, expected",
        [
            ("1200", "float", 1200),
            ("1", "float", float(1)),
            ("test", "float", "test"),
            ("4", "set", "4"),
            ("NA", "float", ""),
            ("12,4", "float", 12.4),
        ],
    )
    def test_convert_str(self, test_input, test_to, expected):
        """Return to:format(value) else return value"""
        assert convert_str(test_input, test_to) == expected

    def test_set_stringfields_to_upper(self):
        df = pd.DataFrame({"col1": ["A", "b", "c", "dgh"], "col2": [5, 2, 7, "gtt"]})
        result = set_stringfields_to_upper(df)
        assert result["col1"].tolist() == ["A", "B", "C", "DGH"]
        assert result["col2"].tolist() == [5, 2, 7, "GTT"]
