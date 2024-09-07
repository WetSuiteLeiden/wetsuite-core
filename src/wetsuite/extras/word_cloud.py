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
import warnings
from typing import List

import wetsuite.helpers.strings


# The wordcloud module imports matplotlib so we might need to ensure a non-graphical backend
#   TODO: read up, IIRC it's good to do this conditionally and lazily?

with warnings.catch_warnings():
    warnings.simplefilter("ignore")  # meant to ignore some deprecation warnings
    import matplotlib

    matplotlib.use("Agg")

import wordcloud  #  if not installed, do  pip3 install wordcloud       also this is intentionally after the previous, so:   pylint: disable=C0413

# note that it draws in matplotlib, numpy, and PIL
# and unlike the linter suggests, it should _NOT_ be above the matplotlib import


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


def wordcloud_from_stringlist(string_list: List[str], counter=wetsuite.helpers.strings.count_case_insensitive, **kwargs):
    """ Work from a non-processed string; makes choices in counting.
    """
    freqs = counter( string_list )
    return wordcloud_from_freqs(freqs,**kwargs)


# TODO: clarify the args
def wordcloud_from_string(s:str, tokenizer=wetsuite.helpers.strings.simple_tokenize, counter=wetsuite.helpers.strings.count_case_insensitive, **kwargs):
    """ Work from a non-processed string; makes choices in tokenizing and counting.
    """
    string_list = tokenizer(s)
    return wordcloud_from_stringlist( string_list, counter=counter, **kwargs )
