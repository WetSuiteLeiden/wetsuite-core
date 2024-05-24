'''
    Functions that help access the BulkUitleverSysteem,
    an SFTP store mentioned e.g. in 
    https://data.overheid.nl/sites/default/files/dataset/d0cca537-44ea-48cf-9880-fa21e1a7058f/resources/Handleiding%2BSRU%2B2.0.pdf
'''

import tempfile

_bf = None


def normalize_path( path:str ):
    ''' Given a path like either of:
          - ftps://bestanden.officielebekendmakingen.nl/2024/05/17/gmb/gmb-2024-216934/
          - /2024/05/17/gmb/gmb-2024-216934/
        Returns the path within that server, in this example: 
          - /2024/05/17/gmb/gmb-2024-216934/
    '''
    if path.startswith('sftp://'):
        path = path[path.find('/', 10):]
    if path.startswith('ftps://'): # the OEP SRU interface seems to just get this wrong, but so let's be robust to that
        path = path[path.find('/', 10):]
    return path


def id_from_path( path:str ):
    ''' Given a path like
          - ftps://bestanden.officielebekendmakingen.nl/2024/05/17/gmb/gmb-2024-216934/
          - /2024/05/17/gmb/gmb-2024-216934/
          
        Returns: 
          - 'gmb-2024-216934'

        TODO: mention the various edge cases
    '''
    path = normalize_path( path )
    return path.split('/')[5]



class BUSFetcher:
    '''
        The server we're accessing doesn't like us having more than two connections within some time,
        so let's try to keep it open and share between calling code.

        It's a little more awkward if you just want to fetch one document, though. 
    '''
    def __init__(self):
        self._sftp_connection = None

    def connect(self):
        """ (re)connect if necessary (necessity judged based on whether a simple listdir works)
            I expect the setup behind this SSH/SFTP connection is finicky. 
            If it doesn't connect at all, it isn't you, and we should do more research and fix it for you.
        """
        reconnect = False
        if self._sftp_connection is None:
            reconnect = True
        else: # must be a connection object
            try:
                self._sftp_connection.listdir('/') # should be a bunch of years
            except OSError: # we expect this to be "Socket is closed"
                # TODO: figure out other specific exceptions
                reconnect = True

        if reconnect:
            import pysftp   # if this line fails, you probably want to do a   !pip install pysftp   (which would also install paramiko)
            cnopts = pysftp.CnOpts()
            cnopts.hostkeys = None    # TODO: figure out whether this can pick up ~/.ssh/config regardless
            self._sftp_connection   = pysftp.Connection('bestanden.officielebekendmakingen.nl', username='anonymous', password='anonymous', cnopts=cnopts)
            #could throw paramiko.ssh_exception.SSHException   (which only inherits form Exception)

        return self._sftp_connection


    def listdir(self, path): # , stat=True
        """
            Given a path like either of:
            - ftps://bestanden.officielebekendmakingen.nl/2024/05/17/gmb/gmb-2024-216934/
            - /2024/05/17/gmb/gmb-2024-216934/
            Returns: a list of files under that path.

            You probaby ONLY want to use this for specific document sets -- where such a path ends in a specific identifier.
            Any more general and would be SLOW, particularly if you are only doing it to list files
        """
        sftp = self.connect()
        path = normalize_path( path )
        # CONSIDER: raise on unexpected path values
        #ret = []
        #def _add(fn):
        #    ret.append( fn )
        #def _ignore(_):
        #    pass
        return sftp.listdir(path)#, fcallback=_add, dcallback=_ignore, ucallback=_ignore)
        #return ret



    def get_file(self, remotepath, saveto):
        ''' Save a remote path to a local filesystem by path.
            Be careful with the target path.
        '''
        sftp = self.connect()
        sftp.get(remotepath, saveto)


    def get_bytes(self, remotepath):
        ''' Save a remote path to memory, return as a bytes object
            (goes via a temporary file on the filesystem, which should be cleaned up before this function returns)
        '''
        sftp = self.connect()
        with tempfile.NamedTemporaryFile() as tf: # (note: close implies delete of that temporary file, so we don't have to worry about it)
            #print( tf.name )
            try:
                sftp.get(remotepath, tf.name)
            except Exception as e:
                raise ValueError( 'ERROR fetching %r: %s'%(remotepath, e) )  from e
                #raise
            tf.seek(0)
            filedata = tf.read()
        return filedata


# for less typing for some one-offs:
def _bus_get_bytes(path:str):
    global _bf
    if _bf is None:
        _bf = BUSFetcher()
    return _bf.get_bytes(path)
