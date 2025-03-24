""" Query PDFs about the text objects that they contain (which is not always clean, structured, correct, or present at all)

    If you want clean structured output, 
    then you likely want to put it more work,
    but for a bag-of-words method this may be enough.

    See also ocr.py, and note that we also have "render PDF pages to image"
    so we can hand that to that OCR module.

    TODO: read about natural reading order details at:
    https://pymupdf.readthedocs.io/en/latest/recipes-text.html#how-to-extract-text-in-natural-reading-order
"""

import fitz  # which is pymupdf

import wetsuite.helpers.strings


def perpage_text_generator(filedata: bytes, option="text"):  # TODO: rename to perpage_text_generator
    """Takes PDF file data, yields a page's worth of its EMBEDDED text at a time (is a generator),
    according to the text objects in the PDF stream.

    ...which are essentially a "please render this text", but note that this is not 1:1 
    with the text you see, or as coherent as the way you would naturally read it.
    So it requests sort the text fragments in reading order,
    in a way that is usually roughly right, but is far from perfect.
    """

    with fitz.open(stream=filedata, filetype="pdf") as document:  # open document
        for page in document:
            yield page.get_text(
                option=option, sort=True
            )  # sort only applies to some options


def doc_text(filedata: bytes, strip=True, join_on='\n\n'):
    """Takes PDF file data, returns all EMBEDDED text in it as a single string

    Mostly just puts some newlines (by default) 
    between the chunks that perpage_text_generator() outputs,
    so this has as few guarantees about clean output as it.

    @param filedata: PDF file data as a bytes object
    @param strip: whether to strip after joining.
    @return: all text as a single string.
    """
    ret = join_on.join( perpage_text_generator(filedata) )
    if strip:
        ret = ret.strip()
    return ret


_html_header_tag_names = ("h1", "h2", "h3", "h4", "h5", "h6")


#def page_fragmentss(page: fitz.Page):


def document_fragments(filedata: bytes, hint_structure=True, debug=True):
    '''
    Tries to be slightly smarter than perpage_text_generator,
    making it slightly easier to see paragraphs and _maybe_ headings.
    
    @param hint_structure: 
      - if True, return the structure internal to this function 
      - if False, returns a text string.

    @return: a list of strings  (note that split.Fragments_PDF_Fallback relies on that)
    '''
    import bs4
    ret = []

    part_name = ""
    part_ary  = []

    def marker_now(hint):
        ret.append(({"hints": [hint]}, {}, ""))

    def flush(hint_first=None):
        "any parts of part_ary are"
        #global part_ary, part_name
        nonlocal part_ary, part_name
        # if hint_first:
        #    ret.append( ( {'hints':[hint_first]},   {},   '') )

        pa = list(
            filter(lambda x: len(x.strip()) > 0, part_ary)
        )  # remove empty-text elements from part_ary
        if len(pa) > 0:
            for i, frag in enumerate(pa):
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
    with fitz.open(stream=filedata, filetype="pdf") as document:

        bupless = 0

        # for page_results in wetsuite.extras.pdf.perpage_text_generator(docdata, option='xhtml'):

        for page in document:
            flush()
            marker_now("newpage")

            # TODO: move to use 'html' rather than 'xhtml' because it lets us do more.

            page_results = page.get_text(
                option="xhtml",
                flags=fitz.TEXTFLAGS_XHTML & ~fitz.TEXT_PRESERVE_IMAGES,
            )

            soup = bs4.BeautifulSoup(page_results, features="lxml")
            div = soup.find("div")
            #if debug:
            #    print(div)
            for elem in div.children:
                if isinstance(elem, bs4.NavigableString):
                    if len(elem.string.strip()) > 0:
                        if debug:
                            print("TopText %r" % elem.string)
                else:
                    # if elem.find('img'):# assumes
                    #    continue

                    # bold can mean a header -- but not if everything in an area is
                    # also, just an isolated (bolded) number in a paragraphs does not mean much
                    b = elem.find("b")
                    bupwish = (  b is not None  and   b.string is not None  and not wetsuite.helpers.strings.is_numeric( b.string ) )  

                    if elem.name in _html_header_tag_names: # seems like header; flush it into our structure that way
                        flush()
                        part_name = " ".join(elem.find_all(string=True))
                        flush(hint_first="header")
                    else:
                        if bupwish:
                            if bupless > -1 and bupwish:
                                flush(hint_first="bold")
                            bupless = 0
                        else:  # bupless is about not triggering on areas of everything-bold
                            bupless += 1

                    text = " ".join(elem.find_all(string=True))
                    part_ary.append(text)

        flush()
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







###############################################################################################################


