'''
Tests related to the Dataset module
'''
import pytest

import wetsuite.datasets



def test_fetch_index():
    ' test whether the index fetches (online, so can fail) '
    wetsuite.datasets.fetch_index()


def test_list_datasets():
    ' test whether the index fetches (online, so can fail) '
    wetsuite.datasets.list_datasets()


def test_load():
    ' test whether we can load a dataset '
    wetsuite.datasets.load( 'gemeentes-struc' )
#   wetsuite.datasets.load( wetsuite.datasets.list_datasets()[0] ) # (implicitly tests that there is at least one currently at the configured index path


def test_load_noexist():
    ' test whether it complains about a non-existing dataset '
    with pytest.raises(ValueError, match=r'.*matched none.*'):
        wetsuite.datasets.load( 'sjkldfghghuiwser' )


def test_generated_today_text():
    ' test whether this function does not fail '
    wetsuite.datasets.generated_today_text()


def test_dataset_class_basics( ):
    ' test Some Dataset basics '
    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':b'b', 'c':b'd'},
        name  = 'name')
    assert ds.description == 'descr'
    assert ds.data == {'a':b'b', 'c':b'd'}
    assert ds.name == 'name'
    assert ds.num_items == 2

    str(ds)


def test_dataset_class_export( tmp_path ):
    ' test whether the "export this file by python type" makes basic sense '
    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':'b', 'c':'d'},
        name  = 'name')
    ds.export_files( in_dir_path=tmp_path )

    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':b'b', 'c':b'd'},
        name  = 'name')
    ds.export_files( in_dir_path=tmp_path )

    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':{1:2}, 'c':{3:4}},
        name  = 'name')
    ds.export_files( in_dir_path=tmp_path )

    # TODO: more


def test_dataset_class_export_zip1( tmp_path ):
    ' test whether the "export this file by python type" makes basic sense, ZIP variant '
    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':'b', 'c':'d'},
        name  = 'name')
    ds.export_files( to_zipfile_path=tmp_path/'test.zip' )


def test_dataset_class_export_zip2( tmp_path ):
    ' test whether the "export this file by python type" makes basic sense, ZIP variant '
    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':b'b', 'c':b'd'},
        name  = 'name')
    ds.export_files( to_zipfile_path=tmp_path/'test.zip' )


def test_dataset_class_export_zip3( tmp_path ):
    ' test whether the "export this file by python type" makes basic sense, ZIP variant '
    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':{1:2}, 'c':{3:4}},
        name  = 'name')
    ds.export_files( to_zipfile_path=tmp_path/'test.zip' )


def test_sizecheck( ):
    ' test whether the "do we have enough space?" check will work '

    def lots_of_space(path=None): # monkey patch  pylint: disable=unused-argument
        return 555555555555
    wetsuite.helpers.util.free_space = lots_of_space
    wetsuite.datasets.load( 'gemeentes-struc' )

    with pytest.raises(IOError, match=r'.*only.*'):
        def no_space(path=None): # monkey patch  pylint: disable=unused-argument
            return 5   # When I was young, five whole bytes, etc.
        wetsuite.helpers.util.free_space = no_space
        wetsuite.datasets.load( 'gemeentes-struc' )
