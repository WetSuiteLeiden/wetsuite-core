" test etree / lxml related functions "
import pytest
from wetsuite.helpers.etree import (
    fromstring,
    tostring,
    strip_namespace,
    _strip_namespace_inplace,
    strip_comment_pi,
    _strip_comment_pi_inplace, 
    all_text_fragments,
    indent,
    path_count,
    kvelements_to_dict,
    path_between,
    node_walk,
    debug_pretty,
    html_text,
    debug_color
)


def test_strip_namespace():
    """Test some basic assumptions around strip_namespace() and strip_namespace_inplace()"""
    original = '<a xmlns:pre="foo"> <pre:b/> </a>'
    reserialized = '<a xmlns:ns0="foo"> <ns0:b /> </a>'

    tree = fromstring(original)

    # lxml seems to preserve prefix strings, others do not, so either is good   (TODO: check)
    assert tostring(tree).decode("u8") in (original, reserialized)

    # test whether it actually stripped the namespaces
    stripped = strip_namespace(tree)
    assert stripped.find("{foo}b") is None and stripped.find("b").tag == "b"

    # test whether deepcopy does what I think it does - whether the original tree is untouched
    assert tostring(tree).decode("u8") in (original, reserialized)

    _strip_namespace_inplace(tree)

    # back and forth to remove any difference in serialization
    assert tostring(tree) == tostring(fromstring(b"<a> <b/> </a>"))
    # and test _that_ assumption too
    assert tostring(tree) == tostring(fromstring(b"<a> <b /> </a>"))

    # test whether it alters in-place
    assert tree.find("{foo}b") is None and tree.find("b").tag == "b"

    with pytest.raises(ValueError, match=r".*Handed None.*"):
        strip_namespace(None)


def test_strip_comment_pi_inplace():
    ' Test whether we can strip comments and/or processing instructions from lxml trees, in-place '
    t = fromstring('<html><a/><!-- --><b/><?xml-stylesheet type="text/xsl" href="style.xsl"?></html>')
    _strip_comment_pi_inplace(t, True, False)
    assert tostring( t ) == b'<html><a/><b/><?xml-stylesheet type="text/xsl" href="style.xsl"?></html>'

    t = fromstring('<html><a/><!-- --><b/><?xml-stylesheet type="text/xsl" href="style.xsl"?></html>')
    _strip_comment_pi_inplace(t, False, True)
    assert tostring( t ) == b'<html><a/><!-- --><b/></html>'

    t = fromstring('<html><a/><!-- --><b/><?xml-stylesheet type="text/xsl" href="style.xsl"?></html>')
    _strip_comment_pi_inplace(t, True, True)
    assert tostring( t ) == b'<html><a/><b/></html>'


def test_strip_comment_pi_copy():
    ' Test whether we can strip comments and/or processing instructions from lxml trees '
    t = fromstring('<html><a/><!-- --><b/><?xml-stylesheet type="text/xsl" href="style.xsl"?></html>')

    assert tostring( strip_comment_pi(t, True, False) ) == b'<html><a/><b/><?xml-stylesheet type="text/xsl" href="style.xsl"?></html>'

    assert tostring( strip_comment_pi(t, False, True) ) == b'<html><a/><!-- --><b/></html>'

    assert tostring( strip_comment_pi(t, True, True) ) == b'<html><a/><b/></html>'

    # check that original is untouched
    assert tostring( t ) == b'<html><a/><!-- --><b/><?xml-stylesheet type="text/xsl" href="style.xsl"?></html>'


def test_attribute_stripping():
    "test that namespaces are aolso stripped from attribute names"
    with_attr = fromstring('<a xmlns:pre="foo"> <b pre:at="tr"/> </a>')
    _strip_namespace_inplace(with_attr)
    assert tostring(with_attr) == b'<a> <b at="tr"/> </a>'


def test_comment_robustness():
    "tests whether we're not assuming the only node type is element"
    _strip_namespace_inplace(fromstring("<a> <b /><!--comment--> </a>"))


