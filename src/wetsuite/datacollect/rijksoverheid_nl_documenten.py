#!/usr/biny/python3
""" 

Code to help fetch things from https://www.rijksoverheid.nl/documenten

"""

import datetime
import warnings
import time
import urllib.parse

import bs4

import wetsuite.helpers.net
import wetsuite.helpers.strings
import wetsuite.helpers.etree
import wetsuite.helpers.escape



# In case we want to use this source for more than Woo, ministerie and doctype

ministeries = [
  ('Alle ministeries', 'Alle ministeries'),
  ('Ministerie van Algemene Zaken', 'Ministerie van Algemene Zaken'),
  ('Ministerie van Asiel en Migratie', 'Ministerie van Asiel en Migratie'),
  ('Ministerie van Binnenlandse Zaken en Koninkrijksrelaties',
   'Ministerie van Binnenlandse Zaken en Koninkrijksrelaties'),
  ('Ministerie van Buitenlandse Zaken', 'Ministerie van Buitenlandse Zaken'),
  ('Ministerie van Defensie', 'Ministerie van Defensie'),
  ('Ministerie van Economische Zaken', 'Ministerie van Economische Zaken'),
  ('Ministerie van Financiën', 'Ministerie van Financiën'),
  ('Ministerie van Infrastructuur en Waterstaat',
   'Ministerie van Infrastructuur en Waterstaat'),
  ('Ministerie van Justitie en Veiligheid',
   'Ministerie van Justitie en Veiligheid'),
  ('Ministerie van Klimaat en Groene Groei',
   'Ministerie van Klimaat en Groene Groei'),
  ('Ministerie van Landbouw, Visserij, Voedselzekerheid en Natuur',
   'Ministerie van Landbouw, Visserij, Voedselzekerheid en Natuur'),
  ('Ministerie van Onderwijs, Cultuur en Wetenschap',
   'Ministerie van Onderwijs, Cultuur en Wetenschap'),
  ('Ministerie van Sociale Zaken en Werkgelegenheid',
   'Ministerie van Sociale Zaken en Werkgelegenheid'),
  ('Ministerie van Volksgezondheid, Welzijn en Sport',
   'Ministerie van Volksgezondheid, Welzijn en Sport'),
  ('Ministerie van Volkshuisvesting en Ruimtelijke Ordening',
   'Ministerie van Volkshuisvesting en Ruimtelijke Ordening')
 ]

doctypes = [
  ('Alle documenten', 'Alle documenten'),
  ('Ambtsbericht', 'Ambtsbericht'),
  ('Begroting', 'Begroting'),
  ('Beleidsnota', 'Beleidsnota'),
  ('Besluit', 'Besluit'),
  ('Brief', 'Brief'),
  ('Brochure', 'Brochure'),
  ('Circulaire', 'Circulaire'),
  ('Convenant', 'Convenant'),
  ('Diplomatieke verklaring', 'Diplomatieke verklaring'),
  ('Formulier', 'Formulier'),
  ('Geluidsfragment', 'Geluidsfragment'),
  ('Jaarplan', 'Jaarplan'),
  ('Jaarverslag', 'Jaarverslag'),
  ('Kaart', 'Kaart'),
  ('Kamerstuk', 'Kamerstuk'),
  ('Mediatekst', 'Mediatekst'),
  ('Rapport', 'Rapport'),
  ('Regeling', 'Regeling'),
  ('Richtlijn', 'Richtlijn'),
  ('Toespraak', 'Toespraak'),
  ('Vergaderstuk', 'Vergaderstuk'),
  ('Vergunning', 'Vergunning'),
  ('Video', 'Video'),
  ('Vraag en antwoord', 'Vraag en antwoord'),
  ('Wob-verzoek', 'Wob-verzoek'),
  ('Woo-besluit', 'Woo-besluit')
]

#We assume the two above lists won't change, but if they do, they came from the following code:
# htmlbytes = wetsuite.helpers.net.download( 'https://www.rijksoverheid.nl/documenten' )
# soup = bs4.BeautifulSoup(htmlbytes, features='lxml')
#
# ministeries = []
# for option in soup.select('select#unit option'): # ministerie
#     ministeries.append( (option.get('value'), option.text.strip()) )
#
# doctypes = []
# for option in soup.select('select#type option'): # document type
#     doctypes.append( (option.get('value'), option.text.strip()) )
#
# In both cases, the first is the form value, the second the description. These currently match.



