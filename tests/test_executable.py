import pathlib
import subprocess
import sys

import pytest

from odoo_sort import __version__
from odoo_sort._utils import escape_path

_good = b"""
def _private():
    pass

def public():
    return _private()
"""

_unsorted = b"""
def public():
    return _private()

def _private():
    pass
"""

_encoding = b"""
# coding=invalid-encoding
"""

_character = b"""
# coding=ascii
\xfe = 2
"""

_syntax = b"""
def _private(
    pass

def public(
    return _private()
"""

_resolution = b"""
def _private():
    pass

def public():
    return _other()
"""

_double_resolution = b"""
def _private():
    pass

def public():
    return _other() + _same()
"""


def _write_fixtures(dirpath, texts):
    paths = []
    for index, text in enumerate(texts):
        path = dirpath / f"file_{index:04}.py"
        path.write_bytes(text)
        paths.append(str(path))
    return paths


@pytest.fixture(params=["entrypoint", "module"])
def check(request):
    def _check(dirpath):
        odoo_sort_exe = {
            "entrypoint": ["odoo_sort"],
            "module": [sys.executable, "-m", "odoo_sort"],
        }[request.param]

        result = subprocess.run(
            [*odoo_sort_exe, "--check", str(dirpath)],
            capture_output=True,
            encoding="utf-8",
        )
        return result.stderr.splitlines(keepends=True), result.returncode

    return _check


@pytest.fixture(params=["entrypoint", "module"])
def odoo_sort(request):
    def _odoo_sort(dirpath):
        odoo_sort_exe = {
            "entrypoint": ["odoo_sort"],
            "module": [sys.executable, "-m", "odoo_sort"],
        }[request.param]

        result = subprocess.run(
            [*odoo_sort_exe, str(dirpath)],
            capture_output=True,
            encoding="utf-8",
        )
        return result.stderr.splitlines(keepends=True), result.returncode

    return _odoo_sort


def test_check_all_well(check, tmp_path):
    _write_fixtures(tmp_path, [_good, _good, _good])
    expected_msgs = [
        "3 files would be left unchanged\n",
    ]
    expected_status = 0
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_check_one_unsorted(check, tmp_path):
    paths = _write_fixtures(tmp_path, [_unsorted, _good, _good])
    expected_msgs = [
        f"ERROR: {escape_path(paths[0])} is incorrectly sorted\n",
        "1 file would be resorted, 2 files would be left unchanged\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_check_all_unsorted(check, tmp_path):
    paths = _write_fixtures(tmp_path, [_unsorted, _unsorted, _unsorted])
    expected_msgs = [
        f"ERROR: {escape_path(paths[0])} is incorrectly sorted\n",
        f"ERROR: {escape_path(paths[1])} is incorrectly sorted\n",
        f"ERROR: {escape_path(paths[2])} is incorrectly sorted\n",
        "3 files would be resorted\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_check_one_syntax_error(check, tmp_path):
    paths = _write_fixtures(tmp_path, [_syntax, _good, _good])
    expected_msgs = [
        f"ERROR: syntax error in {escape_path(paths[0])}: line 3, column 5\n",
        "2 files would be left unchanged, 1 file would not be sortable\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_check_all_syntax_error(check, tmp_path):
    paths = _write_fixtures(tmp_path, [_syntax, _syntax, _syntax])
    expected_msgs = [
        f"ERROR: syntax error in {escape_path(paths[0])}: line 3, column 5\n",
        f"ERROR: syntax error in {escape_path(paths[1])}: line 3, column 5\n",
        f"ERROR: syntax error in {escape_path(paths[2])}: line 3, column 5\n",
        "3 files would not be sortable\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_check_resolution_error(check, tmp_path):
    paths = _write_fixtures(tmp_path, [_resolution, _good, _good])
    expected_msgs = [
        f"ERROR: unresolved dependency '_other' in {escape_path(paths[0])}: line 6, column 11\n",
        "2 files would be left unchanged, 1 file would not be sortable\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_check_double_resolution_error(check, tmp_path):
    paths = _write_fixtures(tmp_path, [_double_resolution, _good, _good])
    expected_msgs = [
        f"ERROR: unresolved dependency '_other' in {escape_path(paths[0])}: line 6, column 11\n",
        f"ERROR: unresolved dependency '_same' in {escape_path(paths[0])}: line 6, column 22\n",
        "2 files would be left unchanged, 1 file would not be sortable\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_check_one_unsorted_one_syntax_error(check, tmp_path):
    paths = _write_fixtures(tmp_path, [_syntax, _unsorted, _good])
    expected_msgs = [
        f"ERROR: syntax error in {escape_path(paths[0])}: line 3, column 5\n",
        f"ERROR: {escape_path(paths[1])} is incorrectly sorted\n",
        "1 file would be resorted, 1 file would be left unchanged, 1 file would not be sortable\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = check(tmp_path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_all_well(odoo_sort, tmp_path):
    _write_fixtures(tmp_path, [_good, _good, _good])

    expected_msgs = [
        "3 files were left unchanged\n",
    ]
    expected_status = 0

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_one_unsorted(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_unsorted, _good, _good])

    expected_msgs = [
        f"Sorting {escape_path(paths[0])}\n",
        "1 file was resorted, 2 files were left unchanged\n",
    ]
    expected_status = 0

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_all_unsorted(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_unsorted, _unsorted, _unsorted])

    expected_msgs = [
        f"Sorting {escape_path(paths[0])}\n",
        f"Sorting {escape_path(paths[1])}\n",
        f"Sorting {escape_path(paths[2])}\n",
        "3 files were resorted\n",
    ]
    expected_status = 0

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_one_syntax_error(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_syntax, _good, _good])

    expected_msgs = [
        f"ERROR: syntax error in {escape_path(paths[0])}: line 3, column 5\n",
        "2 files were left unchanged, 1 file was not sortable\n",
    ]
    expected_status = 1

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_all_syntax_error(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_syntax, _syntax, _syntax])

    expected_msgs = [
        f"ERROR: syntax error in {escape_path(paths[0])}: line 3, column 5\n",
        f"ERROR: syntax error in {escape_path(paths[1])}: line 3, column 5\n",
        f"ERROR: syntax error in {escape_path(paths[2])}: line 3, column 5\n",
        "3 files were not sortable\n",
    ]
    expected_status = 1

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_resolution_error(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_resolution, _good, _good])

    expected_msgs = [
        f"ERROR: unresolved dependency '_other' in {escape_path(paths[0])}: line 6, column 11\n",
        "2 files were left unchanged, 1 file was not sortable\n",
    ]
    expected_status = 1

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_one_unsorted_one_syntax_error(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_syntax, _unsorted, _good])

    expected_msgs = [
        f"ERROR: syntax error in {escape_path(paths[0])}: line 3, column 5\n",
        f"Sorting {escape_path(paths[1])}\n",
        "1 file was resorted, 1 file was left unchanged, 1 file was not sortable\n",
    ]
    expected_status = 1

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_encoding_error(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_encoding])

    expected_msgs = [
        f"ERROR: unknown encoding, 'invalid-encoding', in {escape_path(paths[0])}\n",
        "1 file was not sortable\n",
    ]
    expected_status = 1

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_character_error(odoo_sort, tmp_path):
    paths = _write_fixtures(tmp_path, [_character])

    expected_msgs = [
        f"ERROR: encoding error in {escape_path(paths[0])}: 'ascii' codec can't decode byte 0xfe in position 16: ordinal not in range(128)\n",
        "1 file was not sortable\n",
    ]
    expected_status = 1

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_preserve_crlf_endlines(odoo_sort, tmp_path):
    input = b"a = b\r\nb = 4"
    expected_output = b"b = 4\r\na = b\r\n"

    paths = _write_fixtures(tmp_path, [input])

    expected_msgs = [
        f"Sorting {escape_path(paths[0])}\n",
        "1 file was resorted\n",
    ]
    expected_status = 0

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert actual_msgs == expected_msgs
    assert actual_status == expected_status

    (output,) = [pathlib.Path(path).read_bytes() for path in paths]
    assert output == expected_output


