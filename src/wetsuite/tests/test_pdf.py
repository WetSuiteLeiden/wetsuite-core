" test of PDF-related functions "
import os

import pytest

import wetsuite.extras.pdf
from wetsuite.helpers.strings import contains_all_of


def read_file(basename: str):
    " Open file within a specific subdirectory relative to this test code. "
    import test_pdf  # import for self-reference is intentional, pylint: disable=W0406
    eggs_filename = os.path.join( os.path.dirname(test_pdf.__file__), "testfiles", basename )
    with open(eggs_filename, "rb") as f:
        eggs_data = f.read()
    return eggs_data


def read_eggs():
    "return eggs.pdf as bytes"
    return read_file( 'eggs.pdf' )


def read_imagepdf():
    "return image.pdf as bytes"
    import test_pdf  # import for self-reference is intentional, pylint: disable=W0406
    imagepdf_filename = os.path.join( os.path.dirname(test_pdf.__file__), "testfiles", "image.pdf" )
    with open(imagepdf_filename, "rb") as f:
        imagepdf_data = f.read()
    return imagepdf_data


def test_page_text():
    'test the "hey PDF, what text do you contain?" function (page at a time)'
    pages_text = list(wetsuite.extras.pdf.page_embedded_text_generator( read_eggs() ))
    # pymupdf: ['I am Sam\nDr. Seuss\n1960\nI do not like green eggs and ham.\n1\n']
    # poppler: ['I am Sam Dr. Seuss 1960 I do not like green eggs and ham. 1']
    # we mainly care that it's extracting at all, so be more accepting
    assert contains_all_of(
        pages_text[0], ["I am Sam", "Dr. Seuss", "I do not like green eggs and ham."]
    )


#def test_doc_embedded_text():
#    'test the "hey PDF, what text do you contain?" function (whole doc)'
#    doc_text = wetsuite.extras.pdf.doc_embedded_text( read_eggs() )
#    assert contains_all_of(
#        doc_text, ["I am Sam", "Dr. Seuss", "I do not like green eggs and ham."]
#    )


def test_count_pages_with_embedded_text():
    'test the "do pages have enough text?" function'
    # higher threshold
    res = wetsuite.extras.pdf.count_pages_with_embedded_text(read_eggs(), char_threshold=500)
    chars_per_page, count_pages_with_text_count, count_pages = res
    assert len(chars_per_page) == 1
    assert count_pages == 1
    assert count_pages_with_text_count == 0

    # lower threshold
    res = wetsuite.extras.pdf.count_pages_with_embedded_text(read_eggs(), char_threshold=40)
    chars_per_page, count_pages_with_text_count, count_pages = res
    assert len(chars_per_page) == 1
    assert count_pages == 1
    assert count_pages_with_text_count == 1

    # test that it takes the list-of-page-text input like it says
    pages_text = list(wetsuite.extras.pdf.page_embedded_text_generator( read_eggs() ))
    res = wetsuite.extras.pdf.count_pages_with_embedded_text(pages_text)


def test_page_image_renders_at_all():
    'test that the "render PDF pages as PIL images" functions'
    for page_im in wetsuite.extras.pdf.pages_as_images(read_eggs()):
        # should be around 1241 x 1754
        assert page_im.size[0] > 500



def test_closest_paper_size_name():
    ' test whether we extract page size name and orientation, of a known document '
    import fitz
    for page in fitz.open(stream=read_eggs()): # there will be just one page, actually
        sizename, orientation, wdiff, hdiff = wetsuite.extras.pdf.closest_paper_size_name( page.cropbox )
        assert sizename    == 'A4'
        assert orientation == 'portrait'
        assert wdiff < 10
        assert hdiff < 10


def test_closest_paper_size_name__landscape_letter():
    ' test whether we extract page size name and orientation, of a synthetically made example '
    import fitz
    doc = fitz.open()
    doc.new_page(width=792, height=612)
    doc.new_page(width=792, height=612)
    for page in doc:
        sizename, orientation, _wdiff, _hdiff = wetsuite.extras.pdf.closest_paper_size_name( page.cropbox )
        assert sizename    == 'Letter'
        assert orientation == 'landscape'


def test_closest_paper_size_name__other():
    ' tests whether it says "other" when it should '
    import fitz
    doc = fitz.open()
    doc.new_page(width=123, height=456)
    for page in doc:
        sizename, orientation, _wdiff, _hdiff = wetsuite.extras.pdf.closest_paper_size_name( page.cropbox )
        assert sizename    == 'other'
        assert orientation == 'portrait'


