''' Testing koop_parse and koop_sru modules '''
import os

import pytest

from wetsuite.helpers.koop_parse import cvdr_parse_identifier, cvdr_meta, cvdr_text, cvdr_sourcerefs, cvdr_param_parse, cvdr_normalize_expressionid
from wetsuite.helpers.koop_parse import prefer_types, parse_op_meta
from wetsuite.helpers.koop_parse import alineas_with_selective_path
import wetsuite.datacollect.koop_sru
from wetsuite.datacollect.koop_sru import BWB, CVDR
from wetsuite.datacollect.koop_sru import SamenwerkendeCatalogi, LokaleBekendmakingen, TuchtRecht, WetgevingsKalender, PLOOI, PUCOpenData, EuropeseRichtlijnen
from wetsuite.datacollect.koop_sru import StatenGeneraalDigitaal, Belastingrecht
import wetsuite.helpers.etree


def test_koop_sru_object_constructor():
    ' mostly just that that they construct fine '
    BWB()
    CVDR()

    SamenwerkendeCatalogi()
    LokaleBekendmakingen()
    TuchtRecht()
    WetgevingsKalender()
    PLOOI()
    PUCOpenData()
    EuropeseRichtlijnen()

    Belastingrecht()
    StatenGeneraalDigitaal()



def test_cvdr_parse_identifier():
    ' test cvdr_parse_identifier basics '
    assert cvdr_parse_identifier('101404_1')      ==  ('101404', '101404_1')
    assert cvdr_parse_identifier('CVDR101405_1')  ==  ('101405', '101405_1')
    assert cvdr_parse_identifier('CVDR101406')    ==  ('101406',  None     )
    assert cvdr_parse_identifier('1.0:101407_1')  ==  ('101407', '101407_1')

    assert cvdr_parse_identifier('101404_1',     prepend_cvdr=True)  ==  ('CVDR101404', 'CVDR101404_1')
    assert cvdr_parse_identifier('CVDR101405_1', prepend_cvdr=True)  ==  ('CVDR101405', 'CVDR101405_1')
    assert cvdr_parse_identifier('CVDR101406',   prepend_cvdr=True)  ==  ('CVDR101406',  None     )
    assert cvdr_parse_identifier('1.0:101407_1', prepend_cvdr=True)  ==  ('CVDR101407', 'CVDR101407_1')

    with pytest.raises(ValueError, match=r'.*does not look like.*'):
        assert cvdr_parse_identifier('BLAH')
    # TODO: check about possible edge cases, like leading zeroes


def test_cvdr_param_parse():
    ' param parser (TODO: merge underlying function) '
    res = cvdr_param_parse('BWB://1.0:c:BWBR0008903&artikel=12&g=2011-11-08')
    assert res['artikel'] == ['12']
    assert res['g']       == ['2011-11-08']


def test_cvdr_param_parse_repeat():
    ' test repeated params (nonsense value) '
    res = cvdr_param_parse('BWB://1.0:c:BWBR0008903&a=1&a=2')
    assert res['a']       == ['1','2']


def get_test_data(fn):
    ' open a test file placed in the test directory - probably works unless something is being very protective '
    import test_koop  # that's intentional pylint: disable=W0406
    file = open( os.path.join( os.path.dirname( test_koop.__file__ ), fn), mode='rb' )
    filedata = file.read()
    file.close()
    return filedata


def get_test_etree(fn):
    ' read test data with read_testdata(), parse and return as etree object'
    return wetsuite.helpers.etree.fromstring( get_test_data(fn) )

# TODO: find example with different types of sourcerefs

# just many is e.g.
# New best: 14 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/101112/2/xml/101112_2.xml'
# New best: 17 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR10324/2/xml/CVDR10324_2.xml'
# New best: 25 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR116909/2/xml/CVDR116909_2.xml'
# New best: 49 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR122433/2/xml/CVDR122433_2.xml'
# New best: 59 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR603481/2/xml/CVDR603481_2.xml'
# New best: 62 for 'https://repository.officiele-overheidspublicaties.nl/CVDR/CVDR645418/1/xml/CVDR645418_1.xml'


