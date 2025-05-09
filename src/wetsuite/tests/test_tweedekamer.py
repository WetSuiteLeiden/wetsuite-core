""" Test some functions of the wetsuite.datacollect.tweedekamer_nl module """

import pytest
import wetsuite.datacollect.tweedekamer_nl


def DISABLED_test_fetch_all():  # disabled because it takes ~20 sec
    # def test_fetch_all():
    "test that we can fetch and merge"
    # etrees = wetsuite.datacollect.tweedekamer_nl.fetch_all( 'Zaal') #, break_actually=True )
    etrees = wetsuite.datacollect.tweedekamer_nl.fetch_all("Zaal", break_actually=True)
    merged_tree = wetsuite.datacollect.tweedekamer_nl.merge_etrees(etrees)
    wetsuite.datacollect.tweedekamer_nl.entry_dicts(merged_tree)


def DISABLED_test_fetch_resource():
    ' test that fetches work (more test of remote servers, and not technically deterministic, though) '
    with pytest.raises(ValueError, match=r'.*400.*'):
        wetsuite.datacollect.tweedekamer_nl.fetch_resource('sdfsdf')

    wetsuite.datacollect.tweedekamer_nl.fetch_resource('2d1a7837-c0c4-4971-9e32-feacaa50961b')
