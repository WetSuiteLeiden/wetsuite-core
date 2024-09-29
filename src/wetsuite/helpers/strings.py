""" mostly-basic string helper functions 

    Many are simple enough, or specific, that you'ld easily implement them as you need them, so not that much time is saved.
"""

import re
import unicodedata
import collections
from typing import List


def _matches_anyall(
    haystack: str,
    needles: List[str],
    case_sensitive=True,
    regexp=False,
    encoding=None,
    matchall=False,
):
    "helper for L{contains_any_of} and L{contains_all_of}. See the docstrings for both."
    # and deal with bytes type (if you handed in an encoding)
    if isinstance(haystack, bytes):
        haystack = haystack.decode(encoding)
    elif not isinstance(haystack, str):
        raise TypeError("haystack %r is not str or bytes" % haystack)
    fneedles = []
    for needle in needles:
        if isinstance(needle, bytes):
            fneedles.append(needle.decode(encoding))
        elif isinstance(needle, str):
            fneedles.append(needle)
        else:  # assume str
            raise TypeError("needle %r is not str or bytes" % needle)
    needles = fneedles

    # deal with case insensitivity
    reflags = 0  # 0 is no flags set
    if not case_sensitive:
        if regexp:
            reflags = re.I
        else:
            haystack = haystack.lower()
            needles = list(needle.lower() for needle in needles)

    # do actual test, regexp or not

    matches = []  # whether haystack matches each needle
    for needle in needles:
        if regexp:
            if re.search(needle, haystack, flags=reflags) is not None:
                matches.append(True)
            else:
                matches.append(False)
        else:
            if needle in haystack:
                matches.append(True)
            else:
                matches.append(False)

    # there are more syntax-succinct ways to write this, yes.
    if matchall:  # must match all - any False means the whole is False
        if False in matches:
            return False
        return True
    else:  # match any - any True means the whole is True
        if True in matches:
            return True
        return False


def contains_any_of(
    haystack: str,
    needles: List[str],
    case_sensitive=True,
    regexp=False,
    encoding="utf8",
):  # TODO: rename to matches_any_of
    """Given a string and a list of strings,  returns whether the former contains at least one of the strings in the latter
    e.g. contains_any_of('microfishes', ['mikrofi','microfi','fiches']) == True

    @param needles: the things to look for
    Note that if you use regexp=True and case_sensitive=True, the regexp gets lowercased before compilation,
    which may not always be correct.
    @param case_sensitive: if False, lowercasing hackstack and needle before testing. Defauts to True.
    @param regexp: treat needles as regexps rather than subbstrings.  Default is False, i.e.  substriungs
    @param haystack: is treated like a regular expression (the test is whether re.search for it is not None)
    @param encoding : lets us deal with bytes, by saying "if you see a bytes haystack or needle, decode using this encoding".
    Defaults to utf-8
    """
    return _matches_anyall(
        haystack=haystack,
        needles=needles,
        case_sensitive=case_sensitive,
        regexp=regexp,
        encoding=encoding,
        matchall=False,
    )


def contains_all_of(
    haystack: str,
    needles: List[str],
    case_sensitive=True,
    regexp=False,
    encoding="utf8",
):  # TODO: rename to matches_all_of
    """Given a string and a list of strings, returns whether the former contains all of the substrings in the latter 
    Note that no attention is paid to word boundaries.
    e.g. 
      - contains_all_of('AA (B/CCC)', ('AA', 'BB') ) == False
      - strings.contains_all_of('Wetswijziging', ['wijziging', 'wet'], case_sensitive=False) == True
      - strings.contains_all_of('wijziging wet A', ['wijziging', 'wet'], case_sensitive=False) == True

    @param needles: the things to look for
    Note that if you use regexp=True and case_sensitive=True, the regexp gets lowercased before compilation,
    which may not always be correct.
    @param case_sensitive: if False, lowercasing hackstack and needle before testing. Defauts to True.
    @param regexp: treat needles as regexps rather than subbstrings.  Default is False, i.e.  substriungs
    @param haystack: is treated like a regular expression (the test is whether re.search for it is not None)
    @param encoding : lets us deal with bytes, by saying "if you see a bytes haystack or needle, decode using this encoding".
    Defaults to utf-8
    """
    return _matches_anyall(
        haystack=haystack,
        needles=needles,
        case_sensitive=case_sensitive,
        regexp=regexp,
        encoding=encoding,
        matchall=True,
    )


