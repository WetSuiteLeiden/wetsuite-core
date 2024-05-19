''' Testing koop_bus '''

from wetsuite.datacollect.koop_bus import normalize_path, id_from_path


def test_normalize_path():
    ' test that normalize_path does its basic job '
    assert normalize_path('ftps://bestanden.officielebekendmakingen.nl/2024/05/17/gmb/gmb-2024-216934/') == '/2024/05/17/gmb/gmb-2024-216934/'
    assert normalize_path('/2024/05/17/gmb/gmb-2024-216934/') == '/2024/05/17/gmb/gmb-2024-216934/'


def test_id_from_path():
    ' test that id_from_path does its basic job '
    assert id_from_path('ftps://bestanden.officielebekendmakingen.nl/2024/05/17/gmb/gmb-2024-216934/') == 'gmb-2024-216934'
    assert id_from_path('/2024/05/17/gmb/gmb-2024-216934/') == 'gmb-2024-216934'