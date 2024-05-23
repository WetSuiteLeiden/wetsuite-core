' test of wordcloud wrapping module ' 
from wetsuite.extras.word_cloud import count_normalized, wordcloud_from_freqs, count_case_insensitive#, count_from_spacy_document


def test_count_normalized():
    ' test the count-normalized-form function'

    ci = count_normalized( 'a A A a A A a B b b B b'.split() )
    assert ci['a'] == 3
    assert ci['A'] == 4
    assert ci['b'] == 3
    assert ci['B'] == 2


    cs = count_normalized( 'a A A a A A a B b b B b'.split(), normalize_func=lambda s:s.lower() )
    assert cs['A'] == 7
    assert cs['b'] == 5


    cs = count_case_insensitive( 'a A A a A A a B b b B b'.split() )
    assert cs['A'] == 7
    assert cs['b'] == 5


    cs = count_case_insensitive( 'aa A A aa A A aa B bb bb B bb cc cc dd'.split(), min_word_length=2, min_count=2 )
    assert cs['aa'] == 3
    assert cs['bb'] == 3
    assert cs['cc'] == 2
    assert 'd' not in cs




def test_stop():
    ' test that stopwords functionality seems to work'
    cs = count_normalized( 'a A A a A A a B b b B b'.split(), normalize_func=lambda s:s.lower(), stopwords=(), stopwords_i=())
    assert cs == {'A': 7, 'b': 5}

    cs = count_normalized( 'a A A a A A a B b b B b'.split(), normalize_func=lambda s:s.lower(), stopwords=('a',), stopwords_i=())
    assert cs == {'A': 4, 'b': 5}

    cs = count_normalized( 'a A A a A A a B b b B b'.split(), normalize_func=lambda s:s.lower(), stopwords=(), stopwords_i=('a',))
    assert cs == {'b': 5}

    cs = count_case_insensitive( ['the','een'], stopwords=True ) #  asks for some (english and stuch)
    assert len(cs) == 0


def test_count_normalized_min():
    ' test that the minimum threshold seems to work '
    cs = count_normalized( 'a a a a b b b c'.split(), min_count=2 )
    assert cs['a'] == 4
    assert cs['b'] == 3
    assert 'c' not in cs

    cs = count_normalized( 'a a a a b b b c'.split(), min_count=2.0 )
    assert cs['a'] == 4
    assert cs['b'] == 3
    assert 'c' not in cs

    cs = count_normalized( 'a a a a b b b c'.split(), min_count=3.5 )
    assert cs['a'] == 4
    assert 'b' not in cs
    assert 'c' not in cs

    cs = count_normalized( 'a a a a b b b c'.split(), min_count=0.3 )
    assert cs['a'] == 4
    assert cs['b'] == 3
    assert 'c' not in cs


def test_wordcloud_from_freqs():
    " test that it runs (and doesn't trip over missing X11 stuff) "
    wordcloud_from_freqs( {'a':1} )


# def test_count_from_spacy_document():
#     # can we mock one up without a mess of code?
#     # https://stackoverflow.com/questions/56728218/how-to-mock-spacy-models-doc-objects-for-unit-tests

#     # not sure about this yet
#     from spacy.vocab import Vocab
#     from spacy.tokens import Doc
#     words = "a big fish".split(" ")
#     #spaces = len(words) * [True]
#     vocab = Vocab(strings=words)
#     doc   = Doc(vocab, words=words)#, spaces=spaces
#     doc[0].pos_='DET'
#     doc[1].pos_='ADJ'
#     doc[2].pos_='NOUN'

#     assert count_from_spacy_document( doc ) == {'a':1}
