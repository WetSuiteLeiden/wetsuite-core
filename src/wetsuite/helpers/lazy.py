''' Various functions that allow you to be (a little too) lazy.
    This module itself is a little loosey with the details, don't count on details to stay the same.

    In part is actually calls to other parts
'''

import wetsuite.extras.pdf
import wetsuite.extras.ocr
import wetsuite.helpers.etree



def pdf_text(pdfbytes):
    ''' Given PDF as a bytestring, return the text it reports to have inside it. 
        Expect this to be missing for some PDFs.

        Mostly just a function 
    '''
    return wetsuite.extras.pdf.doc_text( pdfbytes )


def pdf_text_ocr(pdfbytes):
    ''' Given PDF as a bytestring, OCRs it and reports the text in that.
        Expect this to not be the cleanest.
    '''
    _, pages_text = wetsuite.extras.ocr.ocr_pdf_pages(pdfbytes, dpi=150,)
    return '\n\n'.join( pages_text )


def etree(xmlbytes, strip_namespace=True):
    ' mainly ET.fromstring, with optional namespace stripping; returns (root) etree node. '
    tree = wetsuite.helpers.etree.fromstring( xmlbytes )
    if strip_namespace:
        tree = wetsuite.helpers.etree.strip_namespace( tree )
    return tree


#def urls_for_identifier():
#    'html'
#    'xml'


def xml_html_text(cbytes):
    """ Given XML or HTML, try to give us the interesting text. 
    
        Tries to guess what kind of 
    """
    if '<?xml' in cbytes[:100]:
        return xml_parse(  cbytes )
    else:
        return html_parse( cbytes )


def html_parse(htmlbytes):
    ''' 
    
    '''


def xml_parse(xmlbytes):
    ''' 
    
    '''

