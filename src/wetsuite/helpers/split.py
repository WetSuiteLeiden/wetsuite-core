'''
    This module tries to 
    - wrangle a few different formats into a similar intermediate
    - allow you some flexibility in terms of how to take those chunks

    
    Secondary thoughts:
    - we were trying to be inspired by LaTeX hyphenation, which has a simple-but-pretty-great 
      relative "this is the cost of breaking off here",
      the analogue of which were  that makes "Hey can you break this more"

    - 


    TODO: 
    - decide the API (probably make the splitting optional? or write in a way where joining is the original with (nearly) no losses?) 
      because this overlap with just "read contents document of type X"

    - Maybe we shouldn't make too many decisions for you, and merely yield suggestions (often-ignorable) 
        - 'seems like same section, <TEXT>'
        - 'seems like new section, <TEXT>'
        - 'seems like page header/footer, <TEXT>'
        - 'seems like page footnotes, <TEXT>'
        ...so that you, or a helper function, can group into different-sized chunks as you need it.

    
    This module should eventuall grow a basic "we know about this type of document" 
    to cover all common-enough documents and their varian formats.

    It should also have a reasonable fallback for each document type.
'''


import bs4  # arguably should be inside each class so we can do without some of these imports
import fitz # arguably should be inside each class so we can do without some of these imports

import wetsuite.helpers.strings
import wetsuite.helpers.koop_parse
import wetsuite.helpers.etree
import wetsuite.extras.pdf
import wetsuite.datacollect.rechtspraaknl


header_tag_names = ('h1','h2','h3', 'h4', 'h5','h6')


def fix_ascii_blah(bytesdata):
    ''' There are a bunch of XMLs that are invalid _only_ because they contain UTF8 but say they are US-ASCII. 
        This seems constrained to the parliamentary XMLs.

        This code arguably doesn't really belong in this module, but .
    '''
    if b'<?xml version="1.0" encoding="US-ASCII"?>' in bytesdata:
        #print( 'ASCII %d'%time.time() )
        #warnings.warn( 'ASCII %d'%time.time() )
        return bytesdata.replace(
            b'<?xml version="1.0" encoding="US-ASCII"?>', 
            b'<?xml version="1.0" encoding="UTF-8"?>' 
        )
    return bytesdata




def split_op_xml(tree, start_at=None, debug=0):
    ' should be rewritte into a helper function for a number of the below '
    ret = []  #  (metadata, intermediate, debugsomething, text)

    # ensure this is a node, not a string path
    if start_at is None: # if not specified, then anything
        start_at_node = tree
        start_at_path = '/'
    else:
        if isinstance(start_at, str):
            start_at_node = tree.find(start_at)
            if start_at is None:
                raise ValueError("Did not find %s within %s")
        else: # assume it was a node in the tre you find'd or xpath'd yourself
            start_at_node = start_at
        start_at_path = wetsuite.helpers.etree.path_between(tree, start_at_node)


    if tree.tag == 'officiele-publicatie':
        if debug:
            print( 'OP XML (TOD)' )
        for ch in tree:
            if isinstance(ch, (wetsuite.helpers.etree._Comment, wetsuite.helpers.etree._ProcessingInstruction) ): #pylint: disable=protected-access
                pass
                #print('SKIP OP PI/CMNT ')
            elif ch.tag == 'metadata':
                #print('SKIP OP NETA')
                continue
            elif ch.tag == 'kop':
                # regardless of other type parts, this tends to look like
                # <kop>
                #     <titel>GEMEENTEBLAD</titel>
                #     <subtitel>Officiële uitgave van de gemeente Rotterdam</subtitel>
                # </kop>
                #print('SKIP OP KOP')
                #print(wetsuite.helpers.etree.debug_pretty(ch))
                continue
            elif ch.tag in ('staatscourant',
                            'tractatenblad',
                            'gemeenteblad', 'waterschapsblad', 'provinciaalblad','provincieblad',
                            'kamervragen','kamerstuk','niet-dossier-stuk','handelingen'):
                #continue
                fragments = wetsuite.helpers.koop_parse.alineas_with_selective_path(tree, start_at_path=start_at_path) # '/officiele-publicatie/%s'%ch.tag
                if 1: # pylint: disable=using-constant-test
                    for fragment in fragments:
                        #print('FR',fragment)
                        meta       = fragment
                        inter      = {'raw':fragment.pop('raw'), 'raw_etree':fragment.pop('raw_etree')}
                        text_flat  = fragment.pop('text-flat')
                        ret.append( (meta, inter, text_flat) )
                        #print('  -  ')
                        #print('meta ',  pprint.pformat( meta) )
                        #print('inter',  pprint.pformat( inter) )
                        #print('text ',  text_flat)
                if 0: # pylint: disable=using-constant-test
                    print(fragments)
                    # TODO: detect what level gives reasonably-sized chunks on average, to hand into mer
                    for part_id, part_text_list in wetsuite.helpers.koop_parse.merge_alinea_data( fragments ):
                        part_name = ', '.join( ' '.join(tup)  for tup in part_id )
                        part_text = '\n'.join( part_text_list )
                        print( '[%s] %s'%(part_name, part_text) )
                    #pprint.pprint( parts )
            else:
                raise ValueError(ch.tag)
    return ret


