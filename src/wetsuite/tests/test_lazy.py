" test that the calls in lazy.py haven't broken yet "
import os
from wetsuite.helpers.lazy import (
    etree,
    html_text,
    pdf_embedded_text,
    #pdf_text_ocr,
    spacy_parse,
)


def read_eggs():
    "return eggs.pdf as bytes"
    import test_pdf  # import for self-reference is intentional, pylint: disable=W0406

    eggs_filename = os.path.join(
        os.path.dirname(test_pdf.__file__), "testfiles", "eggs.pdf"
    )

    with open(eggs_filename, "rb") as f:
        eggs_data = f.read()

    return eggs_data


def test_etree():
    ' test that the parsing does not fail '
    etree( b'<a xmlns:pre="foo"> <pre:b/> </a>' )
    etree(  '<a xmlns:pre="foo"> <pre:b/> </a>' )



def test_pdf_embedded_text():
    ' test that PDF extraction does not fail '
    pdf_embedded_text( read_eggs() )


#def test_pdf_text_ocr():
#    pdf_text_ocr( read_eggs() )


def test_spacy_parse():
    ' test that spacy arsing call does not fail '
    spacy_parse('I like cheese')
    spacy_parse('I like cheese', force_language='en')


def test_html_text():
    ' test that HTML text extraction does roughly what it is stupposed to (more tests in tests_etree) '
    assert html_text('<a>foo<b></b>quu</a>') == 'fooquu'
    assert html_text('<div>foo</div><p>quu</p>') == 'foo\nquu'


#def test_xml_html_text():
#    assert xml_html_text('<a>foo<b></b>quu</a>') == 'fooquu'
