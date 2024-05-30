''' General utility functions, like "give me a path to where wetsuite can store data" and debug tools to the end of inspecting data. 
'''
import os
import difflib
import hashlib
import zipfile
import io


def wetsuite_dir():
    ''' Figure out where we can store data.
    
        Returns a dict with keys mentioning directories:
          - wetsuite_dir: a directory in the user profile we can store things
          - datasets_dir: a directory inside wetsuite_dir first that datasets.load() will put dataset files in 
          - stores_dir:   a directory inside wetsuite_dir that localdata will put sqlite files in   

        Keep in mind:
          - When windows users have their user profile on the network, we try to pick a directory more likely to be shared by your other logins
          - ...BUT keep in mind network mounts tend not to implement proper locking, 
             so around certain things (e.g. our localdata.LocalKV) you invite corruption when multiple workstations write at the same time, 
             ...so don't do that. If you need distributed work, use an actually networked store, or be okay with read-only access.
    '''
    # CONSIDER: listen to an environment variable to override that base directory,
    #         to allow people to direct where to store this (might be useful e.g. on clustered filesystems)
    #         (an explicit argument wouldn't make sense when internals will call this)

    # CONSIDER: If we wanted to expose this to users, this function deserves to be in a more suitable location - maybe helpers/util?
    #         it's also used by localdata

    ret = {}

    # Note: expanduser("~") would do most of the work, as it works on win+linx+osx.
    #   These additional tests are mainly for the case of AD-managed workstations, to try to direct it to store it in a shared area
    #   HOMESHARE is picked up (and preferred over USERPROFILE) because in this context, USERPROFILE might be a local, non-synced directory
    #     (even if most of its contents are junctions to places that _are_)
    # Yes, we do assume this will stay constant over time.
    # we assume the following are only filled when it's actually windows - we could test that too via os.name or platform.system()
    userprofile = os.environ.get('USERPROFILE', None)
    homeshare   = os.environ.get('HOMESHARE',   None)
    chose_dir = None
    if homeshare is not None:
        r_via_hs = os.path.join(homeshare, 'AppData', 'Roaming')
        if os.path.exists( r_via_hs ):
            chose_dir = os.path.join( r_via_hs, '.wetsuite' )
    elif userprofile is not None:
        r_via_up = os.path.join(userprofile, 'AppData', 'Roaming')
        if os.path.exists( r_via_up ):
            chose_dir = os.path.join( r_via_up, '.wetsuite' )

    if chose_dir is None:
        home_dir = os.path.expanduser("~")
        ret['wetsuite_dir'] = os.path.join( home_dir, '.wetsuite' )
    else:
        ret['wetsuite_dir'] = chose_dir

    # TODO:     more filesystem checking, so we can give clearer errors
    if not os.path.exists( ret['wetsuite_dir'] ):
        os.makedirs( ret['wetsuite_dir'] )
    if not os.access(ret['wetsuite_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory, %r"%ret['wetsuite_dir'])

    ret['datasets_dir'] = os.path.join( ret['wetsuite_dir'], 'datasets' )
    if not os.path.exists( ret['datasets_dir'] ):
        os.makedirs( ret['datasets_dir'] )
    if not os.access(ret['datasets_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory of datasets, %r"%ret['datasets_dir'])

    ret['stores_dir'] = os.path.join( ret['wetsuite_dir'], 'stores' )
    if not os.path.exists( ret['stores_dir' ] ):
        os.makedirs( ret['stores_dir'] )
    if not os.access(ret['stores_dir'], os.W_OK):
        raise OSError("We cannot write to our local directory of datasets, %r"%ret['stores_dir'])

    return ret


def free_space(path=None):
    ''' Says how many bytes are free on the filesystem that stores that mentioned path '''
    import shutil
    if path is None:
        path = wetsuite_dir()['datasets_dir']
    return shutil.disk_usage( path ).free



def unified_diff( before:str, after:str, strip_header=True, context_n=999 ) -> str:
    """ Returns an unified-diff-like indication of how two pieces of text differ, 
        as a single string and with initial header cut off, 

        Not meant for actual patching, just for quick debug printing of changes.

        context_n defaults to something high enough that it'll probably print everything
    """
    lines = list( difflib.unified_diff( before.splitlines(), after.splitlines(), fromfile='before', tofile='after', n=context_n ) )
    if strip_header:
        lines = lines[4:]
    return '\n'.join( lines )


def hash_color( string:str, on=None ):
    ''' Give a CSS color for a string - consistently the same each time based on a hash
        Usable e.g. to make tables with categorical values more skimmable.

        To that end, this takes a string, and
        returns (css_str,r,g,b), where r,g,b are 255-scale r,g,b values for a string
    '''
    dig = hash_hex( string.encode('utf8'), as_bytes=True )
    r, g, b = dig[0:3]
    if on=='dark':
        r = min(255,max(0, r/2+128 ))
        g = min(255,max(0, g/2+128 ))
        b = min(255,max(0, b/2+128 ))
    elif on=='light':
        r = min(255,max(0, r/2 ))
        g = min(255,max(0, g/2 ))
        b = min(255,max(0, b/2 ))
    r, g, b = int(r), int(g), int(b)
    css = '#%02x%02x%02x'%(r,g,b)
    return css,(r,g,b)


def hash_hex( data:bytes, as_bytes:bool=False ):
    ''' Given some byte data, calculate SHA1 hash.
        Returns that hash as a hex string, unless you specify as_bytes=True
    
        Deals with unicode by UTF8-encoding it, which isn't _always_ what you want.
    '''
    if isinstance(data, bytes):
        pass
    elif isinstance(data, str): # assume you are using this in a "I just want a consistent hash value for the same input", not necessarily according to any standard
        data = data.encode('u8')
    else:
        raise TypeError('hash_hex() only accepts byte/str data')
    s1h = hashlib.sha1()
    s1h.update( data )
    if as_bytes:
        return s1h.digest()
    else:
        return s1h.hexdigest()


def is_html( bytesdata ) -> bool:
    ' Do these bytes look loke a HTML document? (no specific distinction to XHTML) '
    if not isinstance(bytesdata, bytes):
        raise TypeError("we expect a bytestring, not a %s"%type(bytesdata))
    if b'<!DOCTYPE html' in bytesdata[:1000]:
        return True
    if b'<html' in bytesdata[:1000]:
        return True
    return False


def is_xml( bytesdata, debug=False ) -> bool:
    ''' Does this look and work like an XML file?

        Note that in this context, XHTML (and valid-enough HTML) are considered NOT XML

        Note: gives a stronger answer than "does it look sort of like an XML" - we could answer _that_ for a lot cheaper,
        (than actually just parseing it, which we do -- TODO: parse only the first kilobyte or so, incrementally)
    '''
    # arguably a simple and thorough way is to tell that
    #   it parses in a fairly strict XML/HTML parser,
    #   and the root node is _not_ called 'html'  (HTML or XHTML)
    #
    # There are many other indicators that are cheaper -- but only a good guess, and not _always_ correct,
    #  depending on whether you are asking

    if not isinstance(bytesdata, bytes):
        raise TypeError("we expect a bytestring, not a %s"%type(bytesdata))

    # the ordering here is more about efficiency than function
    if is_html( bytesdata ): # cheaper than parsing
        #if debug:
        #    print('is html')
        return False
    if is_pdf( bytesdata ): # cheaper than parsing
        #if debug:
        #    print('is html')
        return False

    import wetsuite.helpers.etree
    import lxml.etree
    try:
        root = wetsuite.helpers.etree.fromstring( bytesdata )
    except lxml.etree.XMLSyntaxError as xse: # if it doesn't parse  (not 100% on the exception? What's lxml.etree.ParserError then?)
        #if debug:
        #    print('syntaxerror', xse)
        return False

    # if it's valid as XML but the root node is 'html', we do not consider it XML
    root_tag = root.tag
    if root_tag.startswith('{'): # deal with a namespaced root without calling strip_namespaces
        root_tag = root_tag[root_tag.index('}')+1:]
    return root_tag != 'html'


def is_pdf( bytesdata:bytes ) -> bool:
    ' Does this bytestring look like a PDF document? '
    if not isinstance(bytesdata, bytes):
        raise TypeError("we expect a bytestring, not a %s"%type(bytesdata))
    return bytesdata.startswith( b'%PDF' )


def is_zip( bytesdata:bytes ) -> bool:
    ' Does this bytestring look like a ZIP file? '
    if not isinstance(bytesdata, bytes):
        raise TypeError("we expect a bytestring, not a %s"%type(bytesdata))
    if bytesdata.startswith( b'PK\x03\x04' ): # (most)
        return True
    if bytesdata.startswith( b'PK\x05\x06' ): # empty - not good for us and perhaps deserves a separate test
        return True
    #if bytesdata.startswith( b'PK\x07\x08' ): # spanned - shouldn't apply to us, and I think we cannot currently deal with it
    #    return True
    return False


def is_empty_zip( bytesdata:bytes ) -> bool:
    ' Does this bytestring look like an empty ZIP file? '
    if not isinstance(bytesdata, bytes):
        raise TypeError("we expect a bytestring, not a %s"%type(bytesdata))
    if bytesdata.startswith( b'PK\x05\x06' ): # empty - not good for us and perhaps deserves a separate test
        return True
    return False



def is_htmlzip( bytesdata:bytes ) -> bool:
    ''' Made for the .html.zip files that KOOP puts e.g. in its BUS.
     
        Is this a ZIP file with one entry for which the name ends with .html? 
        (we could test its content with is_html it but given the context we can assume it)
    '''
    if not isinstance(bytesdata, bytes):
        raise TypeError("we expect a bytestring, not a %s"%type(bytesdata))
    if not is_zip( bytesdata ):
        return False
    z = zipfile.ZipFile( io.BytesIO(bytesdata) )
    if len(z.filelist) == 0:
        return False
    for zipinfo in z.filelist:
        if zipinfo.filename.endswith('.html'):
            return True
    return False # is zip, which has files, but no .html


def get_ziphtml( bytesdata:bytes ):
    ''' Made for the .html.zip files that KOOP puts e.g. in its BUS.

        Gets the contents of the first file from the zip with a name ending in .html
        Assuming you tested with is_htmlzip() this should be the main file
        (there might also e.g. be images in there) 

        Returns a bytestring, or raises and exception
    '''
    if not isinstance(bytesdata, bytes):
        raise TypeError("we expect a bytestring, not a %s"%type(bytesdata))
    z = zipfile.ZipFile( io.BytesIO(bytesdata) )
    if len( z.filelist ) == 0:
        raise ValueError('empty ZIP file')
    else:
        for zipinfo in z.filelist:
            if zipinfo.filename.endswith('.html'):
                return z.read( zipinfo )
    raise ValueError('ZIP file without a .html')
