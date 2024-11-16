""" test OCR related functions

"""

import pytest

# import warnings

from PIL import Image, ImageDraw


def test_import():
    "test that the import does not bork, over dependencies"
    import wetsuite.extras.ocr  # pylint: disable=unused-import

    # wetsuite.extras.ocr.easyocr()


@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.filterwarnings("ignore::DeprecationWarning")  # some distutil blah that is not important for this test
def test_image():
    "test that OCR basically functions, on an image we generate with PIL.  This test will take a few seconds just because of heavy overhead. "
    import wetsuite.extras.ocr

    image = Image.new("RGB", (200, 200))
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "Hello from")
    draw.text((10, 25), "Pillow")

    bbox_results = wetsuite.extras.ocr.easyocr(image)
    # detected some text
    assert len(bbox_results) > 0
    assert len(wetsuite.extras.ocr.easyocr_text(bbox_results)) > 0

    # test that it doesn't fail
    wetsuite.extras.ocr.easyocr_draw_eval(image, bbox_results)


# CONSIDER: use_gpu


# TODO:
# def test_page_extent():
# def test_doc_extent():


# page_fragment_filter,
# probably on a real pdf
