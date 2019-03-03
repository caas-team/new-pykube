from pykube.utils import obj_merge


def test_obj_merge():
    assert obj_merge({}, {}) == {}
    assert obj_merge({'a': 1}, {}) == {'a': 1}
    assert obj_merge({}, {'b': 2}) == {'b': 2}
    assert obj_merge({'a': []}, {'a': []}) == {'a': []}
    assert obj_merge({'a': [1, 2]}, {'a': [3, 4]}) == {'a': [1, 2]}
