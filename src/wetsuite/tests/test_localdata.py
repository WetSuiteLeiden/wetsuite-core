" tests related to the localdata module, mostly LocalKV  "
import os
import pytest
import wetsuite.helpers.localdata


# def test_pathlib()
#    import pathlib


def test_crud():
    """basic CRUD test: that setters actually store data, 
       and getters get it out again, and that item counts match
    """
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", key_type=str, value_type=str)
    with pytest.raises(KeyError):
        kv.get("a")
    kv.put("a", "b")
    assert len(kv) == 1
    assert kv.get("a") == "b"
    kv.delete("a")
    assert len(kv) == 0

    kv.put("c", "d")
    assert len(kv) == 1
    kv.delete("c")
    assert len(kv) == 0


def test_metacrud():
    "basic CRUD tests of the (hidden) meta table"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", key_type=str, value_type=str)
    with pytest.raises(KeyError):
        kv._get_meta("a")  # pylint: disable=protected-access
    kv._put_meta("a", "b")  # pylint: disable=protected-access
    assert kv._get_meta("a") == "b"  # pylint: disable=protected-access
    kv._delete_meta("a")  # pylint: disable=protected-access
    kv._put_meta("c", "d")  # pylint: disable=protected-access
    kv._delete_meta("c")  # pylint: disable=protected-access


def test_readonly():
    "test whether opening a store read-only will refuse writing"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str, read_only=True)
    with pytest.raises(RuntimeError, match=r".*Attempted*"):
        kv.put("a", "b")

    with pytest.raises(RuntimeError, match=r".*Attempted*"):
        kv.delete("a")

    with pytest.raises(RuntimeError, match=r".*Attempted*"):
        kv._put_meta("a", "b")  # pylint: disable=protected-access

    with pytest.raises(RuntimeError, match=r".*Attempted*"):
        kv._delete_meta("a")  # pylint: disable=protected-access


def test_moreapi():
    "Testing more class interface stuff, mostly the key and value iterators"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    kv.put("a", "b")
    kv.put("c", "d")
    assert list(kv.keys()) == ["a", "c"]
    assert list(kv.values()) == ["b", "d"]
    assert list(kv.items()) == [("a", "b"), ("c", "d")]
    assert "a" in kv

    assert list(kv.iterkeys()) == ["a", "c"]
    assert list(kv.itervalues()) == ["b", "d"]
    assert list(kv.iteritems()) == [("a", "b"), ("c", "d")]

    assert kv.get("foo", missing_as_none=True) is None

    repr(kv)


def test_moreapi_random():
    "Testing more class interface functions, mainly the randomness related ones"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    kv.put("a", "b")
    kv.put("c", "d")

    kv.random_choice()


    kv.random_sample(1)

    kv.random_keys(1)

    kv.random_values(1)

    # more than we have
    assert len( kv.random_sample(99) ) == 2

    kv.random_keys(99)

    kv.random_values(99)



def test_list():
    """Test that we can list the stores you have created.
       We can't really know what the testing account has, so this wouldn't be deterministic;
       just check that it doesn't fail
    """
    wetsuite.helpers.localdata.list_stores()
    #wetsuite.helpers.localdata.list_stores(look_under="/tmp/") # TODO: something that exists and won't lead e.g. to permission problems
 
    # may take a while if you have made huge stores:
    # wetsuite.helpers.localdata.list_stores(get_num_items=True)


def test_doublecommit():
    "test that we do not trip over excessive/pointless commits"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    kv.commit()
    kv.put("1", "2", commit=False)
    kv.commit()
    kv.commit()


def test_doublerollback():
    "do not trip over excessive/pointless rollbacks"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    kv.commit()
    kv.put("1", "2", commit=False)
    kv.rollback()
    kv.rollback()


def test_rollback():
    """see if rollback does what it should in terms of not adding.
       (And that we do not have basic fetching issues after rollback)"""
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    assert len(kv.keys()) == 0
    kv.put("1", "2", commit=False)
    # assert len( kv.keys() ) == 1    true but not relevant here
    kv.rollback()
    assert len(kv.keys()) == 0
    kv.commit()  # just to be sure there's no leftover state
    assert len(kv.keys()) == 0
    kv.rollback()  # check that it works if not in a transaction
    # TODO: more complex tests


