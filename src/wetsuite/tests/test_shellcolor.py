" test the shell coloring module "

import wetsuite.helpers.shellcolor

# from wetsuite.helpers.shellcolor import *   # Too many to import, okay for test, also linter says what we've not tested   pylint: disable=wildcard-import
from wetsuite.helpers.shellcolor import (
    guess_color_support,
    color_degree,
    _percent_parse,
    real_len,
    cformat,
    WHITE,
    RESET,
    closest_from_rgb255,
    redgreen,
    true_colf,
    hash_color,
    blend,
    truncate_real_len,
)
from wetsuite.helpers.shellcolor import (
    brightblack,
    darkgray,
    darkgrey,
    black,
    red,
    brightred,
    green,
    brightgreen,
    orange,
    yellow,
    brightyellow,
    blue,
    brightblue,
    magenta,
    brightmagenta,
    cyan,
    brightcyan,
    gray,
    grey,
    brightgrey,
    brightgray,
    white,
    bgblack,
    bgred,
    bggreen,
    bgblue,
    bgyellow,
    bgorange,
    bgmagenta,
    bgcyan,
)

# default, reset, clearscreen


def test_color_degree():
    "test the 'color by liner interpolation' function"
    guess_color_support(True, True, True)
    assert (color_degree("foo", 0, 0, 100)) == "\x1b[1;30mfoo\x1b[0m\x1b[39m"
    assert (color_degree("bar", 30, 0, 100)) == "\x1b[37mbar\x1b[0m\x1b[39m"


def test_percent_parse():
    'tests whether the "add number to percentage-formatting widths" function does not bork out'
    assert (
        _percent_parse(" a  %%  qq  %.5d %30s  % -31.7f ", [0, 0, 5, 9])
        == " a  %%  qq  %.5d %35s  % -40.7f "
    )


def test_cformat():
    'test the "string formatter that understands that color escapes have no real width" function'
    assert (
        cformat("%20s", (WHITE + "fork" + RESET,))
        == "                \x1b[1;37mfork\x1b[0m\x1b[39m"
    )


def test_real_len():
    "test the 'ignore some escapes, count the text' function"
    assert real_len("\x1b[1;30mfoo\x1b[0m\x1b[39m")[0] == 3
    assert real_len("\x1b[37mbar\x1b[0m\x1b[39m")[0] == 3


###########


def test_closest_from_rgb255():
    "just tests that it does not bork; TODO: test actual functionality"
    closest_from_rgb255(40, 50, 60)

    closest_from_rgb255(40, 50, 60, nobright=True)


def test_true_colf():
    "just tests that it does not bork; TODO: test actual functionality"
    true_colf("foo", 70, 80, 90)


def test_redgreen():
    "just tests that it does not bork; TODO: test actual functionality"
    redgreen("foo", 0.0)
    redgreen("foo", 0.5)
    redgreen("foo", 1.0)

    redgreen("foo", -1)
    redgreen("foo", -2.0)

    redgreen("foo", 2.0)


def test_blend():
    "just tests that it does not bork; TODO: test actual functionality"
    blend("foo", 0.5, (0, 0, 0), (255, 255, 255))


def test_hash_color():
    "just tests that it does not bork; TODO: test actual functionality"
    hash_color("foo")

    hash_color("foo", hash_instead="bar")

    hash_color("foo", on="dark")
    hash_color("foo", on="light")

    hash_color("foo", rgb=True, on="dark")
    hash_color("foo", rgb=True, on="light")


def test_colors():
    "mainly just for test coverage statistics :)"
    # guess_color_support(True, True, True)
    wetsuite.helpers.shellcolor._guess = (
        True  # force    # pylint: disable=protected-access
    )

    for color_func in (
        brightblack,
        darkgray,
        darkgrey,
        black,
        red,
        brightred,
        green,
        brightgreen,
        orange,
        yellow,
        brightyellow,
        blue,
        brightblue,
        magenta,
        brightmagenta,
        cyan,
        brightcyan,
        gray,
        grey,
        brightgrey,
        brightgray,
        white,
        bgblack,
        bgred,
        bggreen,
        bgblue,
        bgyellow,
        bgorange,
        bgmagenta,
        bgcyan,
    ):
        s = color_func("s")
        assert len(s) > 1

        s = color_func("s", "FOO")
        assert len(s) > 1
        assert "FOO" in s

    #    default
    #    reset
    #    clearscreen


def test_truncate_real_len():
    "just tests that it does not bork; TODO: test actual functionality"
    truncate_real_len("                  ", 10)
