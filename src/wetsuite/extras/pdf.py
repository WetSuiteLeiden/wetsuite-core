""" Query PDFs about the text objects that they contain (which is not always clean, structured, correct, or present at all)

    If you want clean structured output, 
    then you likely want to put it more work,
    but for a bag-of-words method this may be enough.

    See also ocr.py, and note that we also have "render PDF pages to image"
    so we can hand that to that OCR module.

    TODO: read about natural reading order details at:
    https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-text-in-natural-reading-order
"""

import wetsuite.helpers.etree
import wetsuite.helpers.strings
import wetsuite.helpers.util


################ Helpers #############################################################################

def page_embedded_as_xhtml(page):
    ''' Extracts fragments using PyMuPDF's xhtml-style extraction, 
        which analyzed some basic paragraphs and headers so that we don't have to 
        (but also removed the low-level information it based that off)

        @param page: pymupdf page object
        @return:
    '''
    import fitz  # which is pymupdf
    import bs4
    page_results = page.get_text(
        option="xhtml",
        flags=fitz.TEXTFLAGS_XHTML & ~fitz.TEXT_PRESERVE_IMAGES,
    )
    soup = bs4.BeautifulSoup(page_results, features="lxml")
    div = soup.find("div")
    return div


# def _page_fakehocr(page, under_etree_node, page_num):
#     import fitz  # which is pymupdf
#     SE = wetsuite.helpers.etree.SubElement  # for brevity
# 
#     pagediv = SE(under_etree_node, 'div', {
#         'class':  'ocr_page', 
#         'id':    f'page_{page_num+1}',
#         'title': 'bbox %d %d %d %d'%(page.cropbox.x0, page.cropbox.y0, page.cropbox.x1, page.cropbox.y1)
#         })
#     
#     word_results = page.get_text(
#         option="words",
#         flags=fitz.TEXTFLAGS_WORDS & ~fitz.TEXT_PRESERVE_IMAGES,
#     )
# 
#     prev_block_no = -1
#     for x0, y0, x1, y1, word, block_no, line_no, word_no in word_results:
# 
#         if prev_block_no != block_no:
#             #<p class="ocr_par" id="par_1_1" lang="eng" title="bbox 374 74 947 103">
#             # TODO: figure out easy way to give bbox
#             par = SE(pagediv, 'p', {
#                 'class':  'ocr_par',
#                 'id':    f'par_{page_num}_{block_no}',
#             })
# 
#         # <span class="" id="word_1_1" title="bbox 374 74 520 103; x_wconf 91">BIROUL</span>
#         wordspan = SE(par, 'span', {
#             'class': 'ocrx_word',
#             'id':   f'word_{page_num}_{block_no}_{line_no}_{word_no}',
#             'title': 'bbox %d %d %d %d'%(round(x0), round(y0), round(x1), round(y1))
#         })
#         wordspan.text = word
# 
#         prev_block_no = block_no


# def fakehocr(document):
#     """ Yes, we are generating hOCR from what is already PDF text.
#         In general this makes no sense - where would we take that data?
# 
#         It's primarily so that we can have a common (internal-ish) format between
#         OCR and PDF within this project.
# 
#         TODO: I think I got the y coordinates flipped, CHECK
#     """
#     import fitz
#     E,SE = wetsuite.helpers.etree.Element, wetsuite.helpers.etree.SubElement  # for brevity
# 
#     html = E( 'html', {'lang':'en'} )
# 
#     head = SE(html, 'head')
#     SE(head, 'title')
#     SE(head, 'meta', {'name':'ocr-number-of-pages', 'content':str(len(document))})
#     SE(head, 'meta', {'name':'ocr-system', 'content':'pymupdf by proxy'})
#     SE(head, 'meta', {'name':'ocr-capabilities', 'content':'ocr_page ocr_par ocrx_word'})
#     # skipped for now:  ocr_carea (content area), ocr_par (paragraph),  ocr_line (line)
# 
#     body = SE(html, 'body')
# 
#     for page_num, page in enumerate(document):
#         _page_fakehocr(page, body, page_num)
# 
#     return wetsuite.helpers.etree.tostring(html)



