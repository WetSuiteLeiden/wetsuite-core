"""
Extracting specific patterns of text.


Much of the code in here is aimed at identfiers and references - 
identifiers like BWB-ID, CVDR-ID, ECLI, and CELEX,
more textual ones like EU OJ and directive references, vindplaats, kamerstukken, and "artikel 3" style references 
-- see in particular the C{find_references} function for a little more detail

Currently a best-effort proof of concept of each of those matchers,
and contain copious hardcoding and messiness.

We _will_ miss things, as most things like this do. Arguably the only real metric 
is making a list of _everything_ you want to catch and seeing how well you do.

Right now the implementation is mostly regexes -- which aren't great for some of these.
(But so aren't formal grammars, because real-world variation will be missed)


Note that if refined further, this should probably be restructured in a way
where each matcher can register itself, 
so that there _isn't_ one central controller function to entangle everything
"""

import re
import collections
import textwrap
#from typing import List

import wetsuite.datasets
import wetsuite.helpers.strings
import wetsuite.helpers.meta
import wetsuite.helpers.koop_parse


def _wetnamen():
    " a dict from law name to law BWB-id, mostly to try to match the names in find_nonidentifier_references.  Used by find_nonidentifier_references "
    ret = collections.defaultdict( list )
    for bwbid, (betternamelist, iffynamelist) in wetsuite.datasets.load('wetnamen').data.items():
        for name in betternamelist+iffynamelist:
            if name in ('artikel',):
                continue
            if len(name) > 1  and  len(name) < 150:
                ret[ name ].append( bwbid )
    return ret

_mw = r'[\s,]+(%s)'%('|'.join( re.escape(wetnaam)   for wetnaam in sorted(_wetnamen(), key=lambda x:len(x), reverse=True) ) )  # pylint: disable=unnecessary-lambda
_mw_re = re.compile( _mw, flags=re.I )
#def _match_wetnamen(text):
#    return _mw_re.match(text)
#        if m is not None:
#            overallmatch_en += m.endpos


