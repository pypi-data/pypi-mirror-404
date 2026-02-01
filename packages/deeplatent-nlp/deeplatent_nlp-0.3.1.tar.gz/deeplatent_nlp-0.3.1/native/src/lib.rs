//! DeepLatent SARF Core - Native implementation of MYTE tokenization
//!
//! This module provides the complete MYTE (Morphologically-Yielding Tokenizer Encoding)
//! pipeline including:
//! - Byte-level morpheme rewriting (trie-based)
//! - BPE encoding and decoding
//! - Obfuscated data loading
//!
//! The tokenizer can operate in two modes:
//! 1. Standalone: Using embedded obfuscated data (no network required)
//! 2. External: Loading data from external files

use pyo3::prelude::*;
use pyo3::exceptions::PyValueError;
use std::collections::HashMap;

mod bpe;
mod obfuscation;

/// Normalize Arabic text to match the training pipeline normalization.
///
/// This implements the same logic as `prepare_corpus_lexicon.py:normalize_arabic_text(level='medium')`.
fn normalize_arabic(text: &str) -> String {
    let mut result = String::with_capacity(text.len());
    for ch in text.chars() {
        match ch {
            // Remove diacritics (tashkeel): U+064B-U+0652, U+0670
            '\u{064B}'..='\u{0652}' | '\u{0670}' => continue,
            // Remove tatweel
            '\u{0640}' => continue,
            // Remove zero-width characters
            '\u{200B}'..='\u{200D}' | '\u{FEFF}' |
            '\u{202A}'..='\u{202E}' | '\u{2066}'..='\u{2069}' => continue,
            // Alef unification: أ إ آ ٱ -> ا
            '\u{0623}' | '\u{0625}' | '\u{0622}' | '\u{0671}' => result.push('\u{0627}'),
            // Ya normalization: ى -> ي
            '\u{0649}' => result.push('\u{064A}'),
            // Hamza normalization (medium level): ؤ -> و, ئ -> ي
            '\u{0624}' => result.push('\u{0648}'),
            '\u{0626}' => result.push('\u{064A}'),
            // Indic digit normalization
            '\u{0660}' => result.push('0'),
            '\u{0661}' => result.push('1'),
            '\u{0662}' => result.push('2'),
            '\u{0663}' => result.push('3'),
            '\u{0664}' => result.push('4'),
            '\u{0665}' => result.push('5'),
            '\u{0666}' => result.push('6'),
            '\u{0667}' => result.push('7'),
            '\u{0668}' => result.push('8'),
            '\u{0669}' => result.push('9'),
            // Pass through everything else
            other => result.push(other),
        }
    }
    result
}

/// A node in the trie (hash tree) structure for efficient prefix matching
#[derive(Default, Clone)]
struct TrieNode {
    children: HashMap<u8, TrieNode>,
    value: Option<Vec<u8>>,
}

impl TrieNode {
    fn new() -> Self {
        TrieNode {
            children: HashMap::new(),
            value: None,
        }
    }

    fn insert(&mut self, key: &[u8], value: Vec<u8>) {
        let mut current = self;
        for &byte in key {
            current = current.children.entry(byte).or_insert_with(TrieNode::new);
        }
        current.value = Some(value);
    }
}

/// Core byte-level rewriter using a trie structure for morpheme matching.
///
/// This class builds a prefix tree from morpheme mappings and uses it to
/// efficiently find and replace morpheme sequences in byte streams.
#[pyclass]
pub struct ByteRewriterCore {
    forward_tree: TrieNode,
    reverse_tree: TrieNode,
    num_rules: usize,
}

#[pymethods]
impl ByteRewriterCore {
    /// Create a new ByteRewriterCore from a dictionary of rewriting rules.
    ///
    /// Args:
    ///     rules: Dictionary mapping source strings to target strings
    #[new]
    fn new(rules: HashMap<String, String>) -> PyResult<Self> {
        let mut forward_tree = TrieNode::new();
        let mut reverse_tree = TrieNode::new();
        let num_rules = rules.len();

        // Group rules by target to find canonical (shortest) source for each target
        let mut target_to_sources: HashMap<String, Vec<String>> = HashMap::new();
        for (source, target) in rules.iter() {
            target_to_sources
                .entry(target.clone())
                .or_insert_with(Vec::new)
                .push(source.clone());
        }

        // For each target, sort sources so the canonical form is processed last
        // Canonical form = shortest length, then highest Unicode code points (plain alef comes last)
        let mut sorted_rules: Vec<(String, String)> = Vec::with_capacity(rules.len());
        for (target, mut sources) in target_to_sources {
            // Sort by: 1) length descending, 2) string value ascending
            // This puts longest first, and for same length, lower code points first
            // Plain Arabic letters (like ا U+0627) have higher code points than variants (آ U+0622)
            sources.sort_by(|a, b| {
                match b.len().cmp(&a.len()) {
                    std::cmp::Ordering::Equal => a.cmp(b),
                    other => other,
                }
            });
            for source in sources {
                sorted_rules.push((source, target.clone()));
            }
        }

        for (source, target) in sorted_rules.iter() {
            let source_bytes = source.as_bytes().to_vec();
            let target_bytes = target.as_bytes().to_vec();

            // Build forward tree
            forward_tree.insert(&source_bytes, target_bytes.clone());

            // Build reverse tree - shortest source will be last, becoming the canonical form
            reverse_tree.insert(&target_bytes, source_bytes);
        }

        Ok(ByteRewriterCore {
            forward_tree,
            reverse_tree,
            num_rules,
        })
    }

