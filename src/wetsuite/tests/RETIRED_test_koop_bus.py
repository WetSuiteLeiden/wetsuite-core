""" Testing koop_bus """

import os
from wetsuite.datacollect.koop_bus import normalize_path, id_from_path, BUSFetcher


def test_normalize_path():
    "test that normalize_path does its basic job"
    assert (
        normalize_path(
            "ftps://bestanden.officielebekendmakingen.nl/2024/05/17/gmb/gmb-2024-216934/"
        )
        == "/2024/05/17/gmb/gmb-2024-216934/"
    )
    assert (
        normalize_path("/2024/05/17/gmb/gmb-2024-216934/")
        == "/2024/05/17/gmb/gmb-2024-216934/"
    )


def test_id_from_path():
    "test that id_from_path does its basic job"
    assert (
        id_from_path(
            "ftps://bestanden.officielebekendmakingen.nl/2024/05/17/gmb/gmb-2024-216934/"
        )
        == "gmb-2024-216934"
    )
    assert id_from_path("/2024/05/17/gmb/gmb-2024-216934/") == "gmb-2024-216934"


def test_interact_listdir():
    "test that we can log in, and list contents"
    bf = BUSFetcher()
    c = bf.connect()
    assert len(c.listdir("/")) > 0
    assert len(bf.listdir("/")) > 0


def test_get_bytes():
    "test that we can log in, and list contents"
    bf = BUSFetcher()
    # c = bf.connect()
    assert len(bf.get_bytes("/1995/01/02/changelog.xml")) > 0


def test_get_file(tmp_path):
    "test that we can log in, and list contents"
    bf = BUSFetcher()
    # c = bf.connect()
    bf.get_file("/1995/01/02/changelog.xml", os.path.join(tmp_path, "changelog"))
