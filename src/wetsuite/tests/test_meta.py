" tests of meta.py "
# pylint: disable=C0301
import os

import pytest

import test_meta

from wetsuite.helpers.meta import parse_jci
from wetsuite.helpers.meta import parse_ecli, findall_ecli
from wetsuite.helpers.meta import (
    parse_celex,
    is_equivalent_celex,
    parse_kst_id,
    parse_bekendmaking_id,
)
from wetsuite.helpers.meta import findall_bekendmaking_ids


def test_parse_jci():
    "basic test"
    d = parse_jci("jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3.1")
    assert d["version"] == "1.31"
    assert d["type"] == "c"
    assert d["bwb"] == "BWBR0012345"
    assert d["params"]["g"] == ["2005-01-01"]


def test_parse_jci_more():
    "another"
    d = parse_jci(
        "jci1.31:c:BWBR0012345&g=2005-01-01&z=2006-01-01&hoofdstuk=3&paragraaf=2&artikel=3"
    )
    assert d["params"]["g"] == ["2005-01-01"]
    assert d["params"]["z"] == ["2006-01-01"]
    assert d["params"]["hoofdstuk"] == ["3"]
    assert d["params"]["paragraaf"] == ["2"]
    assert d["params"]["artikel"] == ["3"]


def test_parse_jci_al():
    "simpler"
    d = parse_jci("jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&lid=1")
    assert d["params"]["artikel"] == ["3"]
    assert d["params"]["lid"] == ["1"]


def test_parse_jci_al_badencoding():
    "observed invalidity"
    d = parse_jci("jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&amp;lid=1")
    assert d["params"]["artikel"] == ["3"]
    assert d["params"]["lid"] == ["1"]


def test_parse_jci_multi():
    "multiple values for a parameter"
    d = parse_jci("jci1.31:c:BWBR0012345&g=2005-01-01&artikel=3&lid=1&lid=2")
    assert d["params"]["lid"] == ["1", "2"]


def test_parse_jci_error():
    "does it throw an error?"
    with pytest.raises(ValueError, match=r".*does not look like a valid jci.*"):
        parse_jci("FIIIISH!")


def test_parse_ecli():
    "basic parse test"
    parsed = parse_ecli("ECLI:NL:RBDHA:2016:4235")

    assert parsed["country_code"] == "NL"
    assert parsed["court_code"] == "RBDHA"
    assert parsed["year"] == "2016"

    # this is optional, so maybe don't fail on it?
    assert parsed["court_details"]["name"] == "Rechtbank Den Haag"


def test_parse_ecli_bad1():
    "non-ECLI"
    with pytest.raises(ValueError, match=r".*expected.*"):
        parse_ecli("FIIIISH!")


def test_parse_ecli_bad2():
    "ECLI-ish non-ECLI"
    with pytest.raises(ValueError, match=r".*First.*"):
        parse_ecli("A:B:C:D:E")


def test_parse_ecli_bad3():
    "bad ECLI"
    with pytest.raises(ValueError, match=r".*country.*"):
        parse_ecli("ECLI:B:C:D:E")


def test_findall_ecli_strip():
    "see if an ECLI is found (also stripped of the period)"
    assert findall_ecli(" .nl/inziendocument?id=ECLI:NL:RBDHA:2016:4235. ", True) == [
        "ECLI:NL:RBDHA:2016:4235"
    ]


def test_findall_ecli_nostrip():
    "see if an ECLI is found (no stripping of the period)"
    assert findall_ecli(" .nl/inziendocument?id=ECLI:NL:RBDHA:2016:4235. ", False) == [
        "ECLI:NL:RBDHA:2016:4235."
    ]


def test_parse_ecli_good_file():
    "see if it is found (no stripping)"
    good_ecli_fn = os.path.join(
        os.path.dirname(test_meta.__file__), "testfiles", "ecli_good.txt"
    )
    with open(good_ecli_fn, "r", encoding="utf8") as good_ecli_file:
        for line in good_ecli_file:
            text, _ = line.rstrip("\n").split("\t")
            parse_ecli(text)


