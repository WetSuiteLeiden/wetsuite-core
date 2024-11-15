""" test functions in the wetsuite.helpers.split module """

# import os
# import pytest

import wetsuite.helpers.localdata
import wetsuite.datacollect.koop_frbr



def test_koop_frbr_init():
    " test that that class even instatiates "
    fetch_store = wetsuite.helpers.localdata.LocalKV(":memory:", str, bytes)
    cache_store = wetsuite.helpers.localdata.LocalKV(":memory:", str, bytes)

    wetsuite.datacollect.koop_frbr.FRBRFetcher(
        fetch_store=fetch_store, cache_store=cache_store
    )


def DISABLED_test_koop_frbr_fetch():
    """ test of code involved in fetching.  
        By actually fetching a document set, so this takes at least a dozen seconds, which is why this is disabled for now. """
    fetch_store = wetsuite.helpers.localdata.LocalKV(":memory:", str, bytes)
    cache_store = wetsuite.helpers.localdata.LocalKV(":memory:", str, bytes)

    ff = wetsuite.datacollect.koop_frbr.FRBRFetcher(
        fetch_store=fetch_store, cache_store=cache_store
    )

    ff.add_page('https://repository.overheid.nl/frbr/officielepublicaties/bgr/2015/bgr-2015-1/1')
    list( ff.work() )

    # IIRC three each
    assert len(fetch_store) > 0
    assert len(cache_store) > 0
