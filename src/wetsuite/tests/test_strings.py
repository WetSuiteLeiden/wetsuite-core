" basic tests for the strings-related helper functions"
import pytest

from wetsuite.helpers.strings import (
    contains_any_of,
    contains_all_of,
    ordered_unique,
    findall_with_context,
)
from wetsuite.helpers.strings import (
    is_numeric,
    is_mainly_numeric,
    has_text,
    count_unicode_categories,
    remove_diacritics,
)
from wetsuite.helpers.strings import (
    interpret_ordinal_nl,
    ordinal_nl,
    simple_tokenize,
    simplify_whitespace,
)


def test_contains_any_of():
    'test some basic cases for the "matches any of these strings/patterns" function'
    assert contains_any_of("microfishkes", ["mikrofi", "microfi", "fiches"]) is True
    assert contains_any_of("microforks", ["mikrofi", "microfi", "fiches"]) is False
    assert (
        contains_any_of(
            "CASe",
            [
                "case",
            ],
            case_sensitive=False,
        )
        is True
    )

    # test whether strings work as regexp
    assert (
        contains_any_of("microfish", ["mikrofi", "microfi", "fiches"], regexp=True)
        is True
    )
    assert (
        contains_any_of(
            "CASe",
            [
                r"case\b",
            ],
            case_sensitive=False,
            regexp=True,
        )
        is True
    )

    # test interpretation
    assert contains_any_of("microforks", [r"fork$", r"forks$"], regexp=False) is False
    assert contains_any_of("microforks", [r"fork$", r"forks$"], regexp=True) is True
    assert contains_any_of("microfork", [r"forks$"], regexp=True) is False
    assert contains_any_of("forks micro", [r"forks$"], regexp=True) is False


def test_contains_all_of():
    'test some basic cases for the "matches all of these strings/patterns" function'
    assert contains_all_of("AA (BB/CCC)", ("AA", "BB", "CC")) is True
    assert contains_all_of("AA (B/CCC)", ("AA", "BB", "CC")) is False
    assert contains_all_of("AA (B/CCC)", ("aa", "BB"), case_sensitive=False) is False

    assert contains_all_of("AA (BB/CCC)", ("AA", "BB", "CC"), regexp=True) is True
    assert contains_all_of("AA (BB/CCC)", ("^AA", "BB", "CC"), regexp=False) is False

    assert contains_all_of("AA (BB/CCC)", ("^AA", "BB", "CC"), regexp=True) is True
    assert contains_all_of("AA (BB/CCC)", ("^AA", "BB", "CC"), regexp=True) is True
    assert contains_all_of("AA (BB/CCC)", ("^AA", "^BB", "CC"), regexp=True) is False
    assert (
        contains_all_of(
            "AA (BB/CCC)", ("^AA", "bb", "CC"), case_sensitive=True, regexp=True
        )
        is False
    )
    assert (
        contains_all_of(
            "AA (BB/CCC)", ("^AA", "bb", "CC"), case_sensitive=False, regexp=True
        )
        is True
    )


def test_contains_bytes():
    "decode bytes from (default) utf8"
    assert contains_all_of(b"AA (BB/CCC)", (b"^AA",), regexp=True) is True
    # these two are dangerously inconsistent of you, but hey...
    assert contains_all_of("AA (BB/CCC)", (b"^AA",), regexp=True) is True
    assert contains_all_of(b"AA (BB/CCC)", ("^AA",), regexp=True) is True


def test_contains_other():
    "fail on things not str or bytes"
    with pytest.raises(TypeError):
        assert contains_all_of("AA (BB/CCC)", (2,)) is True

    with pytest.raises(TypeError):
        assert contains_all_of(5, ("five",)) is True


def test_ordered_unique():
    "see if we can keep them in order"
    assert ordered_unique(["b", "a", "a"]) == ["b", "a"]
    assert ordered_unique(["b", "a", None, "a"]) == ["b", "a"]
    assert ordered_unique(["b", "a", "A"]) == ["b", "a", "A"]
    assert ordered_unique(["b", "a", "A"], case_sensitive=False) == ["b", "a"]


def test_findall_with_context():
    'test that the "match thing within text, and return some of the string around it" function'
    matches = list(findall_with_context(" a ", "I am a fork and a spoon", 5))
    print(matches)
    assert len(matches) == 2

    before_str, _, _, after_str = matches[0]
    assert before_str == "I am"
    assert after_str == "fork "
    before_str, _, _, after_str = matches[1]
    assert before_str == "k and"
    assert after_str == "spoon"