def find_artikel_references(
    text:str, context_amt:int=60, debug:bool=False
):
    """Attempts to find references like ::
        "artikel 5.1, tweede lid, aanhef en onder i, van de Woo"
    and parse and resolve as much as it can.

    This is a a separate function because it is more complex than most others, 
    but if you want to look for more than just these, 
    then you probably want to wield it via C{find_references}.

    These  references are not a formalized format,
    and while the law ( https://wetten.overheid.nl/BWBR0005730/ ) that suggests 
    the format of these should be succinct, and sometimes it looks like these have near-templates,
    that is not what real-world use looks like.

    Another reasonable approach might be include each real-world variant format explicitly,
    as it lets you put stronger patterns first and fall back on fuzzier ones,
    it makes it clear what is being matched, and it's easier to see how common each is.
    However, that also easily leads to false negatives -- missing real references.

    Instead, we
        - start by finding some strong anchors
        - keep accepting bits of adjacent string as long as they look like things we know
        "artikel 5.1,"   "tweede lid,"   "aanhef en onder i"
        - then seeing what text is around it, which should be at least the law name

    Neither will deal well with the briefest forms, e.g. C{"(81 WWB)"}
    which is arguably only reasonable to recognize when you recognize either side
    (by known law name, which is harder for abbreviations in that it probably leads to false positives)
    ...and in that example, we might want to
        - see if character context makes it reasonable - the parthentheses make it more reasonable than
        if you found the six characters '81 WWB' in any context
        - check whether the estimated law (Wet werk en bijstand - BWBR0015703) has an article 81
        - check, in some semantic way, whether Wet werk en bijstand makes any sense in context of the text

    TODO: ...also so that we can return some estimation of
        - how sure we are this is a reference,
        - how complete a reference is, and/or
        - how easy to resolve a reference is.    

    @param text: the text to look in

    @param context_amt: how much context to find another piece in (TODO: make this part of internal parameters)
    
    @return: a list of dict matches, as also mentioned on find_references()
    """
    ret = []
    artikel_matches = []

    for artikel_matchobject in re.finditer(
        r"\b(?:[Aa]rt(?:ikel|[.]|\b)\s*([0-9.:]+[a-z]*))", text
    ):
        artikel_matches.append(artikel_matchobject)

    # note to self: just the article bit also good for creating an anchor for test cases later,
    #               to see what we miss and roughly why

    for matchnum, artikel_matchobject in enumerate(artikel_matches):  # these should be unique references
        details = collections.OrderedDict()
        details["artikel"] = artikel_matchobject.group(1)
        # if debug:
        #    print('------')
        #    print(artikel_mo)

        overallmatch_st, overallmatch_en = artikel_matchobject.span()

        # based on that anchoring match, define a range to search in
        wider_start = max(0, overallmatch_st - context_amt)
        wider_end = min(
            overallmatch_st + context_amt,
            len(text),
        )

        if matchnum + 1 < len(artikel_matches): # hard cut at the next 'artikel'. Ideally not special case, but good enough for now.
            nextmatch = artikel_matches[ matchnum + 1 ]
            wider_end = min( wider_end, nextmatch.start())

        # Look for some specific strings around the matched 'artikel', (and record whether they came before or after)
        find_things = {
            # name -> ( match before and/or after,  include or exclude in match,    regexp to match)
            # the before/after, inclide/exclude are not used yet, but are meant to set hard borders when seen before/after the anchor match
            "grond":       ["B", "E", r"\bgrond(?:_van)?\b"],
            "bedoeld":     ["B", "E", r"\bbedoeld_in\b"],
            #'komma':          [  '.',  re.compile(r',')                                         ],
            "hoofdstuk":   ["A", "I", r"\bhoofdstuk#\b"],
            "paragraaf":   ["A", "I", r"\bparagraaf#\b"],
            "aanwijzing":  ["A", "I", r"\b(?:aanwijzing|aanwijzingen)#\b"],
            "lid":         ["A", "I", r"\b(?:lid_(#)|(L)_(?:lid|leden))"],
            "volzin":      ["A", "I", r"\b(?:volzin_(#)|(L)_(?:volzin|volzinnen))"],
            "aanhefonder": ["A", "I", r"((?:\baanhef_en_)?(onder|onderdeel|onderdelen)_[a-z0-9\u00ba]{1,2})"],  # CONSIDER: "en onder d en g", "aanhef en onder a of c"
            "sub":         ["A", "I", r"\bsub_[a-z0-9\u00ba]+\b"],
            'vandh':       ['A', 'I',  r'\bvan_(?:het|de)\b'                                    ],
            ##'dezewet':       [  'I',  r'\bde(?:ze)? wet\b'                                    ],
            #'hierna':          [ 'A', 'E',  r'\b[(]?hierna[:\s]'                               ],
            #'artikel':          [ 'A', 'E',  r'\bartikel'                                      ],
        }
        # https://wetten.overheid.nl/jci1.3:c:BWBR0005730&hoofdstuk=3&paragraaf=3.3&aanwijzing=3.29

        # numbers in words form
        re_some_ordinals = "(?:%s)" % (
            "|".join(wetsuite.helpers.strings.ordinal_nl(i)  for i in range(100))
        )

        for k, (_, _, res) in find_things.items():
            # make all the above multiline matchers, and treat specific characters as signifiers we should be replacing
            #   the 'replace this character' is cheating somewhat because and can lead to incorrect nesting,
            #   so take care, but it seems worth it for some more readability
            res = res.replace("_", r"[\s\n]+")
            res = res.replace("#", r"([0-9.:]+[a-z]*)")

            if "L" in res:
                # TODO: recall what this... is... doing.
                rrr = r"(?:O(?:,?_O)*(?:,?_en_O)?)".replace("_", r"[\s\n]+").replace(
                    "O", re_some_ordinals
                )
                res = res.replace("L", rrr)
                # print('AFT',res)

            compiled = re.compile(res, flags=re.I | re.M)
            find_things[k][2] = compiled


        ## the main "keep adding things" loop
        range_was_widened = True
        while range_was_widened:
            range_was_widened = False

            if debug:
                s_art_context = "%s[%s]%s" % (
                    text[wider_start:overallmatch_st],
                    text[overallmatch_st:overallmatch_en].upper(),
                    text[overallmatch_en:wider_end],
                )
                print(
                    "SOFAR",
                    "\n".join(
                        textwrap.wrap(
                            s_art_context.strip(),
                            width=70,
                            initial_indent="     ",
                            subsequent_indent="     ",
                        )
                    ),
                )

            for rng_st, rng_en, where in (
                (wider_start,      overallmatch_st,  "before"),
                (overallmatch_en,  wider_end,        "after"),
            ):
                for find_name, ( before_andor_after, incl_excl, find_re ) in find_things.items():
                    # print('looking for %s %s current match (so around %s..%s)'%(find_re, where, rng_st, rng_en))
                    if "A" not in before_andor_after and where == "after":
                        continue # not what we're currently doing
                    if "B" not in before_andor_after and where == "before":
                        continue # not what we're currently doing

                    # TODO: ideally, we use the closest match; right now we assume there will be only one in range (TODO: fix that)
                    for now_mo in re.compile(find_re).finditer(
                        text, pos=rng_st, endpos=rng_en
                    ):  # TODO: check whether inclusive or exclusive
                        # now_size = now_mo.end() - now_mo.start()

                        if incl_excl == "E":
                            # recognizing a string that we want _not_ to include
                            #   (not all that different from just not seeing something)
                            # print( 'NMATCH', find_name )
                            pass

                        elif incl_excl == "I":
                            nng = list(s for s in now_mo.groups() if s is not None)
                            if len(nng) > 0:
                                details[find_name] = nng[0]
                            if (
                                now_mo.end() <= overallmatch_st
                            ):  # roughly the same test as where==before
                                howmuch = overallmatch_st - now_mo.end()
                                overallmatch_st = (
                                    now_mo.start()
                                )  #  extend match  (to exact start of that new bit of match)
                                wider_start = max(
                                    0, wider_start - howmuch
                                )  #  extend search range (by the size, which is sort of arbitrary)
                            else:  # we can assume where==after
                                howmuch = now_mo.start() - overallmatch_en  #
                                overallmatch_en = now_mo.end()  #  extend match
                                wider_end = min(
                                    wider_end + howmuch, len(text)
                                )  #  extend search range

                            range_was_widened = True

                            if debug:
                                print(
                                    "MATCHED type=%-20s:   %-25r  %s chars %s "
                                    % (
                                        find_name,
                                        now_mo.group(0),
                                        howmuch,
                                        where,
                                    )
                                )
                            # TODO: extract what we need here
                            # changed = True
                            break  # break iter
                        else:
                            raise ValueError("Don't know IE %r" % incl_excl)
                    # if changed:
                    #    break # break pattern list
                # if changed:
                #    break # break before/after

        s_art_context = "%s[%s]%s" % (
            text[wider_start:overallmatch_st],
            text[overallmatch_st:overallmatch_en].upper(),
            text[overallmatch_en:wider_end],
        )
        # if debug:
        #     print( 'SETTLED ON')
        #     print( '\n'.join( textwrap.wrap(s_art_context.strip(),
        #                 width=70, initial_indent='     ', subsequent_indent='     ') ) )
        #     print( details )

        # parse ordinals in certain fields:
        for key, target in (
            ('lid', 'lid_num'),
            ('volzin', 'volzin_num'),
        ):
            if key in details:
                details[target] = []
                lidtext = details[key]
                words = list(
                    s.strip()
                    for s in re.split(r"[\s\n]*(?:,| en\b)", lidtext, flags=re.M)
                    if len(s.strip()) > 0
                )
                for part in words:
                    try:
                        details[target].append(int(part))
                    except ValueError:
                        try:
                            details[target].append(
                                wetsuite.helpers.strings.interpret_ordinal_nl(part)
                            )
                        except ValueError:
                            pass

        #if len(details) > 1: # if it's more details than just "artikel 81"
        # Try to see if the text right after is a known name reference
        try:
            text_after = text[overallmatch_en:overallmatch_en+1000].lstrip(',;. ')
            m = _mw_re.match( text_after )
            if m is not None:
                #print( m.group(0) )
                overallmatch_en += len( m.group(0) )
                details['nameref'] = m.group(0).strip(', ')
        except Exception: #if any any of that fails, don't do it    for now, pylint: disable=broad-exception-caught
            pass
            #print( 'BLAH',e )
            #raise ValueError( "Something failed traing to match law names" ) from e

        ret.append( {
            "type": 'artikel',
            "start": overallmatch_st,
            "end": overallmatch_en,
            "text": text[overallmatch_st:overallmatch_en],
            "details": details,
        } )

    return ret