###################################################################################################

class Fragments:
    ' Abstractish base class explaining the purpose of implementing this '
    def __init__(self, docbytes:bytes):
        ''' Hand the document bytestring into this. Nothing happens yet; you call accepts(), then suitableness(), then possibly fragments() -- see example use in decide(). '''
        if not isinstance(docbytes, bytes):
            raise ValueError("This class only accepts files as bytestrings")
        self.docbytes = docbytes

    def accepts( self ) -> bool:
        ''' whether we would consider parsing that at all.
            Often, "is this the right file type".
        '''
        raise NotImplementedError('Please implement this, it comes from an essentially-abstract class')

    def suitableness( self ) -> int:
        ''' e.g. 
            - 5: I recognize that's PDF, from OP, and specifically Stcrt so I probably know how to fetch out the text fairly well
            - 50: I recognize that's PDF, from OP, so I may do better than entirely generic 
            - 500: I recognize that's PDF, I will do something generic (because I am a fallback for PDFs)
            - 5000: I recognize that's PDF, but I'm specific and it's probably a bad idea if I do something generic
            The idea is that with multiple of these, we can find the thing that (says) is most specific to this document.
        '''
        raise NotImplementedError('Please implement this, it comes from an essentially-abstract class')

    def fragments( self ):
        ' yields a tuple for each fragment '
        raise NotImplementedError('Please implement this, it comes from an essentially-abstract class')




#########################################################

class Fragments_XML_BWB( Fragments ):
    ' Turn BWB in XML form into fragements '
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.tag == 'toestand':
            return 5
        else:
            return 5000

    def fragments(self):
        # PRELIMINARY FUDGING AROUND
        ret = []
        fragments = wetsuite.helpers.koop_parse.alineas_with_selective_path( self.tree )
        # TODO: detect what level gives reasonably-sized chunks on average, to hand into mer
        for part_id, part_text_list in wetsuite.helpers.koop_parse.merge_alinea_data( fragments ):
            for part in part_text_list:
                ret.append( (
                    {'hint':'mergedpart', 'part_id':part_id, 'part_name':', '.join( ' '.join(tup)  for tup in part_id )},
                    {},#'raw':part_text_list},
                    part
                ) )
        return ret