    /// Rewrite text by applying byte-level morpheme replacements.
    ///
    /// This method efficiently processes text using the trie-based matcher
    /// for longest-prefix matching.
    ///
    /// Args:
    ///     text: Input text to preprocess
    ///     reverse: If True, use reverse mapping (for decoding)
    ///
    /// Returns:
    ///     Preprocessed text with morpheme replacements applied
    fn rewrite_text(&self, text: &str, reverse: bool) -> PyResult<String> {
        if text.is_empty() {
            return Ok(String::new());
        }

        let input_bytes = text.as_bytes();
        let tree = if reverse { &self.reverse_tree } else { &self.forward_tree };

        let mut result: Vec<u8> = Vec::with_capacity(input_bytes.len());
        let mut i = 0;

        while i < input_bytes.len() {
            // Try to match longest prefix in tree
            let mut current = tree;
            let mut match_length = 0;
            let mut match_value: Option<&Vec<u8>> = None;

            let mut j = i;
            while j < input_bytes.len() {
                if let Some(child) = current.children.get(&input_bytes[j]) {
                    current = child;
                    j += 1;

                    // Check if this is a complete match
                    if current.value.is_some() {
                        match_length = j - i;
                        match_value = current.value.as_ref();
                    }
                } else {
                    break;
                }
            }

            if let Some(value) = match_value {
                // Found a match - replace with target sequence
                result.extend_from_slice(value);
                i += match_length;
            } else {
                // No match - keep original byte
                result.push(input_bytes[i]);
                i += 1;
            }
        }

        // Convert result bytes back to string
        String::from_utf8(result)
            .map_err(|e| PyValueError::new_err(format!("Invalid UTF-8 in result: {}", e)))
    }

    /// Get the number of rules in this rewriter.
    fn get_num_rules(&self) -> usize {
        self.num_rules
    }

    /// Get statistics about the rewriter.
    fn get_stats(&self) -> HashMap<String, usize> {
        let mut stats = HashMap::new();
        stats.insert("num_rules".to_string(), self.num_rules);
        stats.insert("num_reverse_rules".to_string(), self.num_rules);
        stats
    }
}

/// Unified SARF Tokenizer Core that combines morpheme rewriting with BPE encoding.
///
/// This class provides the complete tokenization pipeline:
/// 1. Text -> Morpheme rewriting (Arabic morphemes to PUA characters)
/// 2. Rewritten text -> BPE encoding -> Token IDs
/// 3. Token IDs -> BPE decoding -> Rewritten text
/// 4. Rewritten text -> Reverse morpheme rewriting -> Original text
#[pyclass]
pub struct SARFTokenizerCore {
    rewriter: ByteRewriterCore,
    bpe: bpe::BPEEncoder,
}

#[pymethods]
impl SARFTokenizerCore {
    /// Create a new SARFTokenizerCore from morpheme rules and BPE data.
    ///
    /// Args:
    ///     morpheme_rules: Dictionary mapping morphemes to PUA characters
    ///     bpe_merges: List of ((left, right), merged_id) tuples
    ///     bpe_vocab: List of (bytes, token_id) tuples
    ///     special_tokens: Dictionary of special token strings to IDs
    ///     pattern: Optional regex pattern for pre-tokenization
    #[new]
    #[pyo3(signature = (morpheme_rules, bpe_merges, bpe_vocab, special_tokens, pattern=None))]
    fn new(
        morpheme_rules: HashMap<String, String>,
        bpe_merges: Vec<((u32, u32), u32)>,
        bpe_vocab: Vec<(Vec<u8>, u32)>,
        special_tokens: HashMap<String, u32>,
        pattern: Option<String>,
    ) -> PyResult<Self> {
        let rewriter = ByteRewriterCore::new(morpheme_rules)?;
        let bpe = bpe::BPEEncoder::new(bpe_merges, bpe_vocab, special_tokens, pattern)
            .map_err(|e| PyValueError::new_err(e))?;

        Ok(SARFTokenizerCore { rewriter, bpe })
    }

    /// Create from encrypted data files.
    ///
    /// Args:
    ///     morpheme_data: Encrypted morpheme map bytes
    ///     bpe_data: Encrypted BPE data bytes
    #[staticmethod]
    fn from_encrypted(morpheme_data: &[u8], bpe_data: &[u8]) -> PyResult<Self> {
        let morpheme_rules = obfuscation::load_morpheme_map(morpheme_data)
            .map_err(|e| PyValueError::new_err(e))?;

        let bpe_data = obfuscation::load_bpe_data(bpe_data)
            .map_err(|e| PyValueError::new_err(e))?;

        let rewriter = ByteRewriterCore::new(morpheme_rules)?;
        let bpe = bpe_data.into_encoder()
            .map_err(|e| PyValueError::new_err(e))?;

        Ok(SARFTokenizerCore { rewriter, bpe })
    }

