''' Extract text from HTML in a somewhat structured way.

    Can be informed of specific types of document
'''


import re
import json
import sys
from typing import List, Union
import warnings

import click

from bs4 import BeautifulSoup, Comment, PageElement


# TODO Include metadata for chunks

presets = {
    'beleidsregels': {
        'body': { 'name': 'div', 'id': 'PaginaContainer' },
        'keep_headers_html': True,
        'keep_tables_html': True,
    },
}
''' Presets are an "if it is this kind of HTML, this is how to extract parts" thing, so that this is separated from code as much as possible.

    body informs it of ( kwargs to find() )

'''
# TODO Add more document presets, and test their validty


# for _flatten_html, matches against element names
table_re           = re.compile(r'table ?')  # optional space because somewhere in beleidsregels typo "table "
header_re          = re.compile(r'h\d')
indentation_re     = re.compile(r'\n(?:  |\t)+')
newlines_re        = re.compile(r'\n\n+')
list_re            = re.compile(r'li')
markup_re          = re.compile(r'strong|em')

# for _table_to_str
non_tabular_tag_re = re.compile(r'<(?!\/?(?:(?:table|td|tr) ?)\b)[^>]+>')

# for _split_cleaned_html
#split_re = re.compile(r'(<h\d>|<table ?>)')
sentence_re = re.compile(r'([^.?!]+[.?!]\b)', flags=re.MULTILINE)




def _flatten_html(html, keep_headers_html, keep_tables_html, body):
    ''' Parse HTML, 
    
    '''
    soup = BeautifulSoup(html, 'html.parser')
    if body := soup.find(**body):
        soup = body

    result = []
    for element in soup.descendants:
        if element.__dict__.get('skip', False):  # will be set to true for all descendants of tables
            continue

        if isinstance(element, Comment):
            continue

        element.attrs = {}

        if keep_headers_html and element.name and header_re.match(element.name):
            result.append('\n' + str(element))
            element.next_element.extract()

        elif keep_tables_html and element.name and table_re.match(element.name):
            tabletext = _table_to_str(element)
            result.append(tabletext)
            for el in element.descendants:
                el.skip = True

        elif element.name and (list_re.match(element.name) or markup_re.match(element.name)):
            result.append(element.text)
            for el in element.descendants:
                el.skip = True

        elif element.strip is not None and element.strip():
            result.append(element.strip())

    flat_html = '\n'.join(result)
    flat_html = indentation_re.sub(' ', flat_html)
    flat_html = newlines_re.sub('\n', flat_html)
    flat_html = flat_html.replace('  ', ' ')

    return flat_html


def html_to_text(html: Union[str, bytes],
                 keep_headers_html: bool = False,
                 keep_tables_html: bool = False,
                 body: Union[str, dict] = None):
    '''
        Takes HTML as a string, return 
        Cleans HTML by removing most/all tags, keeping only headers and tables (if requested).
        :param html: HTML document as a str or bytes (TODO: test that it deals with both)
        :param keep_headers_html:
        :param keep_tables_html:
        :param body: which part of the html to consider; kwargs for BeautifulSoup.find(), for instance {'name': 'div', 'id': 'PaginaContainer'}
        :return: flattened version of the html, with most or all tags removed
    '''
    text = _flatten_html(html, keep_headers_html, keep_tables_html, body)
    return text


def html_to_chunks(html: str,
                   chunk_n_tokens: int = 500,
                   sent_tokenize=False,
                   **kwargs,
                   ) -> str:
    """
    Cleans a html and splits it into chunks, respecting headers and tables if present.
    It assumes lines in the original html are meaningful, and does not by default split them up.
    If resulting chunks are too big, try setting sent_tokenize=True.
    :param html: html string
    :param chunk_n_tokens:
    :param sent_tokenize:
    :param kwargs: passed on to flatten_html
    :return: Plain text representation of the html page
    """

    flat_html = _flatten_html(html, **kwargs)

    basic_chunks = _split_cleaned_html(flat_html, chunk_n_tokens, sent_tokenize=sent_tokenize)
    merged_chunks = _merge_chunks(basic_chunks, chunk_n_tokens)
    for n, chunk in enumerate(merged_chunks):
        yield {'chunk_id': n, 'text': chunk}




