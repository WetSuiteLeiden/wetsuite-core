" tests related to ipyton/jupyter notebook code "
import time
import pytest

import wetsuite.helpers.etree
from wetsuite.helpers.notebook import (
    detect_env,
    is_interactive,
    is_ipython,
    is_notebook,
    is_ipython_interactive,
    progress_bar,
    ProgressBar,
    etree_visualize_selection,
)


def test_detect_env_pytest():
    "test that detect_env, well, detects the pytest special case"
    d = detect_env()
    # from within pytest it's probably...
    assert d["ipython"] is False
    assert d["interactive"] is False
    assert d["notebook"] is False

    assert not is_ipython()
    assert not is_interactive()
    assert not is_notebook()
    assert not is_ipython_interactive()


def test_detect_env_colab(monkeypatch):
    ' Fake that we have google colab '
    import sys, types
    
    with pytest.raises(ImportError):
        import google.colab # we shouldn't have it already

    # knowing that detect_env treats exactly this as a special case, make it skip that
    monkeypatch.delitem( sys.modules, "pytest", raising=False)
    
    # Makes 'import google.colab' work - this is awkward and probably not right or minimal, but good enough for the test.
    go = types.ModuleType('google')
    go.__path__ = []
    co = types.ModuleType("google.colab")
    go.colab = co
    monkeypatch.setitem( sys.modules, 'google',       go )
    monkeypatch.setitem( sys.modules, 'google.colab', co )

    d = detect_env()
    assert d.get("colab",None) is True
    assert d["ipython"] is True
    assert d["interactive"] is True
    assert d["notebook"] is True

    assert is_ipython()
    assert is_interactive()
    assert is_notebook()
    assert is_ipython_interactive()


#a test_detect_env_ipython would probabably be too much mockery. At this point we'd be doing it only for the test coverage



def test_progress_console():
    "test that it does not bork out trying to make a progess bar (probably defaulting to tqdm console, due to pytest environment) "
    pb = progress_bar(10)
    pb.value += 1
    pb.description = "foo"


def test_progress_nbfallback(monkeypatch):
    " Pretend tqdm isn't installed, see if it falls back"

    ## monkey patching to pretend something cannot be loaded. 
    import builtins
    real_import = builtins.__import__
    def filtering_import(name, *args, **kwargs):
        if name == "tqdm":
            raise ModuleNotFoundError(name)
        return real_import(name, *args, **kwargs)
    monkeypatch.setattr(builtins, "__import__", filtering_import)

    # test that the above monkey patching actually blocks the import
    with pytest.raises(ImportError):
        import tqdm

    pb = progress_bar(10)
    pb.value += 1
    pb.description = "foo"


def test_progress_iter():
    """test that it iterates over various things,
    including things that have a length but are not subscriptable,
    and things have neither a length nor are subscribtable
    """

    for _ in ProgressBar([1, 2, 3, 4]):
        time.sleep(0.001)

    for _ in ProgressBar(set([1, 2, 3, 4])):
        time.sleep(0.001)

    # dict views
    for _ in ProgressBar({1: 2, 3: 4}.items()):
        time.sleep(0.001)

    for _ in ProgressBar({1: 2, 3: 4}.keys()):
        time.sleep(0.001)

    for _ in ProgressBar({1: 2, 3: 4}.values()):
        time.sleep(0.001)


def test_progress_enum():  # TODO: figure out whether we want that
    "test that progress bar does not fail on enumerations"
    for _ in ProgressBar(enumerate([5, 6, 7])):
        time.sleep(0.001)


def test_etree_visualize_selection():
    "testing that running it does not error out always"
    tree = wetsuite.helpers.etree.fromstring('<a><b c="d">e</b></a>')
    o = etree_visualize_selection(tree, "//b")
    o._repr_html_()  # pylint: disable=protected-access


def test_etree_visualize_selection_unusualnotes():
    "testing that running it does not error out always"
    tree = wetsuite.helpers.etree.fromstring("<a><!-- --><b/>?<?foo ?></a>")
    o = etree_visualize_selection(tree, "//b", True, True, True, True)
    o._repr_html_()  # pylint: disable=protected-access


def test_etree_visualize_selection_given():
    'testing "highlight given elements" does not error out'
    tree = wetsuite.helpers.etree.fromstring("<a><b/></a>")
    o = etree_visualize_selection(tree, tree.findall("b"))
    o._repr_html_()  # pylint: disable=protected-access
    o = etree_visualize_selection(tree, tree.find("b"))
    o._repr_html_()  # pylint: disable=protected-access


def test_etree_visualize_selection_bytes():
    "test that it does not bork out"
    etree_visualize_selection(b"<a><b/></a>", "//b")
