""" test function in the wetsuite.extras.gerechtcode module """

import wetsuite.extras.gerechtcodes


def test_lookup():
    "test that the lookup works, with a known item"
    res = wetsuite.extras.gerechtcodes.case_insensitive_lookup("GHARL")
    assert res["abbrev"] == "GHARL"
    assert res["name"] == "Gerechtshof Arnhem-Leeuwarden"
    assert res["extra"] == ["gerechtshof"]


def test_lookup_bad():
    "test that the lookup works, with a known item"
    assert wetsuite.extras.gerechtcodes.case_insensitive_lookup("BLAH") is None
