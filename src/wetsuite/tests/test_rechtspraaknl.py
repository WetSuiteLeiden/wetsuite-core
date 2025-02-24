""" test functions in the wetsuite.datacollect.rechtspraaknl module """

# import pytest

import os

import wetsuite.datacollect.rechtspraaknl

import wetsuite.helpers.net
import wetsuite.helpers.etree


def DISABLED_test_value_list_parsing():
    "test that these fetch-and-parse things do not bork out. This test will take ~2sec mostly because of the fetches. "
    wetsuite.datacollect.rechtspraaknl.parse_instanties()
    wetsuite.datacollect.rechtspraaknl.parse_instanties_buitenlands()
    wetsuite.datacollect.rechtspraaknl.parse_proceduresoorten()
    wetsuite.datacollect.rechtspraaknl.parse_rechtsgebieden()
    wetsuite.datacollect.rechtspraaknl.parse_nietnederlandseuitspraken()


def test_search():
    "test that the basic API search works"
    # import datetime
    # yesterday_date = ( datetime.datetime.now() - datetime.timedelta(days=1) ).date()
    # yesterday_str  = yesterday_date.strftime('%Y-%m-%d')

    results = wetsuite.datacollect.rechtspraaknl.search(
        params=[
            ("max", "20"),
            # ('return', 'DOC'),                                         # DOC asks for things with body text only
            # ('modified', '2023-10-01'), ('modified', '2023-11-01')    # date range    (keep in mind that larger ranges easily means we hit the max)
            ("modified", "2023-11-01"),
        ]
    )

    assert len(results.getchildren()) > 0

    wetsuite.datacollect.rechtspraaknl.parse_search_results(results)


def test_parse():
    "test that those documents parse without failing"
    import test_rechtspraaknl

    path = os.path.join(
        os.path.dirname(test_rechtspraaknl.__file__), "testfiles", "rechtspraak1.xml"
    )
    with open(path, "rb") as f:
        tree = wetsuite.helpers.etree.fromstring(f.read())
        wetsuite.datacollect.rechtspraaknl.parse_content(tree)

    path = os.path.join(
        os.path.dirname(test_rechtspraaknl.__file__), "testfiles", "rechtspraak2.xml"
    )
    with open(path, "rb") as f:
        tree = wetsuite.helpers.etree.fromstring(f.read())
        wetsuite.datacollect.rechtspraaknl.parse_content(tree)