def find_references(text:str,
                    bwb:bool=True,
                    cvdr:bool=True,
                    ecli:bool=True,
                    celex:bool=True,
                    ljn:bool=False,
                    bekendmaking_ids:bool=False,
                    vindplaatsen:bool=True,
                    artikel:bool=True,
                    kamerstukken:bool=True,
                    euoj:bool=True,
                    eudir:bool=True,
                    eureg:bool=True,
                    debug:bool=False):
    ''' Looks for various different kinds of references in the given text, sorts the results. 

    Note that there is a gliding scale between 'is this and identifier and will we probably find most of them'
    and 'is this more textual, more varied, so more easily miss parts'
    (...and should this perhaps not be implemented with regexes as it currently is)

    See also:
      - Leidraad voor juridische auteurs

    @param text: the string to look in. Note that matches return offsets within this string.
    @param bwb: whether to look for BWB identifiers, e.g. BWBR0006501
    @param cvdr: whether to look for CVDR work and expression identifiers, e.g. CVDR101405_1  CVDR101405/1  CVDR101405
    @param ecli: whether to look for ECLI identifiers, e.g. ECLI:NL:HR:2005:AT4537
    @param celex: whether to look for CELEX identifiers, e.g. 32000L0060 and some variations
    @param ljn: whether to look for LJN identifiers, e.g. AT4537
    (disabled by default because we want you to be explicitly aware of false negatives. Also they aren't used anymore)
    @param bekendmaking_ids: whether to look for bekendmaking-ids like kst-26643-144-h1 and h-tk-20082009-7140-7144.
    Disabled by default because you're not usally seeing these in text.
    @param vindplaatsen: whether to look for vindplaatsen for Trb, Stb, Stcrt, e.g. C{"Stb. 2011, 35"} are actually quite regular (mostly by merit of being simple)
    @param artikel: whether to look for B{artikel 3, lid 3, aanhef en onder c} style references
    @param kamerstukken: whether to look for kamerstukken references, the ones that look like::
      Kamerstukken I 1995/96, 23700, nr. 188b, p. 3.
      Kamerstukken I 2014/15, 33802, C, p. 3.
      Kamerstukken II 1999/2000, 2000/2001, 2001/2002, 26 855.
      Kamerstukken I 2000/2001, 26 855 (250, 250a); 2001/2002, 26 855 (16, 16a, 16b, 16c).
    @param euoj: whether to look for EU Official Journal references, the ones that look like::
        OJ L 69, 13.3.2013, p. 1
        OJ L 168, 30.6.2009, p. 41–47
    @param eudir: whether to look for EU directive references, the ones that look like::
        Council Directive 93/42/EEC of 14 June 1993
        Directive 93/42/EEC of 14 June 1993
    @param debug: whether to look for

    @return:
    A list of dicts (sorted by the value of `start`), each with at least the keys
      - C{"type"}               - type of reference, e.g. "kst", "euoj", "artikel"
      - C{"start"} and C{"end"} - character offsets of the match
      - C{"text"}               - all the matched text
    and probably
      - C{"details"}, with contents that are mostly specific to the type of reference
    '''
    ret = []

    # There is a good argument to make this funcion call a more pluggable set of functions, rather than be one tangle of a function.
    ret = []

    ### More on the identifier side #######################################################
    if bwb:
        _RE_BWBFIND = re.compile( r'(BWB[RV][0-9]+)', flags=re.M )

        for rematch in _RE_BWBFIND.finditer( text ): # pylint: disable=protected-access
            match = {}
            match["type"] = "bwb"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            ret.append(match)

    if cvdr:
        _RE_CVDRFIND = re.compile("(CVDR)([0-9]+)([/_][0-9]+)?")
        for rematch in _RE_CVDRFIND.finditer( text ):
            match = {}
            match["type"] = "cvdr"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            try:
                workid, expressionid = wetsuite.helpers.koop_parse.cvdr_parse_identifier(rematch.group(0))
                match["details"] = {'workid':workid, 'expressionid':expressionid}
            except Exception: # for now, pylint: disable=broad-exception-caught
                pass

            ret.append(match)

    if ljn:
        for rematch in re.finditer(
            r"\b[A-Z][A-Z][0-9][0-9][0-9][0-9](,[\n\s]+[0-9]+)?\b", text, flags=re.M
        ):
            # CONSIDER: we could add a "is it _not_ part of an ECLI" check
            match = {}
            match["type"] = "ljn"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            ret.append(match)

    if ecli:
        for rematch in wetsuite.helpers.meta._RE_ECLIFIND.finditer( # pylint: disable=protected-access
            text
        ):
            match = {}
            match["type"] = "ecli"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            try:
                match["details"] = wetsuite.helpers.meta.parse_ecli(match["text"])
            except ValueError: # as of this writing this seems impossible as all the things it checks for are also the thing _RE_ECLIFIND matches on, but it's a good check to have should either change.
                match["invalid"] = True
            ret.append(match)

    if celex:
        for rematch in wetsuite.helpers.meta._RE_CELEX.finditer( # pylint: disable=protected-access
            text
        ):
            match = {}
            match["type"] = "celex"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            try:
                match["details"] = wetsuite.helpers.meta.parse_celex(rematch.group(0))
            except ValueError:
                match["invalid"] = True
            ret.append(match)

    if bekendmaking_ids:
        for rematch in wetsuite.helpers.meta._re_bekendid.finditer( # pylint: disable=protected-access
            text
        ):
            match = {}
            match["type"] = "bekend"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            try:
                match["details"] = wetsuite.helpers.meta.parse_bekendmaking_id(rematch.group(0))
            except Exception: # for now, pylint: disable=broad-exception-caught
                match["invalid"] = True
            ret.append(match)


    if vindplaatsen:
        # https://www.kcbr.nl/beleid-en-regelgeving-ontwikkelen/aanwijzingen-voor-de-regelgeving/hoofdstuk-3-aspecten-van-vormgeving/ss-33-aanhaling-en-verwijzing/aanwijzing-345-vermelding-vindplaatsen-staatsblad-ed
        for rematch in re.finditer(
            r"\b((Trb|Stb|Stcrt)[.]?[\n\s]+([0-9\u2026.]+)(?:,[\n\s]+([0-9\u2026.]+))?)",
            text,
            flags=re.M,
        ):
            match = {}
            match["type"] = "vindplaats"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            try:
                match["details"] = {}
                match["details"]['what']   = rematch.groups()[1]
                match["details"]['jaar']   = rematch.groups()[2]
                match["details"]['nummer'] = rematch.groups()[3]
            except Exception: # for now, pylint: disable=broad-exception-caught
                pass
            ret.append(match)

    ### Less structured #################################################
    if kamerstukken:
        # I'm not sure about the standard here, and the things I've found seem frequently violated
        # vergaderjaar is required
        # the rest is technically made optional here, though in practice some of them must be there
        # allow abbreviations/misspellings?
        #                                                                         _____________________________________  ________________________________________________________________________
        kre = r"(Kamerstukken|Aanhangsel Handelingen|Handelingen)( I\b| II\b| 1\b| 2\b)?@(,?@(?:vergaderjaar )?[0-9]+[/-][0-9]+)((?:@,@[0-9]+(?: [XVI]+)?|@, item [0-9]+|@, (?:nr|p|blz)[.]@[0-9-]+|@, [A-Z]+)*)"
        # these two replaces imply:
        # - ' ' actually means one or more newline-or-space
        # - '@' actually means zero or more newline-or-space
        kre = kre.replace( " ", r"[\n\s]+" ).replace( "@", r"[\n\s]*" )
        #print(kre)
        for rematch in re.finditer(kre, text, flags=re.M):
            match = {}
            match["type" ] = "kamerstukken"
            match["start"] = rematch.start()
            match["end"]   = rematch.end()
            match["text"]  = rematch.group(0)
            # try: # CONSIDER: we have to consider all the optional parts, so this would probably change
            #     groups = rematch.groups()
            #     match["details"] = {}
            #     #match["details"]['groups']  = groups
            #     match["details"]['what']    = groups[0]
            #     match["details"]['whatnum'] = groups[1]
            #     match["details"]['jaar']    = groups[2]
            #     match["details"]['rest']    = groups[3]
            # except Exception as e:
            #     pass
            ret.append(match)

    if euoj:
        # Turns out there is a lot more variation than want I initially found
        # TODO: figure out what variations there are  (to the degree there is standardization at all)
        # OJ C, C/2024/5510, 11.9.2024
        # OJ L 69, 13.3.2013, p. 1
        # OJ L 168, 30.6.2009, p. 41–47
        _RE_EUOJ = re.compile(
            r"(OJ|Official Journal)[\s]?(C|CA|CI|CE|L|LI|LA|LM|A|P) [0-9]+([\s]?[A-Z]|/[0-9])*(,? p. [0-9\u2013-]+(\s*[\u2013-]\s*[0-9-]+)*|, [0-9]{1,2}[./][0-9]{1,2}[./][0-9][0-9]{2,4})+".replace(
                " ", r"[\s\n]+"
            ),
            flags=re.M,
        )
        for rematch in _RE_EUOJ.finditer(text):
            match = {}
            match["type"] = "euoj"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            # TODO: add parsed details
            ret.append(match)

    if eudir:
        # TODO: figure out real variation
        _RE_EUDIR = re.compile(
            r"(?:Council )?(Directive) [0-9]{2,4}/[0-9]+(/EC|/EEC|/EU)?".replace(" ", r"[\s\n]+"),
            flags=re.M,
        )

        for rematch in _RE_EUDIR.finditer(text):
            match = {}
            match["type"] = "eudir"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            # TODO: parse details
            ret.append(match)

    if eureg:
        # eureg like "Council Regulation (EEC) No 2658/87"
        # TODO: find more real examples, this regex is guessing
        _RE_EUREG = re.compile(
            r"(?:Council )?(Regulation) [(]?(EC|EEC|EU)[)] (No.? [0-9/]+)".replace(" ", r"[\s\n]+"),
            flags=re.M,
        )
        for rematch in _RE_EUREG.finditer(text):
            match = {}
            match["type"] = "eureg"
            match["start"] = rematch.start()
            match["end"] = rematch.end()
            match["text"] = rematch.group(0)
            try:
                match["details"] = {}
                match["details"]['what'] = rematch.groups()[1]
                match["details"]['number'] = rematch.groups()[2]
            except Exception: # for now, pylint: disable=broad-exception-caught
                pass
            ret.append(match)

    ### Less structured yet #############################################
    if artikel:
        ret.extend( find_artikel_references(text, debug=debug) )

    ret.sort(key=lambda d:d['start'])
    return ret