def scrape_pagination(doctype, detail_page_callback,  from_date=None, to_date=None, debug=False):
    ''' Go through the pagination for a specific document type,
        calls a callback for each item's detail page URL.

        What to do with the result is still up to you: you implement a 
        detail_page_callback that gets the URL.
        There is a notebook with some examples.
    
        As of this writing, we work around a flaw that has probably been corrected since;
        TODO: describe, check, remove?

        This should take _order of magnitude_ of dozens of minutes per thousand items
        ...mostly because of the backoff to be nice to the server.

        This function hardcodes some delays, to not be rude to the server. 
        We could make that async.

        @param from_date: Start of date range to fetch
        When from_date and to_date are not given, it defaults to the last four weeks, from call time.
        If given, both should be a date or datetime. 
        This in part because if you want to fetch _everything_ from the servers, we make you be explicit about it.

        @param to_date: End of date range to fetch (if from_date is also given)

        @param detail_page_callback: this is called for each item. It should accept two arguments
        - soup fragment for it on the pagination page (you can often ignore this)
        - a detail page URL
    '''

    if from_date is None and to_date is None:
        from_date = (datetime.datetime.now() - datetime.timedelta(days=4*7))
        to_date = datetime.datetime.now()
    else:
        if not isinstance(from_date, (datetime.date, datetime.datetime)) or not isinstance(to_date, (datetime.date, datetime.datetime)):
            raise ValueError("from_date and to_date must be given at the same time, and both be date or datetime")

    pagination_to_fetch = set() # set of urls
    pagination_fetched  = {} # url -> (ignored)

    ## Split query into shortish date intervals
    # searches don't seem to show more than 50 pages of results (500 results at 10 per page),
    #   so larger ranges should be split into separate searches.
    # This is overzealous for most oocument types, but necessary for some.
    # since we can (later) pick up the other-page links,
    #   we can add the first page for each range, and it'll pick up the rest of the results.
    interval_start = from_date
    days_indrement = 30 # if the query results in > 500 in 30 days, this omits some in that period
    while interval_start < to_date:
        interval_end = interval_start + datetime.timedelta(days=days_indrement) 
        # TODO: see if we need a min() to not ask for future dates


        add_url = 'https://www.rijksoverheid.nl/documenten?type=%s&startdatum=%s&einddatum=%s'%(
                wetsuite.helpers.escape.uri_component(doctype),
                interval_start.strftime('%d-%m-%Y'),  # e.g. 01-01-2022
                interval_end.strftime('%d-%m-%Y'),
            )
        if debug:
            print('add_url', add_url )
        pagination_to_fetch.add( add_url )
        interval_start = interval_end

    ## Fetch the pagination pages -- not yet the detail pages
    while len(pagination_to_fetch) > 0:   # we add numbered pagination pages as we go
        result_page_url = pagination_to_fetch.pop()                 # pick a page to do next
        if debug:
            print('PAGE', result_page_url)
        page_bytes = wetsuite.helpers.net.download( result_page_url ) # fetch
        result_page_soup = bs4.BeautifulSoup(page_bytes, features='lxml') # parse HTML
        for a in result_page_soup.select("ul.paging__numbers li a"): # look for links to other pages
            other_page_url = a.get('href')
            if 'pagina' in other_page_url  and  other_page_url not in pagination_fetched:
                pagination_to_fetch.add(other_page_url) # add to the 'still to fetch' set
                if 'pagina=50' in other_page_url:
                    warnings.warn(
                        'Arrived at page 50 for a search, we may be missing some data. '
                        'Make the suggestion to programmers that days_increment should be lower. ')
        pagination_fetched[result_page_url] = True
        time.sleep(2)  # be slightly nice to the server  (makes up most of the time spent)

        for li in result_page_soup.select('main ol.results li.results__item'):
            # each result item on that page is mostly a short summary,
            #   and a link to a detail page at another URL, which duplicates most information so we only focus on the detail page
            a = li.select('a.publication')[0] # assumes there is just one a in the item / li
            url = urllib.parse.urljoin( result_page_url, a.get('href') ) # relative to the page, so resolve it relative to the page URL we're on

            detail_page_callback(li, url)
            #time.sleep(2)  # be slightly nice to the server  (makes up most of the time spent)
