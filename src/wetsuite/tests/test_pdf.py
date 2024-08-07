" test of PDF-related functions "
import os

import pytest

import wetsuite.extras.pdf
from wetsuite.helpers.strings import contains_all_of


def read_eggs():
    "return eggs.pdf as bytes"
    import test_pdf  # import for self-reference is intentional, pylint: disable=W0406

    eggs_filename = os.path.join(
        os.path.dirname(test_pdf.__file__), "testfiles", "eggs.pdf"
    )

    with open(eggs_filename, "rb") as f:
        eggs_data = f.read()

    return eggs_data


def test_page_text():
    'test the "hey PDF, what text do you contain?" function (page at a time)'
    pages_text = list(wetsuite.extras.pdf.page_text(read_eggs()))
    # pymupdf: ['I am Sam\nDr. Seuss\n1960\nI do not like green eggs and ham.\n1\n']
    # poppler: ['I am Sam Dr. Seuss 1960 I do not like green eggs and ham. 1']
    # we mainly care that it's extracting at all, so be more accepting
    assert contains_all_of(
        pages_text[0], ["I am Sam", "Dr. Seuss", "I do not like green eggs and ham."]
    )


def test_doc_text():
    'test the "hey PDF, what text do you contain?" function (whole doc)'
    doc_text = wetsuite.extras.pdf.doc_text(read_eggs())
    assert contains_all_of(
        doc_text, ["I am Sam", "Dr. Seuss", "I do not like green eggs and ham."]
    )


def test_count_pages_with_text():
    'test the "do pages have enough text?" function'
    # higher threshold
    res = wetsuite.extras.pdf.count_pages_with_text(read_eggs(), char_threshold=500)
    chars_per_page, count_pages_with_text_count, count_pages = res
    assert len(chars_per_page) == 1
    assert count_pages == 1
    assert count_pages_with_text_count == 0

    # lower threshold
    res = wetsuite.extras.pdf.count_pages_with_text(read_eggs(), char_threshold=40)
    chars_per_page, count_pages_with_text_count, count_pages = res
    assert len(chars_per_page) == 1
    assert count_pages == 1
    assert count_pages_with_text_count == 1

    # test that it takes the list-of-page-text input like it says
    pages_text = list(wetsuite.extras.pdf.page_text(read_eggs()))
    res = wetsuite.extras.pdf.count_pages_with_text(pages_text)


def test_page_image_renders_at_all():
    'test that the "render PDF pages as PIL images" functions'
    for page_im in wetsuite.extras.pdf.pages_as_images(read_eggs()):
        # should be around 1241 x 1754
        assert page_im.size[0] > 500


# both sets of warnings seem about deprecated stuff - might break in the future?
@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
def test_pdf_text_ocr():
    "mostly a test of the ocr module does not bork out"
    wetsuite.extras.pdf.pdf_text_ocr(read_eggs())
