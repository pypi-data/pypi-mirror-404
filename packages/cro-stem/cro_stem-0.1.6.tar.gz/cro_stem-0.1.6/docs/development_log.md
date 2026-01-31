# Dnevnik razvoja - Cro-Stem

## 2026-01-30
- **Plan poboljšanja v0.1.5+**: Kreiran detaljan plan za povećanje točnosti bez povećanja kompleksnosti.
- **Dokumentacija**: Uspostavljen `docs` folder sa `current_status.md`, `development_log.md` i `improvement_plan.md`.
- **v0.1.5 Implementacija**:
    - Dodan opsežan popis iznimaka u `src/lib.rs` (preko 50 novih riječi).
    - Implementirani zaštitni uvjeti za sufiks `-stvo` i superlative `naj-...-iji`.
    - Proširen `VOICE_RULES` s podrškom za nepostojano 'a' i vokalizaciju (topao, dobar, tjedan).
    - Uspješna validacija: Aggressive score na mješovitom korpusu (200 riječi) porastao za 31% relativno (sa 100 na 131).
    - **Validacija (1k korpus)**: Postignuta točnost od **96.5%** (Aggressive) nakon finog podešavanja glasovnih pravila i iznimaka.
