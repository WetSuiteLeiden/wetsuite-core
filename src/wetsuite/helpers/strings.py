''' mostly-basic string helper functions 

    Many are simple enough, or specific, that you'ld easily implement them as you need them, so not that much time is saved.
'''
import re
import unicodedata
import collections
from typing import List


def _matches_anyall(haystack:str, needles:List[str], case_sensitive=True, regexp=False, encoding=None, matchall=False):
    ' helper for L{contains_any_of} and L{contains_all_of}. See the docstrings for both. '
    # and deal with bytes type (if you handed in an encoding)
    if isinstance(haystack, bytes):
        haystack = haystack.decode(encoding)
    elif not isinstance(haystack, str):
        raise TypeError('haystack %r is not str or bytes'%haystack)
    fneedles = []
    for needle in needles:
        if isinstance(needle, bytes):
            fneedles.append( needle.decode(encoding) )
        elif isinstance(needle, str):
            fneedles.append( needle )
        else: # assume str
            raise TypeError('needle %r is not str or bytes'%needle)
    needles = fneedles

    # deal with case insensitivity
    reflags = 0    # 0 is no flags set
    if not case_sensitive:
        if regexp:
            reflags = re.I
        else:
            haystack = haystack.lower()
            needles = list(needle.lower()  for needle in needles)

    # do actual test, regexp or not

    matches = [] # whether haystack matches each needle
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
    if matchall: # must match all - any False means the whole is False
        if False in matches:
            return False
        return True
    else:  # match any - any True means the whole is True
        if True in matches:
            return True
        return False


def contains_any_of( haystack:str, needles:List[str], case_sensitive=True, regexp=False, encoding='utf8' ): # TODO: rename to matches_any_of
    ''' Given a string and a list of strings,  returns whether the former contains at least one of the strings in the latter
        e.g. contains_any_of('microfishes', ['mikrofi','microfi','fiches']) == True

        @param needles: the things to look for
        Note that if you use regexp=True and case_sensitive=True, the regexp gets lowercased before compilation,
        which may not always be correct.
        @param case_sensitive: if False, lowercasing hackstack and needle before testing. Defauts to True.
        @param regexp: treat needles as regexps rather than subbstrings.  Default is False, i.e.  substriungs
        @param haystack: is treated like a regular expression (the test is whether re.search for it is not None)
        @param encoding : lets us deal with bytes, by saying "if you see a bytes haystack or needle, decode using this encoding". 
        Defaults to utf-8
    '''
    return _matches_anyall(haystack=haystack, needles=needles, case_sensitive=case_sensitive, regexp=regexp, encoding=encoding, matchall=False)


def contains_all_of( haystack:str, needles:List[str], case_sensitive=True, regexp=False, encoding='utf8' ): # TODO: rename to matches_all_of
    ''' Given a string and a list of strings,  returns whether the former contains all of the strings in the latter 
        e.g. contains_all_of('AA (B/CCC)', ('AA', 'BB') ) == False

        @param needles: the things to look for
        Note that if you use regexp=True and case_sensitive=True, the regexp gets lowercased before compilation,
        which may not always be correct.
        @param case_sensitive: if False, lowercasing hackstack and needle before testing. Defauts to True.
        @param regexp: treat needles as regexps rather than subbstrings.  Default is False, i.e.  substriungs
        @param haystack: is treated like a regular expression (the test is whether re.search for it is not None)
        @param encoding : lets us deal with bytes, by saying "if you see a bytes haystack or needle, decode using this encoding". 
        Defaults to utf-8
    '''
    return _matches_anyall(haystack=haystack, needles=needles, case_sensitive=case_sensitive, regexp=regexp, encoding=encoding, matchall=True)



def ordered_unique( strlist, case_sensitive=True, remove_none=True ):
    ''' Takes a list of strings, returns one without duplicates,
        keep the first of each (so take out later duplicates).
       
        So unlike a plain set(strlist), 
        it keeps the order of what we keep.

        Can be made case insensitive. It then keeps the first casing it saw.
        Can be made faster.
    '''
    ret = []
    retlow = []
    for onestr in strlist:
        if remove_none and onestr is None:
            continue
        if case_sensitive:
            if onestr in ret:
                continue
            ret.append( onestr )
        else:
            strlow = onestr.lower()
            if strlow in retlow:
                continue
            ret.append( onestr )
            retlow.append( strlow )
    return ret


def findall_with_context(pattern:str, s:str, context_amt:int):
    ''' Matches substrings/regexpe, 
        and for each match also gives some of the text context (on a character basis). 

        Is a generator that yields tuples of (
            - string before, 
            - matched string 
            - match object   (may seem redundant, but you often want a distinction between what is matched and captured)
            - string after 

        For example
    '''
    for match_object in re.finditer( pattern, s ):
        st, en = match_object.span()
        yield (
            s[max(0, st-context_amt):st],
            s[st:en],
            match_object,
            s[en:en+context_amt],
        )



re_combining = re.compile(r'[\u0300-\u036f\u1dc0-\u1dff\u20d0-\u20ff\ufe20-\ufe2f]',re.U)
" helps remove diacritics - list a number of combining (but not actually combin*ed*) character ranges in unicode, since you often want to remove these (after decomposition) " 

def remove_diacritics(s: str):
    """ Unicode decomposes, remove combining characters, unicode compose.
        e.g. remove_diacritics( 'ol\xe9' ) == 'ole'
    """
    #TODO: Figure out what the compose is doing, and whether it is necessary at all.
    return unicodedata.normalize('NFC', re_combining.sub('', unicodedata.normalize('NFD', s)) )



def is_numeric(string: str):
    ''' Does this string contain _only_ something we can probably consider a number?    That is, [0-9.,] and optional whitespace around it '''
    return  re.match(r'^\s*[0-9,.]+\s*$', string) is not None


