import pytest

from statistiek_hub.utils.converter import convert_str


class TestConverter:
    @pytest.mark.parametrize(
        "test_input, test_to, expected",
        [
            ("1200", "float", 1200),
            ("1", "float", float(1)),
            ("test", "float", "test"),
            ("4", "set", "4"),
        ],
    )
    def test_convert_str(self, test_input, test_to, expected):
        """Return to:format(value) else return value"""

        assert convert_str(test_input, test_to) == expected