# def page_embedded_as_html(page):
#     ''' Extracts fragments using PyMuPDF's html-style extraction, 
#         which lets us do more than page_embedded_as_xhtml, but with more work
# 
#         Not currently used.
# 
#         @param page: pymupdf page object
#     '''
#     import fitz  # which is pymupdf
#     import bs4
#     page_results = page.get_text(
#         option="html",
#         flags=fitz.TEXTFLAGS_HTML & ~fitz.TEXT_PRESERVE_IMAGES,
#     )
#     soup = bs4.BeautifulSoup(page_results, features="lxml")
#     div = soup.find("div")
#     return div



def page_as_image(page, dpi=150):
    ''' Takes a single pymupdf Page object, and renders it as a PIL color Image at a specific resolution '''
    from PIL import Image
    page_pixmap = page.get_pixmap(dpi=dpi)
    im = Image.frombytes(
        mode="RGB",
        size=[page_pixmap.width, page_pixmap.height],
        data=page_pixmap.samples,
    )
    return im


def _open_pdf(pdf):
    """ 
    helper function that lets varied functions deal with being given one of
      - an already-opened pymupdf Document
      - PDF file as bytes 
      - CONSIDER: or a filename
    """
    import fitz  # (PyMuPDF)
    if isinstance( pdf, fitz.fitz.Document ):
        return pdf
    elif isinstance( pdf, bytes ):
        #if pdf.startswith('%PDF')
        return fitz.open( stream=pdf, filetype='pdf' )
        #else:
        #    raise ValueError("given byte sequence does not seem like a PDF")

    else:
        raise ValueError("Don't know what to do with argument of type %s"%type(pdf))


def pages_as_images(pdf, dpi=150):
    """Takes PDF byte document, yields one page at a time as a PIL image object.

    @param pdf: PDF file contents as a bytes object, or an already-opened fitz Document
    @param dpi: the resolution to render at.  
    Higher is slower, and not necessarily much better; in fact there are cases where higher is worse.
    150 to 200 seems a good tradeoff.
    @return: a generator yielding images, one page at a time (because consider what a 300-page PDF would do to RAM use)
    """
    document = _open_pdf( pdf )
    for page in document:
        im = page_as_image(page, dpi=dpi)
        yield im




def count_pages_with_embedded_text(pdf, char_threshold=200):
    """Counts the number of pages that have a reasonable amount of embedded text on them.

    Intended to help detect PDFs that are partly or fully images-of-text instead.

    Counts characters per page plus spaces between words, but strips edges;
    TODO: think about that more.

    @param pdf: either:
      - PDF file data (as bytes)

      - the output of page_embedded_text_generator()
    @param char_threshold: how long the text on a page should be, in characters, after strip()ping.
    Defaults to 200, which is maybe 50 words.
    @return: (list_of_number_of_chars_per_page, num_pages_with_text, num_pages)
    """
    import types
    if isinstance(pdf, (types.GeneratorType,   # inspect technically has a better answer
                        list,tuple,
                        )):
        it = pdf
    else:
        document = _open_pdf( pdf )
        it = page_embedded_text_generator( document )

    chars_per_page = []
    count_pages = 0
    count_pages_with_text_count = 0

    for page in it:
        count_pages += 1

        chars_per_page.append(len(page.strip()))
        if len(page.strip()) >= char_threshold:
            count_pages_with_text_count += 1

    return chars_per_page, count_pages_with_text_count, count_pages


_page_sizes = (
    ( "A4",     595, 842, ),  # (   210 x 297mm,     8.3 x 11.7",   595 x 842 pt)
    ( "Letter", 612, 792, ),  # (~215.9 x 279.4mm,   8.5 x 11",     612 × 792 pt)
)


