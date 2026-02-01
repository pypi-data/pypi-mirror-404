# Cro-Stem 🇭🇷⚡

![Cro-Stem Header](crostem_header.png)

[![PyPI version](https://badge.fury.io/py/cro-stem.svg)](https://badge.fury.io/py/cro-stem)
[![Rust](https://img.shields.io/badge/language-Rust-orange.svg)](https://www.rust-lang.org/)
[![WASM](https://img.shields.io/badge/wasm-supported-blueviolet.svg)](https://ja1denis.github.io/Cro-Stem/)
[![License](https://img.shields.io/badge/License-AGPL_v3-blue.svg)](LICENSE)

### „Zašto trošiti gigabajte na AI, kada Rust može isto u 500KB?“

Dosta je bilo tromih modela koji gutaju RAM i usporavaju tvoju produkciju. **Cro-Stem** je kirurški precizan alat za hrvatski jezik koji donosi performanse bez kompromisa.

## 🏆 Grand Slam Ponuda (The Value Stack)

- **⚡ Munjevita Obrada**: Preko 1,000,000 riječi u sekundi. Dok se AI model tek "probudi", Cro-Stem je već obradio tvoju cijelu bazu.
- **🎯 Preciznost Bez Premca (91.4%)**: Validiran na korpusu od 1000 autentičnih hrvatskih riječi. Ne pogađamo — znamo.
- **🎛️ Dual-Core Engine**:
    - **Aggressive**: Ekstremno rezanje za tražilice (Elasticsearch/Solr). Donosi rezultate koje korisnici traže.
    - **Conservative**: Čuva lingvističku bit. Idealno za naprednu NLP analizu podataka.
- **📦 Zero-Bloat Dizajn**: Cijela moć u manje od 1MB. Nema PyTorcha, nema TensorFlow ovisnosti, samo čisti binarni kôd.

## 📉 Formula Vrijednosti

- **Dream Outcome**: Savršeno indeksiran i pretraživ hrvatski tekst bez troškova serverske infrastrukture.
- **Vjerojatnost Uspjeha**: **91.4%** preciznost + Rust-ova garancija memorijske sigurnosti.
- **Vremenska Odgoda**: **TRENUTNA.** Od `pip install` do produkcije u manje od 2 minute.
- **Trud i Žrtva**: **NULA.** Zaboravi na GPU servere i komplicirane enviromente. Cro-Stem radi i na starom laptopu i na najmodernijem cloud serveru.

---

## 🛠️ Brzi Start

### 🐍 Python
```bash
pip install cro-stem
```
```python
import cro_stem
# Rezultat prilagođen za maksimalnu pretraživost
print(cro_stem.stem("učiteljicama")) # Output: "učitelj"
```

### 🦀 Rust
```rust
use cro_stem::{CroStem, StemMode};

let stemmer = CroStem::new(StemMode::Aggressive);
assert_eq!(stemmer.stem("ljepših"), "ljep");
```

## 🌐 Live Debugger
Isprobaj snagu Rust-a izravno u svom pregledniku:
👉 **[https://ja1denis.github.io/Cro-Stem/](https://ja1denis.github.io/Cro-Stem/)**

---

## ☕️ Dev Corner

- **🚀 Brži od konobara na Rivi:** Cro-Stem obrađuje tvoj CSV brže nego što stigneš naručiti kavu s hladnim mlijekom.
- **🛥️ Bez redova za trajekt:** Naš Rust engine nema kašnjenja. Za razliku od ulaska na trajekt u špici sezone, ovdje nema čekanja u redu — tvoji podaci se procesuiraju odmah.
- **🏫 Kraj traumama iz škole:** Sjećaš se tablica s padežima? Mi smo ih pretvorili u kod da ti više nikada ne bi morao razmišljati o *instrumentalu množine*.

## ⚖️ Licenca i Komercijalna Upotreba

Ovaj projekt je pod **AGPL-3.0** licencom — srce mu kuca za Open Source.

- ✅ **Besplatno** za sve projekte otvorenog koda.
- 💼 **Komercijalna licenca (Enterprise)**: Ako gradiš zatvoreni softver i želiš Cro-Stem u svojoj produkciji bez obveze dijeljenja koda, kontaktiraj autora za kupnju komercijalne licence.

---
*Gradiš budućnost hrvatskog jezika? Gradi je s povjerenjem. Gradi je s Cro-Stem-om.*