def test_cvdr_normalize_expressionid():
    " test whether we can reasonably use this to normalize the identifier "
    assert cvdr_normalize_expressionid('CVDR112779_1') == 'CVDR112779_1'
    assert cvdr_normalize_expressionid('112779_1')     == 'CVDR112779_1'
    with pytest.raises(ValueError, match=r'.*expression.*'):
        assert cvdr_normalize_expressionid('112779')     == 'CVDR112779'


def test_cvdr_meta():
    ' test cvdr_meta, mostly just for not borking out immediately '
    tree = get_test_etree( 'cvdr_example1.xml' )

    meta = cvdr_meta(tree)
    assert isinstance( meta['issued'], list ) # i.e. not flattened

    meta = cvdr_meta(tree, flatten=True)
    assert meta['identifier'] == '112779_1' # a value as expected  TODO: check that we normalize this?


def test_cvdr_meta_bytes():
    ' test that giving it bytes instead of an etree node works at all  (shortish XML that still passes the basic tests, but contains nothing)' 
    cvdr_meta(b'''<?xml version="1.0" encoding="utf-8"?><cvdr>
                     <meta><owmskern></owmskern><owmsmantel></owmsmantel><cvdripm></cvdripm></meta>
                     <body></body></cvdr>''')


def test_cvdr_meta_nonmeta():
    ' test that it rejects non-metadata records ' 
    with pytest.raises(ValueError, match=r'.*neither a document or a search result.*'):
        cvdr_meta(b'''<body></body>''')


def test_cvdr_enriched():
    ' parse a query response with enrichedData nodes '
    cvdr_meta(b'''
    <record>
      <recordSchema>http://standaarden.overheid.nl/sru/</recordSchema>
      <recordPacking>xml</recordPacking>
      <recordData>
        <gzd gzd="http://standaarden.overheid.nl/sru http://standaarden.overheid.nl/sru/gzd.xsd">
          <originalData>
            <meta>
              <owmskern>
              </owmskern>
              <owmsmantel>
              </owmsmantel>
              <cvdripm>
              </cvdripm>
            </meta>
          </originalData>
          <enrichedData>
            <organisatietype>Provincie</organisatietype>
            <publicatieurl_xhtml>https://repository.officiele-overheidspublicaties.nl/cvdr/CVDR717960/1/html/CVDR717960_1.html</publicatieurl_xhtml>
            <publicatieurl_xml>https://repository.officiele-overheidspublicaties.nl/cvdr/CVDR717960/1/xml/CVDR717960_1.xml</publicatieurl_xml>
            <preferred_url>https://lokaleregelgeving.overheid.nl/CVDR717960/1</preferred_url>
          </enrichedData>
        </gzd>
      </recordData>
      <recordPosition>1501</recordPosition>
    </record>
''')



def test_cvdr_text():
    ' test cvdr_text, currently just for not borking out immediately '
    tree = get_test_etree( 'cvdr_example1.xml' )
    cvdr_text(tree)



def test_cvdr_sourcerefs():
    ' test cvdr_text, currently just for not borking out immediately '
    tree = get_test_etree('cvdr_example1.xml')
    cvdr_sourcerefs(tree)

    tree = get_test_etree('cvdr_example2.xml')
    cvdr_sourcerefs(tree)


def test_search_related_parsing():
    ' do a bunch of search related parsing '
    # CONSIDER: currently based on an actual search - TODO: fetch a triple of XML files to not rely on taht
    #from wetsuite.helpers.net import download
    #from wetsuite.helpers.etree import fromstring
    bwb_sru =  wetsuite.datacollect.koop_sru.BWB()
    for record in bwb_sru.search_retrieve('dcterms.identifier = BWBR0045754'):
        wetsuite.helpers.koop_parse.bwb_searchresult_meta( record )