class Fragments_XML_CVDR( Fragments ):
    ' Turn CVDR in XML form into fragements '
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.tag == 'cvdr':
            return 5
        else:
            return 5000

    def fragments(self):
        # PRELIMINARY FUDGING AROUND
        ret = []
        fragments = wetsuite.helpers.koop_parse.alineas_with_selective_path( self.tree )
        # TODO: detect what level gives reasonably-sized chunks on average, to hand into merge
        for part_id, part_text_list in wetsuite.helpers.koop_parse.merge_alinea_data( fragments ):
            for part in part_text_list:
                ret.append( (
                    {'hint':'mergedpart', 'part_id':part_id, 'part_name':', '.join( ' '.join(tup)  for tup in part_id )},
                    {},#'raw':part_text_list},
                    part
                ) )
        return ret




# CONSIDER: It seems that for OP, the meta fields are the same between HTML and XML,
#           which would mean the detection methods could be the same (and more code shared)
#           On the other hand, the //looking-for//specifics is great at highlighting weird edge caes

class Fragments_HTML_OP_Stcrt( Fragments ):
    " Turn staatscourat in HTML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Staatscourant':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_HTML_OP_Stb( Fragments ):
    " Turn staatsblad in HTML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Staatsblad':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_HTML_OP_Gmb( Fragments ):
    " Turn gemeenteblad in HTML form (from KOOP's BUS) into fragements "

    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Gemeenteblad':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret



class Fragments_HTML_OP_Trb( Fragments ):
    " Turn tractatenblad in HTML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Tractatenblad':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret



class Fragments_HTML_OP_Prb( Fragments ):
    " Turn provincieblad in HTML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Provincieblad':
            return 5
        elif pname is not None and pname.get('content')=='Provinciaal blad':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_HTML_OP_Wsb( Fragments ):
    " Turn waterschapsblad in HTML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Waterschapsblad':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_HTML_OP_Bgr( Fragments ):
    " Turn blad gemeenschappelijke regeling in HTML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Blad gemeenschappelijke regeling':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret




class Fragments_XML_OP_Stcrt( Fragments ):
    " Turn staatscourant in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//staatscourant//circulaire-tekst/tekst'):
            return 5
        elif self.tree.xpath('//staatscourant//vrije-tekst/tekst'):
            return 5
        elif self.tree.xpath('//staatscourant//zakelijke-mededeling-tekst/tekst'):
            return 5
        elif self.tree.xpath('//staatscourant//regeling-tekst'):
            return 5
        elif self.tree.xpath('//staatscourant'):
            return 50
        elif self.tree.tag == 'stcart': # is this wrong?
            return 50
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_OP_Stb( Fragments ):
    " Turn sstaatsblad in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//staatsblad//wettekst'):
            return 5
        elif self.tree.xpath('//staatsblad/verbeterblad/vrije-tekst/tekst'): # exception?
            return 5
        #elif self.tree.xpath('//staatsblad'):
        #    return 50
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_OP_Trb( Fragments ):
    " Turn tractatenblad in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//tractatenblad//vrije-tekst'):
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_OP_Gmb( Fragments ):
    " Turn gemeenteblad in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//gemeenteblad//regeling-tekst'):
            return 5
        if self.tree.xpath('//gemeenteblad//zakelijke-mededeling-tekst/tekst'):
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_OP_Prb( Fragments ):
    " Turn provincieblad in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//provinciaalblad//regeling-tekst/tekst'):
            return 5
        elif self.tree.xpath('//provinciaalblad//zakelijke-mededeling-tekst/tekst'):
            return 5
        elif self.tree.xpath('//provincieblad//zakelijke-mededeling-tekst/tekst'):
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_OP_Wsb( Fragments ):
    " Turn waterschapsblad in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//waterschapsblad//zakelijke-mededeling-tekst/tekst'):
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_OP_Bgr( Fragments ):
    " Turn blad gemeenschappelijke regeling in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//bladgemeenschappelijkeregeling//regeling-tekst'):
            return 5
        if self.tree.xpath('//bladgemeenschappelijkeregeling//zakelijke-mededeling-tekst/tekst'):
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret




