from pathlib import Path

from sphinx_pyrunblock.utils import linerange, shorter


def test_linerange_none():
    assert linerange(None) == set()


def test_linerange_closed():
    assert linerange("5-10") == set(range(5, 11))


def test_linerange_single_point():
    assert linerange("3-3") == {3}


def test_linerange_open_ended():
    result = linerange("3-")
    assert result == set(range(3, 101))


def test_linerange_open_ended_truncates_past_100():
    # Known limitation: an open-ended range is capped at 100 rather than
    # materialising an unbounded set. See the sphinx-pyrunblock planning
    # notes for why this wasn't changed in this pass.
    result = linerange("3-")
    assert 100 in result
    assert 150 not in result


def test_shorter_two_components():
    assert shorter("/a/b/c/d.rst") == str(Path("c", "d.rst"))


def test_shorter_single_component():
    assert shorter("d.rst") == "d.rst"


def test_linerange_bare_number():
    assert linerange("4") == {4}