def test_more_parsing():
    ' do a bunch of search related parsing '
    # CONSIDER: currently based on an actual search - TODO: fetch a triple of XML files to not rely on taht
    # import wetsuite.datacollect.koop_sru
    # from wetsuite.helpers.net import download
    # from wetsuite.helpers.etree import fromstring
    # bwb =  wetsuite.datacollect.koop_sru.BWB()
    # for record in bwb.search_retrieve('dcterms.identifier = BWBR0045754'):
    #     search_meta = wetsuite.helpers.koop_parse.bwb_searchresult_meta( record )

    # test case is BWBR0045754
    toe_etree = get_test_etree('bwb_toestand.xml')
    toe_usefuls = wetsuite.helpers.koop_parse.bwb_toestand_usefuls( toe_etree )
    wetsuite.helpers.koop_parse.bwb_toestand_text(    toe_etree ) # (not used here)

    wti_etree = get_test_etree('bwb_wti.xml')
    wti_usefuls = wetsuite.helpers.koop_parse.bwb_wti_usefuls(      wti_etree )

    man_etree = get_test_etree('bwb_manifest.xml')
    man_usefuls = wetsuite.helpers.koop_parse.bwb_manifest_usefuls( man_etree )

    wetsuite.helpers.koop_parse.bwb_merge_usefuls(toe_usefuls, wti_usefuls, man_usefuls)



def test_prefer_types_1():
    " this is counting on argument's current default values;  TODO: don't do that "
    assert prefer_types(  ['metadata', 'metadataowms', 'pdf','odt', 'jpg', 'coordinaten', 'ocr', 'html', 'xml'] ) ==  ['metadata', 'metadataowms', 'xml', 'html']


def test_prefer_types_2():
    " this too is counting on argument's current default values;  TODO: don't do that "
    assert prefer_types(  ['metadata', 'metadataowms', 'pdf',] ) ==  ['metadata', 'metadataowms', 'pdf']


# the distinction behind the following two is explained better in prefer's type docstring

def test_prefer_types_exclusive():
    ' note that all_of and first_of are considered somewhat independently '
    assert prefer_types(  ['metadata', 'metadataowms', 'xml', 'pdf',],
        all_of=  ('metadata', 'metadataowms', 'xml'),
        first_of=('html', 'pdf', 'odt') )         ==  ['metadata', 'metadataowms', 'xml', 'pdf']


def test_prefer_types_one():
    ' compared with test_prefer_types_exclusive: duplicate between all_of and first_of so we get just one '
    assert prefer_types(  ['metadata', 'metadataowms', 'xml', 'pdf',],
        all_of=  ('metadata', 'metadataowms', 'xml'),
        first_of=('xml', 'html', 'pdf', 'odt') )  ==  ['metadata', 'metadataowms', 'xml']



def test_parse_op_meta():
    ' test that parsing these files gives results '
    import test_koop  # that's intentional pylint: disable=W0406
    for fn in (
        'opmeta1.xml',
        'opmeta2.xml'
        ):
        with open( os.path.join( os.path.dirname( test_koop.__file__ ), fn), mode='rb' ) as f:
            docbytes = f.read()
            assert len( parse_op_meta( docbytes ) ) > 5
            assert len( parse_op_meta( docbytes, as_dict=True ) ) > 5


def test_parse_op_meta_bad():
    ' test that it tests it applies '
    with pytest.raises(ValueError, match=r'.*not expect.*'):
        parse_op_meta(b'''<body></body>''')


def test_alineas_with_selective_path():
    ''' test that the basic extraction idea works 
        TODO: add a bunch more real cases
    '''
    tree = wetsuite.helpers.etree.fromstring( b'<body><al>test1</al><!-- --><al>test2</al></body>' )
    res = alineas_with_selective_path( tree)
    assert res[0]['path']      == '/body/al[1]'
    assert res[0]['text-flat'] == 'test1'
    assert res[0]['raw']       == b'<al>test1</al>'

    assert res[1]['path'] == '/body/al[2]'
    assert res[1]['text-flat'] == 'test2'
