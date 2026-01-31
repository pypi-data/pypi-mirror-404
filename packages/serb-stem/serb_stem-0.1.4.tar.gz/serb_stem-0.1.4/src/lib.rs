pub mod transliteration;
pub mod normalization;
pub mod stemmer;
pub mod voice_rules;

pub use transliteration::{cyrillic_to_latin, latin_to_cyrillic};
pub use normalization::{ekavize, normalize_case, remove_punctuation};
pub use stemmer::{stem, conservative_stem};
pub use voice_rules::apply_voice_rules;

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_cyrillic_to_latin() {
        assert_eq!(cyrillic_to_latin("Здраво свете!"), "Zdravo svete!");
        assert_eq!(cyrillic_to_latin("Љубав"), "Ljubav");
        assert_eq!(cyrillic_to_latin("Њујорк"), "Njujork");
        assert_eq!(cyrillic_to_latin("Џем"), "Džem");
    }

    #[test]
    fn test_latin_to_cyrillic() {
        assert_eq!(latin_to_cyrillic("Zdravo svete!"), "Здраво свете!");
        assert_eq!(latin_to_cyrillic("Ljubav"), "Љубав");
        assert_eq!(latin_to_cyrillic("Njujork"), "Њујорк");
        assert_eq!(latin_to_cyrillic("Džem"), "Џем");
    }

    #[test]
    fn test_ekavize() {
        assert_eq!(ekavize("mlijeko"), "mleko");
        assert_eq!(ekavize("vrijeme"), "vreme");
        assert_eq!(ekavize("svijet"), "svet");
        assert_eq!(ekavize("BIJELO"), "BELO");
        assert_eq!(ekavize("brijeg"), "breg");
    }

    #[test]
    fn test_normalize_case() {
        assert_eq!(normalize_case("Hello World"), "hello world");
        assert_eq!(normalize_case("RUST Programming"), "rust programming");
    }

    #[test]
    fn test_remove_punctuation() {
        assert_eq!(remove_punctuation("Hello, World!"), "Hello World");
        assert_eq!(remove_punctuation("Rust is great (isn't it?)."), "Rust is great isnt it");
    }

    #[test]
    fn test_stem_basic() {
        assert_eq!(stem("knjigama"), "knjig");
        assert_eq!(stem("učenici"), "učenik");
        assert_eq!(stem("prozorima"), "prozor");
        assert_eq!(stem("najlepši"), "lep"); // Test with ekavization, prefix removal and suffix removal
        assert_eq!(stem("trčanje"), "trč");
        assert_eq!(stem("radili"), "rad");
        assert_eq!(stem("певајући"), "pev"); // Test cyrillic to latin and suffix removal
    }

    #[test]
    fn test_conservative_stem_basic() {
        // For now, conservative stem should behave like aggressive stem
        assert_eq!(conservative_stem("knjigama"), "knjig");
        assert_eq!(conservative_stem("učenici"), "učenik");
    }

    // #[test]
    // fn test_apply_voice_rules() {
    //     let mut word = "učenic".to_string();
    //     apply_voice_rules(&mut word);
    //     assert_eq!(word, "učenik");
    #[test]
    fn test_accuracy_percentage() {
        use std::fs;
        use serde::Deserialize;

        #[derive(Deserialize, Debug)]
        struct TestCorpus { test_corpus: Vec<TestEntry> }
        #[derive(Deserialize, Debug)]
        struct TestEntry { original: String, expected_stem: String }

        let file_content = fs::read_to_string("tests/test_data/serbian_stemming_corpus.json").unwrap();
        let corpus: TestCorpus = serde_json::from_str(&file_content).unwrap();
        
        let mut passed = 0;
        let total = corpus.test_corpus.len();

        for entry in corpus.test_corpus {
            let stemmed = stem(&entry.original);
            if stemmed == entry.expected_stem {
                passed += 1;
            }
        }
        println!("\nSERBSTEM ACCURACY: {}/{} ({:.2}%)", passed, total, (passed as f64 / total as f64) * 100.0);
    }
}
// --- Python Bindings ---
#[cfg(feature = "python")]
use pyo3::prelude::*;

#[cfg(feature = "python")]
#[pyfunction]
fn stem_py(word: &str) -> PyResult<String> {
    Ok(stem(word))
}

#[cfg(feature = "python")]
#[pyfunction]
fn conservative_stem_py(word: &str) -> PyResult<String> {
    Ok(conservative_stem(word))
}

#[cfg(feature = "python")]
#[pymodule]
fn serb_stem(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(stem_py, m)?)?;
    m.add_function(wrap_pyfunction!(conservative_stem_py, m)?)?;
    Ok(())
}

// --- WebAssembly Bindings ---
#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
pub fn stem_wasm(word: &str) -> String {
    stem(word)
}

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
pub fn stem_debug_wasm(word: &str) -> Vec<String> {
    crate::stemmer::stem_debug(word)
}

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
pub fn conservative_stem_wasm(word: &str) -> String {
    conservative_stem(word)
}
