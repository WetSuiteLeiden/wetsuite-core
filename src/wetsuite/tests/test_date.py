" test of date related code "
import datetime

import pytest

from wetsuite.helpers.date import parse, find_dates_in_text
from wetsuite.helpers.date import (
    days_in_range,
    date_ranges,
    format_date_list,
    yyyy_mm_dd,
)
from wetsuite.helpers.date import (
    date_today,
    date_weeks_ago,
    date_months_ago,
    date_first_day_in_year,
    date_last_day_in_year,
    date_first_day_in_month,
)


def test_dates_in_range():
    "test of date_range"
    should_be = [
        datetime.date(2022, 1, 29),
        datetime.date(2022, 1, 30),
        datetime.date(2022, 1, 31),
        datetime.date(2022, 2, 1),
        datetime.date(2022, 2, 2),
    ]

    rng = days_in_range(datetime.date(2022, 1, 29), datetime.date(2022, 2, 2))
    assert rng == should_be

    rng = days_in_range("29 jan 2022", "2 feb 2022")
    assert rng == should_be

    rng = days_in_range(datetime.datetime(2022, 1, 29), datetime.datetime(2022, 2, 2))
    assert rng == should_be


def test_days_in_range2():
    "more test of date_range"
    assert days_in_range(datetime.date(2022, 1, 1), datetime.date(2022, 1, 1)) == [
        datetime.date(2022, 1, 1)
    ]

    with pytest.raises(ValueError, match=r".*of type.*"):
        days_in_range(b"29 jan 2022", b"29 jan 2022")

    with pytest.raises(ValueError, match=r".*of type.*"):
        days_in_range((2022, 1, 1), (2022, 1, 1))


def test_format_days_in_range():
    "test string formatting of day ranges"
    assert days_in_range(
        datetime.date(2022, 1, 30),
        datetime.date(2022, 2, 1),
        strftime_format="%Y-%m-%d",
    ) == ["2022-01-30", "2022-01-31", "2022-02-01"]


def test_date_ranges():
    'test "split larger interval into shorter intervals"'
    assert date_ranges("1 nov 1988", "30 nov 1988", increment_days=7) == [
        (datetime.date(1988, 11, 1), datetime.date(1988, 11, 8)),
        (datetime.date(1988, 11, 8), datetime.date(1988, 11, 15)),
        (datetime.date(1988, 11, 15), datetime.date(1988, 11, 22)),
        (datetime.date(1988, 11, 22), datetime.date(1988, 11, 29)),
        (datetime.date(1988, 11, 29), datetime.date(1988, 11, 30)),
    ]

    assert date_ranges("1 nov 1988", "15 nov 1988", increment_days=7) == [
        (datetime.date(1988, 11, 1), datetime.date(1988, 11, 8)),
        (datetime.date(1988, 11, 8), datetime.date(1988, 11, 15)),
    ]
    # possible regression - because if you <=, you get  [('1988-11-01', '1988-11-08'), ('1988-11-08', '1988-11-15'), ('1988-11-15', '1988-11-15')]


def test_format_date_ranges():
    "test the string output of date_ranges"
    assert date_ranges(
        "1 nov 1988", "15 nov 1988", increment_days=7, strftime_format="%Y-%m-%d"
    ) == [("1988-11-01", "1988-11-08"), ("1988-11-08", "1988-11-15")]


def test_format_date_list():
    "format list of datetimes with (by default) '%Y-%m-%d'"
    assert format_date_list([datetime.date(2022, 1, 29), datetime.date(2022, 1, 30)]) == [
        "2022-01-29",
        "2022-01-30",
    ]


def test_parse():
    "test the parsing of sligtly free-form strings"
    assert parse("2022-1-1")             == datetime.datetime(2022, 1,   1,   0, 0)
    # invalid but I've seen it
    assert parse("2022-01-01+0200")      == datetime.datetime(2022, 1,   1,   0, 0)

    assert parse("  5 may 1988  ")       == datetime.datetime(1988, 5,   5,   0, 0)
    assert parse("  1 november 1988  ")  == datetime.datetime(1988, 11,  1,   0, 0)
    assert parse("  1e november 1988  ") == datetime.datetime(1988, 11,  1,   0, 0)
    assert parse("  20 december 2022  ") == datetime.datetime(2022, 12, 20,   0, 0)

