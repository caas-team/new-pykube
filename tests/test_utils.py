from pykube.utils import obj_merge


def test_obj_merge():
    assert obj_merge({}, {}) == {}
    assert obj_merge({'a': 1}, {}) == {'a': 1}
    assert obj_merge({}, {'b': 2}) == {'b': 2}
    assert obj_merge({'a': []}, {'a': []}) == {'a': []}
    assert obj_merge({'a': [1, 2]}, {'a': []}) == {'a': [1, 2]}
    assert obj_merge({'a': []}, {'a': [1, 2]}) == {'a': [1, 2]}
    assert obj_merge({'a': [1, 2]}, {'a': [3, 4]}) == {'a': [1, 2]}
    assert obj_merge({'a': {'b': [1, 2]}}, {'a': {'b': [3, 4, 5], 'c': [1, 2]}}) == {'a': {'b': [1, 2, 5], 'c': [1, 2]}}

    assert obj_merge({'a': {'e': [1, 2], 'f': [5, 6]}}, {'a': {'e': [3, 4]}, 'b': ['1']}, is_strategic=False) == {'a': {'e': [1, 2], 'f': [5, 6]}}
    assert obj_merge({'a': []}, {'a': [1, 2]}, is_strategic=False) == {'a': []}
    assert obj_merge({'a': {'b': [1, 2]}}, {'a': [1, 2]}, is_strategic=False) == {'a': {'b': [1, 2]}}
    assert obj_merge({'a': {'b': [1, 2]}}, {'a': {'b': [], 'c': [1, 2]}}, is_strategic=False) == {'a': {'b': [1, 2]}}
    assert obj_merge({'a': {'b': [1, 2]}}, {'a': {'b': [3, 4, 5], 'c': [1, 2]}}, is_strategic=False) == {'a': {'b': [1, 2]}}
