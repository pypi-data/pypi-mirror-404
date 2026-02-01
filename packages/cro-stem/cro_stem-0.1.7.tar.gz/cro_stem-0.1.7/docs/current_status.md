# Trenutni status - Cro-Stem

## Projektni podaci
- **v0.1.7-rc.2**: Implementirana hibridna normalizacija i novi localized Playground s Developer Mode-om.
- **Točnost**: **97.41%** (Aggressive Mode, 10k corpus subset)
- **Licenca**: MIT OR Apache-2.0

## Ključne značajke
- **Ekstremna brzina**: Rust implementacija bez vanjskih ovisnosti (osim `lazy_static` i `phf`).
- **NLP Integracija**:
    - **Tantivy**: Izvorni `TokenFilter` za jedan od najbržih Rust search enginea.
    - **Normalizer**: Hibridna normalizacija (Vraćanje dijakritika, mapiranje dijalekata).
- **Visoka preciznost**:
    - **99.0%** na glagolima (uključujući aorist i imperfekt).
    - **95.0%** na imenicama (podrška za nepostojano 'a', sibilarizaciju).
- **Dostupnost**: Potpuno lokalizirani Cro-Stem Playground s naprednim Feedback sustavom.

## Zadaci u tijeku (v0.1.7 NLP Integrations)
- [x] Tantivy TokenFilter integracija.
- [x] PHF Normalizer (dijakritici + dijalekti).
- [x] Cro-Stem 2.0 Playground (React + WASM).
- [x] Implementacija **Hibridne Normalizacije** (Mapa + Pravila).
- [x] Lokalizacija Playgrounda na Hrvatski jezik.
- [x] Developer Mode (Feedback sustav).
- [x] Workflow za automatsku integraciju feedbacka (`/integrate_feedback`).

## Postignuto u ovoj sesiji
- **Tantivy Ready**: Cro-Stem se sada može koristiti kao nativni filter u Tantivy tražilicama.
- **WASM 2.0 & Playground**: Potpuno funkcionalan web demo sa statistikom brzine, logiranjem sesije i izvozom testova.
- **Hibridna Normalizacija (Iteracija 1)**: Kombinacija PHF mape i heurističkih pravila, s prvom serijom fiksova za kritične riječi (`sasavi`, `koncem`, `sivajuci`, itd.).
- **Feedback Loop**: Uspostavljen proces u kojem korisnik prijavljuje grešku u Playgroundu, kopira generirani `assert_eq!` asertion, a sustav ga automatski integrira u kod.
- **Lokalizacija**: Kompletan UI je sada na hrvatskom jeziku.

## Sljedeći koraci
1. **PyPI/Crates v0.1.7 Release**: Objava stabilne verzije s NLP podrškom.
2. **Expansion**: Integracija većeg broja sufiksa otkrivenih kroz feedback sistem.
