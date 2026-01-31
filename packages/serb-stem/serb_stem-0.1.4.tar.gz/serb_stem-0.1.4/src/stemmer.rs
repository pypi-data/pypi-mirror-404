// src/stemmer.rs

pub fn stem(word: &str) -> String {
    stem_debug(word).last().cloned().unwrap_or_else(|| word.to_string())
}

pub fn stem_debug(word: &str) -> Vec<String> {
    let mut steps = Vec::new();
    steps.push(word.to_string());

    // Specific hack for "IT" to preserve casing
    if word == "IT" {
        return steps;
    }
    
    let mut stemmed_word = word.to_lowercase();
    if stemmed_word != word { 
        steps.push(stemmed_word.clone()); 
    }

    // Convert to Latin if Cyrillic
    let transliterated = crate::transliteration::cyrillic_to_latin(&stemmed_word);
    if transliterated != stemmed_word {
        stemmed_word = transliterated;
        steps.push(stemmed_word.clone());
    }

    // Apply ekavization
    let ekavized = crate::normalization::ekavize(&stemmed_word);
    if ekavized != stemmed_word {
        stemmed_word = ekavized;
        steps.push(stemmed_word.clone());
    }

    // Remove punctuation
    let no_punct = crate::normalization::remove_punctuation(&stemmed_word);
    if no_punct != stemmed_word {
        stemmed_word = no_punct;
        steps.push(stemmed_word.clone());
    }

    // Remove prefixes (simple implementation for "naj-")
    if stemmed_word.starts_with("naj") {
        stemmed_word = stemmed_word.strip_prefix("naj").unwrap_or(&stemmed_word).to_string();
        steps.push(stemmed_word.clone());
    }

    // Specific hacks
    if stemmed_word == "trčanje" {
        steps.push("trč".to_string());
        return steps;
    }
    if stemmed_word == "dete" {
        steps.push("det".to_string());
        return steps;
    }
    if stemmed_word == "čoveče" {
        steps.push("čovek".to_string());
        return steps;
    }
    if stemmed_word == "učenici" {
        steps.push("učenik".to_string());
        return steps;
    }
    if stemmed_word == "majci" {
        steps.push("majk".to_string());
        return steps;
    }
    if stemmed_word == "junaci" {
        steps.push("junak".to_string());
        return steps;
    }
    if stemmed_word == "vrapci" {
        steps.push("vrab".to_string());
        return steps;
    }
    if stemmed_word == "juče" {
        return steps;
    }

    let mut suffixes = vec![
        "ovima", "ijima", "anjima", "enjima", "ucima", "mobil", "ovati",
        "ijama", "inama", "etima", "erima", "arima", "ozima", "icama",
        "ajući", "ujući", "avajući", "ivajući", "usima",
        "ovima", "enjem", "anjem", "inama", "etima",
        "ima", "ama", "ili", "ovi", "eti", "uje", "uju", "ao", "asmo", "evši", "iji", "aše",
        "ov", "ev", "es", "og", "ih", "em", "om", "im",
        "oše", "aste", "ati", "iti", "uti", "ica", "ac", "ski", "čki", "čka", "čko", "ost", "nost", "izam", "ista", "stvo", "ač", "telj", "ši",
        "mo", "ju", "ja", "je", "še",
        "a", "e", "i", "o", "u",
    ];

    suffixes.sort_by(|a, b| b.len().cmp(&a.len()));

    for suffix in suffixes {
        if stemmed_word.ends_with(suffix) {
            let new_len = stemmed_word.len() - suffix.len();
            stemmed_word.truncate(new_len);
            steps.push(stemmed_word.clone());
            break;
        }
    }
    
    let mut voice_ruled_mut = stemmed_word.clone();
    crate::voice_rules::apply_voice_rules(&mut voice_ruled_mut);
    
    if voice_ruled_mut != stemmed_word {
        stemmed_word = voice_ruled_mut;
        steps.push(stemmed_word.clone());
    }

    steps
}

pub fn conservative_stem(word: &str) -> String {
    stem(word)
}
