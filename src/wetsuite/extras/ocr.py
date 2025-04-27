""" Extract text from images, mainy aimed at PDFs that contain pictures of documents

    Largely a wrapper for OCR package, currently just EasyOCR; we really should TODO: add tesseract
    https://github.com/sirfz/tesserocr

    And then, ideally, TODO: add an interface in front of both it an tesseract 
    (and maybe, in terms of 'text fragment placed here', also pymudpdf)
    so that the helper functions make equal sense
"""

import sys
import re

from PIL import ImageDraw
import numpy

import wetsuite.extras.pdf       # mostly for pages_as_images
import wetsuite.helpers.util


# keep EasyOCR reader in memory to save time when you call it repeatedly
#   Two, so that we can honour the use_gpu call each call, not just use and cache whatever the first call did
# However, torch seems to occupy the GPU even when asked not to, so maybe you should only use it in short-running scripts?
_easyocr_reader_cpu = None
_easyocr_reader_gpu = None


###### debug and helpers #############################################################################################################

# functions that help deal with the numbers in the EasyOCR output fragments,
#
# ...and potentially also other OCR and PDF-extracted text streams, once we get to it.


def easyocr_draw_eval(image, ocr_results):
    """Given 
      - a PIL image (the image you handed into OCR), 
      - the results from ocr()
    draws the bounding boxes, with color indicating the confidence.

    Made for inspection of how much OCR picks up, and what it might have trouble with.

    @param image: the image that you ran ocr() on
    @param ocr_results: the output of ocr()
    @return: a copy of the input image with boxes drawn on it
    """
    image = image.convert("RGB")
    draw = ImageDraw.ImageDraw(image, "RGBA")
    for bbox, _, conf in ocr_results:
        topleft, _, botright, _ = bbox
        xy = [tuple(topleft), tuple(botright)]
        draw.rectangle(
            xy,  outline=10,  fill=(int((1 - conf) * 255),  int(conf * 255),  0,    125)
        )
    return image


# These are easocr-specific, rename them?
def bbox_height(bbox):
    """Calculate a bounding box's height.
    @param bbox: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: the bounding box's width
    """
    topleft, _, botright, _ = bbox
    return abs(botright[1] - topleft[1])

def bbox_width(bbox):
    """Calcualte a bounding box's width.
    @param bbox: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: the bounding box's width
    """
    topleft, _, botright, _ = bbox
    return abs(botright[0] - topleft[0])

def bbox_xy_extent(bbox):
    """Calcualte a bounding box's X and Y extents
    @param bbox: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: the bounding box's (min(x), max(x), min(y), max(y))
    """
    xs, ys = [], []
    for x, y in bbox:
        xs.append(x)
        ys.append(y)
    return min(xs), max(xs), min(ys), max(ys)

def bbox_min_x(bbox):
    """minimum X coordinate - redundant with bbox_xy_extent, but sometimes more readable in code
    @param bbox: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: the bounding box's minimum x coordinate
    """
    topleft, topright, botright, botleft = bbox
    return min(list(x  for x, _ in (topleft, topright, botright, botleft)))

def bbox_max_x(bbox):
    """maximum X coordinate - redundant with bbox_xy_extent, but sometimes more readable in code
    @param bbox: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: the bounding box's maximum x coordinate
    """
    topleft, topright, botright, botleft = bbox
    return max(list(x  for x, _ in (topleft, topright, botright, botleft)))

def bbox_min_y(bbox):
    """minimum Y coordinate - redundant with bbox_xy_extent, but sometimes more readable in code
    @param bbox: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: the bounding box's minimum y coordinate
    """
    topleft, topright, botright, botleft = bbox
    return min(list(y  for _, y in (topleft, topright, botright, botleft)))

def bbox_max_y(bbox):
    """maximum Y coordinate - redundant with bbox_xy_extent, but sometimes more readable in code
    @param bbox: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: the bounding box's maximum y coordinate
    """
    topleft, topright, botright, botleft = bbox
    return max(list(y  for _, y in (topleft, topright, botright, botleft)))

def page_allxy(page_easyocr_fragments):
    """Given a page's worth of OCR results, return list of X, and list of Y coordinates,
    meant for e.g. statistics use.

    @param page_easyocr_fragments: a bounding box, as a 4-tuple (tl,tr,br,bl)
    @return: ( all x list, all y list )
    """
    xs, ys = [], []
    for bbox, _, _ in page_easyocr_fragments:
        topleft, topright, botright, botleft = bbox
        for x, y in (topleft, topright, botright, botleft):
            xs.append(x)
            ys.append(y)
    return xs, ys

