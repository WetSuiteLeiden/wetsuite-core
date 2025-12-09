"""
Helpers to deal with XML data, largely a wrapper around lxml and its ElementTree interface.

TODO: minimize the amount of "will break because we use the lxml flavour of ElementTree", and add more tests for that.

Some general helpers.
...including some helper functions shared by some debug scripts.

CONSIDER:
  - A "turn tree into nested dicts" function - see e.g. https://lxml.de/FAQ.html#how-can-i-map-an-xml-tree-into-a-dict-of-dicts
  - have a fromstring() as a thin wrapper but with strip_namespace in there? (saves a lines but might be a confusing API change)
"""

import copy
import warnings
import re

import lxml.etree
import lxml.html
from lxml.etree import (  # to expose them as if they are our own members     pylint: disable=no-name-in-module,unused-import
    ElementTree,
    fromstring,
    tostring,
    register_namespace,
    Element,
    SubElement,
    _Comment,
    _ProcessingInstruction,
)

SOME_NS_PREFIXES = {  # CONSIDER: renaming to something like _some_ns_prefixes_presetation_only
    # Web and data
    "http://www.w3.org/2000/xmlns/": "xmlns",
    "http://www.w3.org/2001/XMLSchema": "xsd",
    # ?   Also, maybe avoid duplicate names? Except we are only doing this _only_ for pretty printing.
    #'http://www.w3.org/2001/XMLSchema#':'xsd',
    "http://www.w3.org/XML/1998/namespace": "xml",
    "http://www.w3.org/2001/XMLSchema-instance": "xsi",
    "http://www.w3.org/1999/xhtml": "xhtml",
    "http://www.w3.org/1999/xlink": "xlink",
    "http://schema.org/": "schema",
    "http://www.w3.org/2005/Atom": "atom",
    "http://www.w3.org/2000/svg": "svg",
    "http://www.w3.org/1998/Math/MathML": "mathml",  # more usually m: or mml: but this may be clearer
    "http://www.w3.org/2001/XInclude": "xi",
    "http://www.w3.org/1999/XSL/Transform": "xsl",  # there seem to be multiple. See also http://www.w3.org/XSL/Transform/1.0 and http://www.w3.org/TR/WD-xsl ?
    "http://www.w3.org/2005/xpath-functions#": "xpath-fn",
    #'http://icl.com/saxon':'saxon',
    #'http://xml.apache.org/xslt':'xalan',
    "http://www.w3.org/1999/XSL/Format": "fo",
    "http://www.w3.org/2003/g/data-view#": "grddl",
    "http://www.w3.org/2006/time#": "time",
    # getting into semantic data, linked data
    # cf dc, see also https://stackoverflow.com/questions/47519315/what-is-the-difference-between-dublin-core-terms-and-dublin-core-elements-vocabu
    "http://purl.org/dc/terms/": "dcterms",
    "http://purl.org/dc/elements/1.1/": "dc",
    "http://purl.org/cld/freq/": "freq",
    "http://www.w3.org/1999/02/22-rdf-syntax-ns#": "rdf",
    "http://www.w3.org/2000/01/rdf-schema": "rdfs",
    "http://www.w3.org/2000/01/rdf-schema#": "rdfs",
    "http://www.w3.org/ns/rdfa#": "rdfa",
    "http://www.w3.org/TR/vocab-regorg/": "rov",
    "http://www.w3.org/TR/vocab-org/": "org",
    "http://www.w3.org/2004/02/skos/core#": "skos",
    "http://www.w3.org/TR/skos-reference/": "skosref",
    "http://www.w3.org/2008/05/skos-xl#": "skosxl",
    "http://www.w3.org/2002/07/owl#": "owl",
    "http://rdfs.org/ns/void#": "void",  # Vocabulary of Interlinked Datasets
    "http://purl.org/rss/1.0/modules/content/": "content",
    "http://purl.org/linked-data/version#": "version",
    "http://www.w3.org/ns/locn": "location",
    "http://xmlns.com/foaf/0.1/": "foaf",
    "http://ogp.me/ns#": "opengraph",
    "http://rdfs.org/sioc/ns#": "sioc",
    "http://rdfs.org/sioc/types#": "sioc-types",
    "http://purl.org/linked-data/registry#": "reg",
    "http://www.w3.org/ns/prov#": "prov",
    "http://purl.org/pav/": "pav",
    # Government
    "http://tuchtrecht.overheid.nl/": "tucht",
    "http://www.tweedekamer.nl/xsd/tkData/v1-0": "tk",
    "http://publications.europa.eu/celex/": "celex",
    "http://decentrale.regelgeving.overheid.nl/cvdr/": "cvdr",
    "http://psi.rechtspraak.nl/": "psi",
    "https://e-justice.europa.eu/ecli": "ecli",
    "http://www.rechtspraak.nl/schema/rechtspraak-1.0": "recht",  # ?
    "http://standaarden.overheid.nl/owms/terms/": "overheid",
    "http://standaarden.overheid.nl/owms/terms": "overheid",  # maybe 'owms' would be clearer?
    "http://standaarden.overheid.nl/rijksoverheid/terms": "rijksoverheid",
    "http://standaarden.overheid.nl/inspectieloket/terms/": "inspectieloket",
    "http://standaarden.overheid.nl/buza/terms/": "overheid-buza",
    "http://standaarden.overheid.nl/oep/meta/": "overheid-oep",
    "http://standaarden.overheid.nl/op/terms/": "overheid-op",
    "http://standaarden.overheid.nl/product/terms/": "overheid-product",
    "http://standaarden.overheid.nl/cvdr/terms/": "overheid-rg",  # decentrale regelgeving
    "http://standaarden.overheid.nl/vac/terms/": "overheid-vac",  # ?vocabularies?
    "http://standaarden.overheid.nl/vb/terms/": "overheid-vastgoedbeheer",
    "http://standaarden.overheid.nl/bm/terms/": "overheid-bm",
    "http://standaarden.overheid.nl/vergunningen/terms/": "overheid-vergunning",
    "http://standaarden.overheid.nl/dcatnl/terms/": "dcatnl",
    "http://publications.europa.eu/resource/authority/file-type/": "file-type",
    "http://standaarden-acc.overheid.nl/owms/oquery/": "oquery",
    "https://identifier.overheid.nl/tooi/id/ministerie/": "ministerie",
    "https://identifier.overheid.nl/tooi/def/": "tooi",
    "https://identifier.overheid.nl/tooi/def/ont/": "tooiont",
    "https://identifier.overheid.nl/tooi/def/thes/top/": "tooitop",
    "https://identifier.overheid.nl/tooi/def/wl/": "tooiwl",
    # unsorted
    "http://spinrdf.org/sp#": "sparql-spin",
    "http://proton.semanticweb.org/2005/04/protons#": "protons",
    "http://purl.org/NET/scovo#": "scovo",  # Statistical Core Vocabulary?
    "http://rdf4j.org/schema/rdf4j#": "rdf4j",
    "http://www.openrdf.org/schema/sesame#": "sesame",
    "http://schemas.microsoft.com/ado/2007/08/dataservices": "ms-odata",
    "http://schemas.microsoft.com/ado/2007/08/dataservices/metadata": "ms-odata-meta",
    "www.kadaster.nl/schemas/lvbag/gem-wpl-rel/gwr-producten-lvc/v20200601": "bag",
    "www.kadaster.nl/schemas/lvbag/gem-wpl-rel/bag-types/v20200601": "bag-types",
    #'www.kadaster.nl/schemas/lvbag/gem-wpl-rel/gwr-deelbestand-lvc/v20200601':'bag-o',
    #'http://www.kadaster.nl/schemas/lvbag/extract-selecties/v20200601':'bag-s',
}
""" some readable XML prefixes, for friendlier display.
    This is ONLY for consistent pretty-printing in debug,
    and WILL NOT BE CORRECT according to the document definition.
    (It is not used by code in this module, just one of our CLI utilities).
"""
# It might be useful to find namespaces from many XML files, with something like:
#   locate .xml | tr '\n' '\0' | xargs -0 grep -oh 'xmlns:[^ >]*'
# with an eventual
#   | sort | uniq -c | sort -rn