def test_parse_celex_noerror():
    "test that these do not throw errors"
    parse_celex("32016R0679")
    parse_celex("CELEX:32016R0679")
    parse_celex("Celex: 32016R0679")
    parse_celex("02016R0679-20160504")
    parse_celex("32012A0424(01)")
    parse_celex("72014L0056FIN_240353")


def test_parse_celex_error():
    "test that these do throw errors"
    with pytest.raises(ValueError, match=r".*Did not understand.*"):
        parse_celex("2012A0424")

    # it is not clear to me whether this is valid
    # with pytest.raises(ValueError, match=r'.*Did not understand.*'):
    #    parse_celex('02012A0424WERWW')


def test_parse_celex_extract():
    "test some extracted values"
    assert parse_celex("32016R0679")["id"] == "32016R0679"
    assert parse_celex("02016R0679-20160504")["id"] == "02016R0679"

    assert parse_celex("32012L0019")["sector_number"] == "3"
    assert parse_celex("32012L0019")["year"] == "2012"
    assert parse_celex("32012L0019")["document_type"] == "L"
    # assert parse_celex( '32012L0019' )['document_type_description'] == 'Directives'   # not really part of the parsing

    # TODO: test combinations of additions
    # TODO: read specs, not sure what to test for here
    # assert parse_celex( '32012A0424(01)' )['id'] == '32012A0424(01)'


def test_is_equivalent_celex():
    'test the "these two CELEXes ought to be treated as equivalent" test'
    assert is_equivalent_celex("CELEX:32012L0019", "32012L0019") is True
    assert is_equivalent_celex("02016R0679-20160504", "32016R0679") is True
    assert is_equivalent_celex("02016R0679", "32012L0019") is False







def test_findall_bekendmaking_ids():
    "test the basic promise of finding these identifiers"
    assert findall_bekendmaking_ids(
        "identifiers like 'stcrt-2009-9231' and 'ah-tk-20082009-2945' in text"
    ) == ["stcrt-2009-9231", "ah-tk-20082009-2945"]


def test_parse_bekendmaking_id_bad():
    "See that it trips over a non-id"
    with pytest.raises(ValueError):
        parse_bekendmaking_id("blah")


def test_parse_kst_id_1():
    "test the parse of kamerstukken document-in-dossier identifiers"
    assert parse_kst_id("kst-32123-I-5") == {
        "type": "kst",
        "docnum": "5",
        "dossiernum": "32123-I",
    }


def test_parse_kst_id_2():
    "test the parse of kamerstukken document-in-dossier identifiers"
    assert parse_kst_id("kst-20082009-32024-C") == {
        "type": "kst",
        "docnum": "C",
        "dossiernum": "32024",
    }


def test_parse_kst_id_3():
    "test the parse of kamerstukken document-in-dossier identifiers"
    assert parse_kst_id("kst-32142-A2E") == {
        "type": "kst",
        "docnum": "A2E",
        "dossiernum": "32142",
    }


def test_parse_kst_id_4():
    "test the parse of kamerstukken document-in-dossier identifiers"
    assert parse_kst_id("kst-26643-144-h1") == {
        "type": "kst",
        "docnum": "144-h1",
        "dossiernum": "26643",
    }


def test_parse_kst_id_5():
    "test the parse of kamerstukken document-in-dossier identifiers"
    assert parse_kst_id("kst-32123-XIV-A-b1") == {
        "type": "kst",
        "docnum": "A-b1",
        "dossiernum": "32123-XIV",
    }


def test_parse_kst_id_6():
    "test the parse of kamerstukken document-in-dossier identifiers"
    assert parse_kst_id("kst-32168-3-b2") == {
        "type": "kst",
        "docnum": "3-b2",
        "dossiernum": "32168",
    }


def test_parse_kst_id_bad_1():
    "Pretty sure that's invalid"
    with pytest.raises(ValueError):
        parse_kst_id("kst-LXXX-B")


