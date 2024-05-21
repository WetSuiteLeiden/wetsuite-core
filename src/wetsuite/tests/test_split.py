''' test functions in the wetsuite.helpers.split module '''

import os

import pytest

import wetsuite.helpers.split
import wetsuite.helpers.etree

test_file_list = ( # these are test files in the repo
    'bwb_toestand.xml',
    'cvdr_example1.xml',
    'eggs.pdf',
    'gmb.xml',
    'gmb.html',
    'gmb.html.zip',
    'prb.xml',
    'bgr.html',
    'rechtspraak2.xml',
)

def test_ascii_fix():
    ' test that this dumb fixing function does a thing, and does not break itself '
    assert b'UTF' in wetsuite.helpers.split.fix_ascii_blah( b'   <?xml version="1.0" encoding="US-ASCII"?>  <a/>' )

def test_decide():
    ' see whether decide() deals with a file'
    import test_split

    for test_path in test_file_list:
        one_path = os.path.join( os.path.dirname( test_split.__file__ ), test_path )
        with open(one_path,'rb') as f:
            for _, _ in wetsuite.helpers.split.decide( f.read() ):
                pass

def test_fragments():
    ' see whether decide() deals with a file'
    import test_split

    for test_path in test_file_list:
        one_path = os.path.join( os.path.dirname( test_split.__file__ ), test_path )
        with open(one_path,'rb') as f:
            for _, procobj in wetsuite.helpers.split.decide( f.read() ):
                list( procobj.fragments() )


def test_firstonly():
    ' see whether decide() deals with a file'
    import test_split

    gmb_path = os.path.join( os.path.dirname( test_split.__file__ ), 'gmb.xml' )
    with open(gmb_path,'rb') as f:
        docbytes = f.read()

    assert (
        len( wetsuite.helpers.split.decide( docbytes ) ) > 1   # ther are more than one (we need an example for which that is true)
        and
        len( wetsuite.helpers.split.decide( docbytes, first_only=True ) ) == 1 # but not if you ask for one
    )


def test__split_op_xml__start_at_none():
    ' test the code path for starting at root '
    import test_split
    gmb_path = os.path.join( os.path.dirname( test_split.__file__ ), 'gmb.xml' )
    with open( gmb_path, 'rb') as gmb_file:
        gmb_tree = wetsuite.helpers.etree.fromstring( gmb_file.read() )
        wetsuite.helpers.split._split_op_xml( gmb_tree, start_at=None)


def test__split_op_xml__start_at_nonsemse():
    ' test the code path for starting at root '
    import test_split
    gmb_path = os.path.join( os.path.dirname( test_split.__file__ ), 'gmb.xml' )
    with open( gmb_path, 'rb') as gmb_file:
        gmb_tree = wetsuite.helpers.etree.fromstring( gmb_file.read() )
        with pytest.raises(ValueError,  match=r'.*Did not find.*'):
            wetsuite.helpers.split._split_op_xml( gmb_tree, start_at='/przewalski')



def test_Fragments_nonbytes():
    ' test that it complains about input that is not bytes '
    with pytest.raises(ValueError,  match=r'.*bytestrings.*'):
        wetsuite.helpers.split.Fragments('')


def test_Fragments_notimplemented():
    ' test that it complains when not implemented (arguably only valuable to test on all implementation classes in the same module)'
    fop = wetsuite.helpers.split.Fragments(b'')
    with pytest.raises(NotImplementedError,  match=r'.*Please.*'):
        fop.accepts()

    with pytest.raises(NotImplementedError,  match=r'.*Please.*'):
        fop.suitableness()

    with pytest.raises(NotImplementedError,  match=r'.*Please.*'):
        fop.fragments()
