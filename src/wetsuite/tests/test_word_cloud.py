" test of wordcloud wrapping module "
from wetsuite.extras.word_cloud import (
    wordcloud_from_freqs,
    wordcloud_from_stringlist,
    wordcloud_from_string,
    count_from_string,
    merge_counts
)


def test_wordcloud_from_freqs():
    "test that it runs  (and doesn't trip over missing X11 stuff)"
    wordcloud_from_freqs({"a": 1})


def test_wordcloud_from_stringlist():
    "test that it runs, and procsses a string list"
    wordcloud_from_stringlist( 'Foo foo foo bar'.split() )


def test_wordcloud_from_strings():
    "test that it runs, and processes a string"
    wordcloud_from_string('Foo foo foo bar')


def test_count_from_string():
    "test that it runs, and processes a string, according to the default tokenizer "
    assert count_from_string('Foo foo foo bar') == {'foo': 3, 'bar': 1}


def test_merge_counts():
    "test that it runs, and processes a string, according to the default tokenizer "
    a = count_from_string('Foo foo foo bar')
    b = count_from_string('Foo foo foo bar')
    assert merge_counts([a,b]) == {'foo': 6, 'bar': 2}



# def test_count_from_spacy_document():
#     # can we mock one up without a mess of code?  is make_doc enough?
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
