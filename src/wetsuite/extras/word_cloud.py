#!/usr/bin/python3
"""
    Create wordcloud images; mostly a thin wrapper module around an existing wordcloud module.

    The wordcloud module we use likes to wrap all logic and parameters in one big class,
    so this (thin) wrapper module exists largely to separate out the counting,
        - to introduce some flexibility in how we count in a wordcloud.
        - and to make those counting functions usable for other things

    That image will look a bunch cleaner when you have cleaned up the string:count,
    so take a look at using the counting helper functions in helpers.strings.
"""
import collections
import warnings
from typing import List

# The wordcloud module imports matplotlib so we might need to ensure a non-graphical backend by doing that _first_
#   TODO: read up, IIRC it's good to do this conditionally and lazily?
with warnings.catch_warnings():
    #warnings.simplefilter("ignore")  # meant to ignore some deprecation warnings
    import matplotlib
    matplotlib.use("Agg")

import wordcloud  #  if not installed, do  pip3 install wordcloud       also this is intentionally after the previous, so:   pylint: disable=C0413

import wetsuite.helpers.strings



def count_from_string(s:str, tokenizer=wetsuite.helpers.strings.simple_tokenize, stopwords=(), stopwords_i=()):
    """ Take string, tokenize, count, return word:count dict.

        @param tokenizer: function to tokenize with.
        @param stopwords: sequence of strings to remove (case sensitive)
        @param stopwords_i: sequence of strings to remove (case insensitive)
        @return: a dict of string to count
    """
    string_list = tokenizer(s)
    return count_from_stringlist(string_list, stopwords=stopwords, stopwords_i=stopwords_i)


def count_from_stringlist(string_list: List[str], stopwords=(), stopwords_i=()):
    """ Takes a list of strings (e.g. a document that you have already tokenized into words; if you want us to do that for you, look at count_from_string).

        Fixed to count in a way that is count insensitive, and then uses the most common capitalisation it saw.
        If you want control over the counting, do it yourself and look at wordcloud_from_freqs.

        @param string_list: list of strings, the input to work on
        @param stopwords: sequence of strings to remove (case sensitive)
        @param stopwords_i: sequence of strings to remove (case insensitive)
        @return: a dict of string to count
    """
    return wetsuite.helpers.strings.count_case_insensitive( string_list, stopwords=stopwords, stopwords_i=stopwords_i)



def merge_counts(count_dicts: List[dict]):
    " Take a sequence of string-to-count dicts,  add counts together into one dict "
    count = collections.Counter()
    for count_dict in count_dicts:
        count += collections.Counter( count_dict )
    return count



def wordcloud_from_freqs(
    freqs: dict,
    width: int = 1200,
    height: int = 300,
    background_color="white",
    min_font_size=10,
    **kwargs
):
    """Takes a {string: count} dict, returns a PIL image object.

    @return: a PIL image  (you can e.g. display() or .save() this)
    """
    wco = wordcloud.WordCloud(
        width=width,
        height=height,
        background_color=background_color,
        min_font_size=min_font_size,
        **kwargs
    )
    im = wco.generate_from_frequencies(freqs)
    return im.to_image()


def wordcloud_from_string(s:str, tokenizer=wetsuite.helpers.strings.simple_tokenize, counter=wetsuite.helpers.strings.count_case_insensitive, **kwargs):
    """ Work from a non-processed string; makes choices in tokenizing and counting.
        @param tokenizer: function to tokenize with.
        @param counter: function to count with
        @return: Image
    """
    string_list = tokenizer(s)
    return wordcloud_from_stringlist( string_list, counter=counter, **kwargs )


def wordcloud_from_stringlist(string_list: List[str], counter=wetsuite.helpers.strings.count_case_insensitive, **kwargs):
    """ Work from a non-processed string; makes choices in counting.
        
        @return: Image
    """
    freqs = counter( string_list )
    return wordcloud_from_freqs(freqs,**kwargs)
