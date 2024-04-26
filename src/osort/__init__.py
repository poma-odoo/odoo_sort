"""
The python source code statement sorter.
"""

from osort._exceptions import (
    DecodingError,
    ParseError,
    ResolutionError,
    UnknownEncodingError,
    WildcardImportError,
)
from osort._osort import osort

# Let linting tools know that we do mean to re-export exception classes.
assert DecodingError is not None
assert ParseError is not None
assert ResolutionError is not None
assert UnknownEncodingError is not None
assert WildcardImportError is not None

try:
    from osort._version import VERSION as __version__  # type: ignore
except ImportError:
    __version__ = "0.0.1+dev"

__all__ = ["osort"]