def is_mainly_numeric(string:str, threshold=0.8):
    ''' Returns whether the amount of characters of the string 
        that are 0123456789, -, or space,
        make up more than threshold of the entire string lengt.
        
        Meant to help ignore serial numbers and such.
    '''
    nonnum = re.sub(r'[^0-9\s.]','',string)
    numfrac = float(len(nonnum)) / len(string)
    if numfrac >  threshold:
        return True
    return False


def count_unicode_categories(string, nfc_first=True):
    ''' Returns two dicts, one counting the unicode categories per character, 
        one simplified creatively. For example::
            'Fisher 99 \u2222 \uc3a9 \U0001F9C0'
        would return
          - {'textish': 7, 'space': 4, 'number': 2, 'symbol': 2},
          - {'Lu': 1, 'Ll': 5, 'Zs': 4, 'Nd': 2, 'Sm': 1, 'Lo': 1, 'So': 1}

        Could support a number of string tests.

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
    '''
    count = collections.defaultdict(int)
    simpl = collections.defaultdict(int)
    #seq=[]

    # compose to reduce the influence of combining characters
    if nfc_first:
        string = unicodedata.normalize('NFC', string )

    for character in string:
        cat = unicodedata.category( character )
        #seq.append(cat)
        count[cat] += 1
        if 'L' in cat:
            simpl['textish'] += 1
        elif 'M' in cat:
            simpl['textish'] += 1
        elif 'S' in cat:
            simpl['symbol'] += 1
        elif 'N' in cat:
            simpl['number'] += 1
        elif 'P' in cat:
            simpl['punct'] += 1
        elif 'Z' in cat:
            simpl['space'] += 1
        elif 'C' in cat:
            simpl['other'] += 1
        #else:
        #    raise ValueError("forgot %r"%cat)

    return dict(simpl), dict(count)


def has_text(string: str, mincount=1):
    ''' Does this string contain at least something we can consider text? '''
    simpler, _ = count_unicode_categories(string)
    return simpler.get('textish', 0) >= mincount


def has_lowercase_letter(s):
    ''' Returns whether the string contains at least one lowercase letter 
        (that is, one that would change when calling upper()) '''
    return s != s.upper()




def simplify_whitespace(string: str): #, strip=True, newline_to_space=True, squeeze_space=True)
    ''' Remove newlines, squeeze spaces (C{tr -s '\n' ' '}), thenstrip the whole '''
    return re.sub( r'[\s\n]+', ' ', string.strip() ).strip()


### Somewhat more creative functions


# TODO: add tests
def simple_tokenize(text):
    ''' Split string into words 
        _Very_ basic - splits on and swallows symbols and such.
        
        Real NLP tokenizers are often more robust, 
        but for a quick test we can avoid a big depdenency (and sometimes execution slowness)

        @param text: a single string
        @return: a list of words
    '''
    l = re.split(r'[\s!@#$%^&*()\[\]"\':;/.,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+', text)
    return list(e   for e in l  if len(e)>0)
    #return list(e.strip("'")   for e in l  if len(e)>0)


_ordinal_nl_20 = {
          "nulde":0,
         "eerste":1,
         "tweede":2,
          "derde":3,
         "vierde":4,
         "vijfde":5,
          "zesde":6,
        "zevende":7,
        "achtste":8,
        "negende":9,
         "tiende":10,  
          "elfde":11,
       "twaalfde":12,
      "dertiende":13, 
     "veertiende":14,
     "vijftiende":15,
      "zestiende":16,
    "zeventiende":17,
      "achtiende":18,
    "negentiende":19,
     "twintigste":20,
}
_ordinal_nl_20_rev = {}
for k, v in _ordinal_nl_20.items():
    _ordinal_nl_20_rev[v] = k

_tigste1 = {
           '':0,
      'eenen':1,
     'tweeen':2,
     'drieen':3,
     'vieren':4,
     'vijfen':5,
      'zesen':6,
    'zevenen':7,
     'achten':8,
    'negenen':9,
}
_tigste1_rev = {}
for k, v in _tigste1.items():
    _tigste1_rev[v] = k

_tigste10 = {
     'twintigste':20,
      'dertigste':30,
    'veertichste':40,
     'vijftigste':50,
      'zestigste':60,
    'zeventigste':70,
     'tachtigste':80,
    'negentigste':90,
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

_re_tig = re.compile( '(%s)(%s)'%( '|'.join(_tigste1), '|'.join(_tigste10) ) )

def interpret_ordinal_nl(s:str):
    " Given ordinals, gives the integer it represents (for 0..99), e.g. interpret_ordinal_nl('eerste') -> 1 "
    s = remove_diacritics(s).strip() # remove_diacritics mostly to remove the dearesis (we could have hardcoded U+00EB to u+0065)
    if s in _ordinal_nl_20:
        return _ordinal_nl_20[s]
    m = _re_tig.search(s)
    if m is not None:
        s1, s10 = m.groups()
        return _tigste1[s1] + _tigste10[s10]
    raise ValueError("interpret_ordinal_nl doesn't understand %r"%s)


def ordinal_nl(i:int):
    """ Give a number, gives the ordinal word for dutch number (0..99) 
        e.g. 1 -> 'eerste' 
    """
    i = int(i)
    if i < 0:
        raise ValueError("Values <0 make no sense")
    elif i in _ordinal_nl_20_rev:  # first 20
        return _ordinal_nl_20_rev[i]
    elif i <= 99:
        i1  = int( i%10 )
        i10 = i-i1  # round(-1) may be clearer?
        return '%s%s'%( _tigste1_rev[i1], _tigste10_rev[i10] )
    raise ValueError("can't yet do integers > 99")
