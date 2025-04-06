""" test functions in the wetsuite.helpers.collocation module """

import os
import wetsuite.helpers.collocation
import wetsuite.helpers.etree




def test_text():
    ' get text from one of our own test files.  Test values below were chosen based on its contents '
    import test_collocation  # that's intentional pylint: disable=W0406
    with open( os.path.join(os.path.dirname(test_collocation.__file__), "testfiles", 'bwb_toestand.xml'), mode="rb" ) as f:
        tree = wetsuite.helpers.etree.fromstring( f.read() )
        text = wetsuite.helpers.etree.html_text( tree )
        return text


def test_basics():
        text = test_text()

        coll = wetsuite.helpers.collocation.Collocation()
        coll.consume_tokens( text.split(), gramlens=(3,) )
        coll.cleanup_ngrams(   mincount=10 )
        coll.cleanup_unigrams( mincount=2  )

        grams = coll.score_ngrams()
        def has_sequence(test_tup):
            for tup, _, _, _ in grams:
                if test_tup == tup:
                    return True
            return False

        assert has_sequence( ('als','bedoeld','in') )
        assert has_sequence( ('tot', 'geheimhouding', 'verplicht') )
        assert not has_sequence( ('foo', 'bar', 'quu') )



def test_cleanup():
    text = test_text()

    coll = wetsuite.helpers.collocation.Collocation()
    coll.consume_tokens( text.split(), gramlens=(3,) )

    assert coll.counts()['ngrams'] > 1000
    coll.cleanup_ngrams( mincount=10 )
    assert coll.counts()['ngrams'] < 100

    assert coll.counts()['unigrams'] > 1000
    coll.cleanup_unigrams( mincount=10 )
    assert coll.counts()['unigrams'] < 200




