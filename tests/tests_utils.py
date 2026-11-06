from array import array
from ast import literal_eval
from collections import defaultdict
from io import BytesIO
from typing import Union  # py<3.10

from pytest import warns

from tqdm.utils import CallbackIOWrapper, envwrap


def test_envwrap_deprecated(monkeypatch):
    monkeypatch.setenv('FUNC_A', "42")
    monkeypatch.setenv('FUNC_TyPe_HiNt', "1337")
    monkeypatch.setenv('FUNC_Unused', "x")

    with warns(DeprecationWarning, match="Trailing underscore in `name` is automatic"):
        @envwrap("FUNC_")
        def func(a=1, b=2, type_hint: int = None):
            return a, b, type_hint

    assert (42, 2, 1337) == func()
    assert (99, 2, 1337) == func(a=99)


def test_envwrap(monkeypatch):
    monkeypatch.setenv('NAME_FUNC_A', "42")
    monkeypatch.setenv('NAME_TyPe_HiNt', "1337")
    monkeypatch.setenv('NAME_unused', "x")

    @envwrap("name", "func")
    def func(a=1, b=2, type_hint: int = None):
        return a, b, type_hint

    assert (42, 2, 1337) == func()
    assert (99, 2, 1337) == func(a=99)


def test_envwrap_types(monkeypatch):
    monkeypatch.setenv('FUNC_notype', "3.14159")

    @envwrap("func", types=defaultdict(lambda: literal_eval))
    def func(notype=None):
        return notype

    assert 3.14159 == func()

    monkeypatch.setenv('FUNC_number', "1")
    monkeypatch.setenv('FUNC_string', "1")

    @envwrap("func", types={'number': int})
    def nofallback(number=None, string=None):
        return number, string

    assert 1, "1" == nofallback()


def test_envwrap_annotations(monkeypatch):
    monkeypatch.setenv('FUNC_number', "1.1")
    monkeypatch.setenv('FUNC_string', "1.1")

    @envwrap("func")
    def annotated(number: Union[int, float] = None, string: int = None):
        return number, string

    assert 1.1, "1.1" == annotated()


def test_callbackiowrapper_write_counts_bytes():
    """wrapped write() must report bytes written, not data element count"""
    stream = BytesIO()
    counts = []
    writer = CallbackIOWrapper(counts.append, stream, 'write')
    # untyped memoryview: len(data) is the element count, not byte count
    writer.write(memoryview(array('I', [1, 2, 3])))
    assert [array('I').itemsize * 3] == counts
    # byte-like data: reported count unchanged
    writer.write(b'test')
    assert [array('I').itemsize * 3, 4] == counts


def test_callbackiowrapper_write_counts_fallback():
    """streams returning None on write() fall back to len(data)"""
    class NullStream:
        def write(self, data):
            return None

    counts = []
    writer = CallbackIOWrapper(counts.append, NullStream(), 'write')
    writer.write(b'test')
    assert [4] == counts