def mark_references_spacy(doc, matches, # replace=True,
                          ):
    ''' Takes a spacy Doc, and matches from you calling C{find_references}, marks it as entities. 

        *Replaces* the currently marked entities, to avoid overlap.
        (CONSIDER: marking up in spans instead)
        (...also because char_span() with alignment_mode='expand' probably makes this easier.
        
        Bases this on the plain text, and then trying to find all the tokens necessary to cover that
        (that code needs some double checking).
    '''
    import spacy # (local import so that this module could be taken out of this context more easily)
    # most of the work is figuring out character index to token index.

    ref_spans = []
    start_tok_i, end_tok_i = 0, 0

    for reference_dict in matches:
        #print('Looking for %r'%reference_dict['text'], end='')
        start_char_offset, end_char_offset = reference_dict['start'], reference_dict['end']
        #print( ' at char offsets %d..%d'%(start, end) )

        # in theory can start with the same start as the last round's start, because references might overlap and are sorted
        # but actually, spacy doesn't like overlapping entities, so we use the previous round's end:
        start_tok_i = end_tok_i
        tokamt = len(doc)

        # TODO: think about this more. There are bugs here.
        while start_tok_i < tokamt  and  doc[start_tok_i].idx < start_char_offset:
            start_tok_i += 1

        end_tok_i = start_tok_i
        while end_tok_i < tokamt  and  doc[end_tok_i].idx < end_char_offset:
            end_tok_i += 1
        ref_spans.append( spacy.tokens.Span( doc, start_tok_i, end_tok_i, reference_dict['type'].upper() ) )

    #if replace==True:
    doc.set_ents( ref_spans )
    #else: # currently hopes for no overlap; we could actiely prefer one or the other
    #    doc.set_ents( list(doc.ents)+spans )