def test_processing_instruction_robustness():
    """test that we do not trip over processing instructions
    note: apparently an initial <?xml doesn't count as a processing expression
    """
    _strip_namespace_inplace(
        fromstring(b'<a><?xml-stylesheet type="text/xsl" href="style.xsl"?></a>')
    )


def test_strip_default():
    "test strip_namespace with defaults"
    withns1 = b'<a xmlns="foo"><b/></a>'
    withns2 = b'<a><b xmlns="foo"/></a>'
    withoutns = b"<a><b/></a>"

    to1 = tostring(strip_namespace(fromstring(withns1)))
    to2 = tostring(strip_namespace(fromstring(withns2)))
    assert to1 == withoutns
    assert to2 == withoutns


def test_all_text_fragments():
    "test all_text_fragments function"
    assert all_text_fragments(fromstring("<a>foo<b>bar</b>quu</a>")) == [
        "foo",
        "bar",
        "quu",
    ]


def test_all_text_fragments_emptiness():
    "test all_text_fragments function around empty text or tail"
    # rather than a '', is expected behaviour.
    assert all_text_fragments(fromstring("<a>foo<b></b>quu</a>")) == ["foo", "quu"]

    assert all_text_fragments(fromstring("<a>foo<b> </b>quu</a>")) == ["foo", "", "quu"]
    assert all_text_fragments(
        fromstring("<a>foo<b> </b>quu</a>"), ignore_empty=True
    ) == ["foo", "quu"]

    assert all_text_fragments(
        fromstring("<a>foo<b>bar</b>quu<c> </c> </a>"), ignore_empty=True
    ) == ["foo", "bar", "quu"]


def test_all_text_fragments_ignoretag():
    "test all_text_fragments function ignores tags as requested"
    assert all_text_fragments(
        fromstring("<a>foo<b>bar</b>quu</a>"), ignore_tags=["b"]
    ) == ["foo", "quu"]


def test_all_text_fragments_stopat():
    "test all_text_fragments function stops at tag names as requested"
    assert all_text_fragments(
        fromstring("<a>foo<b>bar</b><c>quu</c></a>"), stop_at=("b",)
    ) == ["foo", "bar"]
    # NOTE: we may wish to change its behaviour a little, in particular exclude the .tail


def test_all_text_fragments_join():
    "test all_text_fragments with string joining"
    assert (
        all_text_fragments(fromstring("<a>foo<b>bar</b>quu</a>"), join=" ")
        == "foo bar quu"
    )


def test_indent():
    "test reindenting"
    xml = '<a xmlns:pre="foo"> <pre:b/> </a>'
    assert (
        tostring(indent(fromstring(xml))) == b'<a xmlns:pre="foo">\n  <pre:b/>\n</a>\n'
    )


def test_pathcount():
    "test the path counting"
    xml = "<a><b>><c/><c/><c/><!-- --></b><d/><d/></a>"
    assert path_count(fromstring(xml)) == {"a": 1, "a/b": 1, "a/b/c": 3, "a/d": 2}


def test_node_walk_none():
    "mostly tested by (test_)pathcount, except for this"
    # might be a clearer way to write that?
    g = node_walk(None)
    with pytest.raises(StopIteration):
        next(g)


def test_kvelements_to_dict():
    "test kv_elements_to_dict() basically works"
    assert (
        kvelements_to_dict(
            fromstring(
                """<foo>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp/>
           </foo>"""
            )
        )
        == {"identifier": "BWBR0001840", "title": "Grondwet"}
    )


def test_kvelements_to_dict_ignore():
    "test kv_elements_to_dict() ignores tags by name as requested"
    assert (
        kvelements_to_dict(
            fromstring(
                """<foo>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp>ignore me</onderwerp>
           </foo>"""
            ),
            ignore_tagnames=["onderwerp"],
        )
        == {"identifier": "BWBR0001840", "title": "Grondwet"}
    )


