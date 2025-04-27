#!/usr/bin/python3.8
""" test functions in the wetsuite.helpers.split module """

import os, time

import pytest

import wetsuite.helpers.split
import wetsuite.helpers.etree

_test_file_list = (  # these are test files also in the repo
    "bwb_toestand.xml",
    "cvdr_example1.xml",
    "gmb.html",
    "gmb.xml",
    "gmb.html.zip",
    "stcrt.html",
    "stcrt.xml",
    "stb.html",
    "stb.xml",
    "trb.html.zip",
    "prb.xml",
    "prb.html.zip",
    "bgr.html",
    "bgr.xml",
    "rechtspraak1.xml",
    "rechtspraak2.xml",
    # TODO: parliament
    "eggs.pdf",
)


def test_ascii_fix():
    "test that this dumb fixing function does a thing, and does not break itself"
    assert b"UTF" in wetsuite.helpers.split.fix_ascii_blah(
        b'   <?xml version="1.0" encoding="US-ASCII"?>  <a/>'
    )


def test_decide():
    "see whether decide() deals with each test file without failing"
    import test_split

    for test_path in _test_file_list:
        one_path = os.path.join(
            os.path.dirname(test_split.__file__), "testfiles", test_path
        )
        with open(one_path, "rb") as f:
            filedata = f.read()

            for _, _ in wetsuite.helpers.split.decide(filedata, debug=True):
                pass


def test_fragments():
    "see whether fragments() deals with each test file without failing"
    import test_split

    for test_path in _test_file_list:
        one_path = os.path.join(
            os.path.dirname(test_split.__file__), "testfiles", test_path
        )
        with open(one_path, "rb") as f:
            filedata = f.read()
            for _, procobj in wetsuite.helpers.split.decide(filedata):
                list(procobj.fragments())


# def test_firstonly():
#     ' see whether asking decide() for _only_ the first/best choice works  (COMMENTED BECAUSE THERE ARE CURRENTLY NO CASES FOR THIS)  '
#     import test_split

#     gmb_path = os.path.join( os.path.dirname( test_split.__file__ ), 'testfiles', 'gmb.xml' )
#     with open(gmb_path,'rb') as f:
#         docbytes = f.read()
#         assert len( wetsuite.helpers.split.decide( docbytes ) ) > 1                    # there are more than one (we need an example for which that is true)
#         assert len( wetsuite.helpers.split.decide( docbytes, first_only=True ) ) == 1  # ...but not if you ask for one


def test__split_officielepublicaties_xml__start_at_none():
    "test the code path for starting at root"
    import test_split

    gmb_path = os.path.join(
        os.path.dirname(test_split.__file__), "testfiles", "gmb.xml"
    )
    with open(gmb_path, "rb") as gmb_file:
        gmb_tree = wetsuite.helpers.etree.fromstring(gmb_file.read())
        wetsuite.helpers.split._split_officielepublicaties_xml( gmb_tree, start_at=None )  # pylint: disable=protected-access


def test__split_officielepublicaties_xml__list_test():
    "test the code path testing for lsit"
    tree = wetsuite.helpers.etree.fromstring("<r/>")
    with pytest.raises(ValueError, match=r".*given a list.*"):
        wetsuite.helpers.split._split_officielepublicaties_xml( tree, start_at=tree.xpath("/") )  # pylint: disable=protected-access


def test__split_officielepublicaties_xml__start_at_nonsense():
    "test the code path for starting at path that does not exist"
    import test_split

    gmb_path = os.path.join( os.path.dirname(test_split.__file__), "testfiles", "gmb.xml" )
    with open(gmb_path, "rb") as gmb_file:
        gmb_tree = wetsuite.helpers.etree.fromstring(gmb_file.read())
        with pytest.raises(ValueError, match=r".*Did not find.*"):
            wetsuite.helpers.split._split_officielepublicaties_xml( gmb_tree, start_at="/przewalski" )  # pylint: disable=protected-access


def test__split_officielepublicaties_xml__start_at_node():
    "test the code path for starting at root"
    import test_split

    gmb_path = os.path.join(
        os.path.dirname(test_split.__file__), "testfiles", "gmb.xml"
    )
    with open(gmb_path, "rb") as gmb_file:
        gmb_tree = wetsuite.helpers.etree.fromstring(gmb_file.read())
        node = gmb_tree.find("gemeenteblad/zakelijke-mededeling")
        wetsuite.helpers.split._split_officielepublicaties_xml( gmb_tree, start_at=node )  # pylint: disable=protected-access


def test_Fragments_nonbytes():
    "test that it complains about input that is not bytes"
    with pytest.raises(ValueError, match=r".*bytestrings.*"):
        wetsuite.helpers.split.Fragments("")


def test_Fragments_notimplemented():
    "test that it complains when not implemented  (arguably only valuable to test on all implementation classes in the same module)"
    fop = wetsuite.helpers.split.Fragments(b"")
    with pytest.raises(NotImplementedError, match=r".*Please.*"):
        fop.accepts()

    with pytest.raises(NotImplementedError, match=r".*Please.*"):
        fop.suitableness()

    with pytest.raises(NotImplementedError, match=r".*Please.*"):
        fop.fragments()




if __name__ == '__main__':
    # When run as a main script this profiles (primarily) test_decide and test_fragments
    #  because as o this writing they take ~2s each (more when profiled), as each file takes 0.4s to decide
    from cProfile import Profile
    from pstats import SortKey, Stats

    for func in (
        test__split_officielepublicaties_xml__list_test,
        test__split_officielepublicaties_xml__start_at_node,
        test__split_officielepublicaties_xml__start_at_none,
        test__split_officielepublicaties_xml__start_at_nonsense,
        test_ascii_fix,
        test_decide,
        test_fragments,
        test_Fragments_nonbytes,
        test_Fragments_notimplemented,
    ):
        start = time.time()
        func()
        took = time.time() - start
        if took > 0.2:
            print(f" ====== {func.__name__} took {took:.2f}sec, profiling... ===== ")
            with Profile() as profile:
                print(f"{func()} = ")
                (
                    Stats(profile)
                    #.strip_dirs()
                    .sort_stats(SortKey.CUMULATIVE)
                    .print_stats(20)
                )