def simple_tokenize(text: str):
    "quick and dirty splitter into words. Mainly used by C{abbrev_find}"
    l = re.split(
        '[\\s!@#$%^&*":;/,?\xab\xbb\u2018\u2019\u201a\u201b\u201c\u201d\u201e\u201f\u2039\u203a\u2358\u275b\u275c\u275d\u275e\u275f\u2760\u276e\u276f\u2e42\u301d\u301e\u301f\uff02\U0001f676\U0001f677\U0001f678-]+',
        text,
    )
    return list(e.strip("'") for e in l if len(e) > 0)


def abbrev_find(text: str):
    """Finds abbreviations with explanations next to them.
    
    Looks for patterns like
      -  "Word Combination (WC)"
      -  "Wet Oven Overheid (Woo)"
      -  "With Periods (W.P.)"
      -  "(EA) Explained After"    (probably rare)

      -  "BT (Bracketed terms)"
      -  "(Bracketed terms) BT"    (probably rare)

    Will both over- and under-accept, so if you want clean results, consider e.g. reporting only things present in multiple documents.
    see e.g. merge_results()

    CONSIDER:
      - how permissive to be with capitalization. Maybe make that a parameter?
      - allow and ignore words like 'of', 'the'
      - rewrite to deal with cases like
        - Autoriteit Consument en Markt (ACM)
        - De Regeling werving, reclame en verslavingspreventie kansspelen (hierna: Rwrvk)
        - Nationale Postcode Loterij N.V. (hierna: NPL)
        - Edelmetaal Waarborg Nederland B.V. (EWN)
        - College voor Toetsen en Examens (CvTE)
        - (and maybe:)
        - Pensioen- en Uitkeringsraad (PUR)
        - Nederlandse Loodsencorporatie (NLC)
        - Nederlandse Emissieautoriteit (NEa)
        - Kamer voor de Binnenvisserij (Kabivi)
        - (and maybe not:)
        - College van toezicht collectieve beheersorganisaties auteurs- en naburige rechten (College van Toezicht Auteursrechten (CvTA))
        - Keurmerkinstituut jeugdzorg (KMI)
      - listening to 'hierna: ', e.g.
        - "Wet Bevordering Integriteitbeoordelingen door het Openbaar Bestuur (hierna: Wet BIBOB)"
        - "Drank- en horecawet (hierna: DHW)"
        - "Algemene wet bestuursrecht (hierna: Awb)"
        - "het Verdrag betreffende de werking van de Europese Unie (hierna: VWEU)"
        - "de Subsidieregeling OPZuid 2021-2027 (hierna: Subsidieregeling OPZuid)"
        - "de Wet werk en bijstand (hierna: WWB)"
        - "de Wet werk en inkomen naar arbeidsvermogen (hierna: WIA)"
        - "de Wet maatschappelijke ondersteuning (hierna: Wmo)"

        These seem to be more structured, in particular when you use (de|het) as a delimiter
        This seems overly specific, but works well to extract a bunch of these

    @param text: python string to look in.  CONSIDER: accept spacy objects as well

    @return: a list of ('ww', ['word', 'word']) tuples, pretty much as-is so it (intentionally) contains duplicates
    """
    matches = []

    toks = simple_tokenize(text)
    toks_lower = list(tok.lower() for tok in toks)

    ### Patterns where the abbreviation is bracketed
    # look for bracketed letters, check against context
    for tok_offset, tok in enumerate(toks):
        match = re.match(
            r"[(]([A-Za-z][.]?){2,}[)]", tok
        )  # does this look like a bracketed abbreviation?
        if match:
            # (we over-accept some things, because we'll be checking them against contxt anyway.
            # We could probably require that more than one capital should be involved)
            abbrev = match.group().strip("()")
            letters_lower = abbrev.replace(".", "").lower()

            match_before = []
            for check_offset, _ in enumerate(letters_lower):
                check_at_pos = tok_offset - len(letters_lower) + check_offset
                if check_at_pos < 0:
                    break
                if toks_lower[check_at_pos].startswith(letters_lower[check_offset]):
                    match_before.append(toks[check_at_pos])
                else:
                    match_before = []
                    break
            if len(match_before) == len(letters_lower):
                matches.append((abbrev, match_before))

            match_after = []
            for check_offset, _ in enumerate(letters_lower):
                check_at_pos = tok_offset + 1 + check_offset
                if check_at_pos >= len(toks):
                    break
                if toks_lower[check_at_pos].startswith(letters_lower[check_offset]):
                    match_after.append(toks[check_at_pos])
                else:
                    match_after = []
                    break

            if len(match_after) == len(letters_lower):
                matches.append((abbrev, match_after))

    ### Patterns where the explanation is bracketed
    # Look for the expanded form based on the brackets, make that into an abbreviation
    # this is a little more awkward given the above tokenization.
    # We could consider putting brackets into separate tokens.  TODO: check how spacy tokenizes brackets
    for start_offset, tok in enumerate(toks):
        expansion = []
        if tok.startswith("(") and not tok.endswith(
            ")"
        ):  # start of bracketed explanation (or parenthetical or other)
            end_offset = start_offset
            while end_offset < len(toks):
                expansion.append(toks[end_offset])
                if toks[end_offset].endswith(")"):
                    break
                end_offset += 1

        if len(expansion) > 1:  # really >0, but >1 helps at end of the list
            # our tokenization leaves brackets on words (rather than being seprate tokens)
            expansion = list(
                w.strip("()") for w in expansion if len(w.lstrip("()")) > 0
            )
            expected_abbrev_noperiods = "".join(w[0] for w in expansion)
            expected_abbrev_periods = "".join(
                "%s." % let for let in expected_abbrev_noperiods
            )
            if start_offset >= 1 and toks_lower[start_offset - 1] in (
                expected_abbrev_noperiods.lower(),
                expected_abbrev_periods.lower(),
            ):
                matches.append(
                    (toks[start_offset - 1], expansion)
                )  # (add the actual abbreviated form used)
            if end_offset < len(toks) - 1 and toks_lower[end_offset + 1] in (
                expected_abbrev_noperiods.lower(),
                expected_abbrev_periods.lower(),
            ):
                matches.append((toks[end_offset + 1], expansion))

    return matches


