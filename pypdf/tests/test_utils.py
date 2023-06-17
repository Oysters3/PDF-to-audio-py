"""Test the pypdf._utils module."""
import io
from pathlib import Path

import pytest

import pypdf._utils
from pypdf import PdfReader
from pypdf._utils import (
    File,
    _get_max_pdf_version_header,
    _human_readable_bytes,
    deprecate_with_replacement,
    deprecation_bookmark,
    deprecation_no_replacement,
    mark_location,
    matrix_multiply,
    read_block_backwards,
    read_previous_line,
    read_until_regex,
    read_until_whitespace,
    rename_kwargs,
    skip_over_comment,
    skip_over_whitespace,
)
from pypdf.errors import DeprecationError, PdfReadError, PdfStreamError

from . import get_pdf_from_url

TESTS_ROOT = Path(__file__).parent.resolve()
PROJECT_ROOT = TESTS_ROOT.parent
RESOURCE_ROOT = PROJECT_ROOT / "resources"


@pytest.mark.parametrize(
    ("stream", "expected"),
    [
        (io.BytesIO(b"foo"), False),
        (io.BytesIO(b""), False),
        (io.BytesIO(b" "), True),
        (io.BytesIO(b"  "), True),
        (io.BytesIO(b"  \n"), True),
        (io.BytesIO(b"    \n"), True),
    ],
)
def test_skip_over_whitespace(stream, expected):
    assert skip_over_whitespace(stream) == expected


def test_read_until_whitespace():
    assert read_until_whitespace(io.BytesIO(b"foo"), maxchars=1) == b"f"


@pytest.mark.parametrize(
    ("stream", "remainder"),
    [
        (io.BytesIO(b"% foobar\n"), b""),
        (io.BytesIO(b""), b""),
        (io.BytesIO(b" "), b" "),
        (io.BytesIO(b"% foo%\nbar"), b"bar"),
    ],
)
def test_skip_over_comment(stream, remainder):
    skip_over_comment(stream)
    assert stream.read() == remainder


def test_read_until_regex_premature_ending_name():
    import re

    stream = io.BytesIO(b"")
    assert read_until_regex(stream, re.compile(b".")) == b""


@pytest.mark.parametrize(
    ("a", "b", "expected"),
    [
        (((3,),), ((7,),), ((21,),)),
        (((3, 7),), ((5,), (13,)), ((3 * 5.0 + 7 * 13,),)),
        (((3,), (7,)), ((5, 13),), ((3 * 5, 3 * 13), (7 * 5, 7 * 13))),
    ],
)
def test_matrix_multiply(a, b, expected):
    assert matrix_multiply(a, b) == expected


def test_mark_location():
    stream = io.BytesIO(b"abde" * 6000)
    mark_location(stream)
    Path("pypdf_pdfLocation.txt").unlink()  # cleanup


def test_hex_str():
    assert pypdf._utils.hex_str(10) == "0xa"


@pytest.mark.parametrize(
    ("input_str", "expected"),
    [
        ("foo", b"foo"),
        ("😀", "😀".encode()),
        ("‰", "‰".encode()),
        ("▷", "▷".encode()),
        ("世", "世".encode()),
        # A multi-character string example with non-latin-1 characters:
        ("😀😃", "😀😃".encode()),
    ],
)
def test_b(input_str: str, expected: str):
    assert pypdf._utils.b_(input_str) == expected


def test_deprecate_no_replacement():
    with pytest.warns(DeprecationWarning) as warn:
        pypdf._utils.deprecate_no_replacement("foo")
    error_msg = "foo is deprecated and will be removed in pypdf 3.0.0."
    assert warn[0].message.args[0] == error_msg


@pytest.mark.parametrize(
    ("left", "up", "upleft", "expected"),
    [
        (0, 0, 0, 0),
        (1, 0, 0, 1),
        (0, 1, 0, 1),
        (0, 0, 1, 0),
        (1, 2, 3, 1),
        (2, 1, 3, 1),
        (1, 3, 2, 2),
        (3, 1, 2, 2),
        (3, 2, 1, 3),
    ],
)
def test_paeth_predictor(left, up, upleft, expected):
    assert pypdf._utils.paeth_predictor(left, up, upleft) == expected


@pytest.mark.parametrize(
    ("dat", "pos", "to_read", "expected", "expected_pos"),
    [
        (b"abc", 1, 0, b"", 1),
        (b"abc", 1, 1, b"a", 0),
        (b"abc", 2, 1, b"b", 1),
        (b"abc", 2, 2, b"ab", 0),
        (b"abc", 3, 1, b"c", 2),
        (b"abc", 3, 2, b"bc", 1),
        (b"abc", 3, 3, b"abc", 0),
        (b"", 0, 1, None, 0),
        (b"a", 0, 1, None, 0),
        (b"abc", 0, 10, None, 0),
    ],
)
def test_read_block_backwards(dat, pos, to_read, expected, expected_pos):
    s = io.BytesIO(dat)
    s.seek(pos)
    if expected is not None:
        assert read_block_backwards(s, to_read) == expected
    else:
        with pytest.raises(PdfStreamError):
            read_block_backwards(s, to_read)
    assert s.tell() == expected_pos


def test_read_block_backwards_at_start():
    s = io.BytesIO(b"abc")
    with pytest.raises(PdfStreamError) as _:
        read_previous_line(s)


