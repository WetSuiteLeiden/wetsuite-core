"""
This code attempts to make it easier to deal with human variation in references to laws.

This is code that doesn't have a specific spec to adhere to, 
will never be perfect, and is relatively creative in ways 
that you don't have complete control over.

It has nonetheless seen repeated use. 

It is included to make some things easier, 
and to steal fragments of code for if you want to refine its functionality.

"""

import requests
import bs4

import wetsuite.helpers.localdata


_deeplink_resolved_redirections = wetsuite.helpers.localdata.LocalKV( 'redirect_urls.db', str, str )
_deeplink_resolved_bwbs         = wetsuite.helpers.localdata.LocalKV( 'redirect_bwbs.db', str, str )



def resolve_deeplink_bwbid(url, use_cache=True):
    """ 
        CVDR has links to laws that look like:
            http://wetten.overheid.nl/cgi-bin/deeplink/law1/title=Burgerlijk%20Wetboek%20Boek%201
            http://wetten.overheid.nl/cgi-bin/deeplink/law1/bwbid=BWBR0005537/article=1:2
        that go to:
            https://wetten.overheid.nl/BWBR0002656/2024-01-01
            https://wetten.overheid.nl/BWBR0005537/2024-09-01/#Hoofdstuk1_Titeldeel1.1_Artikel1:2

        While 'deeplink' may not be the best name for 'resolver', it's thet term that is used.
        Note that the resolver it quieries live can be SLOW, 
        so this function is equally slow to respond the first time we see such a link.
        We cache results on disk, so that later reponses can be fast,
        but keep in mind that over time the resolver's answer may change.

    """
    if 'http://wetten.overheid.nl/cgi-bin/deeplink/law1' not in url:
        raise ValueError("We only deal with URLs that start with http://wetten.overheid.nl/cgi-bin/deeplink/law1")

    if (use_cache and 
        (url in _deeplink_resolved_bwbs  and  url in _deeplink_resolved_redirections) # we have it in cache
        ): # ensure they keep roughly in sync
        #print("CACHED for %r"%url)
        retval = _deeplink_resolved_bwbs.get( url ) # which might be None
        if retval == 'None': # special casing, since it's either that or a BWBR. We _could_ store 'could not resolve' and its reason, but there is little point.
            return None
        return retval
    else:
        #print("FETCHING %r"%url)
        resp = requests.get(url, allow_redirects=True, timeout=60)  # this redirect service can be SLOW
        # we can record the URL it sent us to, which can help resolve article references too
        _deeplink_resolved_redirections.put( url, resp.url ) # TODO: double check that this we understand this and resp.history

        # but this function cares only about the BWB-ID so we also store just that
        soup = bs4.BeautifulSoup(resp.content)
        identifier_tags = soup.select("meta[name='dcterms:identifier']") # wetten.overheid.nl pages have a <head> <meta> tag
        if len(identifier_tags)>0:
            bwbid = identifier_tags[0].get('content')
            _deeplink_resolved_bwbs.put( url, bwbid )
            return bwbid
        else:
            if b'De opgevraagde pagina is niet gevonden' in resp.content:
                #print("DID NOT RESOLVE %r"%resp.history[-1].url)
                _deeplink_resolved_bwbs.put( url, 'None' )
            elif b'Gebruikt formaat in de URL wordt niet ondersteund' in resp.content:
                #print("DID NOT RESOLVE %r"%resp.history[-1].url)
                _deeplink_resolved_bwbs.put( url, 'None' )
            else:
                raise ValueError("DID NOT HANDLE %r"%resp.history[-1].url)
            return None
