''' Tests of functions in the helpers.util module '''
import os
import re

import pytest

import wetsuite.helpers.util


def test_wetsuite_dir():
    ' test that this seems to give a real path at all (nothing more) '
    d = wetsuite.helpers.util.wetsuite_dir()

    assert len( d['wetsuite_dir'] ) > 10
    assert len( d['datasets_dir'] ) > 10
    assert len( d['stores_dir']   ) > 10


def test_hash_hex():
    ' test that hash works on str and bytes, and not some other types '
    wetsuite.helpers.util.hash_hex('foo')
    wetsuite.helpers.util.hash_hex(b'foo')

    with pytest.raises(TypeError, match=r'.*only.*'):
        wetsuite.helpers.util.hash_hex( re.compile('foo') )


def test_hash_color():
    " test that 'give consistent (CSS) color for a string' functions at all "
    wetsuite.helpers.util.hash_color('foo')
    wetsuite.helpers.util.hash_color('foo', on='dark')
    wetsuite.helpers.util.hash_color('foo', on='light')


def test_diff():
    " test that this 'indicate the changes between these texts' functions at all "
    wetsuite.helpers.util.unified_diff('com','communication')


def test_is_xml():
    " test the 'does this look like XML (rather than HTML/XHTML)' rejects XHTML "
    assert not wetsuite.helpers.util.is_xml( b'''<html> <head><title>Title of document</title></head> <body> stuff </body> </html>''' )

def test_is_xml_encoded():
    " test the 'does this look like XML (rather than HTML/XHTML)' rejects XHTML "
    assert wetsuite.helpers.util.is_xml( '<?xml version="1.0"?><r/>'.encode('utf-16-be') )
    assert wetsuite.helpers.util.is_xml( '<?xml version="1.0"?><r/>'.encode('utf-16-le') )
    assert wetsuite.helpers.util.is_xml( '<?xml version="1.0"?><r/>'.encode('utf8') )


def test_is_with_strings():
    " if you give it strings rather than bytes, does it complain? "
    with pytest.raises(TypeError, match=r'.*expect.*'):
        assert not wetsuite.helpers.util.is_xml( '' )

    with pytest.raises(TypeError, match=r'.*expect.*'):
        assert not wetsuite.helpers.util.is_html( '' )

    with pytest.raises(TypeError, match=r'.*expect.*'):
        assert not wetsuite.helpers.util.is_pdf( '' )

    with pytest.raises(TypeError, match=r'.*expect.*'):
        assert not wetsuite.helpers.util.is_zip( '' )

    with pytest.raises(TypeError, match=r'.*expect.*'):
        assert not wetsuite.helpers.util.is_htmlzip( '' )

    with pytest.raises(TypeError, match=r'.*expect.*'):
        assert not wetsuite.helpers.util.get_ziphtml( '' )


def test_is_xml_html():
    " test the 'does this look like XML (rather than HTML/XHTML)' rejects XHTML "
    assert not wetsuite.helpers.util.is_xml( b'''<html> <head><title>Title of document</title></head> <body> stuff </body> </html>''' )


def test_xml_xhtml_ns():
    " test that 'does this look like XML (rather than HTML/XHTML)' works around namespaced root elements "
    assert not wetsuite.helpers.util.is_xml( b'''<html xmlns="http://www.w3.org/1999/xhtml"> <head><title>Title of document</title></head> <body> stuff </body> </html>''' )


def test_is_html():
    " test that 'does this look like HTML' works "
    assert wetsuite.helpers.util.is_html( b'''<html> <head><title>Title of document</title></head> <body> stuff </body> </html>''' )

    assert wetsuite.helpers.util.is_html( b'''<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd"[]><html>...''' )


def test_is_xml_not_html():
    " See if we can tell a difference between XML and HTML "
    import test_util
    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'bwb_manifest.xml' )
    with open( testzipfn ,'rb') as f:
        assert not wetsuite.helpers.util.is_html( f.read() )


def test_is_pdf():
    " test that a file('s contents) is PDF "
    import test_util
    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'eggs.pdf' )
    with open( testzipfn ,'rb') as f:
        assert wetsuite.helpers.util.is_pdf( f.read() )


def test_is_html_ns():
    " test that 'does this look like HTML' accepts XHTML "
    assert wetsuite.helpers.util.is_html( b'''<html xmlns="http://www.w3.org/1999/xhtml"> <head><title>Title of document</title></head> <body> stuff </body> </html>''' )


def test_is_zip():
    " test the 'does this look like a ZIP file?' "
    import test_util
    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'with_html_and_png.zip' )
    with open( testzipfn ,'rb') as f:
        assert wetsuite.helpers.util.is_zip( f.read() )

    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'empty.zip' )
    with open( testzipfn ,'rb') as f:
        assert not wetsuite.helpers.util.is_htmlzip( f.read() )


def test_is_not_zip():
    ' Something clearly not a .zip '
    assert not wetsuite.helpers.util.is_zip( b'''<html xmlns="http://www.w3.org/1999/xhtml"> <head><title>Title of document</title></head> <body> stuff </body> </html>'''  )


def test_is_htmlzip():
    " test the 'does this look like a HTMLfile-in-a-zipfile' (that KOOP uses) "
    # there is probably a better way of picking up a test file
    import test_util

    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'with_html_and_png.zip' )
    with open( testzipfn ,'rb') as f:
        assert wetsuite.helpers.util.is_htmlzip( f.read() )

    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'eggs.pdf' ) # is not a zip
    with open( testzipfn ,'rb') as f:
        assert not wetsuite.helpers.util.is_htmlzip( f.read() )

    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'empty.zip' ) # is zip, contains no files
    with open( testzipfn ,'rb') as f:
        empty_zip_bytes = f.read()
        assert wetsuite.helpers.util.is_zip( empty_zip_bytes )
        assert not wetsuite.helpers.util.is_htmlzip( empty_zip_bytes )

    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'png.zip' ) # is zip, contains only a .png
    with open( testzipfn ,'rb') as f:
        assert not wetsuite.helpers.util.is_htmlzip( f.read() )



def test_get_ziphtml():
    " test that we can fish the .html out of 'HTMLfile-in-a-zipfile' (that KOOP uses) in the presence of other files (the test example also contains a .png) "
    import test_util
    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'with_html_and_png.zip' )
    with open( testzipfn ,'rb') as f:
        assert wetsuite.helpers.util.is_html( wetsuite.helpers.util.get_ziphtml( f.read() ) ) # check that the extracted data _is_ the

    testzipfn = os.path.join( os.path.dirname( test_util.__file__ ), 'png.zip' )
    with open( testzipfn ,'rb') as f:
        with pytest.raises(ValueError, match=r'.*without.*'):
            wetsuite.helpers.util.is_html( wetsuite.helpers.util.get_ziphtml( f.read() ) )