class Fragments_XML_OP_Handelingen( Fragments ):
    " Turn handelingen in XML form (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        self.docbytes = fix_ascii_blah( self.docbytes )
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.xpath('//handelingen'):
            return 5
        elif self.tree.tag == 'handeling': # is this wrong?
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_BUS_Kamer( Fragments ):
    " Turn other kamer XMLs (from KOOP's BUS) into fragements (TODO: re-check which these are) "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        self.docbytes = fix_ascii_blah( self.docbytes )
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        # may raise
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.tag == 'kamerwrk':
            return 5

        elif self.tree.xpath('//kamerstuk//vrije-tekst/tekst'):
            return 5
        elif self.tree.xpath('//kamervragen'):
            return 5
        elif self.tree.xpath('//kamerstuk//stuk'): # ??
            return 50
        elif self.tree.tag == 'vraagdoc': # is this wrong?
            return 50
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


class Fragments_HTML_BUS_kamer( Fragments ):
    " Turn kamer-related HTMLs (from KOOP's BUS) into fragements "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        # may raise
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
        pname = self.soup.find('meta', attrs={'name':'OVERHEIDop.publicationName'})
        if pname is not None and pname.get('content')=='Kamervragen (Aanhangsel)':
            return 5
        elif pname is not None and pname.get('content')=='Kamervragen zonder antwoord':
            return 5
        elif pname is not None and pname.get('content')=='Kamerstuk':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret


# class Fragments_HTML_Rechtspraak( Fragments ):
#     def __init__(self, data):
#         Fragments.__init__(self, data)
#
#     def accepts( self ):
#         return wetsuite.helpers.util.is_html( self.docbytes )
#
#     def suitableness( self ):
#         self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )
#         ht = self.soup.find('head/title')
#         if ht is not None and ht.text is not None and ht.text.startswith('Rechtspraak.nl'):
#             return 5
#         else:
#             return 5000
#
#     #def fragments


class Fragments_XML_Rechtspraak( Fragments ):
    " turn rechtspraak.nl's XML form into fragments "
    def __init__(self, data):
        Fragments.__init__(self, data)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        self.tree = wetsuite.helpers.etree.fromstring( self.docbytes )
        self.tree = wetsuite.helpers.etree.strip_namespace( self.tree ) # choice to remove namespaces unconditionally
        if self.tree.tag == 'open-rechtspraak':
            return 5
        else:
            return 5000

    def fragments(self):
        ret = []
        return ret

        # examples:
        # https://data.rechtspraak.nl/uitspraken/content?id=ECLI:NL:RBDHA:2023:18504
        #    uitspraak.info, section+
        #

        # ii = tree_nonamespaces.find('inhoudsindicatie')
        # if ii is not None:
        #     print( '[%s]  %s'%(
        #         'inhoudsindicatie', ' '.join( wetsuite.datacollect.rechtspraaknl._para_text( ii ) )
        #     ) )

        # t = None
        # if tree_nonamespaces.find('uitspraak') is not None:
        #     t = tree_nonamespaces.find('uitspraak')
        # elif tree_nonamespaces.find('conclusie') is not None:
        #     t = tree_nonamespaces.find('conclusie')
        # if t is not None:
        #     structured_things = t.xpath('uitspraak.info|section')
        #     if len(structured_things) ==0:
        #         print( "BLAH %s"%list( tag.tag  for tag in t) )
        #     else:
        #         print( "YAY %s"%list( tag.tag  for tag in t) )
        #         for uis in t.getchildren(): # all top-level, ideally is something like <uitspraak.info> followed by <section>s
        #             if uis.tag in ('parablock',):
        #                 continue # TODO: use, probably actually just header


        #             title = uis.find('title')
        #             st = '???'
        #             if title:
        #                 title_nr = title.find('nr')
        #                 if title_nr:
        #                     title_nr.text = ''
        #                 st = ' '.join(wetsuite.helpers.etree.all_text_fragments( title )).strip()
        #                 title.clear()
        #             print( '[%s]  %s'%(
        #                 st, ' '.join( wetsuite.datacollect.rechtspraaknl._para_text( uis ) )
        #             ) )
        #             print('--')
        #     #for thing in wetsuite.datacollect.rechtspraaknl._para_text( t ):
        #     #    print( repr(thing) )

        # # head before
        # #    pre-head b
        # # uitspraak, inleiding, procesverloop, overwegingen, beslissing

        # # smaller sections:
        # #   Proceskosten, Standpunt van verzoeker, Wettelijk kader, Bevoegdheid, Conclusie en gevolgen, Rechtsmiddel

        # # Bijlage