def test_parse_kst_id_bad_2():
    "Nonsense"
    with pytest.raises(ValueError):
        parse_kst_id("blah")




def test_parse_bekendmaking_id_kst_1():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    # raise ValueError('erte')
    d = parse_bekendmaking_id("kst-26643-144-h1")
    assert d["type"] == "kst"
    assert d["dossiernum"] == "26643"
    assert d["docnum"] == "144-h1"


def test_parse_bekendmaking_id_kst_2():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    # raise ValueError('erte')
    d = parse_bekendmaking_id("kst-32360-V-1")
    assert d["type"] == "kst"
    assert d["dossiernum"] == "32360-V"
    assert d["docnum"] == "1"

def test_parse_bekendmaking_id_kst_3():
    "this is one of the said more weird cases"
    # raise ValueError('erte')
    d = parse_bekendmaking_id("kst-20052006-30300F-A")
    assert d["type"] == "kst"
    assert d["dossiernum"] == "30300F"
    assert d["docnum"] == "A" # I guess.




def test_parse_bekendmaking_id_blg_1():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    # raise ValueError('erte')
    d = parse_bekendmaking_id("blg-929493")
    assert d["type"] == "blg"
    assert d["docnum"] == "929493"


def test_parse_bekendmaking_id_blg_2():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    # raise ValueError('erte')
    d = parse_bekendmaking_id("blg-26241-10F")
    assert d["type"] == "blg"
    assert d["docnum"] == "26241-10F"


def test_parse_bekendmaking_id_stcrt():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    # raise ValueError('erte')
    d = parse_bekendmaking_id("stcrt-2009-9231")
    assert d["type"] == "stcrt"
    assert d["jaar"] == "2009"
    assert d["docnum"] == "9231"


# def test_parse_bekendmaking_id_stb():
#     ' test that these parse into parts decently (also TODO: add more weird cases) '
#     #raise ValueError('erte')
#     d = parse_bekendmaking_id( 'stb-2017-479' )
#     assert d['type']        == 'stb'
#     assert d['jaar']        == '2017'
#     assert d['docnum']      == '479'


def test_parse_bekendmaking_id_trb():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("trb-1951-25")
    assert d["type"] == "trb"
    assert d["jaar"] == "1951"
    assert d["docnum"] == "25"


def test_parse_bekendmaking_id_ah_tk():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("ah-tk-20082009-2945")
    assert d["type"] == "ah-tk"
    assert d["jaar"] == "20082009"
    assert d["docnum"] == "2945"


def test_parse_bekendmaking_id_ah():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("ah-187909")
    assert d["type"] == "ah"
    assert d["docnum"] == "187909"


def test_parse_bekendmaking_id_h_tk():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("h-tk-20082009-7140-7144")
    assert d["type"] == "h-tk"
    assert d["docnum"] == "7140-7144"


def test_parse_bekendmaking_id_h_vv():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("h-vv-19961997-2191-2192")
    assert d["type"] == "h-vv"
    assert d["jaar"] == "19961997"
    assert d["docnum"] == "2191-2192"  # I guess?


def test_parse_bekendmaking_id_gmb():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("gmb-2023-502828")
    assert d["type"] == "gmb"
    assert d["jaar"] == "2023"
    assert d["docnum"] == "502828"


def test_parse_bekendmaking_id_wsb():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("wsb-2022-9979")
    assert d["type"] == "wsb"
    assert d["jaar"] == "2022"
    assert d["docnum"] == "9979"


def test_parse_bekendmaking_id_bgr():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("bgr-2024-440")
    assert d["type"] == "bgr"
    assert d["jaar"] == "2024"
    assert d["docnum"] == "440"


def test_parse_bekendmaking_id_prb():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("prb-2023-11394")
    assert d["type"] == "prb"
    assert d["jaar"] == "2023"
    assert d["docnum"] == "11394"


def test_parse_bekendmaking_id_h_ek_1():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("ah-ek-20072008-5")
    assert d["type"] == "ah-ek"
    assert d["jaar"] == "20072008"
    assert d["docnum"] == "5"  # I think?