def test_parse_ignoreday():
    " it doesn't actually understand that (it was a tuesday), but it ignores it fine "
    assert parse("  donderdag 1 november 1988  ") == datetime.datetime(
        1988, 11, 1, 0, 0
    )

def test_parse_includingtime():
    " including time (don't count on this in less formal options) "
    assert parse("2022-01-01 11:22")      == datetime.datetime(2022, 1,   1,   11, 22)


def test_parse_date():
    "same parsing tests, asking for datetime instead of date"
    assert parse("2022-01-01+0200", as_date=True)      == datetime.date(2022, 1, 1)

    assert parse("  5 may 1988  ", as_date=True)       == datetime.date(1988, 5, 5)
    assert parse("  1 november 1988  ", as_date=True)  == datetime.date(1988, 11, 1)
    assert parse("  1e november 1988  ", as_date=True) == datetime.date(1988, 11, 1)
    assert parse("  20 december 2022  ", as_date=True) == datetime.date(2022, 12, 20)

    assert parse("2022-01-01 11:22", as_date=True)     == datetime.date(2022, 1, 1)


def test_yy_mm_dd():
    "test that this formatter basically works"
    assert yyyy_mm_dd(datetime.date(2024, 1, 1)) == "2024-01-01"


def test_noparse():
    "test the parsing of sligtly free-form strings"
    assert parse("booga", exception_as_none=True) is None
    with pytest.raises(ValueError, match=r".*understand.*"):
        assert parse("booga", exception_as_none=False)


def test_find_dates_in_text_textpart():
    "test the text part of find_dates_in_text"
    assert find_dates_in_text(
        "Op 1 november 1988 (oftwel 1988-11-1) gebeurde er vast wel iets."
    )[0] == ["1 november 1988", "1988-11-1"]
    assert find_dates_in_text("  1 november 1988  ")[0][0] == "1 november 1988"
    assert find_dates_in_text("  1 November 1988  ")[0][0] == "1 November 1988"
    assert find_dates_in_text("  1 nov 1988  ")[0][0] == "1 nov 1988"

def test_find_dates_in_text_parsingpart():
    "test the parsing part of find_dates_in_text"
    assert find_dates_in_text("  1 november 1988   2 november, 1988")[1] == [
        datetime.datetime(1988, 11, 1, 0, 0),
        datetime.datetime(1988, 11, 2, 0, 0),
    ]
    assert find_dates_in_text("  3 apr 1988  ")[1][0] == datetime.datetime(
        1988, 4, 3, 0, 0
    )
    assert find_dates_in_text("  4 januari 1988  ")[1][0] == datetime.datetime(
        1988, 1, 4, 0, 0
    )
    assert find_dates_in_text("  5 mei 1988  ")[1][0] == datetime.datetime(
        1988, 5, 5, 0, 0
    )

    assert find_dates_in_text("  5 may 1988  ")[1][0] == datetime.datetime(
        1988, 5, 5, 0, 0
    )
    assert find_dates_in_text("  20 december 2022  ")[1][0] == datetime.datetime(
        2022, 12, 20, 0, 0
    )

    # two-digit years
    assert find_dates_in_text("  1 nov 88  ")[0][0] == "1 nov 88"
    assert find_dates_in_text("  1 nov 88  ")[1][0] == datetime.datetime(
        1988, 11, 1, 0, 0
    )



def test_today_and_ago_noerror():
    "test that these functions do not fail outright"
    date_today()

    date_weeks_ago(1)

    date_months_ago(1)


def test_nobork_firstlast():
    ' test that these functions '
    assert date_first_day_in_year(2024) == datetime.date(2024,1,1)
    assert date_last_day_in_year(2024) == datetime.date(2024,12,31)

    assert date_first_day_in_month(2024,2) == datetime.date(2024,2,1)
    date_first_day_in_month()


def test_nobork_firstlast_2():
    ' TODO: test that these are indeed in the current year? '
    date_first_day_in_year() # current year
    date_last_day_in_year() # current year
