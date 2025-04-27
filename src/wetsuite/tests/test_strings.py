" basic tests for the strings-related helper functions"
import pytest

from wetsuite.helpers.strings import (
    contains_any_of,
    contains_all_of,
    ordered_unique,
    findall_with_context,

    is_numeric,
    is_mainly_numeric,
    has_text,
    count_unicode_categories,
    remove_diacritics,
    remove_privateuse,
    canonical_compare,
    compatibility_compare,
    catshape,
    wordiness,
    has_mostly_wordlike_text,

    interpret_ordinal_nl,
    ordinal_nl,
    simple_tokenize,
    simplify_whitespace,

    ngram_generate,
    ngram_count,
    ngram_matchcount,
    ngram_sort_by_matches,

    count_normalized,
    count_case_insensitive,

    remove_deheteen,
    #remove_initial,
)


def test_contains_any_of():
    'test some basic cases for the "matches any of these strings/patterns" function'
    assert contains_any_of("microfishkes", ["mikrofi", "microfi", "fiches"])                      is True
    assert contains_any_of("microforks", ["mikrofi", "microfi", "fiches"])                        is False
    assert contains_any_of( "CASe", [ "case", ], case_sensitive=False )                           is True

    # test whether strings work as regexp
    assert contains_any_of("microfish", ["mikrofi", "microfi", "fiches"], regexp=True)            is True

    assert ( contains_any_of( "CASe",   [ r"case\b", ],  case_sensitive=False, regexp=True ) )    is True

    # test interpretation
    assert contains_any_of("microforks", [r"fork$", r"forks$"], regexp=False)                     is False
    assert contains_any_of("microforks", [r"fork$", r"forks$"], regexp=True)                      is True
    assert contains_any_of("microfork", [r"forks$"], regexp=True)                                 is False
    assert contains_any_of("forks micro", [r"forks$"], regexp=True)                               is False


def test_contains_all_of():
    'test some basic cases for the "matches all of these strings/patterns" function'
    assert contains_all_of("AA (BB/CCC)", ("AA", "BB", "CC"))                                     is True
    assert contains_all_of("AA (B/CCC)", ("AA", "BB", "CC"))                                      is False
    assert contains_all_of("AA (B/CCC)", ("aa", "BB"), case_sensitive=False)                      is False

    assert contains_all_of("AA (BB/CCC)", ("AA", "BB", "CC"), regexp=True)                        is True
    assert contains_all_of("AA (BB/CCC)", ("^AA", "BB", "CC"), regexp=False)                      is False

    assert contains_all_of("AA (BB/CCC)", ("^AA", "BB", "CC"), regexp=True)                       is True
    assert contains_all_of("AA (BB/CCC)", ("^AA", "BB", "CC"), regexp=True)                       is True
    assert contains_all_of("AA (BB/CCC)", ("^AA", "^BB", "CC"), regexp=True)                      is False
    assert contains_all_of("AA (BB/CCC)", ("^AA", "bb", "CC"), case_sensitive=True, regexp=True)  is False
    assert contains_all_of("AA (BB/CCC)", ("^AA", "bb", "CC"), case_sensitive=False, regexp=True) is True


def test_contains_bytes():
    "decode bytes from (default) utf8"
    assert contains_all_of(b"AA (BB/CCC)", (b"^AA",), regexp=True) is True
    # these two are dangerously inconsistent of you, but hey...
    assert contains_all_of("AA (BB/CCC)", (b"^AA",), regexp=True)  is True
    assert contains_all_of(b"AA (BB/CCC)", ("^AA",), regexp=True)  is True


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


def test_remove_privateuse():
    "see if we manage to remove private use characters"
    assert remove_privateuse(" \ud000 \ue000 \U000F0000 \U0010FFFD ", ' ') == ' \ud000       '
    assert remove_privateuse(" \ud000 \ue000 \U000F0000 \U0010FFFD ", '.') == ' \ud000 . . . '


