"""
DeepLatent SARF Tokenizer - A morphology-aware tokenizer for Arabic/English bilingual text.

This module provides the main SARFTokenizer class that supports two modes:
1. Native mode (default): Uses compiled Rust core with embedded data (no network required)
2. HuggingFace mode: Uses HuggingFace Tokenizers backend (requires transformers)

Usage:
    >>> from deeplatent import SARFTokenizer
    >>> # Native mode (default, no network required)
    >>> tokenizer = SARFTokenizer()
    >>> tokens = tokenizer.encode("مرحبا بكم Hello world")
    >>> text = tokenizer.decode(tokens)
    >>>
    >>> # HuggingFace mode (requires transformers)
    >>> tokenizer = SARFTokenizer.from_pretrained("almaghrabima/deeplatent-tokenizer")
"""
import os
import re
from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from .preprocessing import SARFPreprocessor

if TYPE_CHECKING:
    from deeplatent._core import SARFTokenizerCore


class Encoding:
    """
    Represents the output of tokenization.

    Similar to HuggingFace tokenizers Encoding class.
    """

    def __init__(
        self,
        ids: List[int],
        tokens: Optional[List[str]] = None,
        attention_mask: Optional[List[int]] = None,
        type_ids: Optional[List[int]] = None,
        offsets: Optional[List[Tuple[int, int]]] = None,
    ):
        self.ids = ids
        self.tokens = tokens or []
        self.attention_mask = attention_mask or [1] * len(ids)
        self.type_ids = type_ids or [0] * len(ids)
        self.offsets = offsets or []

    def __len__(self) -> int:
        return len(self.ids)

    def __repr__(self) -> str:
        return f"Encoding(ids={self.ids[:10]}{'...' if len(self.ids) > 10 else ''}, length={len(self.ids)})"