def do_page_sizes_vary(pdf, allowance_pt=36):
    ''' Given a parsed pymupdf document object,
        tells us whether the pages (specifically their CropBox) vary in size at all.

        Meant to help detect PDFs composited from multiple sources.

        @param pdf: the document under test (as bytes, already-parsed Document object)
        @param allowance_pt: the maximum height or width difference between largest and smallest, in pt (default is 36, which is ~12mm)
        @return: a 3-tuple: ( whether there is more than allowance_pt difference, amount of width difference, amount of height difference )
    '''
    document = _open_pdf( pdf )

    ws, hs = [], []
    numpages = 0
    for page in document:
        ws.append(page.cropbox.x1)  # -x0?
        hs.append(page.cropbox.y1)  # -y0?
        numpages += 1

    if numpages == 0:
        return False, 0, 0
    else:
        ws.sort()
        hs.sort()
        wdiff = abs(ws[0] - ws[-1])
        hdiff = abs(hs[0] - hs[-1])
        if wdiff < allowance_pt and hdiff < allowance_pt:
            return False, wdiff, hdiff
        else:
            return True, wdiff, hdiff


def closest_paper_size_name(box, within_pt=36.0):
    """ Given a pymupdf Box, tells you the name of the size, and orientation.
           
        @param box: a pymupdf Box, e.g. a_page.cropbox

        @param within_pt: the amount of size it may be off.
        (Default is 36pt, which is ~12mm, 0.5 inch, which is perhaps overly flexible)

        @return: something like ('A4','portrait', 1,0), which is:
          - the name of the size (currently 'A4', 'Letter', or 'other')
          - whether it's in 'portrait' or 'landscape'
          - the size mismatch to that size, width-wise and height-wise 
            (if name is not 'other', this will be lower than within_pt) 
    """
    def _is_within(test, nearthis, within):
        ' whether two numbers are less than some amount apart '
        amtdiff = abs(test - nearthis)
        return amtdiff <= within, amtdiff

    import fitz

    if isinstance(box, fitz.Page):
        import warnings
        warnings.warn( "closest_paper_size_name given a Page; defaulting to select page.cropbox, you should probably do that explicitly" )
        box = box.cropbox

    box_w_pt, box_h_pt = box.x1, box.y1  # - x0, y0?
    ret = []
    for size_name, size_width_pt, size_height_pt in _page_sizes:
        # TODO: check this is correct at all, whether we should look to page.rotation_matrix instead
        por_w_is, por_w_diff = _is_within(box_w_pt, size_width_pt, within_pt)
        por_h_is, por_h_diff = _is_within(box_h_pt, size_height_pt, within_pt)
        lnd_w_is, lnd_w_diff = _is_within(box_w_pt, size_height_pt, within_pt)
        lnd_h_is, lnd_h_diff = _is_within(box_h_pt, size_width_pt, within_pt)

        if por_w_is and por_h_is:
            ret.append((size_name, "portrait", por_w_diff, por_h_diff))
        if lnd_w_is and lnd_h_is:
            ret.append((size_name, "landscape", lnd_w_diff, lnd_h_diff))
        # maybe also consider equal/square?

    ret.sort(key=lambda l: l[2] + l[3])
    if len(ret) > 0:
        return ret[0]
    else:
        ori = "landscape"
        if box_h_pt > box_w_pt:
            ori = "portrait"
        return ("other", ori, None, None)



################ Extracting embedded text #############################################################################################


def page_embedded_text_generator(pdf, option="text"):
    """Takes PDF file data, yields a page's worth of its embedded text at a time (is a generator),
    according to the text objects in the PDF stream.

    ...which are essentially a "please render this text", but note that this is not 1:1 
    with the text you see, or as coherent as the way you would naturally read it.
    So it requests sort the text fragments in reading order,
    in a way that is usually roughly right, but is far from perfect.

    Note that this is comparable with page_embedded_as_xhtml(); 
    under the covers it is almost the same call but asks the library for plain text instead.
    """
    document = _open_pdf( pdf )
    for page in document:
        yield page.get_text( option=option, sort=True )  # note that sort only applies to some option choices


# def doc_embedded_text(pdf, strip:bool=True, join_on:str='\n\n'): # TODO: rename to embedded_text
#     """Takes PDF file data, returns all embedded text in it as a single string
#     
#     This is a convenience function in that it's primarily just::
#             '\n\n'.join( page_embedded_text_generator( pdf) )
# 
#     @param pdf: PDF file data as a bytes object (or already-parsed fitz Document object)
#     @param strip: whether to strip after joining.
#     @return: all text as a single string.
#     """
#     document = _open_pdf( pdf )
#     # CONSIDER: also taking a fitz document
#     ret = join_on.join( page_embedded_text_generator( document ) )
#     if strip:
#         ret = ret.strip()
#     return ret



