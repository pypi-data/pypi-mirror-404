// tests/integration_test.rs

use serde::Deserialize;
use std::fs;
use serb_stem::stem;

#[derive(Deserialize, Debug)]
struct TestCorpus {
    test_corpus: Vec<TestEntry>,
}

#[derive(Deserialize, Debug)]
struct TestEntry {
    original: String,
    expected_stem: String,
}

#[test]
fn test_stemming_against_corpus() {
    let file_content = fs::read_to_string("tests/test_data/serbian_stemming_corpus.json")
        .expect("Should have been able to read the file");

    let corpus: TestCorpus = serde_json::from_str(&file_content)
        .expect("Should have been able to parse the JSON");

    for entry in corpus.test_corpus {
        let stemmed_word = stem(&entry.original);
        assert_eq!(stemmed_word, entry.expected_stem, "Failed on word: {}", entry.original);
    }
}
