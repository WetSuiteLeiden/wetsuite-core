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


def test_parse_bekendmaking_id_kst_1():
    "test the parse of kamerstukken document-in-dossier identifiers"
    d = parse_kst_id("kst-32123-I-5")
    assert d[ "type"] == "kst"
    assert d[ "docnum"] == "32123-I-5"
    assert d[ "dossiernum"] == "32123-I"

def test_parse_bekendmaking_id_kst_2():
    "test the parse of kamerstukken document-in-dossier identifiers"
    d = parse_kst_id("kst-20082009-32024-C")
    assert d["type"] == "kst"
    assert d["docnum"] == "20082009-32024-C"
    assert d["dossiernum"] == "32024"
    assert d["vj"] == "20082009"

def test_parse_bekendmaking_id_kst_3():
    "test the parse of kamerstukken document-in-dossier identifiers"
    d = parse_kst_id("kst-32142-A2E")
    assert d["type"] == "kst"
    assert d["docnum"] == "32142-A2E"

def test_parse_bekendmaking_id_kst_4():
    "test the parse of kamerstukken document-in-dossier identifiers"
    d = parse_kst_id("kst-26643-144-h1")
    assert d["type"] == "kst"
    assert d["docnum"] == "26643-144-h1"
    assert d["dossiernum"] == "26643"

def test_parse_bekendmaking_id_kst_5():
    "test the parse of kamerstukken document-in-dossier identifiers"
    d = parse_kst_id("kst-32123-XIV-A-b1")
    assert d["type"] == "kst"
    assert d["docnum"] == "32123-XIV-A-b1"
    assert d["dossiernum"] == "32123-XIV"

def test_parse_bekendmaking_id_kst_6():
    "test the parse of kamerstukken document-in-dossier identifiers"
    d = parse_kst_id("kst-32168-3-b2")
    assert d["type"] == "kst"
    assert d["docnum"] == "32168-3-b2"
    assert d["dossiernum"] == "32168"

def test_parse_bekendmaking_id_kst_7():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("kst-26643-144-h1")
    assert d["type"] == "kst"
    assert d["dossiernum"] == "26643"
    assert d["docnum"] == "26643-144-h1"

def test_parse_bekendmaking_id_kst_8():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("kst-32360-V-1")
    assert d["type"] == "kst"
    assert d["dossiernum"] == "32360-V"
    assert d["docnum"] == "32360-V-1"

def test_parse_bekendmaking_id_kst_9():
    "this is one of the said more weird cases"
    d = parse_bekendmaking_id("kst-20052006-30300F-A")
    assert d["type"] == "kst"
    assert d["dossiernum"] == "30300F"
    assert d["docnum"] == "20052006-30300F-A" # I guess.

def test_parse_bekendmaking_id_kst_bad_2():
    "Nonsense"
    with pytest.raises(ValueError):
        parse_kst_id("blah")



def test_parse_bekendmaking_id_blg_1():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("blg-929493")
    assert d["type"] == "blg"
    assert d["docnum"] == "929493"


def test_parse_bekendmaking_id_blg_2():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("blg-26241-10F")
    assert d["type"] == "blg"
    assert d["docnum"] == "26241-10F"


def test_parse_bekendmaking_id_stcrt():
    "test that these parse into parts decently (also TODO: add more weird cases)"
    d = parse_bekendmaking_id("stcrt-2009-9231")
    assert d["type"] == "stcrt"
    assert d["jaar"] == "2009"
    assert d["docnum"] == "9231"


def test_parse_bekendmaking_id_stb():
    ' test that these parse into parts decently (also TODO: add more weird cases) '
    d = parse_bekendmaking_id( 'stb-2017-479' )
    assert d['type']        == 'stb'
    assert d['jaar']        == '2017'
    assert d['docnum']      == '479'


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
        os.path.dirname(test_meta.__file__), "testfiles", "op_keylist.xz"
    )
    with lzma.open(bulk_list_fn, 'rt', encoding='utf-8') as fob:
        for line in fob:
            bkid = line.rstrip('\n')

            # Just checking that that function doesn't raise a complaint in a ValueError for this id
            parse_bekendmaking_id( bkid )
