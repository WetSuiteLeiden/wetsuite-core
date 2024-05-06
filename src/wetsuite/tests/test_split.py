''' test functions in the wetsuite.helpers.split module '''

import os
import wetsuite.helpers.split


def test_ascii_fix():
    assert b'UTF' in wetsuite.helpers.split.fix_ascii_blah( b'   <?xml version="1.0" encoding="US-ASCII"?>  <a/>' )

def test_decide():
    ' see whether decide() deals with a file'
    import test_split

    for test_path in ( # these are test files in the repo
        'bwb_toestand.xml',
        'cvdr_example1.xml',
        'eggs.pdf',
    ):
        bwb_example_path = os.path.join( os.path.dirname( test_split.__file__ ), test_path )
        with open(bwb_example_path,'rb') as f:
            wetsuite.helpers.split.decide( f.read() )
