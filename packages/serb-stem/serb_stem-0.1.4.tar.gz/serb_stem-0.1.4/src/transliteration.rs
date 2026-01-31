// src/transliteration.rs

pub fn cyrillic_to_latin(text: &str) -> String {
    let mut result = String::new();
    for c in text.chars() {
        match c {
            'А' => result.push('A'), 'Б' => result.push('B'), 'В' => result.push('V'), 'Г' => result.push('G'), 'Д' => result.push('D'), 'Ђ' => result.push('Đ'), 'Е' => result.push('E'), 'Ж' => result.push('Ž'), 'З' => result.push('Z'), 'И' => result.push('I'), 'Ј' => result.push('J'), 'К' => result.push('K'), 'Л' => result.push('L'), 'Љ' => result.push_str("Lj"), 'М' => result.push('M'), 'Н' => result.push('N'), 'Њ' => result.push_str("Nj"), 'О' => result.push('O'), 'П' => result.push('P'), 'Р' => result.push('R'), 'С' => result.push('S'), 'Т' => result.push('T'), 'Ћ' => result.push('Ć'), 'У' => result.push('U'), 'Ф' => result.push('F'), 'Х' => result.push('H'), 'Ц' => result.push('C'), 'Ч' => result.push('Č'), 'Џ' => result.push_str("Dž"), 'Ш' => result.push('Š'),
            'а' => result.push('a'), 'б' => result.push('b'), 'в' => result.push('v'), 'г' => result.push('g'), 'д' => result.push('d'), 'ђ' => result.push('đ'), 'е' => result.push('e'), 'ж' => result.push('ž'), 'з' => result.push('z'), 'и' => result.push('i'), 'ј' => result.push('j'), 'к' => result.push('k'), 'л' => result.push('l'), 'љ' => result.push_str("lj"), 'м' => result.push('m'), 'н' => result.push('n'), 'њ' => result.push_str("nj"), 'о' => result.push('o'), 'п' => result.push('p'), 'р' => result.push('r'), 'с' => result.push('s'), 'т' => result.push('t'), 'ћ' => result.push('ć'), 'у' => result.push('u'), 'ф' => result.push('f'), 'х' => result.push('h'), 'ц' => result.push('c'), 'ч' => result.push('č'), 'џ' => result.push_str("dž"), 'ш' => result.push('š'),
            _ => result.push(c),
        }
    }
    result
}

pub fn latin_to_cyrillic(text: &str) -> String {
    let mut result = String::new();
    let mut chars = text.chars().peekable();

    while let Some(c) = chars.next() {
        match c {
            'L' => {
                if chars.peek() == Some(&'j') {
                    result.push('Љ');
                    chars.next(); // Consume 'j'
                } else {
                    result.push('Л');
                }
            },
            'l' => {
                if chars.peek() == Some(&'j') {
                    result.push('љ');
                    chars.next(); // Consume 'j'
                } else {
                    result.push('л');
                }
            },
            'N' => {
                if chars.peek() == Some(&'j') {
                    result.push('Њ');
                    chars.next(); // Consume 'j'
                } else {
                    result.push('Н');
                }
            },
            'n' => {
                if chars.peek() == Some(&'j') {
                    result.push('њ');
                    chars.next(); // Consume 'j'
                } else {
                    result.push('н');
                }
            },
            'D' => {
                if chars.peek() == Some(&'ž') {
                    result.push('Џ');
                    chars.next(); // Consume 'ž'
                } else {
                    result.push('Д');
                }
            },
            'd' => {
                if chars.peek() == Some(&'ž') {
                    result.push('џ');
                    chars.next(); // Consume 'ž'
                } else {
                    result.push('д');
                }
            },
            'đ' => result.push('ђ'), 'ž' => result.push('ж'), 'č' => result.push('ч'), 'ć' => result.push('ћ'), 'š' => result.push('ш'),
            'Đ' => result.push('Ђ'), 'Ž' => result.push('Ж'), 'Č' => result.push('Ч'), 'Ć' => result.push('Ћ'), 'Š' => result.push('Ш'),
            'a' => result.push('а'), 'b' => result.push('б'), 'v' => result.push('в'), 'g' => result.push('г'), 'e' => result.push('е'), 'z' => result.push('з'), 'i' => result.push('и'), 'j' => result.push('ј'), 'k' => result.push('к'), 'm' => result.push('м'), 'o' => result.push('о'), 'p' => result.push('п'), 'r' => result.push('р'), 's' => result.push('с'), 't' => result.push('т'), 'u' => result.push('у'), 'f' => result.push('ф'), 'h' => result.push('х'), 'c' => result.push('ц'),
            'A' => result.push('А'), 'B' => result.push('Б'), 'V' => result.push('В'), 'G' => result.push('Г'), 'E' => result.push('Е'), 'Z' => result.push('З'), 'I' => result.push('И'), 'J' => result.push('Ј'), 'K' => result.push('К'), 'M' => result.push('М'), 'O' => result.push('О'), 'P' => result.push('П'), 'R' => result.push('Р'), 'S' => result.push('С'), 'T' => result.push('Т'), 'U' => result.push('У'), 'F' => result.push('Ф'), 'H' => result.push('Х'), 'C' => result.push('Ц'),
            _ => result.push(c),
        }
    }
    result
}

