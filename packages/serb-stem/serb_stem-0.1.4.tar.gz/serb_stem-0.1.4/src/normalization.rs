// src/normalization.rs

pub fn ekavize(text: &str) -> String {
    text.replace("ije", "e")
        .replace("IJE", "E")
}

pub fn normalize_case(text: &str) -> String {
    text.to_lowercase()
}

pub fn remove_punctuation(text: &str) -> String {
    text.chars().filter(|c| c.is_alphanumeric() || c.is_whitespace()).collect()
}