//! BPE Encoder/Decoder for MYTE tokenization pipeline.
//!
//! This module provides a complete BPE implementation with both encoding (text -> token IDs)
//! and decoding (token IDs -> text) support. It uses the GPT-4 style regex pattern for
//! pre-tokenization and GPT-2 style byte-to-unicode mapping.

use ahash::AHashMap;
use fancy_regex::Regex;
use std::collections::HashMap;

/// Default GPT-4 style regex pattern for splitting text
pub const GPT4_PATTERN: &str = r"'(?i:[sdmt]|ll|ve|re)|[^\r\n\p{L}\p{N}]?+\p{L}+|\p{N}{1,3}| ?[^\s\p{L}\p{N}]++[\r\n]*|\s*[\r\n]|\s+(?!\S)|\s+";

type Pair = (u32, u32);

/// Build the GPT-2 bytes_to_unicode mapping.
/// Maps each byte (0-255) to a unicode character, avoiding control chars.
fn build_bytes_to_unicode() -> [char; 256] {
    let mut bs: Vec<u32> = Vec::new();
    // Printable ASCII range
    bs.extend(0x21u32..=0x7Eu32);
    // Latin-1 supplement (non-control)
    bs.extend(0xA1u32..=0xACu32);
    bs.extend(0xAEu32..=0xFFu32);

    let mut cs: Vec<u32> = bs.clone();

    let mut n: u32 = 0;
    for b in 0u32..256 {
        if !bs.contains(&b) {
            bs.push(b);
            cs.push(256 + n);
            n += 1;
        }
    }

    let mut mapping = ['\0'; 256];
    for (b, c) in bs.iter().zip(cs.iter()) {
        mapping[*b as usize] = char::from_u32(*c).unwrap_or('\0');
    }
    mapping
}

/// Build the reverse unicode_to_bytes mapping.
fn build_unicode_to_bytes(b2u: &[char; 256]) -> AHashMap<char, u8> {
    let mut map = AHashMap::with_capacity(256);
    for (byte_val, &unicode_char) in b2u.iter().enumerate() {
        map.insert(unicode_char, byte_val as u8);
    }
    map
}

/// BPE Encoder/Decoder with full encode and decode support.
///
/// Vocab is stored as GPT-2 unicode strings. Input text bytes are mapped
/// through bytes_to_unicode before BPE, matching HuggingFace's behavior.
pub struct BPEEncoder {
    /// Maps pairs of token IDs to their merged token ID
    merges: HashMap<Pair, u32>,
    /// Compiled regex for pre-tokenization
    pattern: Regex,
    /// Maps token ID to its GPT-2 unicode string
    token_to_str: Vec<String>,
    /// Maps GPT-2 unicode string to token ID
    str_to_token: AHashMap<String, u32>,
    /// Special tokens mapping
    special_tokens: HashMap<String, u32>,
    /// Reverse special tokens mapping
    special_tokens_reverse: HashMap<u32, String>,
    /// Vocabulary size
    vocab_size: usize,
    /// GPT-2 byte to unicode mapping (256 entries)
    byte_to_unicode: [char; 256],
    /// GPT-2 unicode to byte mapping
    unicode_to_byte: AHashMap<char, u8>,
    /// Whether to use regex pre-tokenization
    use_pretokenizer: bool,
}