def ordered_unique(strlist:List[str], case_sensitive:bool=True, remove_none:bool=True):
    """Takes a list of strings, returns one without duplicates, keeping the first of each 
    (so unlike a plain set(strlist), it keeps the order of what we keep)
    (Not the fastest implementation)

    @param strlist: The list of strings to work on
    @param case_sensitive: If False, it then keeps the _first_ casing it saw
    @param remove_none: remove list elements that are None instead of a string
    @return: a list of strings
    """
    ret = []
    retlow = []
    for onestr in strlist:
        if remove_none and onestr is None:
            continue
        if case_sensitive:
            if onestr in ret:
                continue
            ret.append(onestr)
        else:
            strlow = onestr.lower()
            if strlow in retlow:
                continue
            ret.append(onestr)
            retlow.append(strlow)
    return ret


def findall_with_context(pattern: str, s: str, context_amt: int):
    """Matches substrings/regexpe, and for each match also gives some of the text context (on a character-amount basis).

    For example::
            list(findall_with_context(" a ", "I am a fork and a spoon", 5))
    would return::
            [('I am', ' a ', <re.Match object; span=(4, 7), match=' a '>,   'fork '),
            ('k and', ' a ', <re.Match object; span=(15, 18), match=' a '>, 'spoon')]

    @param pattern: the regex (/string) to look for

    @param s: the string to find things in 

    @param context_amt: amount of context, in number of characters

    @return: a generator that yields 4-tuples:
        - string before
        - matched string
        - match object  - may seem redundant, but you often want a distinction between what is matched and captured. Also, the offset can be useful
        - string after
    """
    for match_object in re.finditer(pattern, s):
        st, en = match_object.span()
        yield (
            s[max(0, st - context_amt) : st],
            s[st:en],
            match_object,
            s[en : en + context_amt],
        )


_re_combining = re.compile(
    r"[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]", re.U
)
" helps remove diacritics - list a number of combining (but not actually combin*ed*) character ranges in unicode, since you often want to remove these (after decomposition) "


def remove_diacritics(string: str):
    """Unicode decomposes, remove combining characters, unicode compose.
    Note that not everything next to a letter is considered a diacritic.
    @param string: the string to work on
    @return: a string where diacritics on characters have been removed, e.g.::
        remove_diacritics( 'ol\xe9' ) == 'ole'
    """
    # TODO: Figure out what the compose is doing, and whether it is necessary at all.
    return unicodedata.normalize(
        "NFC", _re_combining.sub("", unicodedata.normalize("NFD", string))
    )


# CONSIDER: base this on count_unicode_categories so we support other languages

def is_numeric(string: str):
    """Does this string contain _only_ something we can probably consider a number?    That is, [0-9.,] and optional whitespace around it
    @param string: the string to look in
    """
    return re.match(r"^\s*[0-9,.]+\s*$", string) is not None


def is_mainly_numeric(string: str, threshold=0.8):
    """Returns whether the amount of characters of the string
    that are 0123456789, -, or space,
    make up more than threshold of the entire string lengt.

    Meant to help ignore serial numbers and such.
    @param string: the text to look in
    @param threshold: if more than this fraction of numbers (or the other mentioned characters), we return True.
    @return: whether it's mostly numbers
    """
    nonnum = re.sub(r"[^0-9\s.]", "", string)
    numfrac = float(len(nonnum)) / len(string)
    if numfrac > threshold:
        return True
    return False