def test_kvelements_to_dict_pi():
    "test kv_elements_to_dict() deals with processing instructions"
    assert (
        kvelements_to_dict(
            fromstring(
                """<foo>
                <?xml-stylesheet type="text/xsl" href="blah.xsl"?>
                <identifier>BWBR0001840</identifier>
                <title>Grondwet</title>
                <onderwerp>ignore me</onderwerp>
           </foo>"""
            ),
            ignore_tagnames=["onderwerp"],
        )
        == {"identifier": "BWBR0001840", "title": "Grondwet"}
    )


def test_nonlxml():
    "Test that we work around (at least some) non-lxml etrees, and that we warn about that."
    import xml.etree.ElementTree

    with pytest.warns(UserWarning, match=r".*non-lxml.*"):
        strip_namespace(
            xml.etree.ElementTree.fromstring(
                b'<a><?xml-stylesheet type="text/xsl" href="style.xsl"?></a>'
            )
        )

    # see also https://lxml.de/compatibility.html


def test_path_between_including():
    "test that path_between basically works"
    xml = "<a><b><c><d/><d/></c><d/></b></a>"
    a = fromstring(xml)
    c = a.find("b/c")
    d0 = c.getchildren()[0]
    d1 = c.getchildren()[1]
    assert path_between(a, d0) == "/a/b/c/d[1]"
    assert path_between(a, d1) == "/a/b/c/d[2]"


def test_path_between_excluding():
    "test that path_between basically works"
    xml = "<a><b><c><d/><d/></c><d/></b></a>"
    a = fromstring(xml)
    c = a.find("b/c")
    d0 = c.getchildren()[0]
    d1 = c.getchildren()[1]
    assert path_between(a, d0, excluding=True) == "b/c/d[1]"
    assert path_between(a, d1, excluding=True) == "b/c/d[2]"


def test_path_between_elsewhere():
    "more path related tests"
    xml = "<a><b><c><d/><d/></c><d/></b></a>"
    a = fromstring(xml)

    with pytest.raises(ValueError, match=r".*Element is not in this tree.*"):
        path_between(a, fromstring(xml))  # new parse is not in the same tree

    # TODO: decide what to do when they're in the same tree but not the way around that you expect
    # with pytest.raises(ValueError, match=r'.*.*'):
    # assert path_between(d1, a)

    # wetsuite.helpers.etree.path_between(tree, body.xpath('//al')[10]) == '/cvdr/body/regeling/regeling-tekst/artikel[1]/al[1]'


def test_debug_pretty():
    "test that debug_pretty basically works"

    # note that the output is intentionally unicode, not bytes
    assert (
        debug_pretty(
            b'<a xmlns:pre="foo"><b/></a>', reindent=True, strip_namespaces=True
        )
        == "<a>\n  <b/>\n</a>\n"
    )

    # more variations would be more thorough

    with pytest.raises(ValueError):
        assert debug_pretty(None)


def test_html_text():
    ' basic test of extracting plain text from HTML with awareness of what nodes split words/paragraphs '
    tree = fromstring( '<body><b>foo</b>bar</body>' )
    assert html_text(tree) == 'foobar'


def test_html_text_list():
    ' list-return test '
    assert html_text( '<body><div>foo</div>bar</body>',join=False  ) == ['foo', '\n', 'bar']


def test_html_text_str_input():
    ' testing that it will take string input '
    assert html_text( '<body><b>foo</b>bar<body>'      ) == 'foobar'
    assert html_text( '<div>foo</div>bar' ) == 'foo\nbar'


def test_html_text_bytes_input():
    ' testing that it will take bytestring input '
    assert html_text( b'<b>foo</b>bar' ) == 'foobar'
    assert html_text( b'<div>foo</div>bar' ) == 'foo\nbar'


def test_html_text_bs4_input():
    ' testing that it will take BeautifulSoup input '
    import bs4
    soup = bs4.BeautifulSoup( b'<html><b>foo</b>bar<br/></html>', features='lxml' )
    assert html_text( soup ) == 'foobar'


def test_debug_color():
    ' just testing that it does not fail on some basic input '
    o = debug_color( fromstring( '<body><b>foo</b>bar</body>' ) )
    o._repr_html_() # pylint: disable=protected-access