def pages_as_images(filedata, dpi=150):
    """Yields one page of the PDF at a time, as a PIL image object.

    Made to be used byL{ pdf_text_ocr}, but you may find use for it too.

    Depends on PyMuPDF (CONSIDER: leaving in the fallback to poppler).

    @param filedata: PDF file contents, as a bytes object
    @param dpi: the resolution to render at.  
    Higher is slower, and not necessarily much better; in fact there are cases where higher is worse.
    150 to 200 seems a good tradeoff.
    @return: a generator yielding images, one page at a time (because consider what a 300-page PDF would do to RAM use)
    """
    # pymupdf
    from PIL import Image
    import fitz  # (PyMuPDF)

    with fitz.open(stream=filedata, filetype="pdf") as document:
        for page in document:
            page_pixmap = page.get_pixmap(dpi=dpi)
            im = Image.frombytes(
                mode="RGB",
                size=[page_pixmap.width, page_pixmap.height],
                data=page_pixmap.samples,
            )
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



def pdf_text_ocr(filedata: bytes, use_gpu=True):
    """Takes a PDF and return pageless plain text, entirely with OCR (instead of PDF objects).

    This is currently
      - wetsuite.datacollect.pdf.pages_as_images()
      - wetsuite.extras.ocr.easyocr()
    and is also:
      - slow (might take a minute or two per document) - consider cacheing the result
      - not clever in any way
    so probably ONLY use this if
      - extracting text objects (e.g. wetsuite.datacollect.pdf.perpage_text_generator) gave you nothing
      - you only care about what words exist, not about document structure

    @param filedata:
    @return: all text, as a single string.
    """
    ret = []

    import wetsuite.extras.ocr

    for page_image in pages_as_images(filedata):
        fragments = wetsuite.extras.ocr.easyocr(page_image, use_gpu=use_gpu)
        for _, text_fragment, _ in fragments:
            ret.append(text_fragment)
    return " ".join(ret)



def embedded_or_ocr_perpage(pdfbytes: bytes, dpi=150):
    ''' For a PDF, walk through its pages
         - if it reports having text, use that text
         - if it does not report having text, render it as an image and run OCR

        ...and relies on our own wetsuite.extras.ocr to do so. 

        This is meant to balance the speed/precision of embedded text,
        with the thoroughness of "there are documents that then go on with scans, 
        get best-effort results for that that."

        CONSIDER: cacheing results (based on hash of image?)

        CONSIDER: rewriting this after restructuring the ocr interface.
    '''
    from PIL import Image
    ret = []
    with fitz.open(stream=pdfbytes, filetype="pdf") as document:  # open document
        for page_i, page in enumerate(document):
   
            # See if it reports as 
            embedded_text = page.get_text( option='text', sort=True )

            if len(embedded_text.strip()) > 0: # TODO: better text
                #print ('PAGE %d EMBEDDED'%page_i)
                ret.append( embedded_text )
                #print ('   len %d '%len(embedded_text), embedded_text )
            else:
                #print ('PAGE %d OCR   (text was %r)'%(page_i, embedded_text))
                # Render page to image,
                page_pixmap = page.get_pixmap(dpi=dpi)
                im = Image.frombytes(
                    mode="RGB",
                    size=[page_pixmap.width, page_pixmap.height],
                    data=page_pixmap.samples,
                )
                # hand to OCR,
                structured_intermediate = wetsuite.extras.ocr.easyocr( im )
                # flatten OCR structure to plain text
                text = wetsuite.extras.ocr.easyocr_text( structured_intermediate )
                ret.append( text )
                #print ('   len %d '%len(text), text )

    return ''.join( ret )




###############################################################################################################


def count_pages_with_text(filedata_or_list, char_threshold=200):
    """Counts the number of pages that have a reasonable amount of EMBEDDED text on them.

    Intended to help detect PDFs that are partly or fully images-of-text instead.

    Counts characters per page plus spaces between words, but strips edges;
    TODO: think about this more

    @param filedata_or_list: either:
      - PDF file data (as bytes)
      - the output of pages_text()
    @param char_threshold: how long the text on a page should be, in characters, after strip()ping.
    Defaults to 200, which is maybe 50 words.
    @return: (list_of_number_of_chars_per_page, num_pages_with_text, num_pages)
    """
    if isinstance(filedata_or_list, bytes):
        it = perpage_text_generator(filedata_or_list)
    else:
        it = filedata_or_list

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
    ( "Letter", 612, 792, ),  # (~215.9 x 279.4mm,   8.5 x 11",     612 × 792 pt )
)


def do_page_sizes_vary(document, allowance_pt=36):
    ''' Given a parsed pymupdf document object,
        tells us whether the pages (specifically their CropBox) vary in size at all.

        Meant to help detect PDFs composited from multiple sources.
    '''
    ws, hs = [], []
    numpages = 0
    for page in document:
        ws.append(page.cropbox.x1)  # -x0?
        hs.append(page.cropbox.y1)  # -y0?
        numpages += 1

    if numpages == 0:
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


def closest_paper_size_name(box, within_pt=36.0):
    """ Given a pymupdf box, tells you 
          - the name of the size (currently 'A4', 'Letter', or 'other')
          - whether it's in portrait or landscape.
          - the size mismatch to that size (up to within_pt) 
           
        @return: something like ('A4','portrait', 1, 0)
        where those numbers are the width and height difference in pt
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

