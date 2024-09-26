""" test spacy-related functions
    
"""

# import pytest

import spacy
import spacy.tokens.doc
import spacy.tokens.span

import wetsuite.helpers.spacy


# def load_nl():
#    download_if_necessary("nl_core_news_sm")


def get_model(lang="nl"):
    "helpers: get empty model of given Language"
    return spacy.blank(lang)


def get_simpledoc():
    "TODO: finish this or remove"

    nlp = get_model()
    #doc = nlp.make_doc("Smeer de zonnebrand")
    doc = spacy.tokens.doc.Doc(vocab=nlp.vocab, words=["Smeer", "de", "zonnebrand"])
    # this is some rather poor and incomplete mocking
    doc[0].pos_ = "VERB"
    doc[1].pos_ = "DET"
    doc[2].pos_ = "NOUN"
    return doc


def test_simpledoc():
    "test that that get_simpledoc vaguely works"
    for _ in get_simpledoc():
        pass


def test_span_as_doc():
    "test that that get_simpledoc vaguely works, part 2"
    doc = get_simpledoc()
    assert isinstance(doc, spacy.tokens.doc.Doc)

    span = doc[2:3]
    assert isinstance(span, spacy.tokens.span.Span)
    asdoc = wetsuite.helpers.spacy.span_as_doc(span)

    assert isinstance(asdoc, spacy.tokens.doc.Doc)


def test_parse():
    "test that a parse doesn't fail"
    nlp = get_model()
    for _ in nlp("I like cheese"):
        pass


# def test_reload():
#     " test that the reload(wetsuite.helpers.spacy) doesn't fail "
#     wetsuite.helpers.spacy.reload()


def test_notebook_content_visualisation():
    "for now just test that it does not bork out"
    doc = get_simpledoc()
    wetsuite.helpers.spacy.notebook_content_visualisation(
        doc
    )._repr_html_()  # pylint: disable=protected-access


# def test_interesting_words():
#     ' for now just test that it does not bork out.   We can mock this one up a bit. '
#     wordlist = wetsuite.helpers.spacy.interesting_words( get_simpledoc() )
#     assert wordlist[0] == 'Smeer'
#     assert wordlist[1] == 'zonnebrand'


# most of the rest needs a real model

# https://stackoverflow.com/questions/56728218/how-to-mock-spacy-models-doc-objects-for-unit-tests

# def test_subjects_in_doc():
#     ' for now just test that it does not bork out '
#     doc = get_simpledoc()
#     wetsuite.helpers.spacy.subjects_in_doc(doc)


# def test_subjects_in_doc():
#     subjects_in_doc

# def test_subjects_in_span():
#     subjects_in_span

# def test_nl_noun_chunks():
#     nl_noun_chunks


# def test_detect_language():
#     detect_language

# def test_sentence_split():
#     test_sentence_split