def count_unicode_categories(string:str, nfc_first:bool=True):
    """ Count the unicode categories within the given string - and also simplify that.

    For reference:
      - Lu - uppercase letter
      - Ll - lowercase letter
      - Lt - titlecase letter
      - Lm - modifier letter
      - Lo - other letter
      - Mn - nonspacing mark
      - Mc - spacing combining mark
      - Me - enclosing mark
      - Nd - number: decimal digit
      - Nl - number: letter
      - No - number: other
      - Pc - punctuation: connector
      - Pd - punctuation: dash
      - Ps - punctuation: open
      - Pe - punctuation: close
      - Pi - punctuation: initial quote (may behave like Ps or Pe depending on usage)
      - Pf - punctuation; final quote (may behave like Ps or Pe depending on usage)
      - Po - punctuation:Other
      - Sm - math symbol
      - Sc - currency symbol
      - Sk - modifier symbol
      - So - other symbol
      - Zs - space separator
      - Zl - line separator
      - Zp - paragraph separator
      - Cc - control character
      - Cf - format character
      - Cs - surrogate codepoint
      - Co - private use character
      - Cn - (character not assigned

    @param string: the string to look in    
    @param nfc_first: whether to do a normalization (that e.g. merges diacritics into the letters they are on)
    @return: two dicts, one counting the unicode categories per character,
    one simplified creatively. 
    For example::
        count_unicode_categories('Fisher 99 \u2222 \uc3a9 \U0001F9C0')
    would return:
      - {'textish': 7, 'space': 4, 'number': 2, 'symbol': 2},
      - {'Lu': 1, 'Ll': 5, 'Zs': 4, 'Nd': 2, 'Sm': 1, 'Lo': 1, 'So': 1}
    """
    count = collections.defaultdict(int)
    simpl = collections.defaultdict(int)
    # seq=[]

    # compose to reduce the influence of combining characters
    if nfc_first:
        string = unicodedata.normalize("NFC", string)

    for character in string:
        cat = unicodedata.category(character)
        # seq.append(cat)
        count[cat] += 1
        if "L" in cat:
            simpl["textish"] += 1
        elif "M" in cat:
            simpl["textish"] += 1
        elif "S" in cat:
            simpl["symbol"] += 1
        elif "N" in cat:
            simpl["number"] += 1
        elif "P" in cat:
            simpl["punct"] += 1
        elif "Z" in cat:
            simpl["space"] += 1
        elif "C" in cat:
            simpl["other"] += 1
        # else:
        #    raise ValueError("forgot %r"%cat)

    return dict(simpl), dict(count)


def has_text(string: str, mincount:int=1):
    """Does this string contain at least something we can consider text?
    Based on unicode codepoint categories - see C{count_unicode_categories}
    @param string: the text to count in
    @param mincount: how many text-like characters to demand
    @return: True or False
    """
    if isinstance(mincount, float): # maybe rename that parameter?
        mincount = mincount * len(string)
    simpler, _ = count_unicode_categories(string)
    return simpler.get("textish", 0) >= mincount


def has_lowercase_letter(s):
    """Returns whether the string contains at least one lowercase letter
    (that is, one that would change when calling upper())"""
    return s != s.upper()


def simplify_whitespace(
    string: str,
):  # CONSIDER: separately doing  strip=True, newline_to_space=True, squeeze_space=True
    """Replaces newlines with spaces, squeeze multiple spaces into one, then strip() the whole. 
    May e.g. be useful to push spaces into functions that trip over newlines, series of newlines, or series of spaces. 

    WARNING: Don't use this when you waned to preserve empty lines.

    @param string: the string you want less whitespace in
    @return: that string with less whitespace
    """
    return re.sub(r"[\s\n]+", " ", string.strip()).strip()


### Somewhat more creative functions


# TODO: add tests
def simple_tokenize(text):
    """Split string into words
    _Very_ basic - splits on and swallows symbols and such.

    Real NLP tokenizers are often more robust,
    but for a quick test we can avoid a big depdenency (and sometimes execution slowness)

    @param text: a single string
    @return: a list of words
    """
    l = re.split(
        r'[\s!@#$%^&*()\[\]"\':;/.,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+',
        text,
    )
    return list(e for e in l if len(e) > 0)
    # return list(e.strip("'")   for e in l  if len(e)>0)


_ordinal_nl_20 = {
    "nulde": 0,
    "eerste": 1,
    "tweede": 2,
    "derde": 3,
    "vierde": 4,
    "vijfde": 5,
    "zesde": 6,
    "zevende": 7,
    "achtste": 8,
    "negende": 9,
    "tiende": 10,
    "elfde": 11,
    "twaalfde": 12,
    "dertiende": 13,
    "veertiende": 14,
    "vijftiende": 15,
    "zestiende": 16,
    "zeventiende": 17,
    "achtiende": 18,
    "negentiende": 19,
    "twintigste": 20,
}
_ordinal_nl_20_rev = {}
for k, v in _ordinal_nl_20.items():
    _ordinal_nl_20_rev[v] = k

