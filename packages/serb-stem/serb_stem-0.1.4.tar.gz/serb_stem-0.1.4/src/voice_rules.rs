// src/voice_rules.rs

pub fn apply_voice_rules(word: &mut String) {
    if word == "peć" {
        word.clear();
        word.push_str("pek");
        return;
    }
    
    // Protection for specific roots
    if word == "dec" || word == "vitez" || word == "niz" {
        return;
    }

    // Sibilarization reversal (e.g., c -> k, z -> g, s -> h)
    // Only applied if the root remains long enough to be meaningful
    if word.ends_with('c') && word.chars().count() > 3 {
        word.pop();
        word.push('k');
    } 
    else if word.ends_with('z') && word.chars().count() > 3 {
        word.pop();
        word.push('g');
    } 
    else if word.ends_with('s') && word.chars().count() > 3 {
        word.pop();
        word.push('h');
    }

    // Palatalization reversal (e.g., č -> k, ž -> g, š -> h)
    if word.ends_with('č') && word.chars().count() > 3 {
        word.pop();
        word.push('k');
    } else if word.ends_with('ž') && word.chars().count() > 3 {
        word.pop();
        word.push('g');
    } else if word.ends_with('š') && word.chars().count() > 3 {
        word.pop();
        word.push('h');
    }
}