def test_remove_diacritics():
    "see if we manage to remove diacritics"
    assert remove_diacritics("ol\xe9") == "ole"
    assert remove_diacritics("v\xf3\xf3r") == "voor"


def test_is_numeric():
    'test the "does this string contain only a number-like thing?"'
    assert is_numeric("2.1.") is True
    assert is_numeric("2.1. ") is True
    assert is_numeric(" 2.1.") is True
    assert is_numeric("02 ") is True
    assert is_numeric("B2 ") is False
    assert is_numeric(" ") is False


def test_is_mainly_numeric():
    "is a string mostly numbers?"
    assert is_mainly_numeric("C0103-189922")
    assert not is_mainly_numeric("   CARD-189922  ")


def test_has_text():
    'test the "does this contain anything remotely text-like"'
    assert not has_text("189922")
    assert has_text("   CARD-189922  ")

    assert has_text("C-189922")
    assert not has_text("C-189922", mincount=2)


def test_count_unicode_categories_1():
    "more character focused"
    simpler, longer = count_unicode_categories("Fisher 99 \u2222 \uc3a9 \U0001F9C0")
    assert simpler == {"textish": 7, "space": 4, "number": 2, "symbol": 2}
    assert longer == {"Lu": 1, "Ll": 5, "Zs": 4, "Nd": 2, "Sm": 1, "Lo": 1, "So": 1}


def test_count_unicode_categories_2():
    "more exception focused"
    simpler, longer = count_unicode_categories("\x02 \uE123 \u0065\u0301")
    assert simpler == {"textish": 1, "other": 2, "space": 2}
    assert longer == {"Cc": 1, "Zs": 2, "Co": 1, "Ll": 1}

    # also, combining characters, if left in there, are counted as textish
    simpler, longer = count_unicode_categories(
        "\x02 \uE123 \u0065\u0301", nfc_first=False
    )
    assert simpler == {"textish": 2, "other": 2, "space": 2}
    assert longer == {"Cc": 1, "Zs": 2, "Co": 1, "Ll": 1, "Mn": 1}


def test_simplify_whitespace():
    "test whitespace squeeze and strip"
    assert simplify_whitespace("a   sdfsd  ss   ") == "a sdfsd ss"


def test_simple_tokenize():
    "test that this simple tokenizer doesn't do some _overly_ dumb things"
    assert simple_tokenize(
        "Yadaya (Burmese: \u101a\u1010\u103c\u102c, IPA: [j\u025b\u0300d\u0259j\xe0]; from Sanskrit y\u0101tra; variously "
    ) == [
        "Yadaya",
        "Burmese",
        "\u101a\u1010\u103c\u102c",
        "IPA",
        "j\u025b\u0300d\u0259j\xe0",
        "from",
        "Sanskrit",
        "y\u0101tra",
        "variously",
    ]


def test_interpret_ordinal_nl():
    'do we e.g. turn "vierde" into 4?'
    assert interpret_ordinal_nl("vierde") == 4
    assert interpret_ordinal_nl("achtiende") == 18
    assert interpret_ordinal_nl("twee\xebntwintigste") == 22
    assert interpret_ordinal_nl("vierendertigste") == 34
    assert interpret_ordinal_nl("vijftigste") == 50
    assert interpret_ordinal_nl("negenentachtigste") == 89


def test_interpret_ordinal_nl_bad():
    "fail on nonsense word"
    with pytest.raises(ValueError):
        interpret_ordinal_nl("elvenveertigte")


def test_ordinal_nl():
    'do we e.g. turn 4 into "vierde"?'
    assert ordinal_nl(4) == "vierde"
    assert ordinal_nl(18) == "achtiende"
    assert ordinal_nl(22) == "tweeentwintigste"
    assert ordinal_nl(34) == "vierendertigste"
    assert ordinal_nl(50) == "vijftigste"
    assert ordinal_nl(89) == "negenentachtigste"


def test_ordinal_nl_bad():
    "numbers that don't make sense or we can't do yet"
    with pytest.raises(ValueError):
        ordinal_nl(-2)

    with pytest.raises(ValueError):
        ordinal_nl(111)  # not yet