_tigste1 = {
    "": 0,
    "eenen": 1,
    "tweeen": 2,
    "drieen": 3,
    "vieren": 4,
    "vijfen": 5,
    "zesen": 6,
    "zevenen": 7,
    "achten": 8,
    "negenen": 9,
}
_tigste1_rev = {}
for k, v in _tigste1.items():
    _tigste1_rev[v] = k

_tigste10 = {
    "twintigste": 20,
    "dertigste": 30,
    "veertichste": 40,
    "vijftigste": 50,
    "zestigste": 60,
    "zeventigste": 70,
    "tachtigste": 80,
    "negentigste": 90,
}
_tigste10_rev = {}
for k, v in _tigste10.items():
    _tigste10_rev[v] = k

# t1000 = { # note: Dutch uses long scale, not short scale like English does - https://en.wikipedia.org/wiki/Long_and_short_scales
#      'honderd':100,
#      'duizend':1000,
#      'miljoen':1000000,
#      'miljard':1000000000,
#      'biljoen':1000000000000,
#      'biljard':1000000000000000,
#     'triljoen':1000000000000000000,
#     'triljard':1000000000000000000000,
# }


# There are probably more efficient ways to do each of these.

_re_tig = re.compile("(%s)(%s)" % ("|".join(_tigste1), "|".join(_tigste10)))


def interpret_ordinal_nl(string: str):
    """Given ordinals, gives the integer it represents (for 0..99)
    @param string: the string with integer as text
    @return: the integer, e.g.::
        interpret_ordinal_nl('eerste') == 1
    """
    string = remove_diacritics(
        string
    ).strip()  # remove_diacritics mostly to remove the dearesis (we could have hardcoded U+00EB to u+0065)
    if string in _ordinal_nl_20:
        return _ordinal_nl_20[string]
    m = _re_tig.search(string)
    if m is not None:
        s1, s10 = m.groups()
        return _tigste1[s1] + _tigste10[s10]
    raise ValueError("interpret_ordinal_nl doesn't understand %r" % string)


def ordinal_nl(integer: int):
    """Give a number, gives the ordinal word for dutch number (0..99)
    @param integer: the number as an int
    @return: that number as a word in a string, e.g.::
        ordinal_nl(1) == 'eerste'
    """
    integer = int(integer)
    if integer < 0:
        raise ValueError("Values <0 make no sense")
    elif integer in _ordinal_nl_20_rev:  # first 20
        return _ordinal_nl_20_rev[integer]
    elif integer <= 99:
        i1 = int(integer % 10)
        i10 = integer - i1  # round(-1) may be clearer?
        return "%s%s" % (_tigste1_rev[i1], _tigste10_rev[i10])
    raise ValueError("can't yet do integers > 99")



####


def ngram_generate(string:str, n:int):
    ''' Gives all n-grams of a specific length.
        Generator function.
        Quick and dirty version.

        Treats input as sequence, so you can be creative and e.g. give it lists of strings (e.g. already-split words from sentences)

        @param string: the string to take slices of
        @param n: the size, the n in n-gram
        @return: a generator that yields all the n-grams
    '''
    for string_offset in range( len(string)-n+1 ):
        yield string[string_offset:string_offset+n]


def ngram_count(string:str, gramlens:List[int]=(2,3,4), splitfirst:bool=False):
    """ Takes a string, figures out the n-grams, 
        Returns a dict from n-gram strings to how often they occur in this string.

        @param string: the string to count n-grams from 
        @param gramlens: list of lengths you want (defaults to (2,3,4): 2-grams, 3-grams and 4-grams)
        @param splitfirst: is here if you want to apply it to words - that is, do a (dumb) split so that we don't collect n-grams across word boundaries
        @return: a dict with string : occurences
    """
    if splitfirst:
        l = re.split( r'[\s!@#$%^&*()-_=+\'";:\[\{\]\}]', string )
    else:
        l = [string]
    count = {}
    for string in l:
        for n in gramlens:
            if len(string)<n:
                continue
            for i in range(len(string)-(n-1)):
                tg = string[i:i+n]
                if tg not in count:
                    count[tg]=1
                else:
                    count[tg]+=1
    return count


