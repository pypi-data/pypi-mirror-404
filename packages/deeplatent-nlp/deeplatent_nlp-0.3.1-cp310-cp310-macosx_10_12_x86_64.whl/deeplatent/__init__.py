"""
DeepLatent - SARF/MYTE Tokenizer for Arabic/English bilingual text.

DeepLatent provides the MYTE (Morphologically-Yielding Tokenizer Encoding)
tokenizer with built-in morpheme preprocessing for Arabic text, achieving
excellent Arabic/English parity (0.85 - Arabic is MORE efficient than English!).

The complete tokenization pipeline is implemented in Rust for performance
and IP protection. This package provides a Python interface to the compiled core.

v0.3.0 introduces a fully native Rust tokenizer that requires no external
dependencies or network access for basic usage.

Usage (Native mode - recommended):
    >>> from deeplatent import SARFTokenizer
    >>> # No network required, no dependencies needed
    >>> tokenizer = SARFTokenizer.from_native()
    >>> tokens = tokenizer.encode("مرحبا بكم Hello world")
    >>> text = tokenizer.decode(tokens)

Usage (HuggingFace mode - requires transformers):
    >>> from deeplatent import SARFTokenizer
    >>> tokenizer = SARFTokenizer.from_pretrained("almaghrabima/deeplatent-tokenizer")
    >>> tokens = tokenizer.encode("مرحبا بكم Hello world")
    >>> text = tokenizer.decode(tokens)

Performance:
    With SARF/MYTE preprocessing:
        - Arabic Fertility: 1.78 (tokens per word)
        - English Fertility: 2.10
        - Parity: 0.85 (EXCELLENT - Arabic more efficient!)

    Without preprocessing:
        - Arabic Fertility: 5.65
        - English Fertility: 2.91
        - Parity: 1.94 (Moderate)

Changes in v0.3.0:
    - Full Rust tokenization pipeline (encode + decode)
    - Obfuscated morpheme map and BPE vocab embedded in binary
    - No required dependencies (transformers/HF optional)
    - New from_native() class method for dependency-free usage
    - Batch encode/decode in native Rust for performance
"""

__version__ = "0.3.0"
__author__ = "Mohammed Almaghrabi"
__email__ = "almaghrabima@gmail.com"

from .tokenizer import SARFTokenizer, AutoTokenizer, Encoding
from .preprocessing import SARFPreprocessor, ByteRewriter, native_available

__all__ = [
    "SARFTokenizer",
    "AutoTokenizer",
    "Encoding",
    "SARFPreprocessor",
    "ByteRewriter",
    "native_available",
    "__version__",
]