def page_extent(page_easyocr_fragments, percentile_x=(1, 99), percentile_y=(1, 99)):
    """Estimates the bounds that contain most of the page contents
    (uses considers all bbox x and y coordinates)

    'Most' in that we use the 1st and 99th percentiles (by default) - may need tweaking

    @param page_easyocr_fragments:   A list of (bbox, text, cert).
    @param percentile_x:
    @param percentile_y:
    @return: (page_min_x, page_max_x,  page_min_y, page_max_y)  which, note, might not  be exactly what you epxected
    """
    xs, ys = page_allxy( page_easyocr_fragments )
    return (
        numpy.percentile( xs, percentile_x[0] ),
        numpy.percentile( xs, percentile_x[1] ),
        numpy.percentile( ys, percentile_y[0] ),
        numpy.percentile( ys, percentile_y[1] ),
    )

def doc_extent(list_of_page_easyocr_fragments, percentile_x=(1, 99), percentile_y=(1, 99)):
    """ 
    Like page_extent(), but considering all pages at once,
    mostly to ge the overall margins,
    and e.g. avoid doing weird things on a last half-filled page.

    Note that if many pages have little on them, this is somewhat fragile

    @param list_of_page_easyocr_fragments: A list of ( A list of (bbox, text, cert) ) for each page
    @return: (page_min_x, page_max_x,  page_min_y, page_max_y)  which, note, might not  be exactly what you epxected
    """
    xs, ys = [], []
    for page_easyocr_fragments in list_of_page_easyocr_fragments:
        page_xs, page_ys = page_allxy( page_easyocr_fragments )
        xs.extend( page_xs )
        ys.extend( page_ys )
    return (
        numpy.percentile( xs, percentile_x[0] ),
        numpy.percentile( xs, percentile_x[1] ),
        numpy.percentile( ys, percentile_y[0] ),
        numpy.percentile( ys, percentile_y[1] ),
    )
    #return min(xs), max(xs), min(ys), max(ys)

def page_fragment_filter(
    page_easyocr_fragments,
    textre=None,
    q_min_x=None,
    q_min_y=None,
    q_max_x=None,
    q_max_y=None,
    extent=None,
    verbose=False,
):
    """Searches for specific text patterns on specific parts of pages.

    Takes the fragments from a single page
    (CONSIDER: making a doc_fragment_filter).

    This is sometimes overkill, but for some uses this is easier.
    ...in particularly the first one it was written for,
    trying to find the size of the header and footer, to be able to ignore them.

    q_{min,max}_{x,y} can be
      - floats (relative to height and width of text
        ...present within the page, by default
        ...or the document, if you hand in the document extent via extent
        (can make more sense to deal with first and last pages being half filled)
      - otherwise assumed to be ints, absolute units
        (which are likely to be pixels and depend on the DPI),

    @param page_easyocr_fragments:
    @param textre:  include only fragments that match this regular expression
    @param q_min_x: helps restrict where on the page we search (see notes above)
    @param q_min_y: helps restrict where on the page we search (see notes above)
    @param q_max_x: helps restrict where on the page we search (see notes above)
    @param q_max_y: helps restrict where on the page we search (see notes above)
    @param extent:  defines the extent (minx, miny, maxx, maxy) of the page 
                    which, note, is ONLY used when q_ are floats.
    @param verbose: say what we're including/excluding and why
    """
    # when first and last pages can be odd, it may be useful to pass in the documentation extent
    # TODO: figure out why this isn't using the minima, fix if necessary
    if extent is not None:
        _, _, page_max_x, page_max_y = extent
    else:
        _, _, page_max_x, page_max_y = page_extent(page_easyocr_fragments)

    if isinstance(q_min_x, float):  # assume it was a fraction
        # times a fudge factor because we assume there is right margin
        #    that typically has no detected text,
        #  and we want this to be a fraction to be of the whole page,
        #    not of the _use_ of the page
        q_min_x = q_min_x * (1.15 * page_max_x)
    if isinstance(q_max_x, float):
        q_max_x = q_max_x * (1.15 * page_max_x)
    if isinstance(q_min_y, float):
        q_min_y = q_min_y * page_max_y
    if isinstance(q_max_y, float):
        q_max_y = q_max_y * page_max_y

    matches = []
    for bbox, text, cert in page_easyocr_fragments:

        # if text is being filtered for, see if we need to exclude by that
        if textre is not None:  # up here to quieten the 'out of requested bounds' debug
            if re.search(textre, text):
                if verbose:
                    print("Text %r MATCHES %r" % (text, textre))
            else:
                if verbose:
                    print("Text %r NO match to %r" % (textre, text))
                continue

        frag_min_x, _, frag_min_y, _ = bbox_xy_extent(bbox)
        # if overall position is being filtered for, see if we need to exclude by that
        if q_min_x is not None and frag_min_x < q_min_x:
            if verbose:
                print(
                    "%r min_x %d (%20s) (%20s) is under requested min_x %d"
                    % (text, frag_min_x, bbox, text[:20], q_min_x)
                )
            continue

        if q_max_x is not None and frag_min_x > q_max_x:
            if verbose:
                print(
                    "%r max_x %d (%20s) (%20s) is over requested max_x %d"
                    % (text, frag_min_x, bbox, text[:20], q_max_x)
                )
            continue

        if q_min_y is not None and frag_min_y < q_min_y:
            if verbose:
                print(
                    "%r min_y %d (%20s) (%20s) is under requested min_y %d"
                    % (text, frag_min_y, bbox, text[:20], q_min_y)
                )
            continue

        if q_max_y is not None and frag_min_y > q_max_y:
            if verbose:
                print(
                    "%r max_y %d (%20s) (%20s) is over requested max_y %d"
                    % (text, frag_min_y, bbox, text[:20], q_max_y)
                )
            continue

        # passed everything? keep it in.
        matches.append((bbox, text, cert))

    return matches