def kvelements_to_dict(under_node, strip_text=True, ignore_tagnames=()) -> dict:
    """Where people use elements for single text values, it's convenient to get them as a dict.

    Given an etree element containing a series of such values,
    Returns a dict that is mostly just  { el.tag:el.text }  so ignores .tail
    Skips keys with empty values.

    Would for example turn an etree fragment like ::
        <foo>
            <identifier>BWBR0001840</identifier>
            <title>Grondwet</title>
            <onderwerp/>
        </foo>
    into python dict: ::
        {'identifier':'BWBR0001840', 'title':'Grondwet'}

    @param under_node: etree node/element to work under (use the children of)
    @param strip_text: whether to use strip() on text values (defaults to True)
    @param ignore_tagnames: sequence of strings, naming tags/variables to not put into the dict
    @return: a python dict (see e.g. example above)
    """
    ret = {}
    for ch in under_node:
        if isinstance(ch, (_Comment, _ProcessingInstruction)):
            continue
        if ch.tag in ignore_tagnames:
            continue
        if ch.text is not None:
            text = ch.text
            if strip_text:
                text = text.strip()
            ret[ch.tag] = text
    return ret


def _strip_comment_pi_inplace(tree, strip_comment=True, strip_pi=True):
    """ Strip comments and processing instructions from existing tree

        This can be handy in readout code, in that otherwise you have to isinstance-test for that in a lot of code.
    """

    remove_me = set()
    for elem in tree.iter():
        if strip_comment and isinstance(elem, _Comment):
            remove_me.add( elem )
        if strip_pi      and isinstance(elem, _ProcessingInstruction):
            remove_me.add( elem )

    for rm_elem in remove_me:
        rm_elem.getparent().remove( rm_elem ) # note that getparent() only works on lxml style etrees, so maybe prefer strip_comment_pi() ?

    return tree


def strip_comment_pi(tree, strip_comment=True, strip_pi=True):
    """ Returns a copy of a tree, that removes comments and processing instructions.
        This can be handy in readout code, in that otherwise you have to isinstance-test for that in a lot of code.
    """
    tree = _copy(tree)
    _strip_comment_pi_inplace(tree, strip_comment=strip_comment, strip_pi=strip_pi)
    return tree

    


def _copy(tree):
    """ Make independent copy of tree 
        (also helps ensure it's lxml-style etree object) 
    """
    if not isinstance(tree, lxml.etree._Element): #  pylint: disable=protected-access,c-extension-no-member
        # (we assume that means we're using a) non-lxml etree?  (and not that you handed in something completely unrelated)
        warnings.warn(
            "Trying to work around potential issues from non-lxml etrees by converting to it, which might be unnecessarily slow. "
            "If you parse your XML yourself, please consider lxml.etree.fromstring() / wetsuite.helpers.etree.fromstring() instead of e.g. xml.etree.fromstring()."
        )
        try:
            import xml.etree.ElementTree

            if isinstance(tree, xml.etree.ElementTree.Element):
                # We want a copy anyway, so this isn't too wasteful.   Maybe there is a faster way, though.
                tree = lxml.etree.fromstring(xml.etree.ElementTree.tostring(tree)) # pylint: disable=c-extension-no-member
            # implied else: we don't know what that was, and we hope for the best
        except ImportError:
            pass  # xml.etree is stdlib in py3 so this should never happen (in py3), but we can fall back to do nothing
    else: # already an lxml-style etree
        tree = copy.deepcopy( tree )  # assuming this is enough.  TODO: verify with lxml and etree implementation
    return tree


def strip_namespace(tree, remove_from_attr=True):
    """Returns a copy of a tree that has its namespaces stripped.

    More specifically it removes
      - namespace from element names
      - namespaces from attribute names (default, but optional)
      - default namespaces (TODO: test that properly)

    @param tree:             The node under which to remove things
    (you would probably hand in the root)
    @param remove_from_attr: Whether to remove namespaces from attributes as well.
    For attributes with the same name that are unique only because of a different namespace,
    this may cause attributes to be overwritten, For example:  ::
        <e p:at="bar" at="quu"/>
    might become: ::
        <e at="bar"/>
    I've not yet seen any XML where this matters - but it might.
    @return: The URLs for the stripped namespaces.
    We don't expect you to have a use for this most of the time,
    but in some debugging you want to know, and report them.
    """
    if tree is None:  # avoid the below saying something silly when it's you who were silly
        raise ValueError("Handed None to strip_namespace()")
    tree = _copy(tree)
    _strip_namespace_inplace(tree, remove_from_attr=remove_from_attr)
    return tree


def _strip_namespace_inplace(tree, remove_from_attr=True):
    """Takes a parsed ET structure and does an in-place removal of all namespaces.
    Returns a list of removed namespaces, which you can usually ignore.
    Not really meant to be used directly, in part because it assumes lxml etrees.

    @param tree:             See L{strip_namespace}
    @param remove_from_attr: See L{strip_namespace}
    @return:                 See L{strip_namespace}
    """
    ret = {}
    for elem in tree.iter():
        if isinstance(elem, _Comment):  # won't have a .tag to have a namespace in,
            continue  # so we can ignore it
        if isinstance(
            elem, _ProcessingInstruction
        ):  # won't have a .tag to have a namespace in,
            continue  # so we can ignore it
        tagname = elem.tag
        if tagname[0] == "{":
            elem.tag = tagname[tagname.index("}", 1) + 1 :]
        if remove_from_attr:
            to_delete = []
            to_set = {}
            for attr_name in elem.attrib:
                if attr_name[0] == "{":
                    urlendind = attr_name.index("}", 1)
                    ret[attr_name[1:urlendind]] = True
                    old_val = elem.attrib[attr_name]
                    to_delete.append(attr_name)
                    attr_name = attr_name[urlendind + 1 :]
                    to_set[attr_name] = old_val
            for delete_key in to_delete:
                elem.attrib.pop(delete_key)
            elem.attrib.update(to_set)
    lxml.etree.cleanup_namespaces( # pylint: disable=c-extension-no-member
        tree
    )  # remove unused namespace declarations. Will only work on lxml etree objects, hence the code above.
    return ret


def indent(tree, strip_whitespace: bool = True):
    """Returns a 'reindented' copy of a tree,
    with text nodes altered to add spaces and newlines, so that if tostring()'d and printed, it would print indented by depth.

    This may change the meaning of the document, so this output should _only_ be used for presentation of the debugging sort.

    See also L{_indent_inplace}

    @param tree:             tree to copy and reindent
    @param strip_whitespace: make contents that contain a lot of newlines look cleaner, but changes the stored data even more.
    """
    newtree = copy.deepcopy(tree)
    _indent_inplace(newtree, level=0, strip_whitepsace=strip_whitespace)
    return newtree


