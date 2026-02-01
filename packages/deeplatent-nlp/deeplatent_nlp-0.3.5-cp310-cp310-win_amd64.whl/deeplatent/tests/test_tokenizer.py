"""Tests for DeepLatent SARF Tokenizer."""
import pytest
import sys
import os

# Add parent directory to path for testing
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from deeplatent import SARFTokenizer, SARFPreprocessor, ByteRewriter


class TestByteRewriter:
    """Tests for ByteRewriter class."""

    def test_basic_rewriting(self):
        """Test basic morpheme rewriting."""
        rules = {
            "ال": "\x01",  # Arabic definite article
            "و": "\x02",   # Arabic conjunction
        }
        rewriter = ByteRewriter(rules)

        # Test forward rewriting
        result = rewriter.rewrite_text("والمدرسة")
        assert "\x02" in result  # و should be replaced
        assert "\x01" in result  # ال should be replaced

    def test_reverse_rewriting(self):
        """Test reverse morpheme rewriting."""
        rules = {
            "ال": "\x01",
            "و": "\x02",
        }
        rewriter = ByteRewriter(rules)

        # Forward then reverse should give back original
        original = "والمدرسة"
        forward = rewriter.rewrite_text(original, reverse=False)
        back = rewriter.rewrite_text(forward, reverse=True)
        assert back == original

    def test_empty_text(self):
        """Test handling of empty text."""
        rewriter = ByteRewriter({})
        assert rewriter.rewrite_text("") == ""
        assert rewriter.rewrite_text(None) is None or rewriter.rewrite_text("") == ""

    def test_get_stats(self):
        """Test statistics reporting."""
        rules = {"a": "b", "c": "d"}
        rewriter = ByteRewriter(rules)
        stats = rewriter.get_stats()
        assert stats["num_rules"] == 2


class TestSARFPreprocessor:
    """Tests for SARFPreprocessor class."""

    def test_preprocessing_arabic(self):
        """Test Arabic text preprocessing."""
        rules = {"ال": "\x01"}
        preprocessor = SARFPreprocessor(rules)

        result = preprocessor.preprocess("المدرسة")
        assert result != "المدرسة"  # Should be modified

    def test_skip_english(self):
        """Test that English text is not modified when language hint is provided."""
        rules = {"the": "\x01"}
        preprocessor = SARFPreprocessor(rules)

        result = preprocessor.preprocess("the school", language="en")
        assert result == "the school"  # Should not be modified with language hint

    def test_postprocess(self):
        """Test reverse preprocessing."""
        rules = {"ال": "\x01"}
        preprocessor = SARFPreprocessor(rules)

        original = "المدرسة"
        preprocessed = preprocessor.preprocess(original)
        restored = preprocessor.postprocess(preprocessed)
        assert restored == original


class TestSARFTokenizerIntegration:
    """Integration tests for SARFTokenizer (requires HuggingFace model)."""

    @pytest.fixture(scope="class")
    def tokenizer(self):
        """Load tokenizer from HuggingFace."""
        try:
            return SARFTokenizer.from_pretrained("almaghrabima/deeplatent-tokenizer")
        except Exception as e:
            pytest.skip(f"Could not load tokenizer from HuggingFace: {e}")

    def test_encode_arabic(self, tokenizer):
        """Test encoding Arabic text."""
        text = "مرحبا بكم في هذا الاختبار"
        tokens = tokenizer.encode(text)
        assert isinstance(tokens, list)
        assert len(tokens) > 0
        assert all(isinstance(t, int) for t in tokens)

    def test_encode_english(self, tokenizer):
        """Test encoding English text."""
        text = "Hello world, this is a test"
        tokens = tokenizer.encode(text)
        assert isinstance(tokens, list)
        assert len(tokens) > 0

    def test_decode(self, tokenizer):
        """Test decoding tokens back to text."""
        text = "مرحبا"
        tokens = tokenizer.encode(text)
        decoded = tokenizer.decode(tokens)
        # Note: decoded might not be exactly equal due to preprocessing
        assert isinstance(decoded, str)
        assert len(decoded) > 0

    def test_batch_encode(self, tokenizer):
        """Test batch encoding."""
        texts = ["مرحبا", "Hello", "مرحبا بكم"]
        batch_tokens = tokenizer.encode_batch(texts)
        assert len(batch_tokens) == 3
        assert all(isinstance(t, list) for t in batch_tokens)

    def test_vocab_size(self, tokenizer):
        """Test vocabulary size."""
        assert tokenizer.vocab_size == 100000

    def test_preprocessing_enabled(self, tokenizer):
        """Test that preprocessing is enabled."""
        assert tokenizer.preprocessing_enabled

    def test_tokenizer_repr(self, tokenizer):
        """Test string representation."""
        repr_str = repr(tokenizer)
        assert "SARFTokenizer" in repr_str
        assert "vocab_size" in repr_str


class TestSARFTokenizerWithoutPreprocessing:
    """Tests for tokenizer without preprocessing."""

    @pytest.fixture(scope="class")
    def tokenizer(self):
        """Load tokenizer without preprocessing."""
        try:
            return SARFTokenizer.from_pretrained(
                "almaghrabima/deeplatent-tokenizer",
                use_preprocessing=False
            )
        except Exception as e:
            pytest.skip(f"Could not load tokenizer: {e}")

    def test_preprocessing_disabled(self, tokenizer):
        """Test that preprocessing is disabled."""
        assert not tokenizer.preprocessing_enabled


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