def _table_to_str(element: PageElement) -> str:
    '''
    '''
    for el in element.descendants:
        el.attrs = {}
    cleaned = non_tabular_tag_re.sub('', str(element))
    return '\n' + cleaned + '\n'




def _split_cleaned_html(html: str, chunk_size: int, sent_tokenize: bool) -> List[str]:
    ''' Split a (cleaned) html into chunks, trying to respect sections and tables if present, 
        but can split between sentences if necessary (with sent_tokenize=True).
    '''

    if sent_tokenize:
        html = '\n'.join(html.split(sentence_re))

    chunks = [[]]
    current_chunk_size = 0
    currently_in_table = False

    def new_chunk():
        nonlocal current_chunk_size
        if current_chunk_size > chunk_size:
            warnings.warn(f'A chunk is too large ({current_chunk_size} > {chunk_size}), consider setting sent_tokenize to True.')

        if chunks[-1]:
            chunks.append([])
            current_chunk_size = 0

    for line in html.splitlines(keepends=True):
        new_n_tokens = len(line.split())

        if line.startswith('<h') and not chunks[-1][-1].startswith('<h'):  # e.g. don't cut between a <h2> and subsequent <h3>
            new_chunk()

        if line.startswith('<table'):
            new_chunk()
            currently_in_table = True

        if (current_chunk_size + new_n_tokens) > chunk_size and not currently_in_table:
            new_chunk()

        chunks[-1].append(line)
        current_chunk_size += new_n_tokens

        if line.startswith('</table'):
            currently_in_table = False
            new_chunk()

    chunks = [''.join(chunk) for chunk in chunks]
    return chunks


def _merge_chunks(chunks: List[str], chunk_size: int) -> List[str]:
    '''
        Will greedily merge chunks, front to back, until (at most) chunk size is reached.
    '''

    merged_chunks = ['']
    merged_chunk_size = 0
    for chunk in chunks:
        new_n_tokens = len(chunk.split())
        if merged_chunks[-1] and merged_chunk_size + new_n_tokens > chunk_size:
            merged_chunks.append('')
            merged_chunk_size = 0
        merged_chunks[-1] += '\n' + chunk
        merged_chunk_size += new_n_tokens

    merged_chunks = [chunk for chunk in merged_chunks if chunk.strip()]

    return merged_chunks



@click.command()
@click.option("--file", help="Name of html file; omit to read from STDIN.", type=click.File("rt"), default=sys.stdin)
@click.option('--headers', is_flag=True, default=False)
@click.option('--tables', is_flag=True, default=False)
@click.option('--body', is_flag=False, default=None, type=str,
              help='json specification of html element containing the body, e.g., {"name": "div", "id": "PaginaContainer"}')
@click.option('--preset', is_flag=False, default=None, type=str, help='Key for default settings to use, e.g., "beleidsregels"')
@click.option('--chunk_n_tokens', is_flag=False, default=None, type=int, help='Max chunk length in number of tokens.')
def main(file: click.File("rt"), headers: bool, tables: bool, body: str, preset: str, chunk_n_tokens: int):
    """
    Example:
    python html_to_text.py --file "data/damocles/html/CVDR615984_3.html" --headers --tables --body beleidsregels
    """
    if body and body.startswith('{'):
        body = json.loads(body)

    with file:
        html = file.read()

    settings = presets[preset] if preset else {
        'keep_headers_html': headers,
        'keep_tables_html': tables,
        'body': body,
    }

    if chunk_n_tokens:
        # print chunks at a time
        chunks = html_to_chunks(html, chunk_n_tokens, **settings)
        for chunk in chunks:
            chunk['source_file'] = file.name
            chunk['id'] = f"{chunk['source_file']}_{chunk['chunk_id']}"
            print(json.dumps(chunk))
    else:
        # print one big text
        result = html_to_text(html, **settings)
        print(result)


if __name__ == '__main__':
    main()



# test_html_content = """
# <html>
#   <body>
#      <div id='PaginaContainer'>
#     <h1>Title</h1>
#     <p>This is a paragraph.</p>
#     <h2>Subtitle</h2>
#     <p>Another paragraph.</p>
#     <table>
#     <tr><td> <b>test</b> </td> <td> lol </td></tr>
#     <tr><td> test2 </td> <td> lol2 </td></tr>
#     </table>
#     <p>Inside of the div</p>
#     </div>
#     <p>Outside of the div!</p>
#   </body>
# </html>
# """