impl BPEEncoder {
    /// Create a new BPE encoder.
    ///
    /// # Arguments
    /// * `merges` - List of merge pairs in order
    /// * `vocab` - List of (unicode_string_bytes, token_id) pairs. The bytes are UTF-8
    ///   encoded GPT-2 unicode strings (NOT raw byte sequences).
    /// * `special_tokens` - Map of special token strings to their IDs
    /// * `pattern` - Optional regex pattern (defaults to GPT-4 pattern)
    pub fn new(
        merges: Vec<(Pair, u32)>,
        vocab: Vec<(Vec<u8>, u32)>,
        special_tokens: HashMap<String, u32>,
        pattern: Option<String>,
    ) -> Result<Self, String> {
        let use_pretokenizer = pattern.is_some();
        let pattern_str = pattern.unwrap_or_else(|| GPT4_PATTERN.to_string());
        let compiled_pattern = Regex::new(&pattern_str)
            .map_err(|e| format!("Invalid regex pattern: {}", e))?;

        let mut merges_map = HashMap::with_capacity(merges.len());
        for (pair, id) in merges {
            merges_map.insert(pair, id);
        }

        let byte_to_unicode = build_bytes_to_unicode();
        let unicode_to_byte = build_unicode_to_bytes(&byte_to_unicode);

        // Build token_to_str and str_to_token maps
        // vocab entries are UTF-8 encoded GPT-2 unicode strings
        let max_id = vocab.iter().map(|(_, id)| *id).max().unwrap_or(0) as usize;
        let mut token_to_str = vec![String::new(); max_id + 1];
        let mut str_to_token = AHashMap::with_capacity(vocab.len());

        for (utf8_bytes, id) in vocab {
            let s = String::from_utf8(utf8_bytes)
                .map_err(|e| format!("Invalid UTF-8 in vocab entry id={}: {}", id, e))?;
            token_to_str[id as usize] = s.clone();
            str_to_token.insert(s, id);
        }

        let special_tokens_reverse: HashMap<u32, String> = special_tokens
            .iter()
            .map(|(s, id)| (*id, s.clone()))
            .collect();

        let vocab_size = token_to_str.len();

        Ok(BPEEncoder {
            merges: merges_map,
            pattern: compiled_pattern,
            token_to_str,
            str_to_token,
            special_tokens,
            special_tokens_reverse,
            vocab_size,
            byte_to_unicode,
            unicode_to_byte,
            use_pretokenizer,
        })
    }

    /// Get vocabulary size
    #[inline]
    pub fn vocab_size(&self) -> usize {
        self.vocab_size
    }

    /// Map raw bytes to GPT-2 unicode string
    fn bytes_to_gpt2_unicode(&self, input: &[u8]) -> String {
        input.iter().map(|&b| self.byte_to_unicode[b as usize]).collect()
    }

    /// Map GPT-2 unicode string back to raw bytes
    fn gpt2_unicode_to_bytes(&self, s: &str) -> Vec<u8> {
        s.chars()
            .map(|c| {
                self.unicode_to_byte
                    .get(&c)
                    .copied()
                    .unwrap_or_else(|| {
                        // For chars not in GPT-2 mapping, use UTF-8
                        // This shouldn't happen for properly encoded BPE output
                        c as u8
                    })
            })
            .collect()
    }

    /// Encode a single chunk (already mapped to GPT-2 unicode) using BPE merges
    fn encode_chunk(&self, gpt2_str: &str) -> Vec<u32> {
        // Check if this is a special token
        if let Some(&id) = self.special_tokens.get(gpt2_str) {
            return vec![id];
        }

        if gpt2_str.is_empty() {
            return Vec::new();
        }

        // Check if the whole chunk is in vocabulary
        if let Some(&id) = self.str_to_token.get(gpt2_str) {
            return vec![id];
        }

        // Start with per-character tokens (each GPT-2 unicode char = one byte-level token)
        let mut ids: Vec<u32> = gpt2_str
            .chars()
            .map(|c| {
                let s = c.to_string();
                self.str_to_token.get(&s).copied().unwrap_or(0)
            })
            .collect();

        // Apply merges iteratively (greedy: always merge the pair with lowest merge rank)
        while ids.len() >= 2 {
            let mut best_pair: Option<(usize, Pair, u32)> = None;

            for i in 0..ids.len() - 1 {
                let pair: Pair = (ids[i], ids[i + 1]);
                if let Some(&new_id) = self.merges.get(&pair) {
                    if best_pair.is_none() || new_id < best_pair.unwrap().2 {
                        best_pair = Some((i, pair, new_id));
                    }
                }
            }

            if let Some((idx, _pair, new_id)) = best_pair {
                ids[idx] = new_id;
                ids.remove(idx + 1);
            } else {
                break;
            }
        }

        ids
    }

    /// Encode text to token IDs.
    pub fn encode(&self, text: &str) -> Vec<u32> {
        if text.is_empty() {
            return Vec::new();
        }

        // Map input bytes to GPT-2 unicode
        let gpt2_text = self.bytes_to_gpt2_unicode(text.as_bytes());

        if self.use_pretokenizer {
            // Split using regex pattern (on the GPT-2 unicode text)
            let mut all_ids = Vec::new();
            for m in self.pattern.find_iter(&gpt2_text) {
                match m {
                    Ok(mat) => {
                        let chunk = mat.as_str();
                        let ids = self.encode_chunk(chunk);
                        all_ids.extend(ids);
                    }
                    Err(_) => continue,
                }
            }
            all_ids
        } else {
            // No pre-tokenizer: run BPE on the entire GPT-2 unicode text
            self.encode_chunk(&gpt2_text)
        }
    }