####################################################################################

class Fragments_HTML_Fallback( Fragments ):
    " Extract text from HTML from non-specific source into fragments "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.soup = None

    def accepts( self ):
        if wetsuite.helpers.util.is_html( self.docbytes ):
            return True
        if wetsuite.helpers.util.is_htmlzip( self.docbytes ):
            self.docbytes = wetsuite.helpers.util.get_ziphtml( self.docbytes ) # unpack the one-html zip into the html
            return True
        return False

    def suitableness( self ):
        self.soup = bs4.BeautifulSoup( self.docbytes, features='lxml' )

        return 500

    def fragments(self):
        ret = []
        return ret


class Fragments_XML_Fallback( Fragments ):
    " Extract text from XML from non-specific source into fragments "
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.tree = None

    def accepts( self ):
        return wetsuite.helpers.util.is_xml( self.docbytes )

    def suitableness( self ):
        return 500

    def fragments(self):
        ret = []
        return ret


class Fragments_PDF_Fallback( Fragments ):
    ''' Extract text from PDF from non-specific source into fragments

        Tries to look at section titles, 
        but is currently too crude to deal with page headers, footers.
    '''
    def __init__(self, docbytes):
        Fragments.__init__(self, docbytes)
        self.part_name = None
        self.part_ary = None

    def accepts( self ):
        return wetsuite.helpers.util.is_pdf( self.docbytes )

    def suitableness( self ):
        # assuming is_pdf approved, we can read it,
        # but also, we are not as good as anything more targeted that you can register, so:
        return 100

    def fragments(self):
        ret = []
        with fitz.open( stream=self.docbytes, filetype="pdf") as document:
            self.part_name = ''
            self.part_ary = []

            def marker_now( hint ):
                ret.append( ( {'hint':hint},   {},   '') )

            def flush( hint_first = None ):
                ' any parts of part_ary are  '
                #if hint_first:
                #    ret.append( ( {'hint':hint_first},   {},   '') )

                pa = list( filter( lambda x: len(x.strip())>0, self.part_ary) ) # remove empty-text elements from part_ary
                if len(pa) > 0:
                    for i, frag in enumerate(pa):
                        if i==0 and hint_first is not None:
                            hint = hint_first
                        else:
                            hint = '+para'
                        ret.append( ( {'hint':hint, 'lastheader':self.part_name},   {},   frag) )
                self.part_name = ''
                self.part_ary = []

            bupless = 0

            #for page_results in wetsuite.extras.pdf.page_text(docdata, option='xhtml'):

            for page in document:
                flush( )
                marker_now( 'newpage' )

                # TODO: move to use 'html' rather than 'xhtml' because it lets us do more.

                page_results = page.get_text( option='xhtml', flags=fitz.TEXTFLAGS_XHTML & ~fitz.TEXT_PRESERVE_IMAGES )

                soup = bs4.BeautifulSoup(page_results, features='lxml', from_encoding='utf8')
                div = soup.find('div')
                print(div)
                for elem in div.children:
                    if isinstance(elem, bs4.NavigableString):
                        if len(elem.string.strip()) > 0:
                            print('TopText %r'%elem.string)
                    else:
                        #if elem.find('img'):# assumes
                        #    continue


                        b = elem.find('b')
                        bupwish = b is not None  and b.string is not None  and  not wetsuite.helpers.strings.is_numeric( b.string ) # just an isolated number in a paragraphs does not mean much

                        if elem.name in header_tag_names:

                            flush( )
                            self.part_name = ' '.join( elem.find_all(text=True) )
                            flush( hint_first='header' )
                        else:
                            if bupwish:
                                if bupless > -1  and bupwish:
                                    flush( hint_first='bold' )
                                bupless  = 0
                            else: # bupless is about not triggering on areas of everything-bold
                                bupless += 1

                        text = ' '.join( elem.find_all(text=True) )
                        self.part_ary.append( text )

            flush( )
            marker_now( 'end' )

        return ret

        #for page in document:
        #    page_results = page.get_text( option='xhtml', flags=fitz.TEXTFLAGS_XHTML & ~fitz.TEXT_PRESERVE_IMAGES )
        #    print( page_results )
        #    break


        # Use contents to see if we can use one of our specialized handlers,
        # or will be calling split_pdf_fallback

        #Tweede Kamer der Staten-Generaal

        #kst-36428-3
        #ISSN 0921-7371
        #’s-Gravenhage 2023
        #Tweede Kamer, vergaderjaar 2023–2024, 36 428, nr. 3

        # ISSN 0921-7371  is  Bijlagen van het Verslag der Handelingen van de Tweede Kamer der Staten-Generaal
        #      0920-2080      Verslag der Handelingen van de Tweede Kamer der Staten-Generaal
        #      0920-2072      Verslag der Handelingen van de Eerste Kamer der Staten-Generaal
        # https://portal.issn.org/api/search?search[]=MUST=default=Kamer+der+Staten-Generaal&search_id=34863538
        #for page in document:
        #    yield page.get_text( option=option, sort=True )


        # one generalization might be to find all h1, h2, h3, bold-and-uppercase-only things,
        # see how many there are and which splits would make for reasonable chunks
        # also maybe guard against BUPs every line? (e.g. require at least 1 line since the last wish to BUP)