def abbrev_count_results(l, remove_dots:bool=False, case_insensitive_explanations=False):
    """In case you have a lot of data, you can get cleaner (but reduced!) results
    by reporting how many distinct documents report the same specific explanation

    @param l: A nested structure, where 
      - the top level is a list where each item represents a document
      - Each of those is what find_abbrevs() returned, i.e. a list of items like ::
        ('AE', ['Abbreviation', 'Explanation'])

    @param remove_dots: whether to normalize the abbreviated form by removing any dots.

    @param case_insensitive_explanations: whether we consider the explanatory words in a case insensitive way while counting.
    We report whatever the most common capitalisation is.

    @return: something like: ::
        { 'AE' : {
            ['Abbreviation', 'Explanation']: 3,  
            ['Abbreviation', 'Erroneous']: 1 
        } }
    where that number would be how many documents had this explanation (NOT how often we saw this explanation).
    """

    # If case_insensitive_explanations, then we should transform that data list OR decided how to map, _before_ we count
    #TODO: go over this again, and add tests, I'm not yet sure it's correct
    variant_map = {}
    if case_insensitive_explanations:
        # count all the forms
        most_common_counter = collections.defaultdict(list) # tup_lower -> list of tup_real
        for doc_result in l:
            for _, wordlist in doc_result:
                most_common_counter[ tuple(w.lower() for w in wordlist) ].append( tuple(wordlist) )
        # decide which we prefer, and map from each
        for tupreal_list in most_common_counter.values(): # the key doesn't matter anymore, it was only used to group
            most_common_tup, _ = collections.Counter(tupreal_list).most_common(1)[0]
            for tupreal in tupreal_list:
                variant_map[tupreal] = most_common_tup

    intermediate = {} # abbrev ->  (explanatorywordlist -> set of docs that have that)
    for doc_result in l:
        for ab, words in doc_result:
            words = tuple(words)      # (to make it hashable)
            if remove_dots:
                ab = ab.replace(".", "")

            if case_insensitive_explanations:
                words = variant_map[words]

            if ab not in intermediate:
                intermediate[ab] = {}
            if words not in intermediate[ab]:
                intermediate[ab][words] = set()

            intermediate[ab][words].add( id(doc_result) )

    # we could do this with syntax-fu, but this is probably more more readable
    counted = {}
    for abbrev, word_idlist in intermediate.items():
        counted[abbrev] = {}
        for word, idlist in word_idlist.items():
            counted[abbrev][word] = len(idlist)

    return counted
