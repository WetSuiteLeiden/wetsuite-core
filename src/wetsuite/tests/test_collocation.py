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

    def has_sequence(test_tup, grams):
        return test_tup in grams

    assert has_sequence( ('als','bedoeld','in'),      coll.grams )      # count: 26
    assert has_sequence( ('niet','van','toepassing'), coll.grams ) # count:  6
    assert not has_sequence( ('foo', 'bar', 'quu'),   coll.grams )

    print( coll.grams )
    coll.cleanup_ngrams(   mincount=10 )
    # for this data and these settings...
    print( coll.grams )

    assert has_sequence( ('als','bedoeld','in'),          coll.grams )  
    assert not has_sequence( ('niet','van','toepassing'), coll.grams ) 


def test_that_cleanup_reduces():
    text = test_text()

    coll = wetsuite.helpers.collocation.Collocation()
    coll.consume_tokens( text.split(), gramlens=(3,) )

    before_ngram_count   = coll.counts()['ngrams']
    before_unigram_count = coll.counts()['unigrams']
    assert before_ngram_count > 1000
    assert before_unigram_count > 1000
    coll.cleanup_ngrams( mincount=10 )
    assert coll.counts()['ngrams'] < before_ngram_count
    coll.cleanup_unigrams( mincount=10 )
    assert coll.counts()['unigrams'] < before_unigram_count


def test_that_cleanup_func_reduces():
    text = test_text()

    coll = wetsuite.helpers.collocation.Collocation()
    coll.consume_tokens( text.split(), gramlens=(3,) )

    before_ngram_count   = coll.counts()['ngrams']

    def tup_has_van(tup, count):
        return 'van' in tup # one of the words is 'van'
    
    coll.cleanup_ngrams(mincount=None, disqualify_func=tup_has_van)

    assert coll.counts()['ngrams'] < before_ngram_count