# In theory you could nest these (e.g. OP detects and deals with all OP documents)
# but it may be nicer to have it be more pluggible with a registerable list

# ...which might also keep it easier/clearer how this can be extended

####################################################################################

_registered_fragment_parsers = [
   # order doesn't matter, all are checked.

   Fragments_XML_BWB,
   Fragments_XML_CVDR,

   Fragments_XML_OP_Stcrt,
   Fragments_XML_OP_Stb,
   Fragments_XML_OP_Trb,
   Fragments_XML_OP_Gmb,
   Fragments_XML_OP_Prb,
   Fragments_XML_OP_Wsb,
   Fragments_XML_OP_Bgr,

   Fragments_HTML_OP_Stcrt,
   Fragments_HTML_OP_Stb,
   Fragments_HTML_OP_Gmb,
   Fragments_HTML_OP_Trb,
   Fragments_HTML_OP_Prb,
   Fragments_HTML_OP_Wsb,
   Fragments_HTML_OP_Bgr,

   Fragments_XML_OP_Handelingen,
   Fragments_XML_BUS_Kamer,
   Fragments_HTML_BUS_kamer,

   Fragments_XML_Rechtspraak,
   #Fragments_HTML_Rechtspraak,

   Fragments_PDF_Fallback,
   Fragments_XML_Fallback,
   Fragments_HTML_Fallback,
   # opendocument fallback?
]


def decide(docbytes, thresh=1000):
    ''' Ask all processors to say how well they would do, 
        pick any applicable.

        Returns a list of (score, procobject),
        and note that that procobject has had accepts() and suitableness() called 
        so you can now call fragments() to get the fragments.
    '''
    options = [] # list of (score, class)
    for PerhapsClass in _registered_fragment_parsers:
        plcob = PerhapsClass( docbytes )
        if plcob.accepts():              # right file type?
            score = plcob.suitableness() # "how well would you say you would treat this?"
            if score < thresh:
                options.append( [score, plcob] )

    options.sort( key = lambda x:x[0] )
    return options