def test_moretrans():
    "some transaction related tests"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    kv.put("1", "2")
    assert kv._in_transaction is False  # pylint: disable=protected-access
    kv.delete("1", commit=False)  # should start transaction
    assert kv._in_transaction is True  # pylint: disable=protected-access
    kv.vacuum()  # test if it commits before vacuum

    kv.delete("1", commit=False)  # should start transaction
    # also a test of 'do we roll back when still in transaction'
    kv.close() #  (at least, whether that code doesn't error out)


def test_context_manager():
    "see if use of class as a context manager works"
    with wetsuite.helpers.localdata.LocalKV(":memory:", str, str) as kv:
        assert len(kv.keys()) == 0


def test_truncate():
    "see if truncating all data actually removes all data"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    assert len(kv.keys()) == 0
    for i in range(10):
        kv.put(str(i), "blah", commit=False)
    kv.truncate()
    assert len(kv.keys()) == 0
    kv.commit()
    assert len(kv.keys()) == 0

    for i in range(10):
        kv.put(str(i), "blah", commit=False)
    kv.commit()
    assert len(kv.keys()) > 0
    kv.truncate()
    assert len(kv.keys()) == 0
    kv.commit()
    assert len(kv.keys()) == 0

    for i in range(10):
        kv.put(str(i), "blah", commit=False)
    kv.commit()
    assert len(kv.keys()) > 0
    kv.truncate(vacuum=False)
    assert len(kv.keys()) == 0
    kv.commit()
    assert len(kv.keys()) == 0


def test_bytesize():
    'check that "estimate size of contained data" does not error out'
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    initial_size = kv.bytesize()
    assert initial_size > 0  # I believe it counts the overhead
    # it counts in pages, so add more than a few things
    for i in range(1000):
        kv.put(str(i), "blah", commit=False)
    kv.commit()
    assert kv.bytesize() > initial_size


def test_type_init():
    "check that we can only use types the code allows (we restrict it for now)"
    with pytest.raises(TypeError, match=r".*not allowed*"):
        wetsuite.helpers.localdata.LocalKV(":memory:", dict, None)

    with pytest.raises(TypeError, match=r".*not allowed*"):
        wetsuite.helpers.localdata.LocalKV(":memory:", None, dict)


def test_type_check():
    "check that the data passed in is checked for the previously set type, as expected"
    # default str:str
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    kv.put("1", "2")
    with pytest.raises(TypeError, match=r".*are allowed*"):
        kv.put(1, "2")
    with pytest.raises(TypeError, match=r".*are allowed*"):
        kv.put("1", 2)

    # str:bytes
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, bytes)
    kv.put("a", b"b")
    with pytest.raises(TypeError, match=r".*are allowed*"):
        kv.put("a", "s")

    # int:float
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", key_type=int, value_type=float)
    kv.put(1, 2.0)
    with pytest.raises(TypeError, match=r".*are allowed*"):
        kv.put("a", "s")


def test_vacuum(tmp_path):
    "test that vacuum actually reduces file size, and is estimated to do so"
    path = tmp_path / "test1.db"
    kv = wetsuite.helpers.localdata.LocalKV(path, str, str)

    # add a bunch of data
    for i in range(10):
        kv.put(f"key{i}", "1234567890" * 10000, commit=False)
    kv.commit()
    # and remove it again
    for key in list(
        kv.keys()
    ):  # explicit list to materialize, so that we don't iterate while altering
        kv.delete(key)

    assert kv.estimate_waste() > 0  # with the above it would be ~1MB, I think

    size_before_vacuum = os.stat(kv.path).st_size
    kv.vacuum()
    size_after_vacuum = os.stat(kv.path).st_size

    assert size_after_vacuum < size_before_vacuum


def test_cached_fetch():
    "test whether the cacked URL fetch works"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, bytes)
    bytedata, fromcache = wetsuite.helpers.localdata.cached_fetch(
        kv, "https://www.google.com/"
    )
    assert fromcache is False
    assert b"<html" in bytedata

    bytedata, fromcache = wetsuite.helpers.localdata.cached_fetch(
        kv, "https://www.google.com/"
    )
    assert fromcache is True
    assert b"<html" in bytedata

    bytedata, fromcache = wetsuite.helpers.localdata.cached_fetch(
        kv, "https://www.google.com/", force_refetch=True
    )
    assert fromcache is False
    assert b"<html" in bytedata

    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)
    with pytest.raises(TypeError, match=r".*expects*"):  # complaint about type
        wetsuite.helpers.localdata.cached_fetch(kv, "https://www.google.com/")