def test_parse_bekendmaking_id_h_ek_2():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("h-ek-20152016-31-6")
    assert d["type"] == "h-ek"
    assert d["jaar"] == "20152016"
    assert d["docnum"] == "31-6"  # I think?


def test_parse_bekendmaking_id_ag_tk():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("ag-tk-2001-04-10")
    assert d["type"] == "ag-tk"
    assert d["jaar"] == "2001"
    assert d["docnum"] == "04-10"  # I think that's effectively a date, april 10th


def test_parse_bekendmaking_id_ag_ek():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("ag-ek-1997-09-17")
    assert d["type"] == "ag-ek"
    assert d["jaar"] == "1997"
    assert d["docnum"] == "09-17"


def test_parse_bekendmaking_id_ag_vv():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("ag-vv-2013-11-28")
    assert d["type"] == "ag-vv"
    assert d["jaar"] == "2013"
    assert d["docnum"] == "11-28"


def test_parse_bekendmaking_id_kv():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("kv-2000100840")
    assert d["type"] == "kv"
    assert d["docnum"] == "2000100840"


def test_parse_bekendmaking_id_kv_tk_1():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("kv-tk-20062007-KVR27039")
    assert d["type"] == "kv-tk"
    assert d["jaar"] == "20062007"
    assert d["docnum"] == "KVR27039"


def test_parse_bekendmaking_id_kv_tk_2():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("kv-tk-2010Z06025")
    assert d["type"] == "kv-tk"
    assert d["docnum"] == "2010Z06025"


def test_parse_bekendmaking_id_nds_1():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("nds-53676")
    assert d["type"] == "nds"
    assert d["docnum"] == "53676"


def test_parse_bekendmaking_id_nds_2():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("nds-2009D05284-b1")
    assert d["type"] == "nds"
    assert d["docnum"] == "2009D05284-b1"  # I guess


def test_parse_bekendmaking_id_nds_3():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("nds-buza030098-b1")
    assert d["type"] == "nds"
    assert d["docnum"] == "buza030098-b1"  # I guess


def test_parse_bekendmaking_id_nds_tk():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("nds-tk-2013D38756")
    assert d["type"] == "nds-tk"
    assert d["docnum"] == "2013D38756"


def test_parse_bekendmaking_id_stb_1():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("stb-2021-244")
    assert d["type"] == "stb"
    assert d["jaar"] == "2021"
    assert d["docnum"] == "244"


def test_parse_bekendmaking_id_stb_2():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("stb-2021-250-n1")
    assert d["type"] == "stb"
    assert d["jaar"] == "2021"
    assert d["docnum"] == "250-n1"


