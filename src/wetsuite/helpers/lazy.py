""" Various functions that allow you to be (a little too) lazy - less typing and/or less thinking.

    This module itself is a little creative with many details,
    so don't count its details to stay the same, or on reproducability even if it did.

    In part is actually calls to other parts of wetsuite.
"""
import warnings

import wetsuite.helpers.split
import wetsuite.helpers.etree
import wetsuite.extras.pdf
import wetsuite.extras.ocr


def pdf_embedded_text(pdfbytes:bytes, page_join='\n\n'):
    """Given PDF (as a bytestring), 
        Returns the plain text t reports to have inside it.

        Expect this to be missing for some PDFs;
        read our notebooks explaining why, and the use of 
        wetsuite.extras.pdf and wetsuite.extras.ocr to do better.

        @param pdfbytes: PDF document, as bytes object
        @return: all embedded text, as a single string
    """
    return ( page_join.join(
        wetsuite.extras.pdf.page_embedded_text_generator(pdfbytes)
    ) ).strip() # the strip mostly because there are some documents made entirely of newlines


def pdf_text_ocr(pdfbytes:bytes):
    """Given PDF as a bytestring, OCRs it and report the text in that.
        Expect this to not be the cleanest.
        @param pdfbytes: PDF document, as bytes object
        @return: one string  (pages only introduce a double newline, which you can't really fish out later - 
        if you want more control, you probably wwant to look at the underlying module)
    """
    _, pages_text = wetsuite.extras.ocr.ocr_pdf_pages(
        pdfbytes,
        dpi=150,
    )
    return "\n\n".join(pages_text)


#CONSIDER moving pdf.embedded_or_ocr_perpage here / aliasing

#CONSIDER aliasing feeling_lucky

# def urls_for_identifier():
#    'html'
#    'xml'



def etree(xmlbytes:bytes, strip_namespace=True):
    """ Parse XML in a bytestring to an ET object.
        Mostly just ET's fromstring() plus namespace stripping (that you can turn off)
        @param xmlbytes: XML document, as bytes object
        @return: etree root node
    """
    tree = wetsuite.helpers.etree.fromstring(xmlbytes)
    if strip_namespace:
        tree = wetsuite.helpers.etree.strip_namespace(tree)
    return tree



def html_text(htmlbytes:bytes):
    """ Takes a HTML file as a bytestring, returns its body text as a string.
    This is primarily C{wetsuite.helpers.etree.html_text}.

    Will have some use on XML documents, more so on the subset of XMLs used in Dutch government that it is informed of,
    but if you care for some structure on top of that text, now or later, consider using wetsuite.split.feeling_lucky instead of this.
    """
    tree = wetsuite.helpers.etree.parse_html(htmlbytes)
    return wetsuite.helpers.etree.html_text(tree, join=True)




_loaded_models = {} # name -> model object    so we can be a little faster than bare load() because it's likely you will call spacy_parse in quick succession

def spacy_parse(string, force_model=None, force_language=None, detection_fallback='nl'):
    '''
    Takes text and returns a spacy document for it.

    By default, it 
      - estimates the language (based on a specific language detection model)
      - picks an already-installed model of that determined language
    
    In general you might care for the reproducability of explicitly loading a model yourself, 
    but this can be handy in experiments, to parse some fragments of text with less typing.

    Note also that this would fail if it detects a language you do not have an installed model for; use force_language if you want to avoid that.
    
    @param string: string to parse
    @param force_model: if None, detect model; if not None, load this one
    @param force_language: if None, detect language; if not None, assume this one
    @param detection_fallback: if language detection fails (e.g. because _its_ model was not installed), fall back to use this language
    @return: a Doc of that text
    '''
    import spacy, wetsuite.helpers.spacy
    if force_model is None:

        # establish language
        #print('establish language')
        if force_language is None:
            #print("Detecting language")
            try:
                lang, _score = wetsuite.helpers.spacy.detect_language( string )
            except Exception as e:
                warnings.warn('spacy_parse language detection failed (%s), falling back to %r'%(str(e), detection_fallback))
                lang = detection_fallback
        else:
            lang = force_language

        # establish model
        #print('establish model')
        force_model = wetsuite.helpers.spacy.installed_model_for_language( lang )
    # implied else: you gave us what to load

    if force_model in _loaded_models:
        model = _loaded_models[force_model]
    else:
        model = spacy.load(force_model)
        _loaded_models[force_model] = model

    return model(string)
