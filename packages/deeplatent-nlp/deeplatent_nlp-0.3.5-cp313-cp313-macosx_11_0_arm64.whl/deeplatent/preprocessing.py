"""
SARF (Sarf-Aware Representation Framework) Preprocessing Module.

This module provides efficient byte-level morpheme preprocessing.
SARF preprocessing achieves 1.09 Arabic/English parity (vs 1.94 without preprocessing).

The core rewriting logic is implemented in compiled native code for performance
and IP protection. A native extension is REQUIRED for this package to function.
"""
import json
import os
from typing import Dict, Optional, Union

_BUNDLED_MORPHEME_MAP = os.path.join(os.path.dirname(__file__), "morpheme_map.json")

try:
    from deeplatent._core import ByteRewriterCore as _ByteRewriterCore, is_available
    _NATIVE_AVAILABLE = is_available()
except ImportError:
    _NATIVE_AVAILABLE = False
    _ByteRewriterCore = None


def native_available() -> bool:
    """Check if the native core is available."""
    return _NATIVE_AVAILABLE


class ByteRewriter:
    """
    Efficient byte-level rewriter for morpheme matching.

    Requires the native extension to be installed.
    """

    def __init__(self, rewriting_rules: Union[str, Dict]):
        if not _NATIVE_AVAILABLE or _ByteRewriterCore is None:
            raise ImportError(
                "Native core extension not available. "
                "Please install deeplatent-nlp with a compatible wheel for your platform, "
                "or build from source with Rust installed."
            )

        if isinstance(rewriting_rules, str):
            with open(rewriting_rules, 'r', encoding='utf-8') as f:
                self.rules = json.load(f)
        else:
            self.rules = dict(rewriting_rules)

        self._core = _ByteRewriterCore(self.rules)

    @property
    def using_native(self) -> bool:
        """Always returns True - native core is required."""
        return True

    def rewrite_text(self, text: str, reverse: bool = False) -> str:
        if not text:
            return text
        return self._core.rewrite_text(text, reverse)

    def get_stats(self) -> Dict:
        return {
            'num_rules': len(self.rules),
            'num_reverse_rules': len(self.rules),
            'native': True
        }


class SARFPreprocessor:
    """
    SARF preprocessor for Arabic text.

    Results with preprocessing:
        - Arabic Fertility: 2.29
        - English Fertility: 2.10
        - Parity: 1.09 (EXCELLENT)
    """

    def __init__(self, morpheme_map: Union[str, Dict]):
        self.rewriter = ByteRewriter(morpheme_map)

    @classmethod
    def from_file(cls, morpheme_map_path: str) -> "SARFPreprocessor":
        return cls(morpheme_map_path)

    @classmethod
    def from_bundled(cls) -> "SARFPreprocessor":
        if not os.path.exists(_BUNDLED_MORPHEME_MAP):
            raise FileNotFoundError(f"Bundled morpheme_map.json not found at {_BUNDLED_MORPHEME_MAP}")
        return cls(_BUNDLED_MORPHEME_MAP)

    @classmethod
    def from_huggingface(cls, repo_id: str = "almaghrabima/deeplatent-tokenizer") -> "SARFPreprocessor":
        if os.path.exists(_BUNDLED_MORPHEME_MAP):
            return cls(_BUNDLED_MORPHEME_MAP)
        from huggingface_hub import hf_hub_download
        path = hf_hub_download(repo_id=repo_id, filename="morpheme_map.json")
        return cls(path)

    def preprocess(self, text: str, language: Optional[str] = None) -> str:
        if not text or language == 'en':
            return text
        return self.rewriter.rewrite_text(text, reverse=False)

    def postprocess(self, text: str) -> str:
        if not text:
            return text
        return self.rewriter.rewrite_text(text, reverse=True)

    def get_stats(self) -> Dict:
        return self.rewriter.get_stats()
