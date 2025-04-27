""" test OCR related functions """
# CONSIDER: vary on use_gpu

import os
import time

import pytest
from PIL import Image, ImageDraw


def read_eggs():
    "return eggs.pdf as bytes"
    import test_pdf  # import for self-reference is intentional, pylint: disable=W0406

    eggs_filename = os.path.join( os.path.dirname(test_pdf.__file__), "testfiles", "eggs.pdf" )

    with open(eggs_filename, "rb") as f:
        eggs_data = f.read()

    return eggs_data



def test_import():
    "test that the import does not bork, e.g. over dependencies"
    import wetsuite.extras.ocr  # pylint: disable=unused-import



@pytest.mark.filterwarnings("ignore::UserWarning")
@pytest.mark.filterwarnings("ignore::DeprecationWarning")  # some distutil blah that is not important for this test
def test_image():
    "test that OCR basically functions, on an image we generate with PIL.  This test will take a few seconds just because of heavy overhead. "

    import wetsuite.extras.ocr
    image = Image.new("RGB", (200, 200))
    draw = ImageDraw.Draw(image)
    draw.text((10, 10), "Hello from")
    draw.text((10, 25), "Pillow")

    bbox_results = wetsuite.extras.ocr.easyocr(image, use_gpu=False)
    # detected some text
    assert len(bbox_results) > 0
    assert len(wetsuite.extras.ocr.easyocr_toplaintext(bbox_results)) > 0

    # test that it doesn't fail
    wetsuite.extras.ocr.easyocr_draw_eval(image, bbox_results)



#def test_load_unload_extent():
#    "test that OCR basically functions, on an image we generate with PIL.  This test will take a few seconds just because of heavy overhead. "
#
#    import wetsuite.extras.ocr
#    image = Image.new("RGB", (200, 200))
#    draw = ImageDraw.Draw(image)
#    draw.text((10, 10), "Hello from")
#    draw.text((10, 25), "Pillow")
#
#    wetsuite.extras.ocr.easyocr( image, use_gpu=False )
#
#    wetsuite.extras.ocr.easyocr( image, use_gpu=True )
#
#    wetsuite.extras.ocr.easyocr_unload()
#
#    # TODO: see if something like device_memory_used is useful to test (and whether it's in enough versions to stably use here)





def test_ocr_pdf_pages():
    " mostly just tests that it gets out some text "
    import wetsuite.extras.ocr
    egg_bytes = read_eggs()
    _parts, text = wetsuite.extras.ocr.ocr_pdf_pages( egg_bytes, use_gpu=False )
    assert 'euss' in ''.join(text)

# For reference, this is not a font that EasyOCR has a good time with. At different resolutions:
#   1 am Sam Dr. Seuss 1960 Ido not like green eggs and ham_
#   1 am Sam Dr. Seuss 1960 Ido not like green eggs and ham
#   1 am Sam Dr Seuss 1960 I do not like green eggs and ham
#   1 am Sam Dr. Seuss 1960 Ido like green eggs ham and not
#   Iam Sam Dr. Seuss 1960 I do not like green eggs ham and
#   1 am Sam Dr. Seuss 1960 I do not like green eggs ham and
#   Iam Sam Dr Seuss 1960 Ido not like green eggs and ham
#   Iam Sam Dr . Seuss 1960 Ido not like green eggs and ham_
#   I am Sam Dr. Seuss 1960 I do not like green eggs and ham.
#   L am Sam Dr . Seuss 1960 Ido not like green eggs and ham.
#   I am Sam Dr. Seuss 1960 I do not like green eggs and ham-
#   I am Sam Dr. Seuss 1960 Ido not like green eggs ham and



def test_test_ocr_pdf_pages_cache():
    ' test that it stores in a cache, and takes less time if we hit it '
    import wetsuite.helpers.localdata

    mem_cache = wetsuite.helpers.localdata.MsgpackKV(':memory:', str)

    egg_bytes = read_eggs()

    start = time.time()
    struc1, text1 = wetsuite.extras.ocr.ocr_pdf_pages( egg_bytes, page_cache=mem_cache, use_gpu=False )
    took1 = time.time() - start
    assert len(struc1[0])>1  # does the first page cotain several items
    assert len(text1)>0      # did we produce text (note that this variable doesn't separate pages)

    start = time.time()
    struc2, text2 = wetsuite.extras.ocr.ocr_pdf_pages( egg_bytes, page_cache=mem_cache, use_gpu=False )
    took2 = time.time() - start

    # testing  struc1 == struc2  would not work because msgpack does not distinguish between tuple and list
    assert len(struc1[0]) == len(struc2[0]) # so do a much simpler test
    assert text1 == text2 # so just assume
    assert 'euss' in ''.join(text2)

    assert took2 < took1



#    +------------------------------------------+ 216
#    |                                          |       height = 80
#    +------------------------------------------+ 136
#    130                                      844
#                     width = 714
_test_bbox = [(130, 136), (844, 136), (844, 216), (130, 216)]

