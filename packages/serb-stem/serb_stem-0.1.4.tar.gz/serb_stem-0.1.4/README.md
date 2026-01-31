# Serb-Stem 🇷🇸⚡

![Serb-Stem Header](https://raw.githubusercontent.com/Ja1Denis/Serb-Stem/master/docs/serbstem_header.png)

[![PyPI version](https://badge.fury.io/py/serb-stem.svg)](https://badge.fury.io/py/serb-stem)
[![Downloads](https://img.shields.io/pypi/dm/serb-stem)](https://pypi.org/project/serb-stem/)
[![Rust](https://img.shields.io/badge/language-Rust-orange.svg)](https://www.rust-lang.org/)
[![Python](https://img.shields.io/badge/python-3.7%2B-blue.svg)](https://www.python.org/)
[![WebAssembly](https://img.shields.io/badge/wasm-supported-blueviolet.svg)](https://webassembly.org/)
[![License](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](LICENSE)

### „Ponuda koju tvoj NLP procesor ne može da odbije.“

Prestanite da gubite vreme na spora, neprecizna rešenja koja "pucaju" na ćirilici. **Serb-Stem** nije samo biblioteka — to je nepravedna prednost za tvoj pretraživač.

## ✨ Šta dobijaš (The Grand Slam Offer)

- **🚀 Brzina Svetlosti (<1µs Latency)**: Dok drugi učitavaju rečnike, ti si već ostemovao celu bazu. Rust motor radi na metalu — bez smeća, bez čekanja.
- **🎯 Hirurška Preciznost (98.35% Acc)**: Naš algoritam ne nagađa. On poznaje srpsku gramatiku bolje od tvoje profesorke iz srednje.
- **💪 Universal Script Engine**: Ćirilica? Latinica? Ijekavica? Serb-Stem sve žvaće i izbacuje savršen ekavski koren spreman za indeksiranje.
- **🏗️ Zero-Effort Integration**: `pip install` i gotov si. Nema kompajliranja, nema zavisnosti, nema glavobolje.

## 📉 Jednačina Vrednosti (Value Equation)

- **Dream Outcome**: Savršena pretraga i analiza srpskog teksta u realnom vremenu.
- **Likelihood of Success**: **98.35%** verifikovan korpus + Rust memorijska sigurnost.
- **Time Delay**: **NULA.** Od instalacije do prvog `stem()` poziva treba ti 30 sekundi. Latencija obrade je bukvalno nevidljiva.
- **Effort & Sacrifice**: **NULA.** Handling oba pisma i ekavizaciju radimo mi. Ti samo šalješ stringove.

## 🛠️ Instalacija i Korišćenje

### 🐍 Python
```bash
pip install serb-stem
```

```python
import serb_stem

# Latino ulaz
print(serb_stem.stem_py("knjigama"))  # Output: "knjig"

# Ćirilični ulaz
print(serb_stem.stem_py("књигама"))  # Output: "књиг"

# Ekavizacija (mlijeko -> mlek)
print(serb_stem.stem_py("mlijeka"))   # Output: "mlek"
```

### 🦀 Rust
```rust
use serb_stem::stem;

let result = stem("učenici");
assert_eq!(result, "učenik");
```

## 🌐 Interaktivni Demo
Isprobajte Serb-Stem uživo, direktno u vašem browseru:
👉 **[https://ja1denis.github.io/Serb-Stem/](https://ja1denis.github.io/Serb-Stem/)**

Portal je izrađen pomoću React-a i Vite-a, a pokreće ga isti onaj ultra-brzi Rust WASM engine koji koristite u produkciji.

## ⚖️ Licenca i Autorska Prava

Copyright © 2026 Denis Ja1Denis. Sva prava pridržana osim onih dozvoljenih licencom.

Ovaj projekat je licenciran pod **MIT** ili **Apache-2.0** licencom — po vašem izboru.

- 📧 **Email**: sdenis.vr@gmail.com
- 🔗 **LinkedIn**: [Denis Sakač](https://www.linkedin.com/in/denis-sakac-73a99933/)

> **Napomena**: Ako koristite ovo komercijalno, javite mi se za suradnju. Uvijek sam otvoren za feedback i nove prilike!

***

👨‍💻 **Također od autora:**
- **[Cro-Stem](https://github.com/Ja1Denis/Cro-Stem)**: Napredni Stemmer za hrvatski jezik.
- **[Slov-Stem](https://github.com/Ja1Denis/Slov-Stem)**: Prvi pravi Stemmer za slovenski jezik.

---
*Developed with ❤️ by Ja1Denis & Antigravity AI*