def test_canonical_compare():
    " test whether unicode canonical comparison functions"
    assert canonical_compare('e\u0301', '\xe9') is True
    assert canonical_compare('\u2163', 'IV')    is False


def test_compatibility_compare():
    " test whether unicode compatibility comparison functions"
    assert canonical_compare('e\u0301', '\xe9') is True
    assert compatibility_compare('\u2163', 'IV') is True


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


def test_has_text_float():
    'test that "float for fraction of length" works'
    assert has_text("C-189922", 0.1)
    assert not has_text("C-189922", mincount=0.5)


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


def test_catshape():
    ''' Test that we can convert a string to the major category of each codepoint '''
    assert catshape('Hello, world') == 'LLLLLPZLLLLL'

    # U+65, U+301  is   e, combining accent egu
    assert catshape('\u0065\u0301',False,False) == 'LM' # as-is these are letter, mark
    assert catshape('\u0065\u0301',False,True) == 'L'   # we can do a compose to make that a single letter - where such a codepoint exists, which is far from all cases, so
    assert catshape('\u0065\u0301',True,False) == 'LL'  # by default we consider a mark a letter


def test_wordiness():
    ''' Test that we get a basic answer to 'how much does this look like wordy chunks' '''
    assert wordiness("! # $ % & \' \n \n ( ")                             < 0.2
    assert wordiness("a e i o u a b c d e")                               < 0.2
    assert wordiness("The test is\xe9  22!")                              > 0.7
    assert wordiness("The, test, is\xe9, 22!!!!!")                        > 0.7
    assert wordiness("long test 1, fghsdjkfghdfkjghsdfjkgfsdfjkgfsd")     > 0.7
    assert wordiness("long test 2, fghsdj kfghdfkj ghsdfjkgf sdfjkgfsd")  > 0.7


def test_has_mostly_wordlike_text():
    ''' Test that we get a basic answer to 'is this mostly wordy chunks' '''
    assert has_mostly_wordlike_text("! # $ % & \' \n \n ( ")                             is False
    assert has_mostly_wordlike_text("a e i o u a b c d e")                               is False
    assert has_mostly_wordlike_text("The test is\xe9  22!")                              is True
    assert has_mostly_wordlike_text("The, test, is\xe9, 22!!!!!")                        is True
    assert has_mostly_wordlike_text("long test 1, fghsdjkfghdfkjghsdfjkgfsdfjkgfsd")     is True
    assert has_mostly_wordlike_text("long test 2, fghsdj kfghdfkj ghsdfjkgf sdfjkgfsd")  is True



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


def test_ngram_generate():
    "Test that it generates the n-grams we expect"
    assert list( ngram_generate('foo 1', 2) ) == ['fo', 'oo', 'o ', ' 1']
    assert list( ngram_generate('foo 1', 3) ) == ['foo', 'oo ', 'o 1']
    assert len( list( ngram_generate('foo 1', 6) ) ) == 0


def test_ngram_count():
    "Test that it generates and counts the n-grams we expect"
    assert ngram_count('foo fo', (2,3)) == {'fo': 2, 'oo': 1, 'o ': 1, ' f': 1, 'foo': 1, 'oo ': 1, 'o f': 1, ' fo': 1}


def test_ngram_count_splitfirst():
    "Test the 'split first so we don't collect across word boundaries' argument"
    assert ngram_count('fooo baar', (2,3), splitfirst=True) == {'fo': 1, 'foo': 1, 'oo': 2, 'ooo': 1,   'ba': 1, 'baa': 1,  'aa': 1, 'aar': 1, 'ar': 1, }



def test_ngram_matchcount():
    "Test that it scores like it did at first"
    score = ngram_matchcount(
        ngram_count('foo fo', (2,)),
        ngram_count('foo bar', (2,)),
    )

    assert score > 0.63 and score < 0.64 # 0.6363636363636365


