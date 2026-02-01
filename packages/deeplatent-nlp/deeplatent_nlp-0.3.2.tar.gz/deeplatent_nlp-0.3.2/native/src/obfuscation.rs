//! Obfuscation module for embedded tokenizer data.
//!
//! This module handles loading and decrypting embedded morpheme map and BPE data.
//! The data is compressed with zstd and XOR-encrypted for mild obfuscation.

use std::collections::HashMap;
use std::io::Read;

use crate::bpe::BPEData;

/// Embedded encrypted morpheme map data (populated by build process)
/// This is a placeholder - actual data is embedded via include_bytes! or loaded at runtime
#[cfg(feature = "embedded_data")]
const MORPHEME_MAP_DATA: &[u8] = include_bytes!("../data/morpheme_map.bin.enc");

#[cfg(feature = "embedded_data")]
const BPE_DATA: &[u8] = include_bytes!("../data/bpe.bin.enc");

/// XOR encryption key split into parts for mild obfuscation.
/// The key is reconstructed at runtime by concatenating these parts.
const KEY_PARTS: [&[u8]; 4] = [
    b"dL$t0k",  // Part 1
    b"3n_K3y",  // Part 2
    b"_s4rf_",  // Part 3
    b"mYt3!@",  // Part 4
];

/// Reconstruct the XOR key from its parts.
fn get_key() -> Vec<u8> {
    KEY_PARTS.iter().flat_map(|p| p.iter().copied()).collect()
}

/// XOR decrypt/encrypt data with the given key (symmetric).
fn xor_crypt(data: &[u8], key: &[u8]) -> Vec<u8> {
    data.iter()
        .enumerate()
        .map(|(i, &b)| b ^ key[i % key.len()])
        .collect()
}

/// Decompress zstd-compressed data.
fn decompress(data: &[u8]) -> Result<Vec<u8>, String> {
    let mut decoder = zstd::Decoder::new(data)
        .map_err(|e| format!("Failed to create zstd decoder: {}", e))?;

    let mut decompressed = Vec::new();
    decoder
        .read_to_end(&mut decompressed)
        .map_err(|e| format!("Failed to decompress data: {}", e))?;

    Ok(decompressed)
}

/// Load morpheme map from encrypted embedded data.
#[cfg(feature = "embedded_data")]
pub fn load_morpheme_map_embedded() -> Result<HashMap<String, String>, String> {
    let key = get_key();
    let decrypted = xor_crypt(MORPHEME_MAP_DATA, &key);
    let decompressed = decompress(&decrypted)?;

    serde_json::from_slice(&decompressed)
        .map_err(|e| format!("Failed to deserialize morpheme map: {}", e))
}

/// Load BPE data from encrypted embedded data.
#[cfg(feature = "embedded_data")]
pub fn load_bpe_data_embedded() -> Result<BPEData, String> {
    let key = get_key();
    let decrypted = xor_crypt(BPE_DATA, &key);
    let decompressed = decompress(&decrypted)?;

    parse_bpe_binary(&decompressed)
}

/// Load morpheme map from encrypted bytes.
pub fn load_morpheme_map(encrypted_data: &[u8]) -> Result<HashMap<String, String>, String> {
    let key = get_key();
    let decrypted = xor_crypt(encrypted_data, &key);
    let decompressed = decompress(&decrypted)?;

    serde_json::from_slice(&decompressed)
        .map_err(|e| format!("Failed to deserialize morpheme map: {}", e))
}

/// Load BPE data from encrypted bytes.
pub fn load_bpe_data(encrypted_data: &[u8]) -> Result<BPEData, String> {
    let key = get_key();
    let decrypted = xor_crypt(encrypted_data, &key);
    let decompressed = decompress(&decrypted)?;

    parse_bpe_binary(&decompressed)
}

