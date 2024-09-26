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


def pdf_text(pdfbytes):
    """Given PDF as a bytestring, return the text it reports to have inside it.
    Expect this to be missing for some PDFs.

    Mostly just a function
    @param pdfbytes: PDF document, as bytes object
    @return: all embedded text, as a single string
    """
    return wetsuite.extras.pdf.doc_text(pdfbytes)


def pdf_text_ocr(pdfbytes):
    """Given PDF as a bytestring, OCRs it and report the text in that.
    Expect this to not be the cleanest.
    @param pdfbytes: PDF document, as bytes object
    @return: a 2-tuple:
      - a list of the results that easyocr_text outputs
      - a list of "all text on a page" string.    
    """
    _, pages_text = wetsuite.extras.ocr.ocr_pdf_pages(
        pdfbytes,
        dpi=150,
    )
    return "\n\n".join(pages_text)


def etree(xmlbytes, strip_namespace=True):
    """ Parse XML in a bytestring to an ET object.
        Mostly just ET.fromstring() with namespace stripping (that you can turn off)
        @param xmlbytes: XML document, as bytes object
        @return: etree root node
    """
    tree = wetsuite.helpers.etree.fromstring(xmlbytes)
    if strip_namespace:
        tree = wetsuite.helpers.etree.strip_namespace(tree)
    return tree


# def urls_for_identifier():
#    'html'
#    'xml'


def known_doc_split(cbytes):
    """ Given a 
    """

def xml_html_text(cbytes):
    """Given XML or HTML, try to give us the interesting text.
    Tries to guess what kind of document it is.

    This is just a 

    @param pdfbytes: PDF document, as bytes object
    @param pdfbytes: PDF document, as bytes object


    """
    if "<?xml" in cbytes[:100]:
        return xml_text(cbytes)
    else:
        return html_text(cbytes)


def html_text(htmlbytes):
    """ Takes a HTML file as a bytestring,
    returns its body text as a string.

    (note: this is also roughly the implementation of wetsuite.helpers.split.Fragments_HTML_Fallback)
    """
    etree = wetsuite.helpers.etree.parse_html(htmlbytes)
    return wetsuite.helpers.etree.html_text(etree, join=True)


def xml_text(xmlbytes):
    """ 
    
    """



_loaded_models = {} # name -> model object    so we can be a little faster than bare load() because it's likely you will call spacy_parse in quick succession

def spacy_parse(text, force_model=None, force_language=None, detection_fallback='nl'):
    '''
    Takes text and returns a spacy document for it.

    By default, it 
    - estimates the language (based on a specific language detectin model)
    - picks an already-installed model of that determined language
    
    In general you might care for the reproducability of explicitly loading a model yourself, 
    but this can be handy in experiments, to parse some fragments of text with less typing.
    
    @param text: string to parse
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
                lang, _score = wetsuite.helpers.spacy.detect_language( text )
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

    return model(text)
