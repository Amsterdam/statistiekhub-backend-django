import datetime

import pytest

from statistiek_hub.utils.datetime import (
    add_timedelta,
    convert_to_date,
    convert_to_datetime,
    set_year,
)


class TestDatetime:
    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("2022/03/16", datetime.datetime(2022, 3, 16, 0, 0)),
            ("2022-02-11", datetime.datetime(2022, 2, 11, 0, 0)),
            ("2022-00-00", datetime.datetime(2022, 1, 1, 0, 0)),
            ("22-08-2022", datetime.datetime(2022, 8, 22, 0, 0)),
            ("20200822", datetime.datetime(2020, 8, 22, 0, 0)),
            ("2022-02-11 00:00:00.000", datetime.datetime(2022, 2, 11, 0, 0)),
        ],
    )
    def test_convert_to_datetime(self, test_input, expected):
        """Value with format in formats_allowed can be converted to datetime format"""
        assert convert_to_datetime(test_input) == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("17-03-22", "verkeerd"),
            ("test", "verkeerd"),
            ("220810", "verkeerd"),
            ("10052023", "verkeerd"),
            ("10-05-23", "verkeerd"),
        ],
    )
    def test_convert_to_datetime_exception(self, test_input, expected):
        """Raise an exception if value can't be converted to datetime format"""
        with pytest.raises(ValueError) as e:
            convert_to_datetime(test_input)
        assert str(e.value)[0:8] == expected

    @pytest.mark.parametrize(
        "test_input, test_type, expected",
        [
            (
                datetime.datetime(2022, 2, 20, 0, 0),
                "Dag",
                datetime.datetime(2022, 2, 21, 0, 0),
            ),
            (
                datetime.datetime(2022, 2, 20, 0, 0),
                "Week",
                datetime.datetime(2022, 2, 27, 0, 0),
            ),
            (
                datetime.datetime(2022, 2, 27, 0, 0),
                "Week",
                datetime.datetime(2022, 3, 6, 0, 0),
            ),
            (
                datetime.datetime(2022, 2, 20, 0, 0),
                "Maand",
                datetime.datetime(2022, 3, 20, 0, 0),
            ),
            (
                datetime.datetime(2022, 2, 20, 0, 0),
                "Kwartaal",
                datetime.datetime(2022, 5, 20, 0, 0),
            ),
            (
                datetime.datetime(2022, 2, 20, 0, 0),
                "Jaar",
                datetime.datetime(2023, 2, 20, 0, 0),
            ),
            (
                datetime.datetime(2022, 2, 20, 0, 0),
                "Peildatum",
                datetime.datetime(2022, 2, 20, 0, 0),
            ),
            (datetime.datetime(2022, 2, 20, 0, 0), "", None),
        ],
    )
    def test_add_timedelta(self, test_input, test_type, expected):
        """Value with format %Y%m%d can be converted to datetime format"""
        assert add_timedelta(test_input, test_type) == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("2022/03/16", datetime.date(2022, 3, 16)),
            ("2022-02-11", datetime.date(2022, 2, 11)),
            ("2022-00-00", datetime.date(2022, 1, 1)),
            ("22-08-2022", datetime.date(2022, 8, 22)),
            ("20200822", datetime.date(2020, 8, 22)),
            ("2022-02-11 00:00:00.000", datetime.date(2022, 2, 11)),
        ],
    )
    def test_convert_to_date(self, test_input, expected):
        """Value with format in formats_allowed can be converted to datetime format"""
        assert convert_to_date(test_input) == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            ("17-03-22", "verkeerd"),
            ("test", "verkeerd"),
            ("220810", "verkeerd"),
            ("10052023", "verkeerd"),
            ("10-05-23", "verkeerd"),
        ],
    )
    def test_convert_to_date_exception(self, test_input, expected):
        """Raise an exception if value can't be converted to datetime format"""
        with pytest.raises(ValueError) as e:
            convert_to_date(test_input)
        assert str(e.value)[0:8] == expected

    @pytest.mark.parametrize(
        "test_input, expected",
        [
            (
                datetime.date(2022, 2, 20),
                2022,
            ),
            (
                datetime.date(2023, 12, 31),
                2024,
            ),
        ],
    )
    def test_set_year(self, test_input, expected):
        assert set_year(test_input) == expected