def test_parse_bekendmaking_bulk():
    " a list of ~5.5 millions IDs, to check that we don't trip over any. xz complessed because  "
    import lzma
    bulk_list_fn = os.path.join(
        os.path.dirname(test_meta.__file__), "testfiles", "op_keylist.xz" # 
    )
    with lzma.open(bulk_list_fn, 'rt', encoding='utf-8') as fob:
        for line in fob:
            bkid = line.rstrip('\n')

            # consider these known bad cases in that lst. For now, they might not be.
            if bkid in (
                'kst-19941995-00', 
                'kst-19941995-XV'
                'kst-19941995-00',
                'kst-19941995-XV',
                'kst-19941995-XVI',
                'kst-19971998-6-5a',
                'kst-20032004-000IX-A',
                'kst-20032004-000IX-B',
                'kst-20032004-000IX-C',
                'kst-20032004-000XV-A',
                'kst-20032004-000XV-B',
                'kst-20032004-000XV-C',
                'kst-20032004-00XVI-A',
                'kst-20032004-00XVI-B',
                'kst-20042005-XVIII-A',
                'kst-20042005-XXI-A',
                'kst-20042005-XXI-B',
                'kst-20042005-XXI-C',
                'kst-20042005-XXI-D',
                'kst-20042005-XXI-E',
                'kst-20042005-XXI-F',
                'kst-20042005-XXII-A',
                'kst-20042005-XXIII-A',
                'kst-20042005-XXIII-B',
                'kst-20052006-XLIV-A',
                'kst-20052006-XXI-G',
                'kst-20052006-XXI-H',
                'kst-20052006-XXX-A',
                'kst-20052006-XXXIX-A',
                'kst-20062007-L-A-h1',
                'kst-20062007-L-B',
                'kst-20062007-L-C',
                'kst-20062007-L-D',
                'kst-20062007-L-E',
                'kst-20062007-LI-A',
                'kst-20062007-LI-B',
                'kst-20062007-LII-A',
                'kst-20062007-LIII-A',
                'kst-20062007-LIII-B',
                'kst-20062007-LVI-A',
                'kst-20062007-XLIX-A',
                'kst-20062007-XLVII-A',
                'kst-20062007-XLVIII-A',
                'kst-20062007-XXI-I',
                'kst-20062007-XXI-I-b1',
                'kst-20072008-00LXI-A',
                'kst-20072008-00LXV-A',
                'kst-20072008-00LXV-B',
                'kst-20072008-00LXV-C',
                'kst-20072008-00LXV-D',
                'kst-20072008-00LXV-E',
                'kst-20072008-00LXV-F',
                'kst-20072008-00LXX-A',
                'kst-20072008-00LXX-B',
                'kst-20072008-00LXX-C',
                'kst-20072008-0LXIV-A',
                'kst-20072008-0LXVI-A',
                'kst-20072008-LIX-A',
                'kst-20072008-LVII-A',
                'kst-20072008-LVIII-A',
                'kst-20072008-LX-A',
                'kst-20092010-LXXXIII-A',
                'kst-20092010-LXXXIII-B',
                'kst-20092010-LXXXV-A',
                'kst-20092010-LXXXVI-A',
                'kst-301000-G-2',
                'kst-6-1',
                'kst-6-3',
                'kst-6-4',
                'kst-6-4-h1',
                'kst-6-5',
                'kst-6-7',
                'kst-6-8',
                'kst-6-A',
                'kst-935450-A-2',
                'kst-C-A',
                'kst-C-AA',
                'kst-C-AB',
                'kst-C-AC',
                'kst-C-AD',
                'kst-C-AE',
                'kst-C-AF',
                'kst-C-AG',
                'kst-C-AH',
                'kst-C-AI',
                'kst-C-AJ',
                'kst-C-B',
                'kst-C-C',
                'kst-C-D',
                'kst-C-E',
                'kst-C-F',
                'kst-C-G',
                'kst-C-H',
                'kst-C-I',
                'kst-C-J',
                'kst-C-K',
                'kst-C-L',
                'kst-C-M',
                'kst-C-N',
                'kst-C-O',
                'kst-C-P',
                'kst-C-Q',
                'kst-C-R',
                'kst-C-S',
                'kst-C-T',
                'kst-C-U',
                'kst-C-V',
                'kst-C-W',
                'kst-C-X',
                'kst-C-Y',
                'kst-C-Z',
                'kst-CI-A',
                'kst-CI-B',
                'kst-CI-C',
                'kst-CI-D',
                'kst-CI-E',
                'kst-CI-E-n1',
                'kst-CI-F',
                'kst-CI-G',
                'kst-CI-H',
                'kst-CI-I',
                'kst-CII-A',
                'kst-CII-B',
                'kst-CII-C',
                'kst-CII-D',
                'kst-CII-E',
                'kst-CII-F',
                'kst-CII-G',
                'kst-CII-H',
                'kst-CII-I',
                'kst-CII-J',
                'kst-CIII-A',
                'kst-CIII-B',
                'kst-CIV-A',
                'kst-CIV-B',
                'kst-CIV-C',
                'kst-CIV-D',
                'kst-CIX-A',
                'kst-CIX-B',
                'kst-CL-A',
                'kst-CLI-A',
                'kst-CLI-B',
                'kst-CLI-C',
                'kst-CLI-D',
                'kst-CLII-A',
                'kst-CLII-B',
                'kst-CLIII-A',
                'kst-CLIII-B',
                'kst-CLIV-A',
                'kst-CLIV-B',
                'kst-CLIV-C',
                'kst-CLIV-D',
                'kst-CLIX-A',
                'kst-CLIX-B',
                'kst-CLV-A',
                'kst-CLV-B',
                'kst-CLV-C',
                'kst-CLV-D',
                'kst-CLV-E',
                'kst-CLV-F',
                'kst-CLVI-A',
                'kst-CLVI-A-n1',
                'kst-CLVI-AA',
                'kst-CLVI-AB',
                'kst-CLVI-B',
                'kst-CLVI-B-n1',
                'kst-CLVI-C',
                'kst-CLVI-D',
                'kst-CLVI-E',
                'kst-CLVI-F',
                'kst-CLVI-G',
                'kst-CLVI-H',
                'kst-CLVI-I',
                'kst-CLVI-J',
                'kst-CLVI-K',
                'kst-CLVI-L',
                'kst-CLVI-M',
                'kst-CLVI-N',
                'kst-CLVI-O',
                'kst-CLVI-P',
                'kst-CLVI-Q',
                'kst-CLVI-R',
                'kst-CLVI-S',
                'kst-CLVI-T',
                'kst-CLVI-U',
                'kst-CLVI-V',
                'kst-CLVI-W',
                'kst-CLVI-X',
                'kst-CLVI-Y',
                'kst-CLVI-Z',
                'kst-CLVII-A',
                'kst-CLVII-B',
                'kst-CLVII-C',
                'kst-CLVIII-A',
                'kst-CLVIII-B',
                'kst-CLX-A',
                'kst-CLX-B',
                'kst-CLXI-A',
                'kst-CLXII-A',
                'kst-CLXII-B',
                'kst-CLXII-C',
                'kst-CLXIII-A',
                'kst-CLXIV-A',
                'kst-CLXIV-B',
                'kst-CLXIV-C',
                'kst-CLXIV-D',
                'kst-CLXIV-E',
                'kst-CLXIV-F',
                'kst-CLXV-A',
                'kst-CLXV-B',
                'kst-CLXX-A',
                'kst-CV-A',
                'kst-CV-B',
                'kst-CVI-A',
                'kst-CVI-B',
                'kst-CVI-C',
                'kst-CVI-D',
                'kst-CVII-A',
                'kst-CVII-B',
                'kst-CVII-C',
                'kst-CVII-D',
                'kst-CVII-E',
                'kst-CVII-F',
                'kst-CVII-G',
                'kst-CVII-H',
                'kst-CVII-I',
                'kst-CVII-J',
                'kst-CVII-L',
                'kst-CVIII-A',
                'kst-CVIII-B',
                'kst-CVIII-C',
                'kst-CVIII-D',
                'kst-CVIII-E',
                'kst-CVIII-F',
                'kst-CVIII-G',
                'kst-CVIII-H',
                'kst-CVIII-I',
                'kst-CVIII-J',
                'kst-CVIII-K',
                'kst-CVIII-L',
                'kst-CVIII-M',
                'kst-CVIII-N',
                'kst-CVIII-O',
                'kst-CVIII-P',
                'kst-CVIII-Q',
                'kst-CVIII-R',
                'kst-CVIII-S',
                'kst-CVIII-T',
                'kst-CVIII-U',
                'kst-CX-A',
                'kst-CX-B',
                'kst-CX-C',
                'kst-CX-D',
                'kst-CX-E',
                'kst-CX-F',
                'kst-CX-G',
                'kst-CX-H',
                'kst-CX-I',
                'kst-CXI-A',
                'kst-CXII-A',
                'kst-CXII-B',
                'kst-CXII-C',
                'kst-CXII-D',
                'kst-CXII-E',
                'kst-CXII-F',
                'kst-CXII-G',
                'kst-CXII-H',
                'kst-CXIII-A',
                'kst-CXIV-A',
                'kst-CXIV-B',
                'kst-CXIX-A',
                'kst-CXIX-B',
                'kst-CXL-A',
                'kst-CXL-B',
                'kst-CXLI-A',
                'kst-CXLI-B',
                'kst-CXLII-A',
                'kst-CXLII-B',
                'kst-CXLII-C',
                'kst-CXLII-D',
                'kst-CXLII-E',
                'kst-CXLIII-A',
                'kst-CXLIV-A',
                'kst-CXLIV-B',
                'kst-CXLIV-C',
                'kst-CXLIX-A-n1',
                'kst-CXLIX-B',
                'kst-CXLIX-C',
                'kst-CXLIX-D',
                'kst-CXLV-A',
                'kst-CXLV-B',
                'kst-CXLVI-A',
                'kst-CXLVI-AA',
                'kst-CXLVI-AB',
                'kst-CXLVI-AC',
                'kst-CXLVI-AD',
                'kst-CXLVI-AE',
                'kst-CXLVI-B',
                'kst-CXLVI-C',
                'kst-CXLVI-D',
                'kst-CXLVI-E',
                'kst-CXLVI-F',
                'kst-CXLVI-G',
                'kst-CXLVI-H',
                'kst-CXLVI-I',
                'kst-CXLVI-J',
                'kst-CXLVI-K',
                'kst-CXLVI-L',
                'kst-CXLVI-M',
                'kst-CXLVI-N',
                'kst-CXLVI-O',
                'kst-CXLVI-P',
                'kst-CXLVI-Q',
                'kst-CXLVI-R',
                'kst-CXLVI-S',
                'kst-CXLVI-T',
                'kst-CXLVI-U',
                'kst-CXLVI-V',
                'kst-CXLVI-W',
                'kst-CXLVI-X',
                'kst-CXLVI-Y',
                'kst-CXLVI-Z',
                'kst-CXLVII-A',
                'kst-CXLVII-B',
                'kst-CXLVII-C',
                'kst-CXLVII-D',
                'kst-CXLVII-E',
                'kst-CXLVII-F',
                'kst-CXLVII-G',
                'kst-CXLVII-H',
                'kst-CXLVII-I',
                'kst-CXLVII-J',
                'kst-CXLVII-K',
                'kst-CXLVII-L',
                'kst-CXLVII-M',
                'kst-CXLVII-N',
                'kst-CXLVII-O',
                'kst-CXLVII-P',
                'kst-CXLVII-Q',
                'kst-CXLVII-R',
                'kst-CXLVIII-A',
                'kst-CXLVIII-B',
                'kst-CXLVIII-C',
                'kst-CXLVIII-D',
                'kst-CXLVIII-E',
                'kst-CXLVIII-F',
                'kst-CXV-A',
                'kst-CXV-B',
                'kst-CXVI-A',
                'kst-CXVI-B',
                'kst-CXVII-A',
                'kst-CXVII-B',
                'kst-CXVII-C',
                'kst-CXVII-D',
                'kst-CXVII-E',
                'kst-CXVII-F',
                'kst-CXVII-G',
                'kst-CXVII-H',
                'kst-CXVII-I',
                'kst-CXVIII-A',
                'kst-CXVIII-B',
                'kst-CXX-A',
                'kst-CXX-B',
                'kst-CXX-C',
                'kst-CXXI-B',
                'kst-CXXI-C',
                'kst-CXXI-D',
                'kst-CXXI-E',
                'kst-CXXI-F',
                'kst-CXXI-G',
                'kst-CXXI-H',
                'kst-CXXI-I',
                'kst-CXXII-A',
                'kst-CXXIII-A-n1',
                'kst-CXXIII-B',
                'kst-CXXIII-C',
                'kst-CXXIV-A',
                'kst-CXXIV-B',
                'kst-CXXIV-C',
                'kst-CXXIV-D',
                'kst-CXXIV-E',
                'kst-CXXIV-F',
                'kst-CXXIV-G',
                'kst-CXXIV-H',
                'kst-CXXIV-I',
                'kst-CXXIV-J',
                'kst-CXXIV-K',
                'kst-CXXIX-A',
                'kst-CXXV-A',
                'kst-CXXV-B',
                'kst-CXXV-C',
                'kst-CXXV-D',
                'kst-CXXV-E',
                'kst-CXXV-F',
                'kst-CXXV-G',
                'kst-CXXV-H',
                'kst-CXXV-I',
                'kst-CXXV-J',
                'kst-CXXV-K',
                'kst-CXXVI-A',
                'kst-CXXVI-B',
                'kst-CXXVII-A',
                'kst-CXXVII-B',
                'kst-CXXVII-C',
                'kst-CXXVII-D',
                'kst-CXXVII-E',
                'kst-CXXVIII-A',
                'kst-CXXX-A',
                'kst-CXXXI-A',
                'kst-CXXXI-B',
                'kst-CXXXI-C',
                'kst-CXXXI-D',
                'kst-CXXXI-D-n1',
                'kst-CXXXI-E',
                'kst-CXXXI-F',
                'kst-CXXXI-G',
                'kst-CXXXII-A',
                'kst-CXXXII-B',
                'kst-CXXXIII-A',
                'kst-CXXXIV-A',
                'kst-CXXXIV-B',
                'kst-CXXXIX-A',
                'kst-CXXXIX-B',
                'kst-CXXXIX-C',
                'kst-CXXXIX-D',
                'kst-CXXXIX-E',
                'kst-CXXXIX-E-n1',
                'kst-CXXXIX-F',
                'kst-CXXXIX-G',
                'kst-CXXXIX-H',
                'kst-CXXXIX-I',
                'kst-CXXXV-A',
                'kst-CXXXV-B',
                'kst-CXXXVI-A',
                'kst-CXXXVI-B',
                'kst-CXXXVI-C',
                'kst-CXXXVI-D',
                'kst-CXXXVI-E',
                'kst-CXXXVII-A',
                'kst-CXXXVII-B',
                'kst-CXXXVII-C',
                'kst-CXXXVII-D',
                'kst-CXXXVII-E',
                'kst-CXXXVIII-A',
                'kst-CXXXVIII-B',
                'kst-CXXXVIII-C',
                'kst-CXXXVIII-D',
                'kst-CXXXVIII-E',
                'kst-CXXXVIII-F',
                'kst-LXXX-A',
                'kst-LXXX-B',
                'kst-LXXXII-A',
                'kst-LXXXIV-A',
                'kst-LXXXIV-B',
                'kst-LXXXIV-C',
                'kst-LXXXIV-D',
                'kst-LXXXIV-E',
                'kst-LXXXIV-F',
                'kst-LXXXIV-G',
                'kst-LXXXIX-A',
                'kst-LXXXVII-A',
                'kst-LXXXVII-B',
                'kst-LXXXVII-C',
                'kst-LXXXVII-D',
                'kst-LXXXVIII-A',
                'kst-LXXXVIII-B',
                'kst-LXXXVIII-C',
                'kst-LXXXVIII-D',
                'kst-LXXXVIII-E',
                'kst-LXXXVIII-F',
                'kst-LXXXVIII-G',
                'kst-XC-A',
                'kst-XC-B',
                'kst-XC-C',
                'kst-XCI-A',
                'kst-XCI-B',
                'kst-XCII-A',
                'kst-XCII-B',
                'kst-XCIII-A',
                'kst-XCIV-A',
                'kst-XCIV-B',
                'kst-XCIX-A',
                'kst-XCIX-B',
                'kst-XCIX-C',
                'kst-XCIX-D',
                'kst-XCIX-E',
                'kst-XCIX-F',
                'kst-XCIX-G',
                'kst-XCV-A',
                'kst-XCVI-A',
                'kst-XCVII-A',
                'kst-XCVII-B',
                'kst-XCVII-C',
                'kst-XCVIII-A',
                'kst-XCVIII-B',
                'kst-XXIX-A',
                'kst-XXX-1',
                ):
                continue

            # Just checking that that function doesn't raise ValueError for this id
            parse_bekendmaking_id( bkid )