def ngram_matchcount(count_1:dict, count_2:dict):
    """ Score by overlapping n-grams (outputs of ngram_count()) 
        @param count_1: one dict of counts, e.g. from C{ngram_count}
        @param count_2: another dict of counts, e.g. from C{ngram_count}
        @return: a fraction, the amount of matches divided by the total amount of 
    """
    totalcount = 0
    matchcount = 0
    for string, count in count_1.items():
        totalcount+=count
    for string, count in count_2.items():
        totalcount+=count
    k1 = set(count_1.keys())
    k2 = set(count_2.keys())
    inboth = k1.intersection(k2)
    for string in inboth:
        matchcount += count_1[string]
        matchcount += count_2[string]
    return float(matchcount) / totalcount


def ngram_sort_by_matches(string:str, option_strings:List[str],  gramlens:List[int]=(1,2,3,4), with_scores:bool=False):
    ''' Score each item in string-list C{option_strings} they match to string C{string},
        by how many n-gram strings (with n in 1..4), where more matching n-grams means a higher score::
            ngram_sort_by_matches( 'for', ['spork', 'knife', 'spoon', 'fork']) == ['fork', 'spork', 'knife', 'spoon']
        Note that if you pick the first, this is effectively a "which one is the closest string?" function 

        @param string: the string to be most similar to
        @param option_strings: the string list to sort by similarity
        @param gramlens: the n-grams to use, defaults to (1,2,3,4), it may be a little faster to do (1,2,3)
        @param with_scores: if False, returns list of strings. If True, returns list of (string, score).
        @return: List of strings, or of tuples if with_scores==True
    '''
    string_counts = ngram_count(string, gramlens=gramlens)
    options_with_score = []
    for option in option_strings:
        score = 0
        ec = ngram_count(option, gramlens=gramlens)
        for ecs in ec:   # pylint: disable=consider-using-dict-items
            if ecs in string_counts:
                if len(ecs) == 1: # tiny weight in comparison. Only really does anything when nothing longer matches, which is the point.
                    score += 1
                else:
                    score += len(ecs) * string_counts[ecs]*ec[ecs]
            # CONSIDER: normalize by length / score by similar length
        options_with_score.append( (option, score) )

    options_with_score.sort(key=lambda x: x[1], reverse=True)
    if with_scores:
        return options_with_score
    else:
        return list(e[0]   for e in options_with_score)



# some prepared stopword lists, mostly geared towards wordclouds  (and also based _on_ wordcloud.STOPWORDS)
stopwords_en = [
    "a",
    "about",
    "above",
    "after",
    "again",
    "against",
    "all",
    "also",
    "am",
    "an",
    "and",
    "any",
    "are",
    "aren't",
    "as",
    "at",
    "be",
    "because",
    "been",
    "before",
    "being",
    "below",
    "between",
    "both",
    "but",
    "by",
    "can",
    "can't",
    "cannot",
    "com",
    "could",
    "couldn't",
    "did",
    "didn't",
    "do",
    "does",
    "doesn't",
    "doing",
    "don't",
    "down",
    "during",
    "each",
    "else",
    "ever",
    "few",
    "for",
    "from",
    "further",
    "get",
    "had",
    "hadn't",
    "has",
    "hasn't",
    "have",
    "haven't",
    "having",
    "he",
    "he'd",
    "he'll",
    "he's",
    "hence",
    "her",
    "here",
    "here's",
    "hers",
    "herself",
    "him",
    "himself",
    "his",
    "how",
    "how's",
    "however",
    "http",
    "i",
    "i'd",
    "i'll",
    "i'm",
    "i've",
    "if",
    "in",
    "into",
    "is",
    "isn't",
    "it",
    "it's",
    "its",
    "itself",
    "just",
    "k",
    "let's",
    "like",
    "me",
    "more",
    "most",
    "mustn't",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "off",
    "on",
    "once",
    "only",
    "or",
    "other",
    "otherwise",
    "ought",
    "our",
    "ours",
    "ourselves",
    "out",
    "over",
    "own",
    "r",
    "same",
    "shall",
    "shan't",
    "she",
    "she'd",
    "she'll",
    "she's",
    "should",
    "shouldn't",
    "since",
    "so",
    "some",
    "such",
    "than",
    "that",
    "that's",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "there",
    "there's",
    "therefore",
    "these",
    "they",
    "they'd",
    "they'll",
    "they're",
    "they've",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "wasn't",
    "we",
    "we'd",
    "we'll",
    "we're",
    "we've",
    "were",
    "weren't",
    "what",
    "what's",
    "when",
    "when's",
    "where",
    "where's",
    "which",
    "while",
    "who",
    "who's",
    "whom",
    "why",
    "why's",
    "with",
    "won't",
    "would",
    "wouldn't",
    "www",
    "you",
    "you'd",
    "you'll",
    "you're",
    "you've",
    "your",
    "yours",
    "yourself",
    "yourselves",
]
" some English stopwords  "

