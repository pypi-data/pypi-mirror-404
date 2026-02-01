"""
Backwards compatibility shim for suhail package.

This module is DEPRECATED. Please update your imports to use 'deeplatent' instead:

    # Old (deprecated):
    from suhail import SARFTokenizer

    # New (recommended):
    from deeplatent import SARFTokenizer

This shim will be removed in a future version.
"""
import warnings

warnings.warn(
    "The 'suhail' package has been renamed to 'deeplatent'. "
    "Please update your imports: 'from deeplatent import SARFTokenizer'. "
    "The 'suhail' import path will be removed in version 1.0.0.",
    DeprecationWarning,
    stacklevel=2
)

# Re-export everything from deeplatent
from deeplatent import (
    SARFTokenizer,
    AutoTokenizer,
    Encoding,
    SARFPreprocessor,
    ByteRewriter,
    __version__,
)

__all__ = [
    "SARFTokenizer",
    "AutoTokenizer",
    "Encoding",
    "SARFPreprocessor",
    "ByteRewriter",
    "__version__",
]
