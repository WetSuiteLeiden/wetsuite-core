''' Query PDFs about the text objects that they contain (which is not always clean, structured, correct, or present at all)

    If you want clean structured output, 
    then you likely want to put it more work,
    but for a bag-of-words method this may be enough.

    See also ocr.py, and note that we also have "render PDF pages to image"
    so we can hand that to that OCR module.

    TODO: read about natural reading order details at:
    https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-text-in-natural-reading-order
'''



def page_text( filedata:bytes, option='text' ):
    """ Takes PDF file data, yields a page's worth of its text at a time (is a generator),
        according to the text objects in the PDF stream.

        ...which are essentially the "please render this text" requests it contains,
        but note that this is not 1:1 with the text you see, or as coherent as the text you see.
        
        Tries to sort the text fragments in reading order, 
        in a way that is usually roughly right, but is far from perfect.
    """
    import fitz # which is pymupdf
    with fitz.open( stream=filedata, filetype="pdf") as document:  # open document
        for page in document:
            yield page.get_text( option=option, sort=True ) # sort only applies to some options



def doc_text( filedata:bytes, strip=True ):
    ''' Takes PDF file data, returns a single string of the text in it.   
        Mostly just puts some newlines between the chunks that page_text() outputs. 
        
        @param filedata: PDF file data as a bytes object
        @param strip: whether to strip after joining.
        @return: all text as a single string.
    '''
    ret = '\n\n'.join( page_text( filedata ) )
    if strip:
        ret = ret.strip()
    return ret


def count_pages_with_text( filedata_or_list, char_threshold=200 ):
    """ Counts the number of pages that have a reasonable amount of text on them.

        Mainly intended to detect PDFs that are partly or fully images-of-text.

        Counts characters per page counts spaces between words, but strips edges; 
        TODO: think about this more

        @param filedata_or_list: either: 
          - PDF file data (as bytes) 
          - the output of pages_text()
        @param char_threshold: how long the text on a page should be, in characters, after strip()ping. 
        Defaults to 200, which is maybe 50 words.
        @return: (chars_per_page, num_pages_with_text, num_pages)
    """
    if isinstance(filedata_or_list, bytes):
        it = page_text(filedata_or_list)
    else:
        it = filedata_or_list

    chars_per_page = []
    count_pages = 0
    count_pages_with_text_count  = 0

    for page in it:
        count_pages += 1

        chars_per_page.append( len(page.strip() ))
        if len(page.strip()) >= char_threshold:
            count_pages_with_text_count += 1

    return chars_per_page, count_pages_with_text_count, count_pages


_page_sizes = (
    ('A4',     595, 842, ), # (   210x297mm,    8.3x11.7")
    ('Letter', 612, 792, ), # (~215.9x279.4mm,  8.5x11")
)

def _is_within(test, nearthis, within):
    amtdiff = abs(test-nearthis)
    return amtdiff <= within, amtdiff


def do_page_sizes_vary(document, allowance_pt = 36):
    ws, hs = [], []
    numpages = 0
    for page in document:
        ws.append( page.cropbox.x1 ) # -x0?
        hs.append( page.cropbox.y1 ) # -y0?
        numpages += 1
    
    if numpages==0:
        return False
    else:
        ws.sort()
        hs.sort()
        wdiff = abs(ws[0] - ws[-1])
        hdiff = abs(hs[0] - hs[-1])
        if wdiff < allowance_pt and hdiff < allowance_pt:
            return False, wdiff, hdiff
        else:
            return True, wdiff, hdiff