stopwords_nl = (
    "de",
    "het",
    "een",
    "en",
    "of",
    "die",
    "van",
    "op",
    "aan",
    "door",
    "voor",
    "tot",
    "bij",
    "kan",
    "wordt",
    "in",
    "deze",
    "dan",
    "is",
    "dat",
)
" some Dutch stopwords  "



def count_normalized(
    strings: List[str],
    min_count: int = 1,
    min_word_length=0,
    normalize_func=None,
    stopwords=(),
    stopwords_i=(),
):
    """Takes a list of strings, returns a string:count dict, with some extra processing

    Parameters beyond normalize_func are mostly about removing things you would probably call,
    so you do not have to do that separately.

    Note that if you are using spacy or other POS tagging anyway,
    filtering e.g. just nouns and such before handing it into this
    is a lot cleaner and easier (if a little slower).

    CONSIDER: 
     - imitating wordcloud collocations= behaviour
     - imitating wordcloud normalize_plurals=True
     - imitating wordcloud include_numbers=False
     - separating out different parts of these behaviours

    @param strings: a list of strings, the thing we count.

    @param normalize_func: half the point of this function. Should be a str->str function.
      - We group things by what is equal after this function is applied,
        but we report the most common case before it is.
        For example, to _count_ blind to case, but report just one (the most common case) ::
            count_normalized( "a A A a A A a B b b B b".split(),  normalize_func=lambda s:s.lower() )
        would give ::
            {"A":7, "b":5}
      - Could be used for other things.
        For example, if you make normalize_func map a word to its lemma, then you unify all inflections,
        and get reported the most common one.

    @param  min_word_length:
      - strings shorter than this are removed.
        This is tested after normalization, so you can remove things in normalization too.

    @param min_count:
      - if integer, or float >1:
        we remove if final count is < that count,
      - if float  in 0 to 1.0 range:
        we remove if the final count is < this fraction times the maximum count we see

    @param stopwords:
       - defaults to not removing anything
       - handing in True adds some of our own (dutch and english)
       - handing in a list uses yours instead.
         There is a stopwords_nl and stopwords_en in this module
         to get you started but you may want to refine your own
    @param stopwords_i:
       - defaults to not removing anything

    @return: a { string: count } dict
    """
    stoplist = set()
    if stopwords is True:
        stoplist.update(stopwords_en)
        stoplist.update(stopwords_nl)
    elif isinstance(stopwords, (list, tuple)):
        stoplist.update(stopwords)
    stoplist_lower = list(sws.lower() for sws in stopwords_i)

    # count into { normalized_form: { real_form: count } }
    count = collections.defaultdict(lambda: collections.defaultdict(int))
    for string in strings:
        if string in stoplist:
            continue
        if string.lower() in stoplist_lower:
            continue

        norm_string = string
        if normalize_func is not None:
            norm_string = normalize_func(string)

        if len(norm_string) < min_word_length:
            continue
        count[norm_string][string] += 1

    # filter counts, choose preferred form
    ret = {}
    # could do this with expression-fu but let's keep it readable
    max_count = 0
    for normform in count:
        for _, varamt in count[normform].items():
            max_count = max(max_count, varamt)

    for normform in count:
        variants_dict = sorted(
            count[normform].items(), key=lambda x: x[1], reverse=True
        )
        sum_count = sum(cnt for _, cnt in variants_dict)
        if isinstance(min_count, int) or min_count > 1:
            if sum_count >= min_count:
                ret[variants_dict[0][0]] = sum_count
        elif isinstance(min_count, float):
            # TODO: complain if not in 0.0 .. 1.0 range
            if sum_count >= min_count * max_count:
                ret[variants_dict[0][0]] = sum_count
        else:
            raise TypeError("Don't know what to do with %s" % type(min_count))
    return ret