def page_embedded_fragments(page, join=True):
    ''' Quick 'get fragments of text from a page', 
        relying on some pymupdf analysis.

        Note: does less processing than document_fragments, and defaults to a simpler output 
        (string or list of strings, not the hint structure that document_fragments gives)
        CONSIDER: making them work the same

        @param page: pymupdf page object
        @param join: If false, we return a string of lists. 
                     If True, we return a string.
        @return: a single string (often with newlines), or a list of parts.
    '''
    div = page_embedded_as_xhtml( page )
    return wetsuite.helpers.etree.html_text(div, bodynodename=None, join=join)




_html_header_tag_names = ("h1", "h2", "h3", "h4", "h5", "h6")

def document_fragments(pdf, hint_structure=True, debug=True):
    '''
    Tries to be slightly smarter than page_embedded_text_generator,
    making it slightly easier to see paragraphs and _maybe_ headings.
    
    Set up to do some more analysis (than e.g. page_embedded_fragments),

    Note that this is the implementation of split.Fragments_PDF_Fallback,
    so when changing things, consider side effects there.
    
    @param hint_structure: 
      - if True, return the structure internal to this function
      - if False, returns a text string.

    @return: 
      - a list of strings, or 
      - a list of (hintdict, emptydict, textfragment)   (the empty dict is for drop-in use in the split module)
    '''
    document = _open_pdf( pdf )
    #import fitz  # which is pymupdf
    import bs4
    ret = []

    part_name = ""
    part_ary  = []

    def marker_now(hint):
        ret.append(({"hints": [hint]}, {}, ""))

    def flush_section(hint_first=None):
        "any parts of part_ary are"
        #global part_ary, part_name
        nonlocal part_ary, part_name
        # if hint_first:
        #    ret.append( ( {'hints':[hint_first]},   {},   '') )

        temp_collect = list(
            filter(lambda x: len(x.strip()) > 0,  part_ary)
        )  # remove empty-text elements from part_ary
        if len(temp_collect) > 0:
            for i, frag in enumerate(temp_collect):
                if i == 0 and hint_first is not None:
                    hint = hint_first
                else:
                    hint = "+para"
                ret.append(
                    ({"hints": [hint], "lastheader": part_name}, {}, frag)
                )
        part_name = ""
        part_ary  = []

    #CONSIDER: move this to its own function in wetsuite.extras.pdf  (also so we can cache it)

    #bupless = 0

    # for page_results in wetsuite.extras.pdf.page_embeded_text_generator(docdata, option='xhtml'):

    for page in document:
        #flush_section()
        marker_now("newpage")

        div = page_embedded_as_xhtml( page )
        # We now have something like:
        #  <div id="page0">
        #   <h2>I am Sam</h2>
        #   <p>Dr. Seuss</p>
        #   <p>1960</p>
        #   <p>I do not like green eggs and ham.</p>
        #   <p>1</p>
        #  </div>

        # we can post-process that a little - though this is and endless set of possible touchups,
        #   and may wish to first review what input to best do that with
        for elem in div.children:
            if isinstance(elem, bs4.NavigableString):
                pass # top-level text is just indentation, I think?
                #if len(elem.string.strip()) > 0:
                #    if debug:
                #        print("TopText %r" % elem.string)
            else:

                # bold can indicate a header-like thing -- but not if everything in an area is bold
                # also, just an isolated (bolded) number in a paragraphs does not mean much
                #b = elem.find("b")
                #bupwish = (  b is not None  and   b.string is not None  and not wetsuite.helpers.strings.is_numeric( b.string ) )
                # if we have a <b> with string content (that isn't just numeric)

                #print(elem.name, _html_header_tag_names, elem.name in _html_header_tag_names)
                if elem.name in _html_header_tag_names: # seems like header (h1..h6); flush it into our structure that way
                    #flush_section()
                    flush_section(hint_first="header")
                    part_name = ''.join( wetsuite.helpers.etree.html_text(elem) ) # probably overkill
                    #part_name = " ".join( elem.find_all(string=True) )
                #else:
                #    if bupwish:
                #        if bupless > -1 and bupwish:
                #            flush_section(hint_first="bold")
                #        bupless = 0
                #    else:  # bupless is about not triggering on areas of everything-bold
                #        bupless += 1

                # TODO: see if wetsuite.helpers.etree.html_text() makes more sense
                #text = " ".join(elem.find_all(string=True))
                text = ''.join( wetsuite.helpers.etree.html_text(elem))
                part_ary.append( text )
                #print(elem, text)

    flush_section()
    marker_now("end")

    if hint_structure == True:
        return ret
    else:
        text_ary = []
        for meta, _, text_fragment in ret:
            if '+para' in meta['hints']:
                text_ary.append('\n')

            text_ary.append( text_fragment )

            text_ary.append('\n')
        return text_ary