def tesseract_plain(image, lang='eng'):
    ''' Run tesseract OCR an image give results as plain text. '''
    import pytesseract
    return pytesseract.image_to_boxes( image, lang=lang )




# We've also tried paddleocr, which seems to be a little more refined,
# but also a bunch more fragile around installation and around GPUs, and also not focused on Dutch



############## Actual OCR part ####################################################################################################################################


def ocr_pdf_pages(pdfbytes, dpi=150, use_gpu=True, page_cache=None, verbose=True):
    """
    This is a convenience function that wraps EasyOCR to get text from all of a PDF document,
    returning it in a per-page, structured way.

    More precisely, it 
     - iterates through a PDF one page at a time,
       - renders that page it to an image,
       - runs EasyOCR's
       - return  result data on that page image.

    This depends on another of our modules (L{pdf}), and pymupdf

    @param page_cache: 
    CONSIDER: allowing cacheing the result of the easyocr calls into a store

    @param dpi: resolution to render the pages at, before OCRing them. Optimal may be around 200ish? (TODO: test)
    @return: a 2-tuple:
      - a list of the results that easyocr_toplaintext() outputs
      - a list of "all text on all pages" strings (specifically, fed through the simple-and-stupid easyocr_toplaintext()).
        Less structure, and redundant with the first returned, but means less typing for some uses.
    """
    import fitz

    results_structure, text = [], []

    if page_cache is not None:
        hashval = wetsuite.helpers.util.hash_hex( pdfbytes )

    with fitz.open(stream=pdfbytes, filetype="pdf") as document:
        for page_num, page in enumerate( document ):
            # if given a cache, return it from there if we can
            if page_cache is not None:
                cache_key = f'{hashval}:easyocr:pg{page_num}:{dpi}dpi'
                page_results_from_cache = page_cache.get( cache_key, missing_as_none=True )
                if page_results_from_cache is not None:
                    if verbose:
                        print('HIT %s'%cache_key)
                    results_structure.append( page_results_from_cache )
                    text.append( easyocr_toplaintext( page_results_from_cache ) )
                    continue
                if verbose:
                    print('MISS %s'%cache_key)

            #  not in cache - render, run OCR
            page_image = wetsuite.extras.pdf.page_as_image( page, dpi=dpi )
            page_results = easyocr(page_image, use_gpu=use_gpu)

            # add to both return structures
            results_structure.append( page_results                      )
            text.append(              easyocr_toplaintext(page_results) )

            # ...and if given a cache, put it in there
            if page_cache is not None:
                page_cache.put(cache_key, page_results)

    return results_structure, text