@pytest.mark.parametrize(
    ("dat", "pos", "expected", "expected_pos"),
    [
        (b"abc", 1, b"a", 0),
        (b"abc", 2, b"ab", 0),
        (b"abc", 3, b"abc", 0),
        (b"abc\n", 3, b"abc", 0),
        (b"abc\n", 4, b"", 3),
        (b"abc\n\r", 4, b"", 3),
        (b"abc\nd", 5, b"d", 3),
        # Skip over multiple CR/LF bytes
        (b"abc\n\r\ndef", 9, b"def", 3),
    ],
    ids=list(range(8)),
)
def test_read_previous_line(dat, pos, expected, expected_pos):
    s = io.BytesIO(dat)
    s.seek(pos)
    assert read_previous_line(s) == expected
    assert s.tell() == expected_pos


# for unknown reason if the parameters are passed through pytest, errors are reported
def test_read_previous_line2():
    # Include a block full of newlines...
    test_read_previous_line(
        b"abc" + b"\n" * (2 * io.DEFAULT_BUFFER_SIZE) + b"d",
        2 * io.DEFAULT_BUFFER_SIZE + 4,
        b"d",
        3,
    )
    # Include a block full of non-newline characters
    test_read_previous_line(
        b"abc\n" + b"d" * (2 * io.DEFAULT_BUFFER_SIZE),
        2 * io.DEFAULT_BUFFER_SIZE + 4,
        b"d" * (2 * io.DEFAULT_BUFFER_SIZE),
        3,
    )
    # Both
    test_read_previous_line(
        b"abcxyz"
        + b"\n" * (2 * io.DEFAULT_BUFFER_SIZE)
        + b"d" * (2 * io.DEFAULT_BUFFER_SIZE),
        4 * io.DEFAULT_BUFFER_SIZE + 6,
        b"d" * (2 * io.DEFAULT_BUFFER_SIZE),
        6,
    )


def test_get_max_pdf_version_header():
    with pytest.raises(ValueError) as exc:
        _get_max_pdf_version_header(b"", b"PDF-1.2")
    assert exc.value.args[0] == "neither b'' nor b'PDF-1.2' are proper headers"


def test_read_block_backwards_exception():
    stream = io.BytesIO(b"foobar")
    stream.seek(6)
    with pytest.raises(PdfReadError) as exc:
        read_block_backwards(stream, 7)
    assert exc.value.args[0] == "Could not read malformed PDF file"


def test_deprecation_bookmark():
    @deprecation_bookmark(old_param="new_param")
    def foo(old_param: int = 1, baz: int = 2) -> None:
        pass

    with pytest.raises(DeprecationError) as exc:
        foo(old_param=12, new_param=13)
    expected_msg = "old_param is deprecated as an argument. Use new_param instead"
    assert exc.value.args[0] == expected_msg


def test_deprecate_with_replacement():
    def foo() -> None:
        deprecate_with_replacement("foo", "bar", removed_in="4.3.2")
        pass

    with pytest.warns(
        DeprecationWarning,
        match="foo is deprecated and will be removed in pypdf 4.3.2. Use bar instead.",
    ):
        foo()


def test_deprecation_no_replacement():
    def foo() -> None:
        deprecation_no_replacement("foo", removed_in="4.3.2")
        pass

    with pytest.raises(
        DeprecationError,
        match="foo is deprecated and was removed in pypdf 4.3.2.",
    ):
        foo()


def test_rename_kwargs():
    import functools
    from typing import Any, Callable

    def deprecation_bookmark_nofail(**aliases: str) -> Callable:
        """
        Decorator for deprecated term "bookmark".

        To be used for methods and function arguments
            outline_item = a bookmark
            outline = a collection of outline items.
        """

        def decoration(func: Callable) -> Any:  # type: ignore
            @functools.wraps(func)
            def wrapper(*args: Any, **kwargs: Any) -> Any:  # type: ignore
                rename_kwargs(func.__name__, kwargs, aliases, fail=False)
                return func(*args, **kwargs)

            return wrapper

        return decoration

    @deprecation_bookmark_nofail(old_param="new_param")
    def foo(old_param: int = 1, baz: int = 2, new_param: int = 1) -> None:
        pass

    expected_msg = (
        "foo received both old_param and new_param as an argument. "
        "old_param is deprecated. Use new_param instead."
    )
    with pytest.raises(TypeError, match=expected_msg):
        foo(old_param=12, new_param=13)

    with pytest.warns(
        DeprecationWarning,
        match="old_param is deprecated as an argument. Use new_param instead",
    ):
        foo(old_param=12)


@pytest.mark.enable_socket()
def test_escapedcode_followed_by_int():
    # iss #1294
    url = (
        "https://github.com/timedegree/playground_files/raw/main/"
        "%E8%AE%BA%E6%96%87/AN%20EXACT%20ANALYTICAL%20SOLUTION%20OF%20KEPLER'S%20EQUATION.pdf"
    )
    name = "keppler.pdf"

    reader = PdfReader(io.BytesIO(get_pdf_from_url(url, name=name)))
    for page in reader.pages:
        page.extract_text()


@pytest.mark.parametrize(
    ("input_int", "expected_output"),
    [
        (123, "123 Byte"),
        (1234, "1.2 kB"),
        (123_456, "123.5 kB"),
        (1_234_567, "1.2 MB"),
        (1_234_567_890, "1.2 GB"),
        (1_234_567_890_000, "1234.6 GB"),
    ],
)
def test_human_readable_bytes(input_int, expected_output):
    """_human_readable_bytes correctly transforms the integer to a string."""
    assert _human_readable_bytes(input_int) == expected_output


def test_file_class():
    """File class can be instanciated and string representation is ok."""
    f = File(name="image.png", data=b"")
    assert str(f) == "File(name=image.png, data: 0 Byte)"
    assert repr(f) == "File(name=image.png, data: 0 Byte, hash: 0)"