def test_closest_paper_size_name__page():
    ' test whether we extract page size name and orientation, even if we gave it a Page instead of a Document, and whether it warns about that '
    import fitz
    for page in fitz.open(stream=read_eggs()):
        with pytest.warns(UserWarning, match=r".*Page.*"):
            sizename, orientation, wdiff, hdiff = wetsuite.extras.pdf.closest_paper_size_name( page )
        assert sizename    == 'A4'
        assert orientation == 'portrait'
        assert wdiff < 10
        assert hdiff < 10


def test_do_page_sizes_vary():
    ' check that it notices a difference '
    import fitz
    doc = fitz.open()
    _page1 = doc.new_page(width=595, height=842)
    _page2 = doc.new_page(width=123, height=456)
    does_vary, _hdiff, _vdiff = wetsuite.extras.pdf.do_page_sizes_vary( doc )
    assert does_vary is True


def test_do_page_sizes_vary_singlepage():
    ' check that it is fine with just one page '
    import fitz
    does_vary, hdiff, vdiff = wetsuite.extras.pdf.do_page_sizes_vary( fitz.open(stream=read_eggs()) )
    assert does_vary is False
    assert hdiff == 0.0
    assert vdiff == 0.0


def test_do_page_sizes_vary_nopages():
    ' check that it is fine with zero pages '
    import fitz
    doc = fitz.open()
    does_vary, hdiff, vdiff = wetsuite.extras.pdf.do_page_sizes_vary( doc )
    assert does_vary is False
    assert hdiff == 0.0
    assert vdiff == 0.0



def test_page_fragments():
    ' test whether we read text frrom a PDF at all, per page '
    import fitz
    doc = fitz.open( stream=read_eggs() )
    first_page = doc[0]
    text = wetsuite.extras.pdf.page_embedded_fragments( first_page )
    assert len(text) > 10
    assert 'euss' in text


def test_document_fragments():
    ' test whether we read text frrom a PDF at all, overall, with minor structure analysis '
    import fitz
    doc = fitz.open( stream=read_eggs() )
    struclist = wetsuite.extras.pdf.document_fragments( doc,hint_structure=True )
    assert len(struclist[0]) ==3                         # a (hints, empty, text) tuple
    assert len(struclist) > 5 and len(struclist) < 10    # 7 fragments, to be precise


def test_document_fragments_nohints():
    ' test whether we read text frrom a PDF at all, overall, without added structure '
    import fitz
    doc = fitz.open( stream=read_eggs() )
    textlist = wetsuite.extras.pdf.document_fragments( doc, hint_structure=False )
    assert '\n' in textlist # now a list




def test_embedded_or_ocr_perpage():
    ' test whether OCR manages to extract text '
    # picks up embedded text (not easily tested unless  also return that)
    egg_bytes = read_eggs()
    source, text = wetsuite.extras.pdf.embedded_or_ocr_perpage( egg_bytes, use_gpu=False )[0]   # [0] for first page
    assert source == 'embedded'
    assert len( text ) > 20

    # PDF with an image of a graph with text
    imagepdf_bytes = read_imagepdf()
    source, text = wetsuite.extras.pdf.embedded_or_ocr_perpage( imagepdf_bytes, use_gpu=False )[0]   # [0] for first page
    assert source == 'ocr'
    assert len( text ) > 30


def test_garbledness():
    ' test whether font-garbling is detected '
    import fitz
    import wetsuite.helpers.strings

    for page in fitz.open( stream=read_file( 'garble.pdf' ) ):
        page_test_text = ''.join( list(wetsuite.extras.pdf.page_embedded_fragments( page )) )
        assert wetsuite.helpers.strings.has_mostly_wordlike_text( page_test_text ) is False

    for page in fitz.open( stream=read_file( 'eggs.pdf' ) ):
        page_test_text = ''.join( list(wetsuite.extras.pdf.page_embedded_fragments( page )) )
        assert wetsuite.helpers.strings.has_mostly_wordlike_text( page_test_text ) is True




# both sets of warnings seem about deprecated stuff - might break in the future?
@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_pdf_text_ocr():
    "mostly a test of the ocr module does not fail "
    wetsuite.extras.pdf.pdf_text_ocr(read_eggs(), use_gpu=False)