def easyocr(image, pythontypes=True, use_gpu=True, languages=("nl", "en"), **kwargs):
    """Takes an image, returns structured OCR results as a specific python struct.

    Requires easyocr being installed. Will load easyocr's model on the first call,
    so try to do many calls from a single process to reduce that overhead to just once.

    CONSIDER: pass through kwargs to readtext()
    CONSIDER: fall back to CPU if GPU init fails

    @param image: a single PIL image.

    @param pythontypes:
    if pythontypes==False, easyocr gives you numpy.int64 in bbox and numpy.float64 for confidence,
    if pythontypes==True (default), we make that python int and float for you before returning

    @param use_gpu: whether to use GPU (True), or CPU (False).
    Only does anything on the first call, after that relies on that choice.
    GPU generally is a factor faster than a single CPU core (in quick tests, 3 to 4 times),
    so you may prefer GPU unless you don't have a GPU, don't want runtime competition with other GPU use.

    @param languages: what languages to detect. Defaults to 'nl','en'.
    You might occasionally wish to add 'fr'.

    @return: a list of C{[[topleft, topright, botright, botleft], text, confidence]}
    (which are EasyOCR's results)
    """
    import easyocr  # https://www.jaided.ai/easyocr/documentation/  https://www.jaided.ai/easyocr/

    # use already-loaded model (into the requested place) if it's there
    global _easyocr_reader_gpu
    global _easyocr_reader_cpu
    if use_gpu:
        if _easyocr_reader_gpu is None:
            print( "first use of ocr( use_gpu=True ) - loading EasyOCR model (into GPU)", file=sys.stderr )
            _easyocr_reader_gpu = easyocr.Reader(languages, gpu=True)
        reader = _easyocr_reader_gpu
    else:
        if _easyocr_reader_cpu is None:
            print( "first use of ocr( use_gpu=False ) - loading EasyOCR model (into CPU)", file=sys.stderr )
            _easyocr_reader_cpu = easyocr.Reader(languages, gpu=False)
        reader = _easyocr_reader_cpu

    # convert go grayscale and convert to numpy array,
    # for easyocr (which can take a filename, a numpy array, or byte stream (PNG or JPG?))
    if image.getbands() != "L":
        image = image.convert("L")
    ary = numpy.asarray(image)

    result = reader.readtext(ary, **kwargs)

    if pythontypes:
        ret = []
        for bbox, text, cert in result:
            # bbox looks like [[675, 143], [860, 143], [860, 175], [675, 175]]
            # python types from numpy.int64 resp numpy.float64
            # TODO: move that to the easyocr() call
            bbox = list((int(a), int(b)) for a, b in bbox)
            cert = float(cert)
            ret.append((bbox, text, cert))
        result = ret

    return result


#def easyocr_unload(unload_cpu=True, unload_gpu=True, request_gc=True):
#    " Attempt to in particular, unload the EasyOCR model from the GPU.  It seems that torch won't let us, though? "
#    global _easyocr_reader_gpu,_easyocr_reader_cpu
#    if unload_gpu:
#        if _easyocr_reader_gpu is not None:
#            _easyocr_reader_gpu = None
#            if request_gc:
#                import gc
#                gc.collect()
#            try:
#                # TODO: figure out whether there are further useful things to do
#                import torch
#                torch.cuda.empty_cache()
#            except Exception as e: # swallow all errors
#                pass
#    if unload_cpu:
#        if _easyocr_reader_cpu is not None:
#            _easyocr_reader_cpu = None
#            if request_gc:
#                import gc
#                gc.collect()


def easyocr_toplaintext(results):
    """ Take intermediate results with boxes and, at least for now,
        smushes the text together as-is, without much care about placement.

        This is currently NOT enough to be decent processing,
        and we plan to be smarter than this, given time.

        There is some smarter code in kansspelautoriteit fetching notebook.

        CONSIDER centralizing that and/or 'natural reading order' code

        @param results: the output of ocr()
        @return: plain text
    """
    # CONSIDER making this '\n\n',join( the pages function ) instead
    # warnings.warn('easyocr_toplaintext() is currently dumb, and should be made better at its job later')
    ret = []
    for (_, _, _, _), text, _ in results:
        ret.append(text)

    return "\n".join(ret)  # newline is not always correct, but better than not
