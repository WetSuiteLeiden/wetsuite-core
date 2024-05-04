'''
Tests related to the Dataset module
'''
#import pytest

import wetsuite.datasets


def test_fetch_index():
    ' test whether the index fetches (online, so can fail) '
    wetsuite.datasets.fetch_index()


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
    ds.export_files( tmp_path )

    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':b'b', 'c':b'd'},
        name  = 'name')
    ds.export_files( tmp_path )

    ds = wetsuite.datasets.Dataset(
        description = 'descr',
        data  = {'a':{1:2}, 'c':{3:4}},
        name  = 'name')
    ds.export_files( tmp_path )

    # TODO: more