######### Involving OCR ################################################################################################################


def pdf_text_ocr(filedata: bytes, use_gpu=True):
    """Use only OCR to process a PDF (note attempt to use text from PDF objects).

    Mostly a call into wetsuite.extras.ocr, and so relies on it

    This is currently
      - wetsuite.datacollect.pdf.pages_as_images()
      - wetsuite.extras.ocr.easyocr()
    and is also:
      - slow (might take a minute or two per document) - consider cacheing the result
      - not clever in any way
    so probably ONLY use this if
      - extracting text objects (e.g. page_embedded_text_generator) gave you nothing
      - you only care about what words exist, not about document structure

    @param filedata:
    @return: all text, as a single string.
    """
    import wetsuite.extras.ocr

    ret = []
    for page_image in pages_as_images( filedata ):
        fragments = wetsuite.extras.ocr.easyocr( page_image, use_gpu=use_gpu )
        for _, text_fragment, _ in fragments:
            ret.append( text_fragment )
    return " ".join(ret)



def embedded_or_ocr_perpage(pdf, char_threshold:int=30, dpi:int=150, cache_store=None, use_gpu=False):
    ''' For a PDF, walk through its pages
          - if it reports having text, use that text
          - if it does not report having text, render it as an image and run OCR
        ...and relies on our own wetsuite.extras.ocr to do so. 

        Relies on wetsuite.extras.ocr

        compare with
          - pdf_text_ocr(), which applies OCR to all pages

        
        For context:
        
        When given a PDF, you can easily decide to 
          - get all embedded text (and might OCR some empty pages),
            in which case page_embedded_text_generator() does most of what you want,
            which is fast, and as precise as that embedded text is.
          - OCR all pages
            in which case wetsuite.extras.ocr.easyocr and .easyocr_toplaintext() might do what you want.
          
        The limitation to that is that you generally don't know what is in a PDF so 
          - need to write that fallback (just a few lines)
          - if you OCR for thoroughness, you might end up getting a lower-quality OCR
            for pages that already contained good quality text
          - you still can't deal with PDFs that are composited from 
            sources that contain embedded text as well as images of text,
            which are relatively rare, but definitely happen.

        This is mostly a convenience function to make your life simpler: 
        it does that fallback, and it does it per PDF page. 

        This should be a decent balance of fast and precise when we have embedded text,
        and best-effort for pages that might contain images of text.

        CONSIDER: rewriting this after restructuring the ocr interface.

        @return: a list (one item for each page) of 2-tuples (first is 'embedded' or 'ocr', second item is the flattened text)
    '''
    document = _open_pdf( pdf )

    import wetsuite.extras.ocr
    ret = []
    for page_i, page in enumerate(document):

        # See if it reports as containing embedded text; if so, use that.
        embedded_text = page.get_text( option='text', sort=True )
        if len(embedded_text.strip()) > char_threshold: # TODO: better test
            ret.append( ('embedded', embedded_text) )

        else: # if no embedded text, use OCR
            im = page_as_image( page, dpi=dpi ) # Render page to image,
            structured_intermediate = wetsuite.extras.ocr.easyocr( im, use_gpu=use_gpu ) # hand to OCR
            text = wetsuite.extras.ocr.easyocr_toplaintext( structured_intermediate ) # flatten OCR structure to plain text
            ret.append( ('ocr', text) )

    return ret
