# Cro-Stem 2.0 🇭🇷⚡

![Cro-Stem 10k Header](crostem_10k_header.png)

[![PyPI version](https://badge.fury.io/py/cro-stem.svg)](https://badge.fury.io/py/cro-stem)
[![Rust](https://img.shields.io/badge/language-Rust-orange.svg)](https://www.rust-lang.org/)
[![WASM](https://img.shields.io/badge/wasm-supported-blueviolet.svg)](https://ja1denis.github.io/Cro-Stem/)
[![License](https://img.shields.io/badge/License-MIT%20OR%20Apache--2.0-blue.svg)](LICENSE)

### „Zašto koristiti išta drugo kada možeš imati 97% preciznosti u 500KB?“

Ako si ikada pokušao raditi NLP na hrvatskom jeziku, znaš bol: PyTorch modeli koji jedu 4GB RAM-a, spori regexi koji griješe na svakom drugom padežu, ili skripte stare 10 godina koje nitko ne održava. 

**Cro-Stem je rješenje.** To nije samo još jedan stemmer. To je **najbrži i najprecizniji** open-source alat za hrvatski jezik koji postoji.

## 🏆 The Grand Slam Offer (Zašto ovo moraš imati)

### 1. ⚡ **Brzina Koja Briše Pod S Konkurencijom**
Dok tvoj stari Python skript učita biblioteke, Cro-Stem je već obradio cijeli "Rat i mir". Nema čekanja. Nema GPU-a. Samo čisti, optimizirani Rust koji leti.

### 2. 🎯 **97.4% Dokazana Preciznost (NOVO)**
Ažurirali smo algoritam na temelju **zlatnog standarda od 1350 najtežih lingvističkih primjera**. 
- Nepostojano 'a'? Riješeno (`vrabac` <-> `vrapca`).
- Sibilarizacija? Riješena (`majci` <-> `majka`).
- Aorist i imperfekt? Riješeni.
**Ne pogađamo. Znamo.**

### 3. 📉 **The Value Equation (Jednadžba Vrijednosti)**
*   **Dream Outcome (San)**: Savršeno pretraživanje i analiza hrvatskog teksta.
*   **Perceived Likelihood (Vjerojatnost)**: 100% (dokazano testovima).
*   **Time Delay (Vrijeme)**: 0 sekundi (trenutna instalacija i izvršavanje).
*   **Effort & Sacrifice (Trud)**: 1 linija koda.

---

## 🛠️ Kako Početi (U 30 Sekundi)

### 🐍 Python
```bash
pip install cro-stem
```
```python
import cro_stem

# Aggressive Mode (za tražilice) - Preciznost: 97.4%
print(cro_stem.stem("vrapcima")) # Output: "vrabac"
```

### 🦀 Rust
```rust
use cro_stem::{CroStem, StemMode};

let stemmer = CroStem::new(StemMode::Aggressive);
assert_eq!(stemmer.stem("najljepših"), "lijep");
```

### 🌐 Web (WASM)
Radi direktno u browseru. Bez servera. Bez latencije.
👉 **[Isprobaj Live Demo](https://ja1denis.github.io/Cro-Stem/)**

---

## ☕️ Dev Corner (Za Lokalne Heroje)
- **🚀 Brži od konobara na Rivi:** Cro-Stem obrađuje tvoj CSV brže nego što stigneš naručiti kavu s hladnim mlijekom.
- **🛥️ Bez redova za trajekt:** Naš Rust engine nema kašnjenja. Za razliku od ulaska na trajekt u špici sezone, ovdje nema čekanja u redu.
- **🏫 Kraj traumama iz škole:** Sjećaš se tablica s padežima? Mi smo ih pretvorili u kod da ti više nikada ne bi morao razmišljati o *instrumentalu množine*.

---

## ⚖️ Licenca
Ovaj projekt je besplatan. Uzmi ga. Koristi ga. Zaradi milijune s njim.
(Licencirano pod **MIT** ili **Apache-2.0** licencom).

### 👨‍💻 O Autoru
Kreirao **Denis Ja1Denis**.
Ako ti je ovaj alat uštedio vrijeme ili novac, ili ako želiš da tvoj NLP projekt zapravo radi:
- 📧 **Email**: sdenis.vr@gmail.com
- 🔗 **LinkedIn**: [Denis Sakač](https://www.linkedin.com/in/denis-sakac-73a99933/)

***
**Također pogledaj:**
- **[Serb-Stem](https://github.com/Ja1Denis/Serb-Stem)**: Prvi pravi Stemmer za srpski jezik.
- **[Slov-Stem](https://github.com/Ja1Denis/Slov-Stem)**: Prvi pravi Stemmer za slovenski jezik.