def test_bbox_min_x():
    ' test that bbox min-of-x calculation works '
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.bbox_min_x( _test_bbox ) == 130

def test_bbox_max_x():
    ' test that bbox max-of-x calculation works '
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.bbox_max_x( _test_bbox ) == 844

def test_bbox_min_y():
    ' test that bbox min-of-y calculation works '
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.bbox_min_y( _test_bbox ) == 136

def test_bbox_max_y():
    ' test that bbox max-of-y calculation works '
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.bbox_max_y( _test_bbox ) == 216


def test_bbox_xy_extent():
    ' test that bbox extends-of-x-and-y calculation works '
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.bbox_xy_extent( _test_bbox ) == (130, 844, 136, 216)


def test_bbox_width():
    ' test that bbox width calculation works '
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.bbox_width( _test_bbox ) == 714

def test_bbox_height():
    ' test that bbox height calculation works '
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.bbox_height( _test_bbox ) == 80



#            332  381   413  464
#                   ______               551
#                  |Text5|
#                                        537
#
#              _______________           464
#             |Text4_________|
#                                        432
#
#   __________________                   336
#  |   text3          |
#  |__________________|                  282
#   ______________________               262
#  |   text2              |
#  |______________________|__________   ~220
#  |                                |
#  |  Text1                         |
#  |________________________________|    136
# 130                522 591       844

_test_boxes = [  # note: the text was replaced so its length does not match the box sizes
 ([(130, 136), (844, 136), (844, 216), (130, 216)],  'Text1',   0.99),
 ([(132, 212), (591, 212), (591, 262), (132, 262)],  'Text2',   0.69),
 ([(134, 282), (522, 282), (522, 336), (134, 336)],  "Text3",   0.82),
 ([(322, 432), (464, 432), (464, 456), (322, 456)],  'Text4',   0.17),
 ([(381, 537), (413, 537), (413, 551), (381, 551)],  'Text5',   0.85),
]

def test_page_allxy():
    ''' test that list of all x and y values is extracted '''
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.page_allxy( _test_boxes ) == (
        [130,  844,  844,  130,  132,  591,  591,  132,  134,  522,  522,  134,  322,  464,  464,  322,  381,  413,  413,  381],
        [136,  136,  216,  216,  212,  212,  262,  262,  282,  282,  336,  336,  432,  432,  456,  456,  537,  537,  551,  551],
    )


def test_page_extent():
    " Figure out the extent of boxes   (for so few, the percentile logic doesn't affect it) "
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.page_extent( _test_boxes ) == (130, 844,  136, 551) # minx maxx miny maxy


# pretend _test_boxes is on two two pages
# (and interspersed; sort of necessary to have understandable/predictable bounds since statistics on so few items would more easily ignore one)
_test_two = [
    _test_boxes[1::2]+_test_boxes[:2], # text2, text4
    _test_boxes[::2],                  # text1, text3, text5
]

def test_doc_extent():
    " Figure out the extent of boxes, if spread on multiple pages "
    import wetsuite.extras.ocr
    assert wetsuite.extras.ocr.doc_extent( _test_two ) == (130, 844,  136, 551)  # minx maxx miny maxy


def test_page_fragment_filter__textre():
    ' test that filtering fragments by regexp works'
    import wetsuite.extras.ocr
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, textre='1' ) ) == 1
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, textre='Text[0-5]' ) ) == 5
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, textre='text[0-5]' ) ) == 0
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, textre='(?i)text[0-5]' ) ) == 5

def test_page_fragment_filter__xy():
    ' test that filtering fragments by coordinates works '
    import wetsuite.extras.ocr
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_min_x=300 ) ) == 2 # 4 and 5
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_max_x=300 ) ) == 3

    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_min_y=300 ) ) == 2
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_max_y=200 ) ) == 1


def test_page_fragment_filter__extent():
    ' float-of-extent test '
    import wetsuite.extras.ocr
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_min_x=0.5, extent=(400.0, 844.0, 436.0, 551.0) ) ) == 2
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_max_x=0.5, extent=(400.0, 844.0, 436.0, 551.0) ) ) == 3
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_max_y=0.5, extent=(400.0, 844.0, 436.0, 551.0) ) ) == 2
    assert len( wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_min_y=0.5, extent=(400.0, 844.0, 436.0, 551.0) ) ) == 3


def test_page_fragment_filter__verbose():
    " mostly testing that these code paths don't error out  "
    import wetsuite.extras.ocr

    wetsuite.extras.ocr.page_fragment_filter( _test_boxes, textre='1',  verbose=True )
    wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_min_x=0.5, verbose=True )
    wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_max_x=0.5, verbose=True )
    wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_max_y=0.5, verbose=True )
    wetsuite.extras.ocr.page_fragment_filter( _test_boxes, q_min_y=0.5, verbose=True )
