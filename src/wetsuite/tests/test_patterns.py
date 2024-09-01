""" Tests relating to the patterns module
"""

from wetsuite.helpers.patterns import find_references



def test_identifier_parse():
    "see whether these get parsed, in isolation"
    for test_string, expect in (
        ("asdf Stb. 2005 asdf",                                            {"type": "vindplaats", "text": "Stb. 2005"}),
        ("asdf Trb.\xa01966 asdf",                                         {"type": "vindplaats", "text": "Trb.\xa01966"}),
        ("asdf Trb. 1966, 91 asdf",                                        {"type": "vindplaats", "text": "Trb. 1966, 91"}),

        ("asdf Kamerstukken II 1992/1993, 22 asdf",                        {"type": "kamerstukken", "text": "Kamerstukken II 1992/1993, 22"}),

        ("asdf BB7360 asdf",                                               {"type": "ljn", "text": "BB7360"}),
        ("asdf ECLI:NL:CBB:1996:ZG0749 asdf",                              {"type": "ecli", "text": "ECLI:NL:CBB:1996:ZG0749"}),
        ('asdf Kamerstukken 1992/1993, 22 asdf',                           {"type": "kamerstukken", "text": "Kamerstukken 1992/1993, 22"}),

        ("asdf BWBR000011 asdf",                                           {"type": "bwb", "text": "BWBR000011"}),

        ("asdf CVDR101405 asdf",                                           {"type": "cvdr", "text": "CVDR101405"}),
        ("asdf CVDR101405_1 asdf",                                         {"type": "cvdr", "text": "CVDR101405_1"}),
        ("asdf CVDR101405/1 asdf",                                         {"type": "cvdr", "text": "CVDR101405/1"}),

        ("asdf OJ L 69, 13.3.2013 asdf",                                   {"type": "euoj"}),
        ("asdf Council Directive 93/42/EEC EUDIR of 14 June 1993 asdf",    {"type": "eudir"}),

        ("asdf 33684R2020  asdf",                                          {"type": "celex", "text": "33684R2020"}),
        # TODO: more
    ):
        found = find_references(
            test_string,
            bwb=True,
            cvdr=True,
            ljn=True,
            ecli=True,
            celex=True,
            kamerstukken=True,
            vindplaatsen=True,
            nonidentifier=True,
            euoj=True,
            eudir=True,
        )
        assert len(found) > 0

        for key, value in expect.items():
            assert found[0].get(key) == value


def test_nearly():
    " Some cases that look nearly like an identifier but probably shouldn't be detected "
    for test_string in (
       "asdf 3684R2020  asdf",
        # TODO: more
    ):
        found = find_references(
            test_string,
            bwb=True,
            cvdr=True,
            ljn=True,
            ecli=True,
            celex=True,
            kamerstukken=True,
            vindplaatsen=True,
            nonidentifier=True,
            euoj=True,
            eudir=True,
        )
        assert len(found) == 0


def test_reference_parse():
    "test that some basic refernces get parsed"
    matches = find_references("artikel 5:9, aanhef en onder b, Awb", nonidentifier=True)
    d = matches[0]["details"]
    assert d["artikel"] == "5:9"

    matches = find_references(
        "artikel 4, tweede lid, aanhef en onder d, van het reglement van orde voor de ministerraad", nonidentifier=True
    )
    d = matches[0]["details"]
    assert d["artikel"] == "4"
    assert "tweede" in d["lid"]
    assert 2 in d["lid_num"]
    assert d["aanhefonder"] == "aanhef en onder d"


def test_found_artikel():
    "test that we match something at all in each of these"
    for test in [
        'artikel 4, tweede lid, aanhef en onder d, van het reglement van orde voor de ministerraad                     ',
        'artikel 4, tweede lid, onder d, van het reglement                     ',
        'artikel 2, lid 1                   ',
        'artikel 2, lid\n1                   ',
        'artikel 2, eerste\nlid               ',
        'artikel 2, eerste lid                 ',
        'artikel 2, eerste en vijfde lid        ',
        'artikel 2, eerste, tweede, en vijfde lid',

        'artikel 5:9, aanhef en onder b, Awb',
        'artikel 8, aanhef en onder c, Wet bescherming persoonsgegevens (Wbp).'
        'artikel 10, tweede lid, aanhef en onder e, van de Wob',
        "artikel 4, tweede lid, aanhef en onder d, van het reglement van orde voor de ministerraad",
        "artikel 2, eerste, tweede, vijfde, even zesenzestigste lid",
        "Artikel 10, tweede lid, aanhef en onder e van de. Wet openbaarheid van bestuur",
        "artikel 6:80 lid 1 aanhef en onder b BW",
        'artikel 142, eerste lid, aanhef en onder b (en derde lid), van het Wetboek van Strafvordering',
        'artikel 4, aanhef en onder d en g, van de standaardvoorwaarden',
        'artikel 3.3, zevende lid, aanhef en onder i, Woo',
        'artikel 3.3, zevende lid jo. vijfde lid, aanhef en onder i, Woo',
        'artikel 79, aanhef en onder 6\xBA',
        'artikel 15, aanhef en onder a of c (oud) RWN',
        'Wabo, art. 2.12, eerste lid, aanhef en onder a, sub 1\xBA',
        'artikel 4:25, 4:35 van de Awb en artikel 10 van de ASV'

        # Note that these can be references to "gelet op" (Intitule) begipsbepalingen
        #   e.g. the last (from CVDR662488/1) doesn't strictly _define_ Awb or ASV, but of the options of lines like
        #   "artikel 5 van de Tijdelijke aanvulling Algemene subsidieverordening Hoeksche Waard 2020"
        #   we can pick a probably option.

    ]:
        assert len( find_references( test ) ) > 0   # found anything at all?
