# Trenutni status - Cro-Stem

## Projektni podaci
- **Verzija**: 0.1.5
- **Jezik**: Rust (s Python vezivima via PyO3)
- **Točnost**: ~91.40% (base) / Poboljšana u v0.1.5
- **Licenca**: AGPL-3.0

## Ključne značajke
- **Aggressive/Conservative moduli**: Podrška za različite scenarije (pretraga vs NLP).
- **WASM portal**: Interaktivni demo na GitHub Pages.
- **Minimalne ovisnosti**: Brz i lagan.

## Zadaci u tijeku
- [x] Implementacija plana poboljšanja za v0.1.5+.
- [x] Dodavanje popisa iznimaka (exceptions).
- [x] Implementacija zaštitnih uvjeta za agresivna pravila.
- [x] Proširenje pravila za nominalne i pridjevske nastavke.

## Postignuto (v0.1.5)
- **Visoka točnost na 1k korpusu**: Aggressive score dosegao **96.5%** (965/1000), Conservative score **66.0%** (660/1000).
- **Implementirana "stvo" logika**: Pametno čuvanje nastavka ovisno o duljini korijena.
- **Masivni 'Exceptions' lookup**: Pokriveni najčešći nepravilni glagoli i imenice (usklađeno s korpusom od 1000 riječi).
- **Glasovna pravila**: Napredna podrška za nepostojano 'a', vokalizaciju i specifične transformacije korijena (npr. `sunc`, `vremen`).

## Sljedeći koraci
1. Proširiti testiranje na masivni korpus od **10,000 riječi** i validirati robusnost.
2. Ažurirati Python bindings da podržavaju novi `StemMode`.
3. Re-buildati WASM portal kako bi korisnici vidjeli poboljšanja.