class SARFTokenizer:
    """
    SARF (Sarf-Aware Representation Framework) Tokenizer.

    This tokenizer combines BPE tokenization with morpheme-aware preprocessing
    for Arabic text, achieving excellent Arabic/English parity (1.09).

    Supports two modes:
    1. Native mode (default): Uses compiled Rust core (fast, no dependencies)
    2. HuggingFace mode: Uses HuggingFace transformers backend

    Features:
        - Automatic SARF preprocessing for Arabic text
        - HuggingFace transformers compatible API
        - Efficient batch encoding/decoding
        - Support for special tokens

    Example:
        >>> # Native mode (default)
        >>> tokenizer = SARFTokenizer()
        >>> encoding = tokenizer.encode("مرحبا بكم في العالم")
        >>> print(f"Token count: {len(encoding)}")
        >>> decoded = tokenizer.decode(encoding)
        >>>
        >>> # HuggingFace mode
        >>> tokenizer = SARFTokenizer.from_pretrained("almaghrabima/deeplatent-tokenizer")
    """

    # Arabic Unicode ranges for language detection
    ARABIC_PATTERN = re.compile(r'[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF\uFB50-\uFDFF\uFE70-\uFEFF]')

    # Diacritics (tashkeel) pattern for normalization
    _TASHKEEL_RE = re.compile(r'[\u064B-\u0652\u0670]')
    # Zero-width characters pattern
    _ZW_RE = re.compile(r'[\u200B-\u200D\uFEFF\u200C\u202A-\u202E\u2066-\u2069]')
    # Indic digit mapping
    _INDIC_DIGITS = str.maketrans(
        '\u0660\u0661\u0662\u0663\u0664\u0665\u0666\u0667\u0668\u0669',
        '0123456789',
    )

    @staticmethod
    def _normalize_arabic(text: str) -> str:
        """Normalize Arabic text to match the training pipeline (medium level)."""
        if not text:
            return text
        # Remove diacritics and tatweel
        text = SARFTokenizer._TASHKEEL_RE.sub('', text)
        text = text.replace('\u0640', '')
        # Remove zero-width characters
        text = SARFTokenizer._ZW_RE.sub('', text)
        # Alef unification
        text = text.replace('\u0623', '\u0627')
        text = text.replace('\u0625', '\u0627')
        text = text.replace('\u0622', '\u0627')
        text = text.replace('\u0671', '\u0627')
        # Ya normalization
        text = text.replace('\u0649', '\u064A')
        # Hamza normalization (medium)
        text = text.replace('\u0624', '\u0648')
        text = text.replace('\u0626', '\u064A')
        # Indic digits
        text = text.translate(SARFTokenizer._INDIC_DIGITS)
        return text

    def __init__(
        self,
        tokenizer=None,
        preprocessor: Optional[SARFPreprocessor] = None,
        vocab_size: Optional[int] = None,
        *,
        native_core: Optional["SARFTokenizerCore"] = None,
    ):
        """
        Initialize SARFTokenizer.

        Args:
            tokenizer: HuggingFace tokenizer instance (for HF mode)
            preprocessor: Optional SARF preprocessor for morpheme-aware tokenization
            vocab_size: Vocabulary size (auto-detected if not provided)
            native_core: Native SARFTokenizerCore instance (for native mode)
        """
        self._tokenizer = tokenizer
        self._preprocessor = preprocessor
        self._vocab_size = vocab_size
        self._native_core = native_core

        # Determine mode
        self._use_native = native_core is not None

        # Cache special token IDs
        self._special_tokens_cache: Dict[str, int] = {}

    @classmethod
    def from_native(
        cls,
        morpheme_map_path: Optional[str] = None,
        bpe_data_path: Optional[str] = None,
    ) -> "SARFTokenizer":
        """
        Create a tokenizer using the native Rust core.

        This is the recommended way to create a tokenizer when you don't need
        HuggingFace integration. It's faster and doesn't require network access.

        Args:
            morpheme_map_path: Optional path to encrypted morpheme map
            bpe_data_path: Optional path to encrypted BPE data

        Returns:
            SARFTokenizer instance using native core

        Example:
            >>> tokenizer = SARFTokenizer.from_native()
        """
        try:
            from deeplatent._core import SARFTokenizerCore
        except ImportError as e:
            raise ImportError(
                "Native core not available. Please install deeplatent-nlp with "
                "a compatible wheel for your platform, or build from source."
            ) from e

        # Load encrypted data files if provided
        if morpheme_map_path and bpe_data_path:
            with open(morpheme_map_path, "rb") as f:
                morpheme_data = f.read()
            with open(bpe_data_path, "rb") as f:
                bpe_data = f.read()
            native_core = SARFTokenizerCore.from_encrypted(morpheme_data, bpe_data)
        else:
            # Try to load bundled data
            data_dir = os.path.join(os.path.dirname(__file__), "..", "native", "data")
            morpheme_path = os.path.join(data_dir, "morpheme_map.bin.enc")
            bpe_path = os.path.join(data_dir, "bpe.bin.enc")

            if os.path.exists(morpheme_path) and os.path.exists(bpe_path):
                with open(morpheme_path, "rb") as f:
                    morpheme_data = f.read()
                with open(bpe_path, "rb") as f:
                    bpe_data = f.read()
                native_core = SARFTokenizerCore.from_encrypted(morpheme_data, bpe_data)
            else:
                raise FileNotFoundError(
                    "Encrypted tokenizer data not found. Please run "
                    "scripts/prepare_tokenizer_data.py first or use from_pretrained()."
                )

        return cls(native_core=native_core, vocab_size=native_core.vocab_size)

    @classmethod
    def from_pretrained(
        cls,
        repo_id: str = "almaghrabima/deeplatent-tokenizer",
        use_preprocessing: bool = True,
        **kwargs
    ) -> "SARFTokenizer":
        """
        Load tokenizer from HuggingFace Hub.

        This requires the `transformers` package to be installed.
        For a dependency-free option, use `SARFTokenizer.from_native()` instead.

        Args:
            repo_id: HuggingFace repository ID
            use_preprocessing: Whether to apply SARF preprocessing (default: True)
            **kwargs: Additional arguments passed to AutoTokenizer.from_pretrained

        Returns:
            SARFTokenizer instance

        Example:
            >>> tokenizer = SARFTokenizer.from_pretrained("almaghrabima/deeplatent-tokenizer")
        """
        try:
            from transformers import AutoTokenizer
        except ImportError as e:
            raise ImportError(
                "transformers package not installed. Install with "
                "`pip install deeplatent-nlp[hf]` or use SARFTokenizer.from_native() instead."
            ) from e

        # Load HuggingFace tokenizer
        hf_tokenizer = AutoTokenizer.from_pretrained(repo_id, **kwargs)

        # Load SARF preprocessor if requested
        preprocessor = None
        if use_preprocessing:
            try:
                # Use bundled morpheme_map.json (included in package)
                preprocessor = SARFPreprocessor.from_bundled()
            except Exception as e:
                import warnings
                warnings.warn(f"Could not load SARF preprocessor: {e}. Continuing without preprocessing.")

        return cls(
            tokenizer=hf_tokenizer,
            preprocessor=preprocessor,
            vocab_size=hf_tokenizer.vocab_size,
        )

    @classmethod
    def from_directory(
        cls,
        directory: str,
        use_preprocessing: bool = True,
    ) -> "SARFTokenizer":
        """
        Load tokenizer from a local directory.

        Args:
            directory: Path to directory containing tokenizer files
            use_preprocessing: Whether to apply SARF preprocessing (default: True)

        Returns:
            SARFTokenizer instance
        """
        from transformers import AutoTokenizer

        # Load HuggingFace tokenizer
        hf_tokenizer = AutoTokenizer.from_pretrained(directory)

        # Load SARF preprocessor if available
        preprocessor = None
        if use_preprocessing:
            morpheme_map_path = os.path.join(directory, "morpheme_map.json")
            if os.path.exists(morpheme_map_path):
                preprocessor = SARFPreprocessor.from_file(morpheme_map_path)

        return cls(
            tokenizer=hf_tokenizer,
            preprocessor=preprocessor,
            vocab_size=hf_tokenizer.vocab_size,
        )

    @property
    def vocab_size(self) -> int:
        """Return the vocabulary size."""
        if self._vocab_size is not None:
            return self._vocab_size
        if self._use_native:
            return self._native_core.vocab_size
        return self._tokenizer.vocab_size

    @property
    def preprocessing_enabled(self) -> bool:
        """Return whether SARF preprocessing is enabled."""
        if self._use_native:
            return True  # Native core always has preprocessing built-in
        return self._preprocessor is not None

    @property
    def using_native(self) -> bool:
        """Return whether using native Rust core."""
        return self._use_native

    def _detect_language(self, text: str) -> str:
        """
        Detect if text is primarily Arabic or English.

        Args:
            text: Input text

        Returns:
            'ar' for Arabic, 'en' for English
        """
        arabic_chars = len(self.ARABIC_PATTERN.findall(text))
        total_chars = len([c for c in text if c.isalpha()])

        if total_chars == 0:
            return 'en'

        return 'ar' if arabic_chars / total_chars > 0.3 else 'en'

    def _preprocess(self, text: str, language: Optional[str] = None) -> str:
        """
        Apply Arabic normalization and SARF preprocessing if enabled.

        Args:
            text: Input text
            language: Optional language hint

        Returns:
            Preprocessed text
        """
        # Always normalize Arabic text to match training pipeline
        text = self._normalize_arabic(text)

        if self._preprocessor is None:
            return text

        # Auto-detect language if not provided
        if language is None:
            language = self._detect_language(text)

        return self._preprocessor.preprocess(text, language=language)

    def encode(
        self,
        text: Union[str, List[str]],
        pair: Optional[Union[str, List[str]]] = None,
        add_special_tokens: bool = True,
        padding: bool = False,
        truncation: bool = False,
        max_length: Optional[int] = None,
        return_tensors: Optional[str] = None,
        language: Optional[str] = None,
        **kwargs
    ) -> Union[List[int], Encoding, Dict]:
        """
        Encode text to token IDs.

        This method automatically applies SARF preprocessing for Arabic text.

        Args:
            text: Text or list of texts to encode
            pair: Optional second sequence for sequence-pair tasks
            add_special_tokens: Whether to add special tokens (default: True)
            padding: Whether to pad sequences (default: False)
            truncation: Whether to truncate sequences (default: False)
            max_length: Maximum sequence length for truncation/padding
            return_tensors: Return type ('pt' for PyTorch, 'tf' for TensorFlow, None for list)
            language: Optional language hint ('ar' or 'en') for preprocessing
            **kwargs: Additional arguments passed to underlying tokenizer

        Returns:
            Token IDs as list, Encoding object, or tensor dict depending on arguments

        Example:
            >>> ids = tokenizer.encode("مرحبا بكم")
            >>> print(ids)
            [1234, 5678, ...]
        """
        # Native mode - simple and fast
        if self._use_native:
            if isinstance(text, str):
                return list(self._native_core.encode(text))
            else:
                return [list(ids) for ids in self._native_core.encode_batch(text)]

        # HuggingFace mode
        # Handle single string
        if isinstance(text, str):
            preprocessed = self._preprocess(text, language)

            # Simple encoding without padding/truncation
            if not padding and not truncation and return_tensors is None:
                return self._tokenizer.encode(
                    preprocessed,
                    add_special_tokens=add_special_tokens,
                )

            # Full encoding with options
            return self._tokenizer(
                preprocessed,
                text_pair=self._preprocess(pair, language) if pair else None,
                add_special_tokens=add_special_tokens,
                padding=padding,
                truncation=truncation,
                max_length=max_length,
                return_tensors=return_tensors,
                **kwargs
            )

        # Handle batch of strings
        preprocessed_texts = [self._preprocess(t, language) for t in text]
        preprocessed_pairs = None
        if pair is not None:
            preprocessed_pairs = [self._preprocess(p, language) for p in pair]

        return self._tokenizer(
            preprocessed_texts,
            text_pair=preprocessed_pairs,
            add_special_tokens=add_special_tokens,
            padding=padding,
            truncation=truncation,
            max_length=max_length,
            return_tensors=return_tensors,
            **kwargs
        )

    def encode_batch(
        self,
        texts: List[str],
        add_special_tokens: bool = True,
        language: Optional[str] = None,
    ) -> List[List[int]]:
        """
        Encode a batch of texts to token IDs.

        Args:
            texts: List of texts to encode
            add_special_tokens: Whether to add special tokens
            language: Optional language hint

        Returns:
            List of token ID lists
        """
        if self._use_native:
            return [list(ids) for ids in self._native_core.encode_batch(texts)]
        return [
            self.encode(text, add_special_tokens=add_special_tokens, language=language)
            for text in texts
        ]

    def decode(
        self,
        ids: Union[List[int], List[List[int]]],
        skip_special_tokens: bool = True,
        clean_up_tokenization_spaces: bool = True,
        **kwargs
    ) -> Union[str, List[str]]:
        """
        Decode token IDs back to text.

        Args:
            ids: Token IDs or batch of token IDs to decode
            skip_special_tokens: Whether to skip special tokens (default: True)
            clean_up_tokenization_spaces: Whether to clean up spaces (default: True)
            **kwargs: Additional arguments passed to underlying tokenizer

        Returns:
            Decoded text or list of decoded texts

        Example:
            >>> text = tokenizer.decode([1234, 5678])
            >>> print(text)
            "مرحبا بكم"
        """
        # Native mode
        if self._use_native:
            # Handle batch decoding
            if ids and isinstance(ids[0], list):
                return self._native_core.decode_batch(ids)
            # Single sequence decoding
            return self._native_core.decode(list(ids))

        # HuggingFace mode
        # Handle batch decoding
        if ids and isinstance(ids[0], list):
            decoded_list = []
            for id_list in ids:
                decoded = self._tokenizer.decode(
                    id_list,
                    skip_special_tokens=skip_special_tokens,
                    clean_up_tokenization_spaces=clean_up_tokenization_spaces,
                    **kwargs
                )
                if self._preprocessor is not None:
                    decoded = self._preprocessor.postprocess(decoded)
                decoded_list.append(decoded)
            return decoded_list

        # Single sequence decoding
        decoded = self._tokenizer.decode(
            ids,
            skip_special_tokens=skip_special_tokens,
            clean_up_tokenization_spaces=clean_up_tokenization_spaces,
            **kwargs
        )

        # Apply reverse preprocessing if available
        if self._preprocessor is not None:
            decoded = self._preprocessor.postprocess(decoded)

        return decoded

    def decode_batch(
        self,
        batch_ids: List[List[int]],
        skip_special_tokens: bool = True,
    ) -> List[str]:
        """
        Decode a batch of token ID sequences.

        Args:
            batch_ids: List of token ID lists
            skip_special_tokens: Whether to skip special tokens

        Returns:
            List of decoded texts
        """
        if self._use_native:
            return self._native_core.decode_batch(batch_ids)
        return [self.decode(ids, skip_special_tokens=skip_special_tokens) for ids in batch_ids]

    def tokenize(
        self,
        text: str,
        language: Optional[str] = None,
    ) -> List[str]:
        """
        Tokenize text and return tokens as strings.

        Args:
            text: Text to tokenize
            language: Optional language hint

        Returns:
            List of token strings

        Note:
            In native mode, this returns token strings based on decoded individual tokens.
        """
        if self._use_native:
            # Native mode: encode then convert each ID to its token string
            ids = self._native_core.encode(text)
            return [self._native_core.id_to_token(id) or f"[{id}]" for id in ids]

        preprocessed = self._preprocess(text, language)
        return self._tokenizer.tokenize(preprocessed)

    def convert_tokens_to_ids(self, tokens: Union[str, List[str]]) -> Union[int, List[int]]:
        """
        Convert tokens to IDs.

        Args:
            tokens: Token or list of tokens

        Returns:
            Token ID or list of token IDs
        """
        if self._use_native:
            if isinstance(tokens, str):
                return self._native_core.token_to_id(tokens)
            return [self._native_core.token_to_id(t) for t in tokens]
        return self._tokenizer.convert_tokens_to_ids(tokens)

    def convert_ids_to_tokens(self, ids: Union[int, List[int]]) -> Union[str, List[str]]:
        """
        Convert IDs to tokens.

        Args:
            ids: Token ID or list of token IDs

        Returns:
            Token or list of tokens
        """
        if self._use_native:
            if isinstance(ids, int):
                return self._native_core.id_to_token(ids)
            return [self._native_core.id_to_token(id) for id in ids]
        return self._tokenizer.convert_ids_to_tokens(ids)

    def get_vocab(self, with_added_tokens: bool = True) -> Dict[str, int]:
        """
        Get the vocabulary.

        Args:
            with_added_tokens: Whether to include added tokens

        Returns:
            Dictionary mapping tokens to IDs

        Note:
            In native mode, this is not fully supported and returns an empty dict.
        """
        if self._use_native:
            # Native mode doesn't expose full vocab - return empty dict
            # This is a limitation of the native mode to protect IP
            return {}
        return self._tokenizer.get_vocab()

    def token_to_id(self, token: str) -> Optional[int]:
        """
        Convert a single token to its ID.

        Args:
            token: Token string

        Returns:
            Token ID or None if not found
        """
        if self._use_native:
            return self._native_core.token_to_id(token)
        vocab = self.get_vocab()
        return vocab.get(token)

    def id_to_token(self, id: int) -> Optional[str]:
        """
        Convert a single ID to its token.

        Args:
            id: Token ID

        Returns:
            Token string or None if not found
        """
        if self._use_native:
            return self._native_core.id_to_token(id)
        return self._tokenizer.convert_ids_to_tokens(id)

    def add_special_tokens(self, special_tokens: Dict[str, str]) -> int:
        """
        Add special tokens to the tokenizer.

        Args:
            special_tokens: Dictionary of special token names to values

        Returns:
            Number of tokens added

        Note:
            Not supported in native mode.
        """
        if self._use_native:
            raise NotImplementedError(
                "add_special_tokens is not supported in native mode. "
                "Use from_pretrained() for a mutable tokenizer."
            )
        return self._tokenizer.add_special_tokens(special_tokens)

    def add_tokens(self, new_tokens: List[str]) -> int:
        """
        Add new tokens to the vocabulary.

        Args:
            new_tokens: List of new tokens to add

        Returns:
            Number of tokens added

        Note:
            Not supported in native mode.
        """
        if self._use_native:
            raise NotImplementedError(
                "add_tokens is not supported in native mode. "
                "Use from_pretrained() for a mutable tokenizer."
            )
        return self._tokenizer.add_tokens(new_tokens)

    def save_pretrained(self, save_directory: str) -> None:
        """
        Save tokenizer to directory.

        Args:
            save_directory: Directory to save tokenizer files

        Note:
            Not fully supported in native mode.
        """
        import json

        os.makedirs(save_directory, exist_ok=True)

        if self._use_native:
            # Native mode: can only save stats
            stats = self._native_core.get_stats()
            stats_path = os.path.join(save_directory, "tokenizer_stats.json")
            with open(stats_path, "w", encoding="utf-8") as f:
                json.dump(stats, f, indent=2)
            return

        # Save HuggingFace tokenizer
        self._tokenizer.save_pretrained(save_directory)

        # Save morpheme map if preprocessor exists
        if self._preprocessor is not None:
            morpheme_map_path = os.path.join(save_directory, "morpheme_map.json")
            with open(morpheme_map_path, 'w', encoding='utf-8') as f:
                json.dump(self._preprocessor.rewriter.rules, f, ensure_ascii=False, indent=2)

    def __call__(
        self,
        text: Union[str, List[str]],
        **kwargs
    ):
        """
        Tokenize text (callable interface).

        This provides compatibility with HuggingFace tokenizer interface.

        Args:
            text: Text or list of texts to tokenize
            **kwargs: Additional arguments passed to encode

        Returns:
            Tokenization result
        """
        return self.encode(text, **kwargs)

    def __repr__(self) -> str:
        mode = "native" if self._use_native else "huggingface"
        return (
            f"SARFTokenizer("
            f"vocab_size={self.vocab_size}, "
            f"mode={mode}, "
            f"preprocessing={'enabled' if self.preprocessing_enabled else 'disabled'}"
            f")"
        )


# Alias for compatibility
AutoTokenizer = SARFTokenizer
