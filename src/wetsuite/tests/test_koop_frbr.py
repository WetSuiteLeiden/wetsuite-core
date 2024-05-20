''' test functions in the wetsuite.helpers.split module '''

import os

import pytest

import wetsuite.helpers.localdata
import wetsuite.datacollect.koop_frbr


def test_koop_frbr_init():
    fetch_store = wetsuite.helpers.localdata.LocalKV(':memory:', str, bytes)
    cache_store  = wetsuite.helpers.localdata.LocalKV(':memory:', str, bytes)

    ff = wetsuite.datacollect.koop_frbr.FRBRFetcher(fetch_store=fetch_store, cache_store=cache_store)

    #ff.handle_url('https://repository.overheid.nl/frbr/officielepublicaties/ah-tk/19961997/ah-tk-19961997-100/1/html')