def test_ngram_sort_by_matches():
    "test that fork is put in front of that list"
    assert ngram_sort_by_matches( 'for', ['spork', 'knife', 'spoon', 'fork'])[0] == 'fork' # here mainly to point out that's a use
    assert ngram_sort_by_matches( 'for', ['spork', 'knife', 'spoon', 'fork']) == ['fork', 'spork', 'knife', 'spoon']


def test_ngram_sort_by_matches_with_scores():
    "test that fork is put in front of that list"
    assert ngram_sort_by_matches( 'for', ['spork', 'knife', 'spoon', 'fork'], with_scores=True) == [('fork', 10), ('spork', 4), ('knife', 1), ('spoon', 1)]
    # those scores might change with the implementation, maybe only test that we have str,int tuples?


def test_count_normalized():
    "test the count-normalized-form function"

    ci = count_normalized("a A A a A A a B b b B b".split())
    assert ci["a"] == 3
    assert ci["A"] == 4
    assert ci["b"] == 3
    assert ci["B"] == 2

    cs = count_normalized(
        "a A A a A A a B b b B b".split(), normalize_func=lambda s: s.lower()
    )
    assert cs["A"] == 7
    assert cs["b"] == 5


def test_count_case_insensitive():
    ' test the case-insensitive variation '
    cs = count_case_insensitive("a A A a A A a B b b B b".split())
    assert cs["A"] == 7
    assert cs["b"] == 5

    cs = count_case_insensitive(
        "aa A A aa A A aa B bb bb B bb cc cc dd".split(), min_word_length=2, min_count=2
    )
    assert cs["aa"] == 3
    assert cs["bb"] == 3
    assert cs["cc"] == 2
    assert "d" not in cs


def test_count_normalized_mincount_wut():
    ' test that it errors out on things not int or float '
    with pytest.raises(TypeError):
        count_normalized("a A A a A A a B b b B b".split(), min_count=None)

    with pytest.raises(TypeError):
        count_normalized("a A A a A A a B b b B b".split(), min_count='cheese')


def test_stop():
    "test that count_normalized stopword functionality seems to work"
    cs = count_normalized(
        "a A A a A A a B b b B b".split(),
        normalize_func=lambda s: s.lower(),
        stopwords=(),
        stopwords_i=(),
    )
    assert cs == {"A": 7, "b": 5}

    cs = count_normalized(
        "a A A a A A a B b b B b".split(),
        normalize_func=lambda s: s.lower(),
        stopwords=("a",),
        stopwords_i=(),
    )
    assert cs == {"A": 4, "b": 5}

    cs = count_normalized(
        "a A A a A A a B b b B b".split(),
        normalize_func=lambda s: s.lower(),
        stopwords=(),
        stopwords_i=("a",),
    )
    assert cs == {"b": 5}

    cs = count_case_insensitive(
        ["the", "een"], stopwords=True
    )  #  asks for some (english and stuch)
    assert len(cs) == 0


def test_count_normalized_min():
    "test that the minimum threshold seems to work"
    cs = count_normalized("a a a a b b b c".split(), min_count=2)
    assert cs["a"] == 4
    assert cs["b"] == 3
    assert "c" not in cs

    cs = count_normalized("a a a a b b b c".split(), min_count=2.0)
    assert cs["a"] == 4
    assert cs["b"] == 3
    assert "c" not in cs

    cs = count_normalized("a a a a b b b c".split(), min_count=3.5)
    assert cs["a"] == 4
    assert "b" not in cs
    assert "c" not in cs

    cs = count_normalized("a a a a b b b c".split(), min_count=0.3)
    assert cs["a"] == 4
    assert cs["b"] == 3
    assert "c" not in cs


def test_remove_deheteen():
    ' test that we remove an initial "de" or "het" from phrases '
    assert remove_deheteen('het ministerie') == 'ministerie'

#def test_remove_initial():
#    remove_initial