def count_case_insensitive(
    strings: List[str], min_count=1, min_word_length=0, stopwords=(), **kwargs
):
    """Calls count_normalized()  with  normalize_func=lambda s:s.lower()
    which means it is case insensitive in counting strings,
    but it reports the most common capitalisation.

    Explicitly writing a function for such singular use is almost pointless,
    yet this seems like a common case and saves some typing.

    @param strings:
    @param min_count:
    @param min_word_length:
    @param stopwords:
    @return:
    """
    return count_normalized(
        strings,
        min_count=min_count,
        min_word_length=min_word_length,
        normalize_func=lambda s: s.lower(),
        stopwords=stopwords,
        **kwargs
    )


# commented because it's not used yet
# def count_from_spacy_document(doc_or_sequence_of_docs,
#                               remove_stop=True,
#                               restrict_to_tags=('NOUN', 'PROPN', 'ADJ', 'ADV', 'VERB'),
#                               add_ents=True,
#                               add_ncs=True,
#                               weigh_deps={'nsubj':5, 'obj':3} ):
#     ''' Takes a spacy document, returns a string->count dict

#         Does a lot of fairly specific things (a bit too specific to smush into one function, really)
#         to be smart about removing low-content words, and focusing on terms.

#         @param restrict_to_tags:  removes if not in this POS list - which defaults to nouns, adjectives, adverbs,
#                                   and verbs (and removes a lot of fillter words)
#         @param remove_stop:       removes according to Token.is_stop

#         @param add_ents:          whether to add phrases from Doc.ents
#         @param add_ncs:           whether to add phrases from Doc.noun_chunks

#         @param weigh_deps:        exists to weigh words/ent/ncs stronger
#         when they are/involve the sentence's subject or object

#         CONSIDER: make this a filter instead, so we can feed the result to count_normalized()
#         CONSIDER: whether half of that can be part of some topic-modeling filtering.  And how filters might work around spacy.
#     '''
#     counts = collections.defaultdict(int)

#     if isinstance(doc_or_sequence_of_docs, collections.Sequence): # that seems slightly more general than type in (tuple, list)
#         things = doc_or_sequence_of_docs
#     else:
#         things = [doc_or_sequence_of_docs]

#     # TODO: REVIEW THE BELOW BLOCK, IT WAS CERTAINLY INCORRECT BEFORE
#     for thing in things:
#         for token in thing:
#             if remove_stop and token.is_stop:
#                 #print( "SKIP %r - is stopword"%token.text)
#                 continue
#             if restrict_to_tags is not None  and  token.pos_ not in restrict_to_tags:
#                 #print( "SKIP %r - based on tag %s"%(token.text, token.pos_))
#                 continue

#             counts[ token.text  ] += 1

#             # TODO: take dict of weighs

#             # TODO: make the following conditional
#             if hasattr(token, 'dep_'):
#                 if token.dep_ in weigh_deps:
#                     counts[ token.text ] += weigh_deps[token.dep_]
#                 else:
#                     counts[ token.text ] += 1

#             if add_ents  and  hasattr(thing, 'ents'): # TODO: tests
#                 for ent in  thing.ents:
#                     #print( "ENT %s"%ent.text )
#                     counts[ ent.text ] += 2
#                 # TODO: involve weigh_deps

#             if add_ncs  and  hasattr(thing, 'noun_chunks'): # TODO: tests
#                 for nc in thing.noun_chunks:
#                     #print( "NC %s"%nc.text )
#                     counts[ nc.text ] += 2
#                 # TODO: involve weigh_deps

#     return dict(counts)


def remove_deheteen(string, remove=(r'de\b',r'het\b',r'een\b')):
    """ remove 'de', 'het', and 'een' as words from the start of a string - meant to normalize phrases 
    @param string:
    @param remove:
    @return: 
    """
    return remove_initial(string, remove, re.I)


def remove_initial(string:str, remove_relist, flags=re.I):
    """ remove strings from the start of a string, based on a list of regexps 
    @param string:
    @param remove_relist:
    @param flags:
    @return: 
    """
    changed = True
    while changed:
        changed = False
        rrr = '(%s)'%('|'.join(remove_relist)) # TODO: escape properly
        m = re.match( rrr, string, flags=flags)
        if m is not None:
            string = string[m.end():].strip()
            changed = True
    return string



def remove_initial_short_sentences(stringwithnewlines):
    pass