def test_cached_fetch_type():
    "test what happens when you reverse the arguments or otherwise get them wrong"
    kv = wetsuite.helpers.localdata.LocalKV(":memory:", str, str)

    with pytest.raises(TypeError, match=r".*descend*"):  # complaint about type
        wetsuite.helpers.localdata.cached_fetch("https://www.google.com/", kv)

    with pytest.raises(TypeError, match=r".*descend*"):  # complaint about type
        wetsuite.helpers.localdata.cached_fetch({}, kv)


def test_msgpack_crud():
    "various API tests of things MsgpackKV overrides"
    kv = wetsuite.helpers.localdata.MsgpackKV(":memory:")
    with pytest.raises(KeyError):
        kv.get("a")
    kv.put("a", (2, 3, 4))
    assert len(kv) == 1
    assert kv.get("a") == [2, 3, 4]  # list, not tuple
    kv.delete("a")
    assert len(kv) == 0

    kv.put("b", {1: 2, b"b": [{"a": "b"}, {"c": [2, 1, "0"]}]})

    kv.put("c", {1: 2, "v": "a"})
    assert len(kv) == 2
    # checks that strict_map_key is not enforced (things other than str or bytes)
    kv.items()
    kv.values()

    kv.delete("c")
    assert len(kv) == 1


def test_msgpack_moreapi():
    "more API tests of things MsgpackKV overrides"
    kv = wetsuite.helpers.localdata.MsgpackKV(":memory:")
    kv.put("b", 1)
    kv.put("a", 2)
    kv.put("c", (5, 6))

    assert "a" in list(kv.iterkeys())
    assert 1 in list(kv.itervalues())
    assert ("b", 1) in list(kv.iteritems())

    assert "a" in list(kv.keys())
    assert 1 in list(kv.values())
    assert ("b", 1) in list(kv.items())


def test_resolve_path():
    "TODO: better tests"
    assert wetsuite.helpers.localdata.resolve_path(":memory:") == ":memory:"

    assert os.sep in wetsuite.helpers.localdata.resolve_path("foo")

    assert wetsuite.helpers.localdata.resolve_path("foo/bar").count(os.sep) == 1


def test_is_file_a_store(tmp_path):
    "test that we can distinguish between stores and non-stores"

    # fail on a non-file
    wetsuite.helpers.localdata.is_file_a_store("/")

    # fail on a non-sqlite file
    # a file we know exists and isn't a store: this test file itself
    import test_localdata     # so pylint: disable=import-self,import-outside-toplevel
    assert wetsuite.helpers.localdata.is_file_a_store(test_localdata.__file__) is False

    # make a store, to then test that it is one
    path = tmp_path / "test.db"
    kv = wetsuite.helpers.localdata.LocalKV(path, str, str)
    kv.close()
    assert wetsuite.helpers.localdata.is_file_a_store(kv.path) is True



def test_concurrent_rw(tmp_path):
    " test that both views on a database see the same data  even if one was opened later "
    path = tmp_path / "test_rw.db"
    kv1 = wetsuite.helpers.localdata.LocalKV(path, str, str)
    kv1.put("a", "b") # note: implied commit

    kv2 = wetsuite.helpers.localdata.LocalKV(path, str, str)

    kv1.put("c", "d") # note: implied commit
    kv2.put("e", "f") # note: implied commit

    assert len(kv1.items()) > 0
    assert len(kv1.items()) == 3
    assert len(kv2.items()) == 3

    assert kv1.items() == kv2.items()