def _indent_inplace(elem, level: int = 0, strip_whitepsace: bool = True):
    """Alters the text nodes so that the tostring()ed version will look nice and indented when printed as plain text."""
    i = "\n" + level * "  "

    if strip_whitepsace:
        if elem.text:
            elem.text = elem.text.strip()
        if elem.tail:
            elem.tail = elem.tail.strip()

    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            _indent_inplace(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i


def path_between(under_node, element, excluding: bool = False):
    """Given an ancestor and a descentent element from the same tree
    (In many applications you want under to be the the root element)

    Returns the xpath-style path to get from (under) to this specific element
    ...or raises a ValueError mentioning that the element is not in this tree

    Keep in mind that if you reformat a tree, the latter is likely.

    This function has very little code, and if you do this for much of a document, you may want to steal the code

    @param excluding: if we have   a/b/c  and call this between an and c, there are cases for wanting either
      * complete path report, like `/a/b/c` (excluding=False), e.g. as a 'complete
      * a relative path like `b/c` (excluding=True), in particular when we know we'll be calling xpath or find on node a
    @param under_node:
    @param element:
    @return:
    """
    if excluding is False:
        letree = lxml.etree.ElementTree( # pylint: disable=c-extension-no-member
            under_node
        )  # it does, actually, so pylint: disable=I1101
        return letree.getpath(element)
    else:
        letree = lxml.etree.ElementTree( # pylint: disable=c-extension-no-member
            under_node
        )  # it does, actually, so pylint: disable=I1101
        path = letree.getpath(element)
        path = path[path.find("/", 1) + 1 :]
        return path


def node_walk(under_node, max_depth=None):
    """Walks all elements under the given element,
    remembering both path string and element reference as we go.

    (note that this is not an xpath style with specific indices, just the names of the elements)

    For example: ::
        TODO

    TODO: re-test now that I've added max_depth, because I'm not 100% on the details

    @param under_node: If given None, it emits nothing
    (we assume it's from a find() that hit nothing, and that it's slightly easier to ignore here than in your code)
    @param max_depth:
    @return:             a generator yielding (path, element),   and is mainly a helper used by path_count()
    """
    # Based on https://stackoverflow.com/questions/60863411/find-path-to-the-node-using-elementtree
    if under_node is None:
        return
    path_to_element = []
    element_stack = [under_node]
    while len(element_stack) > 0:
        element = element_stack[-1]
        if len(path_to_element) > 0 and element is path_to_element[-1]:
            path_to_element.pop()
            element_stack.pop()
            yield (path_to_element, element)
        else:
            path_to_element.append(element)
            for child in reversed(element):
                if max_depth is None or (
                    max_depth is not None and len(path_to_element) < max_depth
                ):
                    element_stack.append(child)


def path_count(under_node, max_depth=None):
    """Walk nodes under an etree element,
    count how often each path happens (counting the complete path string).
    written to summarize the rough structure of a document.

    Path here means 'the name of each element',
    *not* xpath-style path with indices that resolve to the specific node.

    Returns a dict from each path strings to how often it occurs
    """
    count = {}
    for node_path, n in node_walk(under_node, max_depth=max_depth):
        if isinstance(n, (_Comment, _ProcessingInstruction)):
            continue  # ignore things that won't have a .tag
        path = "/".join(
            [n.tag for n in node_path] + [n.tag]
        )  # includes `under`` element, which is a little redundant, but more consistent
        if path not in count:
            count[path] = 1
        else:
            count[path] += 1
    return count


def debug_pretty(tree, reindent=True, strip_namespaces=True, encoding="unicode"):
    """Return (piece of) tree as a string, readable for debugging

    Intended to take an etree object  (but if give a bytestring we'll try to parse it as XML)

    Because this is purely meant for debugging, it by default
      - strips namespaces
      - reindents
      - returns as unicode (not bytes) so we can print() it

    It's also mostly just short for::
           etree.tostring(  etree.indent( etree.strip_namespace( tree ) ), encoding='unicode' )
    """
    if tree is None:
        raise ValueError("Handed None to debug_pretty()")

    if isinstance(
        tree, bytes
    ):  # if you gave it an unparsed doc instead (as bytes, not str)
        tree = lxml.etree.fromstring(tree) # pylint: disable=c-extension-no-member
    elif isinstance(tree, str):
        warnings.warn("WARNING: you gave us a unicode string. XML as a unicode string generally doesn't make sense, please give us the bytestring it probably came from (if it came from a file, try reading it in binary mode)")
        tree = lxml.etree.fromstring( tree.encode('utf8') ) # pylint: disable=c-extension-no-member

    if strip_namespaces:
        tree = strip_namespace(tree)

    if reindent:
        tree = indent(tree)

    return tostring(tree, encoding=encoding)


class debug_color:
    """Takes XML, parses, reindents, strip_namespaces,
    returns a class that will render it in color in a jupyter notebook (using pygments).

    Relies on pygments; CONSIDER: removing that dependency,
    we already have much of the code in the xml-color tool

    @ivar xstr: XML as a string (after reindent and namespace strip)
    """

    def __init__(self, tree_or_bytestring, strip_namespaces=True):
        "Takes either an etree object, or a bytestring yet to be parsed"
        self.xstr = debug_pretty( tree_or_bytestring, strip_namespaces=strip_namespaces )
        # if isinstance(tree_or_bytestring, (str, bytes)):
        #    self.xstr = tree_or_bytestring # TODO: ensure bytes?
        # else:
        #    self.xstr = tostring( tree_or_bytestring, encoding='utf-8' )

    def _repr_html_(self):
        # try:
        from pygments.lexers.html import XmlLexer
        from pygments.formatters import HtmlFormatter # pylint: disable=no-name-in-module
        from pygments import highlight

        html = highlight(self.xstr, XmlLexer(), HtmlFormatter())
        return "<style>%s%s</style>%s" % (
            HtmlFormatter().get_style_defs(".highlight"),
            "\n* { background-color: transparent !important; color:inherit };",  # TODO: consider a light and dark mode
            html,
        )
        # except ImportError:
        #    fall back to escaped
        #    return escape.  xstr




# def remove_nodes_by_name(tree, nodenames):
#     """ Takes an etree, and removes nodes of a specific name from the tree.
#         This is mostly used as an fewer-lines equivalent of 'do an iter where we avoid iterating into certain nodes',
#     """
#     # code currently makes two assumptions that aren't really verified:
#     # - iter would gets confused if we remove things while iterating
#     # - we can remove elements from their parents even if they technically were removed from the tree already
#     to_remove = []
#     for element in tree.iter():
#         if element.tag in nodenames:
#             to_remove.append( element )
#     for el in to_remove:
#         el.getparent().remove(el) # note that this will also remove .tail, which may not be what you want
#     return tree




def all_text_fragments(
    under_node,
    strip: str = None,
    ignore_empty: bool = False,
    ignore_tags=(),
    join: str = None,
    stop_at: list = None,
):
    """Returns all fragments of text contained in a subtree, as a list of strings.

    For the simplest uses, you may just want to use

    Note that for simpler uses, this is itertext() with extra steps. You may not need this.

    For example,  all_text_fragments( fromstring('<a>foo<b>bar</b></a>') ) == ['foo', 'bar']

    Note that:
      - If your source is XML,
      - this is a convenience function that lets you be pragmatic with creative HTML-like nesting,
        and perhaps should not be used for things that are strictly data.

    TODO: more tests, I'm moderately sure strip doesn't do quite what it should.

    TODO: add add_spaces - an acknowledgment that in non-HTML,
    as well as equally free-form documents like this project often handles,
    that element should be considered to split a word (e.g. p in HTML) or
    that element probably doesn't split a word (e.g. em, sup in HTML)
    The idea would be that you can specify which elements get spaces inserted and which do not.
    Probably with defaults for us, which are creative and not necessarily correct,
    but on average makes fewer weird mistakes (would need to figure that out from the various schemas)

    @param under_node: an etree node to work under

    @param strip: is what to remove at the edges of each .text and .tail
    ...handed to strip(), and note that the default, None, is to strip whitespace
    if you want it to strip nothing at all, pass in '' (empty string)

    @param ignore_empty: removes strings that are empty when after that stripping

    @param ignore_tags: ignores direct/first .text content of named tags (does not ignore .tail, does not ignore the subtree)

    @param join: if None, return a list of text fragments; if a string, we return a single tring, joined on that

    @param stop_at: should be None or a list of tag names.
    If a tag name is in this sequence, we stop walking the tree entirely.
    (note that it would still include that tag's tail; CONSIDER: changing that)

    @return: if join==None (the default), a list of text fragments.
    If join is a string, a single string (joined on that string)
    """
    ret = []
    for elem in under_node.iter():  # walks the subtree
        if isinstance(elem, _Comment) or isinstance(elem, _ProcessingInstruction):
            continue
        # print("tag %r in ignore_tags (%r): %s"%(elem.tag, ignore_tags, elem.tag in ignore_tags))
        if elem.text is not None:
            if (
                elem.tag not in ignore_tags
            ):  # only ignore direct .text contents of ignored tags; tail is considered outside
                etss = elem.text.strip(strip)
                if ignore_empty and len(etss) == 0:
                    pass
                else:
                    ret.append(etss)
        if elem.tail is not None:
            etss = elem.tail.strip(strip)
            if ignore_empty and len(etss) == 0:
                pass
            else:
                ret.append(etss)

        if stop_at is not None and elem.tag in stop_at:
            break

    if join is not None:
        ret = join.join(ret)
    return ret


def parse_html(htmlbytes:bytes):
    """ Parses HTML into an etree.
        NOTE: This is *NOT* what you would use for XML - fromstring() is for XML.

        this parse_html() differs from C{etree.fromstring}
          - in that we use a parser more aware of HTML and deals with minor incorrectness
          - and creates lxml.html-based objects, which have more functions compared to their XML node counterparts

        If you are doing this, consider also
          - BeautifulSoup, as slightly more HTML-aware parse, and an alternative API you might prefer to etree's (or specifically not; using both can be confusing)
          - ElementSoup, to take more broken html into etree via beautifulsoup

        See also https://lxml.de/lxmlhtml.html

        @param htmlbytes: a HTML file as a bytestring

        @return: an etree object
    """
    parser = lxml.html.HTMLParser(recover=True, encoding='utf8')
    return lxml.etree.fromstring(htmlbytes, parser=parser) # pylint: disable=c-extension-no-member


# CONSIDER: augmenting this with "main content or not" information that split can use
_html_text_knowledge = { #  usecontents prepend append removesubtree
    ## HTML
    'html':                   ( False, None, None,   False ),
    'body':                   ( True,  None, None,   False ),

    'script':                 ( False, None, None,   True  ),
    'noscript':               ( False, None, None,   True  ), # arguable?
    'style':                  ( False, None, None,   True  ),
    'iframe':                 ( False, None, None,   True  ), # probably doesn't contain anything anyway
    'svg':                    ( False, None, None,   True  ),
    'font':                   ( True,  None, None,   False ), # old-style styling - https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/font

    'form':                   ( False, None, None,   False ),
    'input':                  ( False, None, None,   False ),
    'textarea':               ( True,  None, '\n\n', False ),
    'select':                 ( False, None, None,   False ),
    'option':                 ( False, None, None,   False ),
    'label':                  ( False, None, None,   False ),
    'button':                 ( False, None, None,   False ),

    'link':                   ( True,  None, ' ',    False ),

    'img':                    ( False, None, None,   True  ),
    'caption':                ( True,  None, '\n',   False ),

    'object':                 ( False, None, ' ',    True  ),

    'abbr':                   ( True,  None, None,   False ),
    'main':                   ( True,  '\n', '\n',   False ),
    'article':                ( True,  '\n', '\n',   False ),
    'nav':                    ( False, '\n', '\n',   True  ),
    'aside':                  ( True,  None, '\n',   False ),
    'section':                ( True,  None, '\n',   False ),
    'time':                   ( True,  None, None,   False ),

    'details':                ( True,  None, '\n',   False ),
    'footer':                 ( True,  None, '\n',   True  ), # arguable on the remove
    'header':                 ( True,  None, '\n',   True  ), # arguable on the remove
    'br':                     ( True,  None, '\n',   False ),
    'nobr':                   ( True,  None, None,   False ),
    'dd':                     ( True,  None, '\n',   False ),
    'dt':                     ( True,  None, '\n',   False ),
    'fieldset':               ( True,  None, '\n',   False ),
    'figcaption':             ( True,  None, '\n',   False ),
    'hr':                     ( True,  None, '\n',   False ),
    'legend':                 ( True,  None, '\n',   False ),
    'table':                  ( True,  '\n', '\n',   False ),
    'tbody':                  ( True,  None, None,   False ),
    'thead':                  ( True,  None, None,   False ),
    'tfoot':                  ( True,  None, None,   False ),
    'colgroup':               ( False, None, ' ',    False ), # TODO: decide
    'col':                    ( False, None, ' ',    False ), # TODO: decide
    'tr':                     ( True,  None, '\n',   False ),
    'td':                     ( True,  None, ' ',    False ),
    'th':                     ( True,  None, ' ',    False ),
    'p':                      ( True,  None, '\n\n', False ),
    'div':                    ( True,  None, '\n',   False ),
    'span':                   ( True,  None, None,   False ),
    'figure':                 ( True,  None, '\n\n', False ),
    'title':                  ( True,  None, '\n\n', False ),
    'h1':                     ( True,  None, '\n\n', False ),
    'h2':                     ( True,  None, '\n\n', False ),
    'h3':                     ( True,  None, '\n\n', False ),
    'h4':                     ( True,  None, '\n\n', False ),
    'h5':                     ( True,  None, '\n\n', False ),
    'h6':                     ( True,  None, '\n\n', False ),
    'ins':                    ( True,  None, None,   False ),
    'del':                    ( True,  None, None,   False ),
    'dl':                     ( True,  None, '\n\n', False ),
    'ol':                     ( True,  '\n', '\n',   False ),
    'ul':                     ( True,  '\n', '\n',   False ),
    'blockquote':             ( True,  None, '\n\n', False ),
    'pre':                    ( True,  None, '\n\n', False ),
    'code':                   ( True,  ' ',  None,   False ), # inline, but CONSIDER whether it should have the space(s) or not
    'a':                      ( True,  None, None,   False ),
    'small':                  ( True,  None, None,   False ),
    's':                      ( True,  None, None,   False ), # strikethrough - could decide not to take text from this?
    'b':                      ( True,  None, None,   False ),
    'u':                      ( True,  None, None,   False ),
    'strong':                 ( True,  None, None,   False ),
    'i':                      ( True,  None, None,   False ),
    'sup':                    ( True,  None, None,   False ),
    'sub':                    ( True,  None, None,   False ),
    'em':                     ( True,  None, None,   False ),
    'tt':                     ( True,  None, None,   False ),
    'cite':                   ( True,  None, ' ',    False ), # arguable

    ## Some BWB, CVDR, OP node names.
    # You wouldn't use this for structured output, but it's arguably a nice alternative for just plain text,
    # better than just fetching getting out the text fragments, and simpler than using wetsuite.split directly.
    'nadruk':                 ( True,   None,None,   False ),
    'marquee':                ( True,   None,None,   False ),

    'meta-data':              ( False,  ' ',' ',      True ),
    'bwb-inputbestand':       ( False,  ' ',' ',      True ),
    'bwb-wijzigingen':        ( False,  ' ',' ',      True ),
    'redactionele-correcties':( False,  ' ',' ',      True ),
    'redactie':               ( False,  ' ',' ',      True ),

    # less interesting as main content
    'aanhef':                 ( True,   ' ',' ',     False ),
    'wij':                    ( False,  '\n','\n',   False ),
    'koning':                 ( False,  ' ',' ',      True ),

    'toestand':               ( False,  None,None,   False ),
    'wet-besluit':            ( True,   ' ',' ',     False ),
    'wetgeving':              ( False,  None,None,   False ),
    'intitule':               ( True,   ' ', '\n',   False ),
    'citeertitel':            ( True,   ' ','\n',    False ),
    'wettekst':               ( True,   None,None,   False ),
    'afkondiging':            ( True,   None,None,   False ),
    'divisie':                ( True,   None, None,  False ),

    'hoofdstuk':              ( True,   ' ','\n',    False ), # TODO: look at
    'titel':                  ( True,   ' ','\n',    False ), # TODO: look at
    'bijlage':                ( True,   ' ','\n',    False ), # TODO: look at

    'publicatiejaar':         ( True,   ' ','\n',    False ),
    'publicatienr':           ( True,   ' ','\n',    False ),
    'brondata':               ( True,   ' ',' ',     False ),
    'oorspronkelijk':         ( True,   ' ',' ',     False ),
    'publicatie':             ( True,   ' ',' ',     False ),
    'uitgiftedatum':          ( True,   ' ',' ',     False ),
    'ondertekeningsdatum':    ( True,   ' ',' ',     False ),
    'dossierref':             ( True,   ' ',' ',     False ),
    'inwerkingtreding':       ( True,   ' ',' ',     False ),

    'considerans':            ( False,  None,None,   False ),
    'considerans.al':         ( False,  None,None,   False ),

    'artikel':                ( True,   '\n',None,   False ),
    'nr':                     ( True,   None, ' ',   False ),
    'lid':                    ( True,   None, ' ',   False ),
    'lidnr':                  ( True,   None, ' ',   False ),
    'kop':                    ( True,   ' ','\n',    False ),
    'tussenkop':              ( True,   ' ',' ',     False ),

    'tgroup':                 ( True,   None,None,   False ),
    'colspec':                ( True,   None,None,   False ),
    'row':                    ( True,   ' ','\n',    False ),
    'entry':                  ( True,   ' ',' ',     False ),

    'lijst':                  ( True,   None,'\n',   False ),
    'li':                     ( True,   None,'\n',   False ),
    'li.nr':                  ( True,   None,' ' ,   False ),

    'definitielijst':         ( True,   None,'\n',   False ),
    'definitie-item':         ( True,   None,'\n',   False ),
    'term':                   ( True,   None,' - ',  False ),
    'definitie':              ( True,   None,'\n',   False ),
    'specificatielijst':      ( True,   None,'\n',   False ),
    'specificatie-item':      ( True,   None,'\n',   False ),
    'specificatie':           ( True,   None,' ',    False ),
    'waarde':                 ( True,   None,' ',    False ),

    'noot':                   ( True,   None,None,   False ),
    'noot.nr':                ( True,   None,' ',    False ),
    'noot.al':                ( True,   None,'\n',   False ),
    'noot.lijst':             ( True,   None,'\n',   False ),
    'noot.li':                ( True,   None,'\n',   False ),

    'al':                     ( True,   None,'\n',   False ),

    'inf':                    ( True,   None,None,   False ),
    'extref':                 ( True,   None,None,   False ),
    'intref':                 ( True,   None,None,   False ),
    'extref-groep':           ( True,   None,None,   False ), # seems rare?
    'intref-groep':           ( True,   None,None,   False ), # seems rare?

    'nootref':                ( True,   None,'\n',   False ),
    'aanhaling':              ( True,   None,'\n',   False ), # TODO: look at
    'bron':                   ( True,   None,'\n',   False ), # TODO: look at

    'plaatje':                ( False,   None,None,  False ),
    'illustratie':            ( False,   None,None,  False ),

    'tekstcorrectie':         ( True,   None,None,   False ),  # TODO: look at

    'wetsluiting':            ( False,   None,None,  False ),
    'slotformulering':        ( True,    ' ',' ',    False ),
    'naam':                   ( True,    None,None,  False ),
    'voornaam':               ( True,    None,None,  False ),
    'functie':                ( True,    None,None,  False ),
    'achternaam':             ( True,    None,None,  False ),
    'ondertekening':          ( False,   None,None,  True  ),
    'plaats':                 ( False,   None,'\n',  True  ),
    'datum':                  ( False,   None,'\n',  True  ),

    'uitgifte':               ( False,   None,None,  True  ),
    'dagtekening':            ( False,   None,None,  True  ),
    'gegeven':                ( False,   None,None,  True  ),


    # note that a lot are strucure elements with no direct contents,
    #   so most of these do nothing and are just acknowledgment they exist
    # Everything below could use some polishing
    'officiele-publicatie':         ( False,  None,None,   False ),
    'metadata':                     ( False,  None,None,   False ),
    'meta':                         ( False,  None,None,   False ),

    'gemeenteblad':                 ( False,  None,None,   False ),
    'provincieblad':                ( False,  None,None,   False ),
    'circulaire':                   ( False,  None,None,   False ),
    'provinciaalblad':              ( False,  None,None,   False ),
    'staatscourant':                ( False,  None,None,   False ),
    'waterschapsblad':              ( False,  None,None,   False ),
    'bladgemeenschappelijkeregeling':(False,  None,None,   False ),
    'regeling':                     ( False,  None,None,   False ),
    'regeling-tekst':               ( False,  None,None,   False ),
    'zakelijke-mededeling-tekst':   ( False,  None,None,   False ),
    'zakelijke-mededeling-sluiting':( False,  None,None,   False ),
    'nota-toelichting':             ( False,  None,None,   False ),
    'zakelijke-mededeling':         ( False,  None,None,   False ),
    'niet-dossier-stuk':            ( False,  None,None,   False ),
    'regeling-sluiting':            ( False,  None,None,   False ), # may have signature, useful for NER
    'circulaire-tekst':             ( False,  None,None,   False ),
    'bijlage-sluiting':             ( False,  None,None,   False ),
    'circulaire.divisie':           ( False,  None,None,   False ),
    'voorstel-wet':                 ( False,  None,None,   False ),
    'voorstel-sluiting':            ( False,  None,None,   False ),
    'circulaire-sluiting':          ( False,  None,None,   False ),

    'preambule':                    ( False,  None,None,   False ),
    'bezwaarschrift':               ( False,  None,None,   False ),
    'kamerwrk':                     ( False,  None,None,   False ),
    'handelingen':                  ( False,  None,None,   False ),

    'algemeen':                     ( False,  None,None,   False ),
    'vrije-tekst':                  ( False,  None,None,   False ),
    'tekst-sluiting':               ( False,  None,None,   False ),
    'kamerstuk':                    ( False,  None,None,   False ),
    'kamerstukkop':                 ( False,  None,None,   False ),
    'tekstregel':                   ( False,  None,None,   False ),
    'dossier':                      ( False,  None,None,   False ),
    'dossiernummer':                ( False,  None,None,   False ),
    'dossiernr':                    ( False,  None,None,   False ),
    'begrotingshoofdstuk':          ( False,  None,None,   False ),

    'stuk':                         ( True,   None,None,   False ),
    'stuknr':                       ( True,   None,None,   False ),
    'ondernummer':                  ( True,   None,None,   False ),
    'datumtekst':                   ( True,   None,None,   False ),
    'amendement':                   ( True,   None,None,   False ),
    'wijziging':                    ( True,   None,None,   False ),
    'wat':                          ( True,   None,None,   False ),
    'wie':                          ( False,  None,None,   False ),
    'notatoe':                      ( False,  None,None,   False ),
    'tuskop':                       ( True,   None,'\n',   False ),

    'al-groep':                     ( True,   None,'\n',   False ),

    'subtitel':                     ( True,   None,'\n',   False ),
    'tekst':                        ( True,   None,None,   False ),
    'nds-nr':                       ( True,   None,None,   False ),
    'nds-stuk':                     ( True,   None,None,   False ),
    'margetekst':                   ( True,   None,None,   False ),
    'amendement-lid':               ( True,   None,None,   False ),
    'frontm':                       ( True,   None,None,   False ),
    'versie':                       ( True,   None,None,   False ),
    'ordernr':                      ( True,   None,None,   False ),
    'vergjaar':                     ( True,   None,None,   False ),
    'onderw':                       ( True,   None,None,   False ),
    'nummer':                       ( True,   None,None,   False ),
    'ltrlabel':                     ( True,   None,None,   False ),
    'witreg':                       ( True,   None,'\n',   False ),
    'ondtek':                       ( True,   None,'\n',   False ),
    'agendapunt':                   ( True,   None,None,   False ),
    'item-titel':                   ( True,   None,None,   False ),
    'onderwerp':                    ( True,   None,None,   False ),
    'spreekbeurt':                  ( True,   None,'\n',   False ),
    'spreker':                      ( True,   None,'\n',   False ),
    'voorvoegsels':                 ( True,   None,None,   False ),
    'politiek':                     ( True,   None,None,   False ),
    'motie':                        ( True,   None,None,   False ),
    'motie-info':                   ( True,   None,None,   False ),
    'organisatie':                  ( True,   None,None,   False ),
    'kamervragen':                  ( True,   None,None,   False ),
    'kamervraagkop':                ( True,   None,None,   False ),
    'kamervraagnummer':             ( True,   None,None,   False ),
    'kamervraagomschrijving':       ( True,   None,None,   False ),
    'kamervraagonderwerp':          ( True,   None,None,   False ),
    'vraag':                        ( True,   None,None,   False ),
    'antwoord':                     ( True,   None,None,   False ),

    'vervangt':                     ( True,   None,None,   False ),
    'voetref':                      ( True,   None,None,   False ),
    'voetnoot':                     ( True,   None,None,   False ),
    'structuurtekst':               ( True,   None,None,   False ),
    'wijzig-artikel':               ( True,   None,None,   False ),
    'artikeltekst':                 ( True,   None,None,   False ),
    'vraagdoc':                     ( True,   None,None,   False ),
    'vragen':                       ( True,   None,None,   False ),
    'omschr':                       ( True,   None,None,   False ),
    'ondw':                         ( True,   None,None,   False ),
    'reactie':                      ( True,   None,None,   False ),

    'handeling':                    ( True,   None,None,   False ),
    'volgnr':                       ( True,   None,None,   False ),
    'part':                         ( True,   None,None,   False ),
    'item':                         ( True,   None,None,   False ),
    'itemnaam':                     ( True,   None,None,   False ),
    'itemkop':                      ( True,   None,None,   False ),
    'actie':                        ( True,   None,None,   False ),
    'motienm':                      ( True,   None,None,   False ),
    'vetnr':                        ( True,   None,None,   False ),
    'draad':                        ( True,   None,None,   False ),
    'voorz':                        ( True,   None,None,   False ),
    'opschr':                       ( True,   None,None,   False ),
    'blwstuk':                      ( True,   None,None,   False ),
    'letter':                       ( True,   None,None,   False ),
    'naderrap':                     ( True,   None,None,   False ),
    'voorwerk':                     ( True,   None,None,   False ),
    'raadnr':                       ( True,   None,None,   False ),
    'box':                          ( True,   None,None,   False ),
    'paragraaf':                    ( True,   None,None,   False ),
    'adviesrvs':                    ( True,   None,None,   False ),
    'nader-rapport':                ( True,   None,None,   False ),
    'advies':                       ( True,   None,None,   False ),
    'object_van_advies':            ( True,   None,None,   False ),
    'boek':                         ( True,   None,None,   False ),
    'aanhangsel':                   ( True,   None,None,   False ),
    'stcart':                       ( True,   None,None,   False ),
    'artcode':                      ( True,   None,'\n',   False ),
    'stcgeg':                       ( True,   None,'\n',   False ),
    'dag':                          ( True,   None,'\n',   False ),
    'chapeau':                      ( True,   None,None,   False ),
    'mincodes':                     ( True,   None,'\n',   False ),
    'kenmerk':                      ( True,   None,None,   False ),
    'afd':                          ( True,   None,None,   False ),
    'backm':                        ( True,   None,None,   False ),
    'nl':                           ( True,   None,None,   False ),
    'context':                      ( True,   None,None,   False ),
    'context.al':                   ( True,   None,None,   False ),
    'staatsbl':                     ( True,   None,None,   False ),
    'stb':                          ( True,   None,None,   False ),
    'jaargang':                     ( True,   None,None,   False ),
    'stbjaar':                      ( True,   None,None,   False ),
    'stbnr':                        ( True,   None,None,   False ),
    'soort':                        ( True,   None,None,   False ),
    'consider':                     ( True,   None,None,   False ),
    'grslag':                       ( True,   None,None,   False ),
    'afkondig':                     ( True,   None,None,   False ),
    'art':                          ( True,   None,None,   False ),
    'nawerk':                       ( True,   None,None,   False ),
    'slotform':                     ( True,   None,None,   False ),
    'ondertek':                     ( True,   None,None,   False ),
    'ondplts':                      ( True,   None,None,   False ),
    'onddatum':                     ( True,   None,'\n',   False ),
    'minister':                     ( True,   None,None,   False ),
    'minvan':                       ( True,   None,None,   False ),
    'gtxt':                         ( True,   None,None,   False ),
    'rijksnr':                      ( True,   None,None,   False ),
    'vraagnummer':                  ( True,   None,None,   False ),
    'trblad':                       ( True,   None,None,   False ),
    'sysnr':                        ( True,   None,None,   False ),
    'dosnr':                        ( True,   None,None,   False ),
    'dosjaar':                      ( True,   None,None,   False ),
    'hfdsta':                       ( True,   None,None,   False ),
    'hfdst':                        ( True,   None,None,   False ),
    'onddat':                       ( True,   None,None,   False ),
    'maand':                        ( True,   None,None,   False ),
    'jaar':                         ( True,   None,None,   False ),
    'min':                          ( True,   None,None,   False ),
    'kamervraagopmerking':          ( True,   None,None,   False ),
    'tractatenblad':                ( True,   None,None,   False ),
    'sys.gegevens':                 ( False,  None,None,   False ),
    'considerans.lijst':            ( True,   None,None,   False ),
    'wijzig-lid':                   ( True,   None,None,   False ),
    'staatsblad':                   ( True,   None,None,   False ),
    'histnoot':                     ( True,   None,None,   False ),
    'intro':                        ( True,   None,None,   False ),
    'tijd':                         ( True,   None,None,   False ),
    'aanvang':                      ( True,   None,None,   False ),
    'vrzlabel':                     ( True,   None,None,   False ),
    'vrznaam':                      ( True,   None,None,   False ),
    'aanw':                         ( True,   None,None,   False ),
    'ontwerp-besluit':              ( True,   None,None,   False ),
    'toelicht':                     ( True,   None,None,   False ),
    'vergadering':                  ( True,   None,None,   False ),
    'vergadering-nummer':           ( True,   None,None,   False ),
    'vergaderdatum':                ( True,   None,None,   False ),
    'vergadertijd':                 ( True,   None,None,   False ),
    'opening':                      ( True,   None,None,   False ),
    'bijschrift':                   ( True,   None,None,   False ),
    'ondertekenaar':                ( True,   None,None,   False ),
    'wart':                         ( True,   None,None,   False ),
    'cao':                          ( True,   None,None,   False ),
    'sector':                       ( True,   None,None,   False ),
    'cao-type':                     ( True,   None,None,   False ),
    'ministerie':                   ( True,   None,None,   False ),
    'dictum':                       ( True,   None,None,   False ),
    'wijzig-cao-tekst':             ( True,   None,None,   False ),
    'wijzig-cao-lid':               ( True,   None,None,   False ),
    'cao-wijziging':                ( True,   None,None,   False ),
    'cao-sluiting':                 ( True,   None,None,   False ),
    'wlid':                         ( True,   None,None,   False ),
    'wond':                         ( True,   None,None,   False ),
    'arttkst':                      ( True,   None,None,   False ),
    'officiele-inhoudsopgave':      ( True,   None,None,   False ),
    'minfinref':                    ( True,   None,None,   False ),
    'wet':                          ( True,   None,None,   False ),
    'artikelkop':                   ( True,   None,None,   False ),
    'wijzig-divisie':               ( True,   None,None,   False ),
    'avvcao':                       ( True,   None,None,   False ),
    'branche':                      ( True,   None,None,   False ),
    'inzake':                       ( True,   None,None,   False ),
    'caonr':                        ( True,   None,None,   False ),
    'bronregel':                    ( True,   None,None,   False ),
    'stcdat':                       ( True,   None,None,   False ),
    'stcnr':                        ( True,   None,None,   False ),
    'besluit':                      ( True,   None,None,   False ),
    'aionder':                      ( True,   None,None,   False ),
    'lijn':                         ( True,   None,None,   False ),
    'handeling_bijlage':            ( True,   None,None,   False ),
    'officielepublicatie':          ( True,   None,None,   False ),
    'expressionidentificatie':      ( True,   None,None,   False ),
    'frbrwork':                     ( True,   None,None,   False ),
    'frbrexpression':               ( True,   None,None,   False ),
    'soortwork':                    ( True,   None,None,   False ),
    'officielepublicatieversiemetadata':( True,   None,None,   False ),
    'gepubliceerdop':               ( True,   None,None,   False ),
    'officielepublicatiemetadata':  ( True,   None,None,   False ),
    'eindverantwoordelijke':        ( True,   None,None,   False ),
    'maker':                        ( True,   None,None,   False ),
    'officieletitel':               ( True,   None,None,   False ),
    'onderwerpen':                  ( True,   None,None,   False ),
    'publicatieidentifier':         ( True,   None,None,   False ),
    'publicatienaam':               ( True,   None,None,   False ),
    'publicatieblad':               ( True,   None,None,   False ),
    'publicatienummer':             ( True,   None,None,   False ),
    'publiceert':                   ( True,   None,None,   False ),
    'uitgever':                     ( True,   None,None,   False ),
    'soortpublicatie':              ( True,   None,None,   False ),
    'bladaanduiding':               ( True,   None,None,   False ),
    'titelregel':                   ( True,   None,None,   False ),
    'kennisgeving':                 ( True,   None,None,   False ),
    'regelingopschrift':            ( True,   None,None,   False ),
    'lichaam':                      ( True,   None,None,   False ),
    'divisietekst':                 ( True,   None,None,   False ),
    'inhoud':                       ( True,   None,None,   False ),
    'opschrift':                    ( True,   None,None,   False ),
    'inspring':                     ( True,   None,None,   False ),
    'eindref':                      ( True,   None,None,   False ),
    'eindnoot':                     ( True,   None,None,   False ),
    'citaat':                       ( True,   None,None,   False ),
    'hfdkop':                       ( True,   None,None,   False ),
    'artkop':                       ( True,   None,None,   False ),
    'bijkop':                       ( True,   None,None,   False ),
    'iszwonder':                    ( True,   None,None,   False ),
    'wlichaam':                     ( True,   None,None,   False ),
    'informatieobjectrefs':         ( True,   None,None,   False ),
    'informatieobjectref':          ( True,   None,None,   False ),
    'rechtsgebieden':               ( True,   None,None,   False ),
    'rechtsgebied':                 ( True,   None,None,   False ),
    'besluitcompact':               ( True,   None,None,   False ),
    'wijzigartikel':                ( True,   None,None,   False ),
    'sluiting':                     ( True,   None,None,   False ),
    'wijzigbijlage':                ( True,   None,None,   False ),
    'regelingmutatie':              ( True,   None,None,   False ),
    'vervangregeling':              ( True,   None,None,   False ),
    'regelingcompact':              ( True,   None,None,   False ),
    'lidnummer':                    ( True,   None,None,   False ),
    'gereserveerd':                 ( True,   None,None,   False ),
    'afdeling':                     ( True,   None,None,   False ),
    'linummer':                     ( True,   None,None,   False ),
    'subparagraaf':                 ( True,   None,None,   False ),
    'begrippenlijst':               ( True,   None,None,   False ),
    'begrip':                       ( True,   None,None,   False ),
    'toelichting':                  ( True,   None,None,   False ),
    'algemenetoelichting':          ( True,   None,None,   False ),
    'artikelgewijzetoelichting':    ( True,   None,None,   False ),
    'wartref':                      ( True,   None,None,   False ),
    'verklaringen':                 ( True,   None,None,   False ),
    'titeldeel':                    ( True,   None,None,   False ),
    'cao-divisie':                  ( True,   None,None,   False ),
    'iszwnr':                       ( True,   None,None,   False ),
    'scheidingsteken':              ( True,   None,None,   False ),
    'verdrag':                      ( True,   None,None,   False ),
    'verdragtekst':                 ( True,   None,None,   False ),
    'bezwaar':                      ( True,   None,None,   False ),
    'taal':                         ( True,   None,None,   False ),
    'landlst':                      ( True,   None,None,   False ),
    'land':                         ( True,   None,None,   False ),
    'aanspr':                       ( True,   None,None,   False ),
    'partij':                       ( True,   None,None,   False ),
    'agenda':                       ( True,   None,None,   False ),
    'agendakop':                    ( True,   None,None,   False ),
    'agenda-uitgifte':              ( True,   None,None,   False ),
    'agenda-divisie':               ( True,   None,None,   False ),
    'wetv':                         ( True,   None,None,   False ),
    'herdruk':                      ( True,   None,None,   False ),
    'deel':                         ( True,   None,None,   False ),
    'rijkswetnr':                   ( True,   None,None,   False ),
    'mo':                           ( True,   None,None,   False ),
    'mbody':                        ( True,   None,None,   False ),
    'ondtit':                       ( True,   None,None,   False ),
    'cao-tekst':                    ( True,   None,None,   False ),
    'cao-bijlage':                  ( True,   None,None,   False ),
    'stukken':                      ( True,   None,None,   False ),
    'toestnd':                      ( True,   None,None,   False ),
    'circulaire.aanhef':            ( True,   None,None,   False ),
    'mtekst':                       ( True,   None,None,   False ),
    'verbeterblad':                 ( True,   None,None,   False ),
    'par':                          ( True,   None,None,   False ),
    'subbranche':                   ( True,   None,None,   False ),
    'kol1':                         ( True,   None,None,   False ),
    'kol2':                         ( True,   None,None,   False ),
    'regelingvrijetekst':           ( True,   None,None,   False ),
    'nootnummer':                   ( True,   None,None,   False ),
    'kadertekst':                   ( True,   None,None,   False ),
    'nootnr':                       ( True,   None,None,   False ),
    'noottkst':                     ( True,   None,None,   False ),
    'besllst':                      ( True,   None,None,   False ),
    'tussennummer':                 ( True,   None,None,   False ),
    'wetvlst':                      ( True,   None,None,   False ),
    'tekstpl':                      ( True,   None,None,   False ),
    'goedkeuring':                  ( True,   None,None,   False ),
    'ondertekendop':                ( True,   None,None,   False ),
    'motivering':                   ( True,   None,None,   False ),
    'vblad':                        ( True,   None,None,   False ),
    'marge-groep':                  ( True,   None,None,   False ),
    'context.lijst':                ( True,   None,None,   False ),
    'lijstaanhef':                  ( True,   None,None,   False ),
    'noten':                        ( True,   None,None,   False ),
    'nootlabel':                    ( True,   None,None,   False ),
    'refop':                        ( True,   None,None,   False ),
    'grondslagen':                  ( True,   None,None,   False ),
    'grondslag':                    ( True,   None,None,   False ),
    'tekstreferentie':              ( True,   None,None,   False ),
    'uri':                          ( True,   None,None,   False ),
    'soortref':                     ( True,   None,None,   False ),
    'groep':                        ( True,   None,None,   False ),
    'opdracht':                     ( True,   None,None,   False ),
    'definitievepublicatiedatum':   ( True,   None,None,   False ),
    'slm':                          ( True,   None,None,   False ),
    'opmerkingen':                  ( True,   None,None,   False ),
    'kamervraagbijlage':            ( True,   None,None,   False ),
    'subsubparagraaf':              ( True,   None,None,   False ),
    'regelingtijdelijkdeel':        ( True,   None,None,   False ),
    'conditie':                     ( True,   None,None,   False ),
    'onderwerpbrief':               ( True,   None,None,   False ),
    'contact':                      ( True,   None,None,   False ),
    'inlinetekstafbeelding':        ( True,   None,None,   False ),
    'basiswet':                     ( True,   None,None,   False ),
    'inleidendetekst':              ( True,   None,None,   False ),
    'commissie':                    ( True,   None,None,   False ),
    'opmerking':                    ( True,   None,None,   False ),
    'gewijzigd-verdrag':            ( True,   None,None,   False ),
    'brieftekst':                   ( True,   None,None,   False ),
    'afzender':                     ( True,   None,None,   False ),
    'geadresseerde':                ( True,   None,None,   False ),
    'adres':                        ( True,   None,None,   False ),
    'adresregel':                   ( True,   None,None,   False ),
    'deze':                         ( True,   None,None,   False ),
    'ondtekst':                     ( True,   None,None,   False ),
    'tekstplaatsing':               ( True,   None,None,   False ),
    'heeftciteertitelinformatie':   ( True,   None,None,   False ),
    'citeertitelinformatie':        ( True,   None,None,   False ),
    'isofficieel':                  ( True,   None,None,   False ),
    'vervangkop':                   ( True,   None,None,   False ),
    'verwijderdetekst':             ( True,   None,None,   False ),
    'nieuwetekst':                  ( True,   None,None,   False ),
    'vervang':                      ( True,   None,None,   False ),
    'verwijder':                    ( True,   None,None,   False ),
    'vervallen':                    ( True,   None,None,   False ),
    'titeldl':                      ( True,   None,None,   False ),
    'figuur':                       ( True,   None,None,   False ),
    'intioref':                     ( True,   None,None,   False ),
    'extioref':                     ( True,   None,None,   False ),
    'subpar':                       ( True,   None,None,   False ),
    'briefaanhef':                  ( False,  None,None,   False ),
    'rectificatietekst':            ( True,   None,None,   False ),
    'subart':                       ( True,   None,None,   False ),
    'voegtoe':                      ( True,   None,None,   False ),
    'sub-paragraaf':                ( True,   None,'\n',   False ),
    'cao-wijziging-groep':          ( True,   None,None,   False ),
    'koptekst':                     ( True,   None,None,   False ),
    'afkortingen':                  ( True,   None,None,   False ),
    'afkorting':                    ( True,   None,None,   False ),
    'besluitklassiek':              ( True,   None,None,   False ),
    'regelingklassiek':             ( True,   None,None,   False ),
    'wijziginstructies':            ( True,   None,None,   False ),
    'instructie':                   ( True,   None,None,   False ),
    'wijziglid':                    ( True,   None,None,   False ),
    'inhopg':                       ( True,   None,None,   False ),
    'stcrt-titel':                  ( True,   None,None,   False ),
    'brongegevens':                 ( True,   None,None,   False ),
    'artikelsgewijs':               ( True,   None,None,   False ),
    'nota-toelichting-sluiting':    ( True,   None,None,   False ),
    'ovl':                          ( True,   None,None,   False ),
    'wijzigingen':                  ( True,   None,None,   False ),
    'plotlines':                    ( True,   None,None,   False ),
    'plotline':                     ( True,   None,None,   False ),
    'alternatievetitels':           ( True,   None,None,   False ),
    'alternatievetitel':            ( True,   None,None,   False ),
    'lijstsluiting':                ( True,   None,None,   False ),
    'raad-van-state':               ( True,   None,None,   False ),
    'wetwijziging':                 ( True,   None,None,   False ),
    
    # TEI.2  though it conflicts somewhat
    'front':                 ( False,   None,None,   True ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-front.html
    'speaker':               ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-speaker.html
    'sp':                    ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-sp.html
    'stage':                 ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-stage.html
    'list':                  ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-list.html
    'note':                  ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-note.html
    'cf':                    ( True,   None,None,   False ), # 
    'xptr':                  ( False,   None,None,  True ),  # I think? 
    'xref':                  ( False,   None,None,   True ), # 
    'interpgrp':             ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-interpGrp.html
    'interp':                ( True,   None,None,   False ), # 
    'text':                  ( True,   None,None,   False ), # 
    'pb':                    ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-pb.html
    'hi':                    ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-hi.html
    'lg':                    ( True,   None,'\n',   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-lg.html
    'l':                     ( True,   None,'\n',   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-l.html 
    'q':                     ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-q.html
    'cell':                  ( True,   None,'\n',   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-cell.html 
    'lb':                    ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-lb.html
    'name':                  ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-name.html
    'figdesc':               ( False,   None,None,   False ), # https://www.tei-c.org/release/doc/tei-p5-doc/en/html/ref-figDesc.html
    'cit':                   ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-cit.html
    'signed':                ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-signed.html
    'c':                     ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-c.html
    'seg':                   ( True,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-seg.html
    'bibl':                  ( False,   None,None,   False ), # https://tei-c.org/release/doc/tei-p5-doc/en/html/ref-bibl.html
    'hy':                    ( True,   None,None,   False ), # ?
    'tune':                  ( True,   None,None,   False ), # ?
    'reg':                   ( True,   None,None,   False ), # ?

    'creator':               ( True,  None, '\n',   False ),
    'publisher':             ( True,  None, '\n',   False ),
    'contributor':           ( True,  None, '\n',   False ),
    'description':           ( True,  None, '\n',   False ),
    'date':                  ( True,  None, '\n',   False ),
    'subject':               ( True,  None, '\n',   False ),
    'language':              ( True,  None, '\n',   False ),
    'identifier':            ( True,  None, '\n',   False ),
                     #  usecontents prepend append removesubtree
}
" The data that html_text works from; we might make this a parameter so you can control that "



# CONSIDER: moving this to its own module, this has little to do with etree anymore
def html_text(etree, join=True, bodynodename='body'):
    '''
    Take an etree (will also take a bytestring) 
    presumed to contain elements with HTML names,
    extract the plain text as a single string.

    What this adds over basic text extraction using C{"".join(elem.itertext())},
    (or C{all_text_fragments()} in this module) is awareness of which HTML elements
    should be considered to split words and to split paragraphs.

    It will selectively insert spaces and newlines,
    as to not smash text together in ways unlikely to how a browser would do it.
    The downside is that this becomes more creative than some might like,
    so if you want precise control, take the code and refine your own.
    (Inspiration was taken from the html-text module. While we're being creative anyway,
    we might _also_ consider taking inspiration from jusText, to remove boilerplate content based on a few heuristics.)

    While this will also take most of the more structured XML seen in BWB, CVDR, and OP,
    it mostly just passes the text through. 
    If you care about structure, now or later, you may prefer C{wetsuite.helpers.split}.
    
    @param etree: Can be one of
    * etree object (but there is little point as most node names will not be known.
    * a bytes or str object - will be assumed to be HTML that isn't parsed yet. (bytes suggests properly storing file data, str might be more fiddly with encodings)
    * a bs4 object - this is a stretch, but could save you some time.

    @param bodynodename: start at the node with this name - defaults to 'body'. Use None to start at the root of what you handed in.

    @param join: If True, returns a single string (with a little more polishing, of spaces after newlines)
    If False, returns the fragments it collected and added.   Due to the insertion and handing of whitespace, this bears only limited relation to the parts.
    '''
    if etree is None:
        raise ValueError( "You handed None into html_text()" )

    # also accept unparsed HTML / XML
    if isinstance( etree, (str, bytes) ):
        etree = parse_html(etree)

    # also accept bs4 objects. It's a stretch for something in an etree module, yes,
    #   but it can be cooperative if you like bs4 to parse HTML
    try: # we don't fail on bs4 not being installed
        from bs4 import Tag
        if isinstance(etree, Tag):
            etree = parse_html( str(etree) ) # bs4 to string, string to etree.html
    except ImportError:
        warnings.warning('no bs4')
        pass

    etree = strip_namespace( etree )

    ## Go through the tree to remove what _html_text_knowledge requests to remove.
    #   yes, it would be more efficient to do skip it in the main treewalk, but that would require some rewrite
    # Note: el.drop_tree() is more correct than a plain el.getparent().remove(el)  due to its handing of tail (joined to the previous element, or parent).
    #   but drop_tree exists only in [lxml.html](https://lxml.de/lxmlhtml.html), not bare lxml, so to ensure this also works on bare lxml objects
    #   that our parse_html return, the toremove part is roughly the contents of drop_tree() implementation
    toremove = []
    for element in etree.iter(): 
        if element.tag in _html_text_knowledge  and  _html_text_knowledge[element.tag][3]: #whether that tag is marked 'remove subtree'
            toremove.append( element )
    
    for el in toremove:
        parent = el.getparent()
        assert parent is not None
        if el.tail:    # if the element we want to remove has .tail text
            previous = el.getprevious()
            if previous is None:                            # - if there isn't a previous sibling, append it to the parent's .text
                parent.text = (parent.text or '') + el.tail
            else:                                           # - if there is a previous sibling, append it to ''its'' tail
                previous.tail = (previous.tail or '') + el.tail
        # and only then actually remove the element
        parent.remove(el)

    ## Now augment and collect the fragments we want
    collect = []
    def add_text(tagtext, tagname):
        if tagname in _html_text_knowledge:
            if tagtext is not None:
                tagtext = re.sub(r'[\s]+', ' ', tagtext) # squeeze whitespace (and remove newlines)
                add_text, _, _, _ = _html_text_knowledge[tagname]
                if add_text:
                    #print("adding %r"%(tagtext))
                    collect.append( tagtext )
        else:
            warnings.warn(f'TODO: handle {repr(tagname)} in html_text()')

    def add_ws_before(tag):
        if tag.tag in _html_text_knowledge:
            _, add_before, _, _ = _html_text_knowledge[tag.tag]
            if add_before is not None:
                collect.append( add_before )

    def add_ws_after(tag):
        if tag.tag in _html_text_knowledge:
            _, _, add_after, _ = _html_text_knowledge[tag.tag]
            if add_after is not None:
                #print("adding %r after %r"%(add_after, tag.tag))
                collect.append( add_after )

    walkfrom = etree # if you hand in None, we do everything
    if bodynodename is not None:
        bf = etree.find( bodynodename )
        if bf is not None:
            walkfrom = bf

    for event, el in lxml.etree.iterwalk(walkfrom, events=('start', 'end')):  # pylint: disable=c-extension-no-member
        # TODO: check that this block isn't wrong
        if event == 'start':
            add_ws_before(el)
            add_text( el.text, el.tag)
        elif event == 'end':
            add_ws_after(el)
            add_text( el.tail, el.tag)

    ## Reduce whitespace from what we just collected
    # There are several possible reasons for a _lot_ of whitepace, such as
    # the indentation in the document, as well as what we just added
    def is_only_whitespace(s):
        if len(re.sub(r'[\r\n\t\s]','',s))==0:
            return True
        return False

    ret = []
    #prev_iow = False
    combine = ''
    for string in collect:
        iow = is_only_whitespace( string )
        if not iow: # add (collected whitespace) and this text
            if len(combine) > 0:
                #ret.append( combine )
                cnl = combine.count('\n')
                if cnl >= 2:
                    ret.append('\n\n')
                if cnl == 1:
                    ret.append('\n')
                else:
                    ret.append(' ')
                combine = ''
            ret.append(string)
        else:
            #print( "IOW, adding %r"%string)
            combine += string
        #if iow and prev_iow:
        #prev_iow=iow

    if join:
        ret = ''.join( ret )
        ret = re.sub(r'\n[\ ]+', '\n', ret.strip()) # TODO: explain the need for this better
        return ret.strip()
    else:
        return ret