def closest_paper_size_name( box, within_pt=36. ):
    " expects a pymupdf box, returns something like ('A4','portrait', 1, 0)  where those numbers are the width and height difference in pt "
    import fitz
    if isinstance(box, fitz.Page):
        import warnings
        warnings.warn( 'closest_paper_size_name defaulting to page.cropbox, you should probably do that explicitly')
        box = box.cropbox

    box_w_pt,box_h_pt = box.x1, box.y1   # - x0, y0?
    ret = []
    for size_name, size_width_pt, size_height_pt in _page_sizes:
        # TODO: check this is correct at all, whether we should look to page.rotation_matrix instead
        por_w_is, por_w_diff = _is_within(box_w_pt, size_width_pt, within_pt)
        por_h_is, por_h_diff = _is_within(box_h_pt, size_height_pt, within_pt)
        lnd_w_is, lnd_w_diff = _is_within(box_w_pt, size_height_pt, within_pt)
        lnd_h_is, lnd_h_diff = _is_within(box_h_pt, size_width_pt, within_pt)

        if por_w_is and por_h_is:
            ret.append( (size_name, 'portrait', por_w_diff, por_h_diff) )
        if lnd_w_is and lnd_h_is:
            ret.append( (size_name, 'landscape', lnd_w_diff, lnd_h_diff) )
        # maybe also consider equal/square?

    ret.sort(key=lambda l: l[2]+l[3])
    if len(ret)>0:
        return ret[0]
    else:
        ori = 'landscape'
        if box_h_pt > box_w_pt:
            ori = 'portrait'
        return ('other',ori, None,None )


def pdf_text_ocr(filedata: bytes):
    ''' Takes a PDF and return pageless plain text, entirely with OCR (instead of PDF objects).

        This is currently
          - wetsuite.datacollect.pdf.pages_as_images()
          - wetsuite.extras.ocr.easyocr()
        and is also:
          - slow (might take a minute or two per document) - consider cacheing the result
          - not clever in any way
        so probably ONLY use this if  
          - extracting text objects (e.g. wetsuite.datacollect.pdf.page_text) gave you nothing
          - you only care about what words exist, not about document structure

        @param filedata:
        @return: all text, as a single string.
    '''
    ret = []

    import wetsuite.extras.ocr
    for page_image in pages_as_images(filedata):
        fragments = wetsuite.extras.ocr.easyocr( page_image )
        for _, text_fragment, _ in fragments:
            ret.append( text_fragment )
    return ' '.join( ret )


def pages_as_images( filedata, dpi=150 ):
    """ Yields one page of the PDF at a time, as a PIL image object.

        Made to be used byL{ pdf_text_ocr}, but you may find use for it too.
    
        Depends on PyMuPDF (CONSIDER: leaving in the fallback to poppler).

        @param filedata: PDF file contents, as a bytes object
        @param dpi: the resolution to render at
        @return: a generator, one page at a time, because consider what a 300-page PDF would do to RAM use.
    """
    #pymupdf
    from PIL import Image
    import fitz   # (PyMuPDF)

    with fitz.open( stream=filedata, filetype="pdf") as document:
        for page in document:
            page_pixmap = page.get_pixmap(dpi=dpi)
            im = Image.frombytes(mode='RGB',
                                 size=[page_pixmap.width, page_pixmap.height],
                                 data=page_pixmap.samples)
            yield im

    # else:
    #     import poppler
    #     dpi = int(dpi)
    #     pdf_doc = poppler.load_from_data( filedata )
    #     num_pages = pdf_doc.pages # zero-based

    #     pr = poppler.PageRenderer() # I'm not sure the python wrapper can be told to use another pixel format?

    #     for page_num in range(num_pages):
    #         page = pdf_doc.create_page(page_num)

    #         if antialiasing:
    #             try:
    #                 import poppler.cpp.page_renderer
    #                 pr.set_render_hint( poppler.cpp.page_renderer.render_hint.text_antialiasing, True)
    #             except Exception as e: # who knows when and why this might break
    #                 warnings.warn('set-antialiasing complained: %s'%str(e))
    #                 pass
    #         poppler_im = pr.render_page( page, xres=dpi, yres=dpi )
    #         pil_im = Image.frombytes( "RGBA",  (poppler_im.width, poppler_im.height), poppler_im.data, "raw", str(poppler_im.format), )
    #         yield pil_im