def test_odoo_sort_empty_dir(odoo_sort, tmp_path):
    expected_msgs = ["No files are present to be sorted. Nothing to do.\n"]
    expected_status = 0

    actual_msgs, actual_status = odoo_sort(tmp_path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_non_existent_file(odoo_sort, tmp_path):
    path = tmp_path / "file.py"

    expected_msgs = [
        f"ERROR: {escape_path(path)} does not exist\n",
        "1 file was not sortable\n",
    ]
    expected_status = 1

    actual_msgs, actual_status = odoo_sort(path)

    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_no_py_extension(odoo_sort, tmp_path):
    path = tmp_path / "file"
    path.write_bytes(_good)
    expected_msgs = ["1 file was left unchanged\n"]
    expected_status = 0
    actual_msgs, actual_status = odoo_sort(path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


@pytest.mark.skipif(
    sys.platform == "win32", reason="can't block read on windows"
)
def test_odoo_sort_unreadable_file(odoo_sort, tmp_path):
    path = tmp_path / "file.py"
    path.write_bytes(_good)
    path.chmod(0)
    expected_msgs = [
        f"ERROR: {escape_path(path)} is not readable\n",
        "1 file was not sortable\n",
    ]
    expected_status = 1
    actual_msgs, actual_status = odoo_sort(path)
    assert (actual_msgs, actual_status) == (expected_msgs, expected_status)


def test_odoo_sort_version():
    result = subprocess.run(
        ["odoo_sort", "--version"],
        capture_output=True,
        encoding="utf-8",
    )
    output = result.stdout
    assert output == f"odoo_sort {__version__}\n"


def test_odoo_sort_run_module():
    entrypoint_result = subprocess.run(
        ["odoo_sort", "--help"],
        capture_output=True,
        encoding="utf-8",
    )
    entrypoint_output = entrypoint_result.stderr.splitlines(keepends=True)

    module_result = subprocess.run(
        [sys.executable, "-m", "odoo_sort", "--help"],
        capture_output=True,
        encoding="utf-8",
    )
    module_output = module_result.stderr.splitlines(keepends=True)

    assert module_output == entrypoint_output