    /// Encode text to token IDs.
    ///
    /// This performs:
    /// 1. Morpheme rewriting (forward)
    /// 2. BPE encoding
    ///
    /// Args:
    ///     text: Input text to encode
    ///
    /// Returns:
    ///     List of token IDs
    fn encode(&self, text: &str) -> PyResult<Vec<u32>> {
        if text.is_empty() {
            return Ok(Vec::new());
        }

        // Step 1: Normalize Arabic text (matches training pipeline)
        let normalized = normalize_arabic(text);

        // Step 2: Apply morpheme rewriting
        let rewritten = self.rewriter.rewrite_text(&normalized, false)?;

        // Step 3: BPE encode
        Ok(self.bpe.encode(&rewritten))
    }

    /// Decode token IDs back to text.
    ///
    /// This performs:
    /// 1. BPE decoding
    /// 2. Morpheme rewriting (reverse)
    ///
    /// Args:
    ///     ids: List of token IDs
    ///
    /// Returns:
    ///     Decoded text
    fn decode(&self, ids: Vec<u32>) -> PyResult<String> {
        if ids.is_empty() {
            return Ok(String::new());
        }

        // Step 1: BPE decode
        let bpe_decoded = self.bpe.decode(&ids)
            .map_err(|e| PyValueError::new_err(e))?;

        // Step 2: Reverse morpheme rewriting
        self.rewriter.rewrite_text(&bpe_decoded, true)
    }

    /// Encode multiple texts to token IDs.
    ///
    /// Args:
    ///     texts: List of input texts
    ///
    /// Returns:
    ///     List of token ID lists
    fn encode_batch(&self, texts: Vec<String>) -> PyResult<Vec<Vec<u32>>> {
        texts
            .iter()
            .map(|text| self.encode(text))
            .collect()
    }

    /// Decode multiple token ID sequences back to text.
    ///
    /// Args:
    ///     ids_batch: List of token ID lists
    ///
    /// Returns:
    ///     List of decoded texts
    fn decode_batch(&self, ids_batch: Vec<Vec<u32>>) -> PyResult<Vec<String>> {
        ids_batch
            .into_iter()
            .map(|ids| self.decode(ids))
            .collect()
    }

    /// Get vocabulary size.
    #[getter]
    fn vocab_size(&self) -> usize {
        self.bpe.vocab_size()
    }

    /// Get number of morpheme rules.
    #[getter]
    fn num_morpheme_rules(&self) -> usize {
        self.rewriter.num_rules
    }

    /// Convert a token string to its ID.
    fn token_to_id(&self, token: &str) -> Option<u32> {
        self.bpe.token_to_id(token)
    }

    /// Convert a token ID to its string representation.
    fn id_to_token(&self, id: u32) -> Option<String> {
        self.bpe.id_to_token(id)
    }

    /// Get statistics about the tokenizer.
    fn get_stats(&self) -> HashMap<String, usize> {
        let mut stats = HashMap::new();
        stats.insert("vocab_size".to_string(), self.bpe.vocab_size());
        stats.insert("num_morpheme_rules".to_string(), self.rewriter.num_rules);
        stats
    }
}

/// Check if the native core is available and working.
#[pyfunction]
fn is_available() -> bool {
    true
}

/// Get the version of the native core.
#[pyfunction]
fn version() -> &'static str {
    env!("CARGO_PKG_VERSION")
}

/// Encrypt data for embedding (used by build scripts).
///
/// Args:
///     data: Raw bytes to encrypt
///
/// Returns:
///     Encrypted bytes (zstd compressed + XOR encrypted)
#[pyfunction]
fn encrypt_data<'py>(py: pyo3::Python<'py>, data: &[u8]) -> PyResult<pyo3::Bound<'py, pyo3::types::PyBytes>> {
    let encrypted = obfuscation::encrypt_data(data)
        .map_err(|e| PyValueError::new_err(e))?;
    Ok(pyo3::types::PyBytes::new_bound(py, &encrypted))
}

/// Normalize Arabic text (exposed to Python for consistency).
///
/// This applies the same normalization as the training pipeline:
/// diacritic removal, alef unification, hamza normalization, digit conversion.
#[pyfunction]
fn normalize_arabic_text(text: &str) -> String {
    normalize_arabic(text)
}

/// Python module definition
#[pymodule]
fn _core(m: &Bound<'_, PyModule>) -> PyResult<()> {
    m.add_class::<ByteRewriterCore>()?;
    m.add_class::<SARFTokenizerCore>()?;
    m.add_function(wrap_pyfunction!(is_available, m)?)?;
    m.add_function(wrap_pyfunction!(version, m)?)?;
    m.add_function(wrap_pyfunction!(encrypt_data, m)?)?;
    m.add_function(wrap_pyfunction!(normalize_arabic_text, m)?)?;
    Ok(())
}