/// Parse BPE data from custom binary format (matches Python prepare_tokenizer_data.py).
///
/// Format:
/// 1. Number of merges (u64 LE)
/// 2. For each merge: left (u32 LE), right (u32 LE), merged (u32 LE)
/// 3. Number of vocab entries (u64 LE)
/// 4. For each vocab: bytes_len (u64 LE), bytes, token_id (u32 LE)
/// 5. Number of special tokens (u64 LE)
/// 6. For each special token: str_len (u64 LE), str_bytes, token_id (u32 LE)
/// 7. Pattern str_len (u64 LE), pattern_bytes
fn parse_bpe_binary(data: &[u8]) -> Result<BPEData, String> {
    let mut offset = 0;

    // Helper to read u64 LE
    let read_u64 = |data: &[u8], offset: &mut usize| -> Result<u64, String> {
        if *offset + 8 > data.len() {
            return Err("Unexpected end of data reading u64".to_string());
        }
        let bytes: [u8; 8] = data[*offset..*offset + 8]
            .try_into()
            .map_err(|_| "Failed to read u64")?;
        *offset += 8;
        Ok(u64::from_le_bytes(bytes))
    };

    // Helper to read u32 LE
    let read_u32 = |data: &[u8], offset: &mut usize| -> Result<u32, String> {
        if *offset + 4 > data.len() {
            return Err("Unexpected end of data reading u32".to_string());
        }
        let bytes: [u8; 4] = data[*offset..*offset + 4]
            .try_into()
            .map_err(|_| "Failed to read u32")?;
        *offset += 4;
        Ok(u32::from_le_bytes(bytes))
    };

    // Helper to read bytes
    let read_bytes = |data: &[u8], offset: &mut usize, len: usize| -> Result<Vec<u8>, String> {
        if *offset + len > data.len() {
            return Err("Unexpected end of data reading bytes".to_string());
        }
        let bytes = data[*offset..*offset + len].to_vec();
        *offset += len;
        Ok(bytes)
    };

    // Read merges
    let num_merges = read_u64(data, &mut offset)? as usize;
    let mut merges = Vec::with_capacity(num_merges);
    for _ in 0..num_merges {
        let left = read_u32(data, &mut offset)?;
        let right = read_u32(data, &mut offset)?;
        let merged = read_u32(data, &mut offset)?;
        merges.push(((left, right), merged));
    }

    // Read vocab
    let num_vocab = read_u64(data, &mut offset)? as usize;
    let mut vocab = Vec::with_capacity(num_vocab);
    for _ in 0..num_vocab {
        let bytes_len = read_u64(data, &mut offset)? as usize;
        let bytes = read_bytes(data, &mut offset, bytes_len)?;
        let token_id = read_u32(data, &mut offset)?;
        vocab.push((bytes, token_id));
    }

    // Read special tokens
    let num_special = read_u64(data, &mut offset)? as usize;
    let mut special_tokens = HashMap::with_capacity(num_special);
    for _ in 0..num_special {
        let str_len = read_u64(data, &mut offset)? as usize;
        let str_bytes = read_bytes(data, &mut offset, str_len)?;
        let token_id = read_u32(data, &mut offset)?;
        let token_str = String::from_utf8(str_bytes)
            .map_err(|e| format!("Invalid UTF-8 in special token: {}", e))?;
        special_tokens.insert(token_str, token_id);
    }

    // Read pattern
    let pattern_len = read_u64(data, &mut offset)? as usize;
    let pattern_bytes = read_bytes(data, &mut offset, pattern_len)?;
    let pattern = String::from_utf8(pattern_bytes)
        .map_err(|e| format!("Invalid UTF-8 in pattern: {}", e))?;

    Ok(BPEData {
        merges,
        vocab,
        special_tokens,
        pattern,
    })
}

/// Encrypt and compress data for embedding.
/// This is used by the build script to prepare data files.
pub fn encrypt_data(data: &[u8]) -> Result<Vec<u8>, String> {
    // Compress with zstd
    let compressed = zstd::encode_all(data, 19) // Level 19 for maximum compression
        .map_err(|e| format!("Failed to compress data: {}", e))?;

    // XOR encrypt
    let key = get_key();
    let encrypted = xor_crypt(&compressed, &key);

    Ok(encrypted)
}

/// Encrypt JSON data (morpheme map).
#[allow(dead_code)]
pub fn encrypt_json<T: serde::Serialize>(data: &T) -> Result<Vec<u8>, String> {
    let json_bytes = serde_json::to_vec(data)
        .map_err(|e| format!("Failed to serialize JSON: {}", e))?;
    encrypt_data(&json_bytes)
}

/// Obfuscation statistics for debugging.
#[derive(Debug)]
#[allow(dead_code)]
pub struct ObfuscationStats {
    pub original_size: usize,
    pub compressed_size: usize,
    pub encrypted_size: usize,
    pub compression_ratio: f64,
}

/// Compute obfuscation statistics.
#[allow(dead_code)]
pub fn compute_stats(original_data: &[u8], encrypted_data: &[u8]) -> ObfuscationStats {
    // Decrypt to get compressed size
    let key = get_key();
    let compressed = xor_crypt(encrypted_data, &key);

    ObfuscationStats {
        original_size: original_data.len(),
        compressed_size: compressed.len(),
        encrypted_size: encrypted_data.len(),
        compression_ratio: compressed.len() as f64 / original_data.len() as f64,
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_xor_roundtrip() {
        let original = b"Hello, World! This is a test message.";
        let key = get_key();

        let encrypted = xor_crypt(original, &key);
        assert_ne!(encrypted, original.to_vec());

        let decrypted = xor_crypt(&encrypted, &key);
        assert_eq!(decrypted, original.to_vec());
    }

    #[test]
    fn test_encrypt_decrypt_json() {
        let mut map = HashMap::new();
        map.insert("hello".to_string(), "world".to_string());
        map.insert("foo".to_string(), "bar".to_string());

        let encrypted = encrypt_json(&map).unwrap();
        let decrypted = load_morpheme_map(&encrypted).unwrap();

        assert_eq!(decrypted.get("hello"), Some(&"world".to_string()));
        assert_eq!(decrypted.get("foo"), Some(&"bar".to_string()));
    }

    #[test]
    fn test_key_consistency() {
        let key1 = get_key();
        let key2 = get_key();
        assert_eq!(key1, key2);
        assert!(!key1.is_empty());
    }
}
