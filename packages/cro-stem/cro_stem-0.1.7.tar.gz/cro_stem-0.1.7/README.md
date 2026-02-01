# Cro-Stem 2.0 🇭🇷⚡

![Cro-Stem 2.0 Header](crostem_v017_header_1769877696463.png)

[![PyPI version](https://badge.fury.io/py/cro-stem.svg)](https://badge.fury.io/py/cro-stem)
[![Rust](https://img.shields.io/badge/language-Rust-orange.svg)](https://www.rust-lang.org/)
[![WASM](https://img.shields.io/badge/wasm-supported-blueviolet.svg)](https://ja1denis.github.io/Cro-Stem/)
[![License](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](LICENSE)
[![PyPI Downloads](https://static.pepy.tech/badge/cro-stem)](https://pepy.tech/project/cro-stem)
[![Crates.io Downloads](https://img.shields.io/crates/d/cro_stem)](https://crates.io/crates/cro_stem)

### „Zašto koristiti išta drugo kada možeš imati 97% preciznosti u 500KB koji trče krugove oko LLM-ova?“

Dosta je sporih Python modela koji traže 4GB RAM-a za bazično stemiranje. Dosta je regexa koji umiru na drugom padežu. Dosta je alata koji se ne održavaju desetljećima.

**Cro-Stem je Grand Slam ponuda za hrvatski NLP.**

---

## 🚀 Ponuda koju ne možeš odbiti (The $100M Value)

Primijenili smo Hormozijevu **jednadžbu vrijednosti** na obradu jezika:

1.  **Dream Outcome (San)**: Savršeno pretraživanje i analiza hrvatskog teksta. Bez gubljenja informacija u padežima. Bez "izgubljenih u prijevodu" momenata.
2.  **Perceived Likelihood (Vjerojatnost)**: **100%**. Testirano na **zlatnom standardu od 1350 najtežih lingvističkih primjera** i validirano na **10k korpusu**.
    - **Točnost (Aggressive)**: **97.41%**
    - **Glagoli**: **99.0%**
    - **Imenice**: **95.0%**
3.  **Time Delay (Vrijeme)**: **NULA**. 0.1ms po riječi. To nije brzo, to je trenutno. Dok tvoje oko trepne, Cro-Stem je procesirao cijelu knjižnicu.
4.  **Effort & Sacrifice (Trud)**: **NULA**. Jedna linija koda za instalaciju. Jedna linija koda za korištenje. Nema konfiguracije. Nema GPU-a. Nema muke.

---

## ✨ NOVO u v0.1.7: Hibridna Normalizacija

Ljudski unosi su grozni. Ljudi pišu "sasavi" umjesto "šašavi". Naša nova **hibridna normalizacija** (PHF Mapa + Heuristička Pravila) automatski "popravlja" dijakritike prije stemiranja.

- **Vraća Dijakritike**: `zvacuci` -> `žvačući`. Automatski. Instantno.
- **Ujedinjuje Dijalekte**: Prepoznaje `lepo` (ekavica) i `lipo` (ikavica) i tretira ih kao `lijepo`.
- **Ekstremna Efikasnost**: Sve to u svega **116 KB WASM-a** koristeći `Cow<'a, str>` za nula alokacija memorije gdje god je to moguće.

---

## 🛠️ Brzi Start (U 30 Sekundi)

### 🐍 Python
```bash
pip install cro-stem
```
```python
import cro_stem
# Aggressive Mode (97.4% točnosti)
print(cro_stem.stem("vrapcima")) # Output: "vrabac"
```

### 🦀 Rust
```rust
use cro_stem::{CroStem, StemMode};

let stemmer = CroStem::new(StemMode::Aggressive);
assert_eq!(stemmer.stem("najljepših"), "lijep");
```

---

## 🔌 Integracije & Ekosustav

- **🦀 Tantivy Integration**: Cro-Stem je sada nativni `TokenFilter` za najbržu Rust tražilicu. Dostupno out-of-the-box.
- **🌐 Playground 2.0**: Potpuno lokalizirani web demo s **Developer Mode-om**.
    - **Feedback Loop**: Pronašao si grešku? Prijavi je direktno u Playgroundu, kopiraj generirani test i pošalji nam ga.
    👉 **[Isprobaj Cro-Stem 2.0 Live](https://ja1denis.github.io/Cro-Stem/)**

---

## ☕️ Dev Corner 

- **🚀 Brži od konobara na Rivi:** Cro-Stem obrađuje tvoj CSV brže nego što stigneš naručiti kavu s hladnim mlijekom.
- **🛥️ Bez redova za trajekt:** Naš Rust engine nema kašnjenja. Za razliku od ulaska na trajekt u špici sezone, ovdje nema čekanja u redu.
- **🏫 Kraj traumama iz škole:** Sjećaš se tablica s padežima? Mi smo ih pretvorili u kod da ti više nikada ne bi morao razmišljati o *instrumentalu množine*.

---

---

## ⚖️ Licenca
Ovaj projekt je besplatan i otvoren. Uzmi ga. Koristi ga. Zaradi milijune s njim.
(Licencirano pod **MIT** ili **Apache-2.0** licencom).

### 👨‍💻 Autor
Kreirao **Denis Ja1Denis**.
Ako ti je ovaj alat uštedio vrijeme ili novac:
- 📧 **Email**: sdenis.vr@gmail.com
- 🔗 **LinkedIn**: [Denis Sakač](https://www.linkedin.com/in/denis-sakac-73a99933/)

***
**Također pogledaj:**
- **[Serb-Stem](https://github.com/Ja1Denis/Serb-Stem)**: Prvi pravi Stemmer za srpski jezik.
- **[Slov-Stem](https://github.com/Ja1Denis/Slov-Stem)**: Prvi pravi Stemmer za slovenski jezik.