    /// Decode token IDs back to text.
    pub fn decode(&self, ids: &[u32]) -> Result<String, String> {
        let mut gpt2_str = String::with_capacity(ids.len() * 4);

        for &id in ids {
            if let Some(token_str) = self.special_tokens_reverse.get(&id) {
                gpt2_str.push_str(token_str);
                continue;
            }

            let id_usize = id as usize;
            if id_usize < self.token_to_str.len() {
                gpt2_str.push_str(&self.token_to_str[id_usize]);
            } else {
                return Err(format!("Unknown token ID: {}", id));
            }
        }

        // Map GPT-2 unicode back to raw bytes
        let bytes = self.gpt2_unicode_to_bytes(&gpt2_str);

        String::from_utf8(bytes)
            .map_err(|e| format!("Invalid UTF-8 in decoded output: {}", e))
    }

    /// Get a token's string representation (decoded to real text).
    pub fn id_to_token(&self, id: u32) -> Option<String> {
        if let Some(token) = self.special_tokens_reverse.get(&id) {
            return Some(token.clone());
        }

        let id_usize = id as usize;
        if id_usize < self.token_to_str.len() {
            let gpt2_str = &self.token_to_str[id_usize];
            let bytes = self.gpt2_unicode_to_bytes(gpt2_str);
            String::from_utf8(bytes).ok()
        } else {
            None
        }
    }

    /// Get a token's ID from its real text representation.
    pub fn token_to_id(&self, token: &str) -> Option<u32> {
        if let Some(&id) = self.special_tokens.get(token) {
            return Some(id);
        }

        // Map the token text to GPT-2 unicode and look up
        let gpt2_str = self.bytes_to_gpt2_unicode(token.as_bytes());
        self.str_to_token.get(&gpt2_str).copied()
    }
}

/// Serializable BPE data structure for embedding in binary.
#[derive(serde::Serialize, serde::Deserialize)]
pub struct BPEData {
    /// Merge pairs: ((left, right), merged_id)
    pub merges: Vec<((u32, u32), u32)>,
    /// Vocabulary: (utf8_bytes_of_gpt2_unicode_string, token_id)
    pub vocab: Vec<(Vec<u8>, u32)>,
    /// Special tokens
    pub special_tokens: HashMap<String, u32>,
    /// Regex pattern
    pub pattern: String,
}

impl BPEData {
    /// Convert to BPEEncoder
    pub fn into_encoder(self) -> Result<BPEEncoder, String> {
        // Empty pattern means no pre-tokenizer
        let pattern = if self.pattern.is_empty() {
            None
        } else {
            Some(self.pattern)
        };
        BPEEncoder::new(
            self.merges,
            self.vocab,
            self.special_tokens,
            pattern,
        )
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn create_test_encoder() -> BPEEncoder {
        // Build the byte_to_unicode mapping to get correct single-char tokens
        let b2u = build_bytes_to_unicode();

        let mut vocab = Vec::new();

        // Add byte-level tokens using GPT-2 unicode chars
        for i in 0..256u32 {
            let s = b2u[i as usize].to_string();
            vocab.push((s.into_bytes(), i));
        }

        // Add a merge: 'a' (id for byte 97) + 'b' (id for byte 98) -> 256
        // In GPT-2 mapping, 'a' and 'b' map to themselves
        let a_id = 97u32;  // 'a' maps to itself in GPT-2
        let b_id = 98u32;  // 'b' maps to itself in GPT-2
        let ab_str = format!("{}{}", b2u[97], b2u[98]);
        vocab.push((ab_str.into_bytes(), 256));

        let merges = vec![((a_id, b_id), 256)];
        let special_tokens = HashMap::new();

        BPEEncoder::new(merges, vocab, special_tokens, None).unwrap()
    }

    #[test]
    fn test_encode_simple() {
        let encoder = create_test_encoder();
        let ids = encoder.encode("ab");
        assert!(ids.contains(&256));
    }

    #[test]
    fn test_decode_simple() {
        let encoder = create_test_encoder();
        let text = encoder.decode(&[256]).unwrap();
        assert_eq!(text, "ab");
    }

    #[test]
    fn test_roundtrip() {
        let encoder = create_test_encoder();
        let original = "ab";
        let ids = encoder.encode(original);
        let decoded = encoder.decode(&ids).unwrap();
        assert_eq!(decoded, original);
    }

    #[test]
    fn test_empty_input() {
        let encoder = create_test_encoder();
        assert!(encoder.encode("").is_empty());
        assert_eq!(encoder.decode(&[]).unwrap(), "");
    }
}
