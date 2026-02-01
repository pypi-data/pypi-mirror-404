//! Build script for deeplatent_core.
//!
//! This script checks for the existence of encrypted data files when
//! building with the `embedded_data` feature.

fn main() {
    // Rerun if data files change
    println!("cargo:rerun-if-changed=data/morpheme_map.bin.enc");
    println!("cargo:rerun-if-changed=data/bpe.bin.enc");
    println!("cargo:rerun-if-changed=build.rs");

    // When building with embedded_data feature, verify data files exist
    #[cfg(feature = "embedded_data")]
    {
        use std::path::Path;

        let morpheme_map_path = Path::new("data/morpheme_map.bin.enc");
        let bpe_path = Path::new("data/bpe.bin.enc");

        if !morpheme_map_path.exists() {
            panic!(
                "Missing embedded data file: {:?}\n\
                 Run `python scripts/prepare_tokenizer_data.py` first to generate encrypted data files.",
                morpheme_map_path
            );
        }

        if !bpe_path.exists() {
            panic!(
                "Missing embedded data file: {:?}\n\
                 Run `python scripts/prepare_tokenizer_data.py` first to generate encrypted data files.",
                bpe_path
            );
        }

        println!("cargo:warning=Building with embedded tokenizer data");
    }

    #[cfg(not(feature = "embedded_data"))]
    {
        println!("cargo:warning=Building without embedded data (data loaded at runtime)");
    }
}
