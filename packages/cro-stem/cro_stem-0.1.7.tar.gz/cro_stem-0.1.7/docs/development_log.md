# Dnevnik razvoja - Cro-Stem

## 2026-01-31 (Verzija 0.1.7 RC - NLP Integrations)
- **Tantivy Integracija**:
    - Razvijen `CroStemFilter` i `CroStemTokenizer` za Tantivy ekosustav.
    - Implementiran `TokenStream` omotač koji podržava stemiranje u realnom vremenu unutar search pipelinea (Tantivy API v0.3).
- **Napredna Normalizacija**:
    - Implementiran PHF-bazirani normalizator za vraćanje dijakritika (`zivot` -> `život`).
    - Dodana podrška za mapiranje dijalekata (Ekavica/Ikavica -> Ijekavica).
    - Identificiran problem skalabilnosti statičkih mapa i kreiran **hibridni plan (Mapa + Pravila)**.
- **Demo Platforma (Playground 2.0)**:
    - Izrađen moderni React Playground (WASM + Tailwind).
    - **Lokalizacija**: Kompletno sučelje prevedeno na hrvatski jezik.
    - **Developer Mode**: Implementiran sustav za prijavu grešaka s automatskim generiranjem Rust `assert_eq!` testova.
    - **Session Log**: Dodan sustav za masovno prikupljanje i izvoz testnih slučajeva (Log preglednik).
    - **Pomoć i Upute**: Dodan interaktivni Help sustav unutar Dev Mode-a.
    - Implementirana real-time vizualizacija procesa: Original -> Normalized -> Stem.
    - Dodana statistika performansi u mikrosekundama (μs).
- **Hibridna Normalizacija (Iteracija 1)**:
    - Dodana mikro-mapa u `heuristics.rs` za brze ispravke kritičnih riječi (`sasavi`, `zutim`, `zenscic`, `carsaf`, `sivajuci`).
    - Spriječena regresija za riječ `koncem`.
- **Verzija**: Bump na **v0.1.7-rc.2** i push na `feat/nlp-integrations`.

## 2026-01-31 (Verzija 0.1.6)
- **Validacija na 10k korpusu**:
    - Uspješno testirano na korpusu od 1350 najtežih lingvističkih primjera.
    - Postignuta impresivna točnost od **97.41%** (Aggressive Mode).
- **Optimizacija algoritma**:
    - Podrška za aorist i imperfekt.
    - Riješeni rubni slučajevi za nepostojano 'a' (vrabac -> vrapca).
- **Objava**: Objavljena verzija 0.1.6 na Crates.io i PyPI.

## 2026-01-30
- **Plan poboljšanja v0.1.5+**: Kreiran detaljan plan za povećanje točnosti.
- **Dokumentacija**: Uspostavljen `docs` folder.
- **v0.1.5 Implementacija**: Proširen popis iznimaka i glasovnih pravila.
