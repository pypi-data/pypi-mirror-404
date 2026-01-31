# Plan poboljšanja Cro-Stem (v0.1.5+)

Evo konkretnih, realnih prijedloga kako poboljšati Cro-Stem a da ga ne učiniš značajno "težim" (memorija + vrijeme izvođenja + kompleksnost koda). Fokus je na malim, pametnim koracima koji daju najviše preciznosti za najmanje troška.

## 1. Dodaj mali popis iznimaka (exceptions) – najveći dobitak za najmanji napor
Ovo je klasičan trik kod rule-based stemmera za slavenske jezike.

Napravi `HashMap<String, String>` ili čak samo `Vec<(prefix, original, stem)>` veličine 150–400 najčešćih problematičnih riječi.
Primjeri riječi koje rule-based stemmeri gotovo uvijek krivo režu (iz iskustva sa srpsko-hrvatskim stemmerima i testova):
- `djeca` → `dijete` (ne `djec`)
- `ljudi` → `čovjek` / `osoba` (ali barem `ljudi` → `ljud`)
- `rekao` → `reći`
- `bio` → `biti`
- `išao` → `ići`
- `može` → `moći`
- `hoće` → `htjeti`
- `neće` → `ne + htjeti`
- `djeca, djecu, djeci, djece...`
- `sunce, suncu, suncem...`
- `srce, srcu, srcem...`
- `oko, oku, očima...`
- `uho, uhu, ušima...`
- `brat, brata, braća, braći...`
- `sestra, sestru, sestre, sestrama...`
- `gradovi` → `grad` (ne `gradov`)
- `knjige` → `knjig` (ali bolje `knjiga`)

Ako dodaš samo ~200–300 najfrekventnijih iznimaka (možeš ih izvući iz HrWaC korpusa ili frequency liste), preciznost može skočiti sa ~91% na 94–96% bez ikakvog usporavanja (lookup je O(1)).

## 2. Dodaj "zaštitne" uvjete prije agresivnih pravila (vrlo jeftino)
Mnogi stemmeri režu previše jer primijene pravilo i na riječi gdje ne bi smjeli.
Primjeri jednostavnih filtera (samo if uvjeti, bez dodatnih struktura):

```rust
if word.ends_with("stvo") && word.len() > 6 { 
    // ne reži "kršćanstvo" → kršćan, ali "graditeljstvo" → graditelj
    // preskoči ili specijalno obradi
}

if word.starts_with("naj") && word.contains("iji") { 
    // superlativi – često se krivo režu
    // ostavi "najljepši" → ljep, ali ne diraj ako je prekratko
}
```

Ovo su samo 5–15 dodatnih ifova koji spašavaju desetke grešaka.

## 3. Proširi pravila za najproblematičnije skupine (nominalni i pridjevski nastavci)
Iz literature (Ljubešić, Pandžić, SCStemmers) najviše boli:

- `-jem` / `-jemu` / `-jega` (instrumental / dativ / genitiv pridjeva) → često ostane `-j`
- `-ima` / `-ama` (instrumental / dativ množine) → preagresivno režu na `-im` / `-am`
- `-og` / `-oga` / `-ome` / `-omu` (muški rod genitiv / dativ)
- `-ih` (genitiv / lokativ / instrumental množine pridjeva)

Dodaj 10–20 specifičnih patterna samo za ove slučajeve – to je najveći "low-hanging fruit".