def test_multiread_and_locking( tmp_path ):
    """
    Test some basic behaviour wen you have multiple readers on a store.

    Might be disabled (e.g. by prepending DISABLED_ to the function name)
    because the test takes longish (on purpose, waiting for a timeout),
    and also isn't as deterministic as it should be.
    """
    import sqlite3 # pylint: disable=import-outside-toplevel

    # similar setup as in test_concurrent_rw
    path = tmp_path / "test1.db"
    kv1 = wetsuite.helpers.localdata.LocalKV(path, str, str)
    kv1.put("a", "b")
    kv2 = wetsuite.helpers.localdata.LocalKV(path, str, str)
    kv1.put("c", "d")
    assert len(kv1.items()) == 2
    assert len(kv2.items()) == 2
    assert kv1.items() == kv2.items()


    # test that not committing leaves the database locked and other opens would fail
    #   (defined sqlite3 behaviour)
    kv1.put("e", "f", commit=False)  # this would keep the database locked until
    with pytest.raises( sqlite3.OperationalError, match=r".*database is locked*" ):
        # Since the file is now considered locked, 
        #   any other view should time out reading or writing anything
        # Note that this will take the default 5 seconds to time out
        kv3 = wetsuite.helpers.localdata.LocalKV(path, str, str)
        kv3.items()


    # test that a commit does fix that
    kv1.commit()
    kv4 = wetsuite.helpers.localdata.LocalKV(path, str, str)
    kv4.items() # i.e. that this line doesn't raise an sqlite3.OperationalError


    # check that a commit=true (default), while in a transaction due to an earlier commit=false,
    #  actually does a commit
    kv1.put("g", "h", commit=False)
    kv1.put("i", "j")
    kv4 = wetsuite.helpers.localdata.LocalKV(path, str, str)
    kv4.items()


    # check that delete has the same behaviour
    kv1.delete("i", commit=False)  # this would keep the database locked until
    with pytest.raises( sqlite3.OperationalError, match=r".*database is locked*" ):
        # note this will take the default 5 seconds to time out
        kv5 = wetsuite.helpers.localdata.LocalKV(path, str, str)
        kv5.items()

    kv1.delete("g", commit=False)  # this would keep the database locked until
    kv1.delete("e")
    kv6 = wetsuite.helpers.localdata.LocalKV(path, str, str)
    kv6.items()


def DISABLED_test_thread(tmp_path):
    """See whether (with the default autocommit behaviour) access is concurrent
    and not _overly_ eager to error out via a timeout.
    Basically see if the layer we added forgot something.

    TODO: loosen up the intensity, it may still race to fail under enough load

    disabled because it (intentionally) takes some time.
    """
    import time      # pylint: disable=import-outside-toplevel
    import threading # pylint: disable=import-outside-toplevel

    # It seems threads may share the module, but not connections
    # https://docs.python.org/3/library/sqlite3.html#sqlite3.threadsafety
    path = tmp_path / "test_thr.db"

    def get_sqlite3_thread_safety():
        """The sqlite module's threadsafety module is hardcoded for now,
           querying the sqlite library itself is technically more accurate.
           See https://ricardoanderegg.com/posts/python-sqlite-thread-safety/ for why this is here
        """
        import sqlite3 # pylint: disable=import-outside-toplevel
        conn = sqlite3.connect(":memory:")
        threadsafe_val = conn.execute(
            "SELECT *  FROM pragma_compile_options  WHERE compile_options LIKE 'THREADSAFE=%'"
        ).fetchone()[0]
        conn.close()
        threadsafe_val = int(threadsafe_val.split("=")[1])
        return {0:0, 2:1, 1:3}[
            threadsafe_val
        ]  # sqlite's THREADSAFE values to DBAPI2 values

    if get_sqlite3_thread_safety() in ( 1, 3, ):
        # in both you can share the module, but only in 3 could you share a connection
        start = time.time()
        end = start + 7

        def writer(end, path):
            myid = threading.get_ident() % 10000
            mycount = 0
            while time.time() < end:
                mykv = wetsuite.helpers.localdata.LocalKV(path, str, str)
                mykv.put("%s_%s" % (myid, mycount), "01234567890" * 500)
                mycount += 1
                # time.sleep(0.01) # it seems that without this it wil
                # mykv.close()

        # mykv = wetsuite.helpers.localdata.LocalKV( path )
        # time.sleep(0.1)
        # also leave this open as reader, why not

        started = []
        # writer(end, path)
        for _ in range( 3 ):
            # Why 3?  It seems to take a few dozen concurrent writers to make it time itself out
            #  (...on an SSD, that may well be relevant).
            th = threading.Thread(target=writer, args=(end, path))
            th.start()
            started.append(th)
            # time.sleep(0.1)

        while time.time() < end:  # main thread watches what the others are managing to do
            # logging.warning( ' FILESIZE   '+str(os.stat(path).st_size) )
            mykv = wetsuite.helpers.localdata.LocalKV(path, str, str)
            # logging.warning( ' AMTO     '+str(len(mykv)) )
            # logging.warning('%s'%mykv.keys())
            mykv.close()
            time.sleep(0.5)

        for th in started:
            th.join()

    else:  # thread-safety is 0
        raise EnvironmentError(
            "SQLite is compiled single-threaded, we can be fairly sure it  would fail"
        )
