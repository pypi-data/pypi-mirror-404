# DeepLatent

**DeepLatent** - SARF Tokenizer for Arabic/English bilingual text with native Rust core.

This package provides the SARF (Sarf-Aware Representation Framework) tokenizer that achieves excellent Arabic/English parity (1.09) by applying morpheme-level preprocessing before BPE tokenization.

## Installation

```bash
pip install deeplatent-nlp
```

### Building from Source

If installing from source, you'll need Rust installed:

```bash
# Install Rust (if not already installed)
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh

# Install from source
pip install .
```

## Quick Start

```python
from deeplatent import SARFTokenizer

# Native mode (default, fast, no network required)
tokenizer = SARFTokenizer.from_native()

# Encode text (Arabic normalization + SARF preprocessing applied automatically)
arabic_text = "مرحبا بكم في هذا الاختبار"
tokens = tokenizer.encode(arabic_text)
print(f"Token count: {len(tokens)}")

# Decode back to text
decoded = tokenizer.decode(tokens)
print(f"Decoded: {decoded}")

# Works with English too
english_text = "Hello world, this is a test"
tokens = tokenizer.encode(english_text)
print(f"English token count: {len(tokens)}")
```

### HuggingFace Mode

```python
from deeplatent import SARFTokenizer

# Load from HuggingFace (requires `pip install deeplatent-nlp[hf]`)
tokenizer = SARFTokenizer.from_pretrained("almaghrabima/deeplatent-tokenizer")
```

## Roundtrip Guarantee

As of v0.3.1, the SARF tokenizer provides an exact roundtrip guarantee:

```
decode(encode(text)) == normalize(text)
```

The encoder applies Arabic text normalization (the same normalization used during BPE training) before tokenization. This means character variants like أ/إ/آ are unified to ا, diacritics are stripped, and Indic digits are converted to ASCII. The roundtrip returns the **normalized** form of the input.

```python
from deeplatent import SARFTokenizer

tokenizer = SARFTokenizer.from_native()

# English roundtrips exactly
text = "Hello world"
assert tokenizer.decode(tokenizer.encode(text)) == text

# Arabic roundtrips to normalized form
text = "أحمد"          # أ = alef with hamza above
decoded = tokenizer.decode(tokenizer.encode(text))
assert decoded == "احمد"  # ا = plain alef (normalized)

# Character variants produce identical token IDs
assert tokenizer.encode("أحمد") == tokenizer.encode("احمد")

# Diacritics are stripped
assert tokenizer.encode("كَتَبَ") == tokenizer.encode("كتب")

# Indic digits map to ASCII
assert tokenizer.encode("١٢٣") == tokenizer.encode("123")
```

### What Gets Normalized

| Input | Output | Rule |
|-------|--------|------|
| أ إ آ ٱ | ا | Alef unification |
| ى | ي | Ya normalization |
| ؤ | و | Hamza-on-waw |
| ئ | ي | Hamza-on-ya |
| كَتَبَ | كتب | Diacritic removal |
| ـعربيـ | عربي | Tatweel removal |
| ١٢٣ | 123 | Indic digit conversion |
| Zero-width chars | *(removed)* | ZWJ/ZWNJ/BOM cleanup |

This normalization matches standard Arabic NLP practice and is the same as GPT-family tokenizers that normalize Unicode on input.

## Performance

| Metric | With SARF Preprocessing | Without Preprocessing |
|--------|------------------------|----------------------|
| Arabic Fertility | 2.29 | 5.65 |
| English Fertility | 2.10 | 2.91 |
| Parity (Ar/En) | **1.09** | 1.94 |
| Interpretation | **EXCELLENT** | Moderate |

*Fertility = average tokens per word. Lower is better. Parity closer to 1.0 means more equal treatment between languages.*

### Supported Platforms

Pre-built wheels are available for:
- Linux (manylinux2014, x86_64)
- macOS (x86_64, arm64)
- Windows (x86_64)

For other platforms, the package will build from source (requires Rust).

## What is SARF?

**SARF (صَرْف)** is the Arabic term for **morphology**. In Arabic linguistics, *ṣarf* refers to the system that governs:

- Word formation
- Roots and patterns (جذر / وزن)
- Prefixes, suffixes, infixes
- Tense, gender, number, and derivation

Most tokenizers treat Arabic as bytes or characters. **SARF treats Arabic as a language.**

## API Reference

### SARFTokenizer

```python
from deeplatent import SARFTokenizer

# Native mode (recommended, fast, no network)
tokenizer = SARFTokenizer.from_native()

# Load from HuggingFace
tokenizer = SARFTokenizer.from_pretrained("almaghrabima/deeplatent-tokenizer")

# Load from local directory
tokenizer = SARFTokenizer.from_directory("./my_tokenizer")

# Disable preprocessing (not recommended for Arabic)
tokenizer = SARFTokenizer.from_pretrained(
    "almaghrabima/deeplatent-tokenizer",
    use_preprocessing=False
)
```

### Encoding

```python
# Simple encoding
tokens = tokenizer.encode("مرحبا بكم")

# With options (HuggingFace mode only)
result = tokenizer.encode(
    "مرحبا بكم",
    add_special_tokens=True,
    padding=True,
    truncation=True,
    max_length=512,
    return_tensors="pt"  # or "tf" for TensorFlow
)

# Batch encoding
texts = ["مرحبا", "Hello", "مرحبا بكم في العالم"]
batch_tokens = tokenizer.encode_batch(texts)
```

### Decoding

```python
# Simple decoding
text = tokenizer.decode([1234, 5678, 9012])

# Batch decoding
texts = tokenizer.decode_batch([[1234, 5678], [9012, 3456]])

# Keep special tokens
text = tokenizer.decode(tokens, skip_special_tokens=False)
```

### Normalization (Rust Core)

```python
# Access the normalization function directly
from deeplatent._core import normalize_arabic_text

normalized = normalize_arabic_text("أحمد")  # returns "احمد"
```

## License

This tokenizer is released under **CC-BY-NC-4.0** (Creative Commons Attribution-NonCommercial 4.0 International).

For commercial licensing, please contact: almaghrabima@gmail.com

## Author

- **Mohammed Almaghrabi**
- Email: almaghrabima@gmail.com

## Links

- [HuggingFace Model](https://huggingface.co/almaghrabima/deeplatent-tokenizer)
- [Evaluation Dataset](https://huggingface.co/datasets/almaghrabima/eval-test-data)
