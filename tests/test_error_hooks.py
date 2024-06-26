import pytest

from osort import (
    DecodingError,
    ParseError,
    ResolutionError,
    UnknownEncodingError,
    WildcardImportError,
    osort,
)


class _DummyException(Exception):
    pass


# === Unknown Encoding Error ===================================================


def test_on_unknown_encoding_error_raise():
    original = b"# coding=invalid-encoding\n"
    with pytest.raises(UnknownEncodingError) as exc_info:
        osort(original, on_unknown_encoding_error="raise")
    assert str(exc_info.value) == "unknown encoding: invalid-encoding"
    assert exc_info.value.encoding == "invalid-encoding"


def test_on_unknown_encoding_error_ignore():
    original = b"# coding=invalid-encoding\n"
    actual = osort(original, on_unknown_encoding_error="ignore")
    assert actual == original


def test_on_unknown_encoding_error_callback():
    original = b"# coding=invalid-encoding\n"

    def on_unknown_encoding_error(message, *, encoding):
        raise _DummyException(message, encoding)

    with pytest.raises(_DummyException) as exc_info:
        osort(original, on_unknown_encoding_error=on_unknown_encoding_error)
    assert exc_info.value.args == (
        "unknown encoding: invalid-encoding",
        "invalid-encoding",
    )


# === Decoding Error ===========================================================


def test_on_decoding_error_raise():
    original = b"# coding=ascii\n\xfe = 2"
    with pytest.raises(DecodingError) as exc_info:
        osort(original, on_decoding_error="raise")
    assert (
        str(exc_info.value)
        == "'ascii' codec can't decode byte 0xfe in position 15: ordinal not in range(128)"
    )


def test_on_decoding_error_ignore():
    original = b"# coding=ascii\n\xfe = 2"
    actual = osort(original, on_decoding_error="ignore")
    assert actual == original


def test_on_decoding_error_callback():
    original = b"# coding=ascii\n\xfe = 2"

    def on_decoding_error(message):
        raise _DummyException(message)

    with pytest.raises(_DummyException) as exc_info:
        osort(original, on_decoding_error=on_decoding_error)
    assert exc_info.value.args == (
        "'ascii' codec can't decode byte 0xfe in position 15: ordinal not in range(128)",
    )


# === Parse Error ==============================================================


def test_on_parse_error_raise():
    original = "a ="
    with pytest.raises(ParseError) as exc_info:
        osort(original, on_parse_error="raise")
    assert str(exc_info.value) == "invalid syntax"
    assert exc_info.value.lineno == 1
    assert exc_info.value.col_offset == 4


def test_on_parse_error_ignore():
    original = "a ="
    actual = osort(original, on_parse_error="ignore")
    assert actual == original


def test_on_parse_error_callback():
    original = "a ="

    def on_parse_error(message, *, lineno, col_offset):
        raise _DummyException(message, lineno, col_offset)

    with pytest.raises(_DummyException) as exc_info:
        osort(original, on_parse_error=on_parse_error)
    assert exc_info.value.args == ("invalid syntax", 1, 4)


# === Unresolved ===============================================================


def test_on_unresolved_raise():
    original = "def fun():\n    unresolved()"

    with pytest.raises(ResolutionError) as exc_info:
        osort(original, on_unresolved="raise")

    assert str(exc_info.value) == "could not resolve 'unresolved'"
    assert exc_info.value.name == "unresolved"
    assert exc_info.value.lineno == 2
    assert exc_info.value.col_offset == 4


def test_on_unresolved_ignore():
    original = "def fun():\n    unresolved()"

    actual = osort(original, on_unresolved="ignore")

    assert actual == original


def test_on_unresolved_callback():
    original = "def fun():\n    unresolved()"

    def on_unresolved(message, *, name, lineno, col_offset):
        raise _DummyException(message, name, lineno, col_offset)

    with pytest.raises(_DummyException) as exc_info:
        osort(original, on_unresolved=on_unresolved)

    assert exc_info.value.args == (
        "could not resolve 'unresolved'",
        "unresolved",
        2,
        4,
    )


# === Wildcard Import ==========================================================


def test_on_wildcard_import_raise():
    original = "from module import *"

    with pytest.raises(WildcardImportError) as exc_info:
        osort(original, on_wildcard_import="raise")

    assert (
        str(exc_info.value)
        == "can't reliably determine dependencies on * import"
    )
    assert exc_info.value.lineno == 1
    assert exc_info.value.col_offset == 0


def test_on_wildcard_import_ignore():
    original = "from module import *\n"

    actual = osort(original, on_wildcard_import="ignore")

    assert actual == original


def test_on_wildcard_import_callback():
    original = "from module import *"

    def on_wildcard_import(*, lineno, col_offset):
        raise _DummyException(lineno, col_offset)

    with pytest.raises(_DummyException) as exc_info:
        osort(original, on_wildcard_import=on_wildcard_import)

    assert exc_info.value.args == (1, 0)
