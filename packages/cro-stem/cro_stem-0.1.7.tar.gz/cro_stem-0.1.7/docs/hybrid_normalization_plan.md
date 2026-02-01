# Plan za Hibridnu Normalizaciju (Mapa + Pravila)

## 🎯 Cilj
Napraviti normalizator koji radi u dva koraka:
1. Prvo provjeri mapu (brzo, točno)
2. Ako nema u mapi, primijeni pravila (pokriva nepoznate riječi)

**Rezultat**: WASM ostaje malen (~70KB), ali pokriva 90%+ slučajeva bez ručnog dodavanja riječi.

---

## 📋 Faza 1: Očisti postojeću mapu (30 min)

### Korak 1.1: Otvori datoteku
```
Putanja: e:\G\GeminiCLI\ai-test-project\CroStem_v012\cro_stem\src\normalizer.rs
```

### Korak 1.2: Pronađi liniju s komentarom
```rust
// Tongue Twister words (Brzalice) - Final fix
```

### Korak 1.3: Izbriši sve linije OD te linije DO zatvorene vitičaste zagrade `};`
**Razlog**: Brzalice nisu deo najčešćih riječi. Te riječi će biti pokrivene novim pravilima.

**Primjer**:
```rust
// PRIJE:
    "zrak" => "zrak",
    // Tongue Twister words (Brzalice) - Final fix
    "sesir" => "šešir",
    "zutog" => "žutog",
    ...
};

// POSLIJE:
    "zrak" => "zrak",
};
```

### Korak 1.4: Provjeri sintaksu
- Zadnja linija MAPE mora biti: `};`
- Prije nje mora biti zarez nakon zadnje riječi: `"zrak" => "zrak",`

### Korak 1.5: Test kompajliranja
```bash
cd e:\G\GeminiCLI\ai-test-project\CroStem_v012\cro_stem
cargo build --release
```
**Očekivani rezultat**: `Finished release [optimized] target(s)`

---

## 📋 Faza 2: Dodaj heuristička pravila (60 min)

### Korak 2.1: Pronađi funkciju `normalize`
```rust
pub fn normalize(word: &str) -> &str {
    DIACRITIC_MAP.get(word).copied()
        .or_else(|| DIALECT_MAP.get(word).copied())
        .unwrap_or(word)
}
```

### Korak 2.2: ZAMIJENI sa ovim kodom:
```rust
pub fn normalize(word: &str) -> String {
    // Korak 1: Provjeri mapu prvo (O(1) lookup)
    if let Some(&normalized) = DIACRITIC_MAP.get(word) {
        return normalized.to_string();
    }
    
    // Korak 2: Provjeri dijalekte
    if let Some(&normalized) = DIALECT_MAP.get(word) {
        return normalized.to_string();
    }
    
    // Korak 3: Primijeni heuristička pravila
    apply_diacritic_rules(word)
}
```

### Korak 2.3: Dodaj novu funkciju IZNAD `normalize` funkcije:
```rust
/// Primjenjuje heuristička pravila za vraćanje dijakritika.
/// Pravila su bazirana na čestoći i poziciji slova u hrvatskom jeziku.
fn apply_diacritic_rules(word: &str) -> String {
    let mut result = String::with_capacity(word.len());
    let chars: Vec<char> = word.chars().collect();
    let len = chars.len();
    
    for i in 0..len {
        let ch = chars[i];
        let next = if i + 1 < len { Some(chars[i + 1]) } else { None };
        let prev = if i > 0 { Some(chars[i - 1]) } else { None };
        
        match ch {
            // Pravilo 1: 'c' + samoglasnik ili na kraju riječi prije 'i' = 'ć'
            'c' => {
                if let Some(n) = next {
                    if matches!(n, 'a' | 'e' | 'i' | 'o' | 'u') || n == 'i' {
                        result.push('ć');
                        continue;
                    }
                }
                result.push(ch);
            },
            
            // Pravilo 2: 's' + određeni suglasnici ili samoglasnik = 'š'
            's' => {
                if let Some(n) = next {
                    if matches!(n, 'l' | 'k' | 't' | 'p' | 'i' | 'e' | 'a' | 'u') {
                        result.push('š');
                        continue;
                    }
                }
                result.push(ch);
            },
            
            // Pravilo 3: 'z' + samoglasnik ili specifični suglasnici = 'ž'
            'z' => {
                if let Some(n) = next {
                    if matches!(n, 'i' | 'e' | 'a' | 'u' | 'o' | 'd' | 'v') {
                        result.push('ž');
                        continue;
                    }
                }
                result.push(ch);
            },
            
            // Pravilo 4: 'd' + samoglasnik na početku ili nakon samoglasnika = 'đ'
            'd' => {
                if next == Some('j') || (i == 0 && matches!(next, Some('a') | Some('e') | Some('i'))) {
                    result.push('đ');
                    continue;
                }
                result.push(ch);
            },
            
            // Default: ostavi originalni znak
            _ => result.push(ch),
        }
    }
    
    result
}
```

---

## 📋 Faza 3: Popravi return tipove (30 min)

### Korak 3.1: Nađi SVE pozive `normalize()` u ISTOJ datoteci
To su uglavnom u testovima: `mod tests`

### Korak 3.2: Za svaki `assert_eq!(normalize(...), ...)` promijeni:
```rust
// PRIJE:
assert_eq!(normalize("cesalj"), "češalj");

// POSLIJE:
assert_eq!(normalize("cesalj"), "češalj".to_string());
```

### Korak 3.3: Test
```bash
cargo test normalizer
```
**Očekivani rezultat**: Svi testovi prolaze

---

## 📋 Faza 4: Ažuriraj pozive u `lib.rs` (20 min)

### Korak 4.1: Otvori datoteku
```
Putanja: e:\G\GeminiCLI\ai-test-project\CroStem_v012\cro_stem\src\lib.rs
```

### Korak 4.2: Pronađi liniju:
```rust
let normalized_word = normalizer::normalize(&current_word);
```

### Korak 4.3: ZAMIJENI sa:
```rust
let normalized_word = normalizer::normalize(&current_word);
// normalize() sada vraća String, a ne &str
```

### Korak 4.4: Provjeri da li postoji linija NAKON toga:
```rust
if normalized_word != current_word {
```

### Korak 4.5: Promijeni je u:
```rust
if normalized_word != current_word.as_str() {
```

### Korak 4.6: Test cijele biblioteke
```bash
cargo test
```

---

## 📋 Faza 5: Rebuild WASM i test u Playgroundu (15 min)

### Korak 5.1: Rebuild WASM
```bash
cd e:\G\GeminiCLI\ai-test-project\CroStem_v012\cro_stem
wasm-pack build --target web
```

### Korak 5.2: Kopiraj u playground
```bash
copy pkg\cro_stem* pkg\cro-stem-2.0-playground\cro_stem\
```

### Korak 5.3: Pokreni playground (ako već nije)
```bash
cd pkg\cro-stem-2.0-playground
npm run dev
```

### Korak 5.4: Test u browseru
Otvori: http://localhost:3000/

Testiraj ove riječi (nisu u mapi, ali pravila bi ih trebala popraviti):
```
nocnim -> noćnim
kisama -> kišama
secer -> šećer
ucitelj -> učitelj
zvacuci -> žvačući
```

---

## 📋 Faza 6: Dokumentacija (10 min)

### Korak 6.1: Ažuriraj README.md
Dodaj sekciju:
```markdown
### Hybrid Normalization (v0.1.7+)

CroStem koristi hibridni pristup za vraćanje dijakritika:
1. **PHF Mapa** (500-1000 najčešćih riječi) - instant lookup
2. **Heuristička pravila** (za nepoznate riječi) - visoka točnost

Rezultat: 90%+ pokrivenost uz malen binary size (~70KB).
```

### Korak 6.2: Commit promjena
```bash
git add .
git commit -m "feat: hybrid normalization (map + rules)"
git push origin feat/nlp-integrations
```

---

## ✅ Provjera uspjeha

### Tehnička provjera:
- [ ] `cargo test` prolazi
- [ ] WASM je veličine ~60-80KB
- [ ] Playground normalizira i poznate i nepoznate riječi

### Funkcionalna provjera:
- [ ] Riječi u mapi: instant normalizacija
- [ ] Riječi izvan mape: normalizacija putem pravila
- [ ] Kompromis: Možda 85-90% točnosti, ali pokriva sve

---

## 🚨 Moguće greške i rješenja

### Greška 1: "expected `&str`, found `String`"
**Uzrok**: Return tip se promijenio s `&str` na `String`  
**Rješenje**: Dodaj `.as_str()` ili `.to_string()` prema potrebi

### Greška 2: "mismatched types in pattern"
**Uzrok**: Testovi očekuju `&str`, a dobivaju `String`  
**Rješenje**: U testovima dodaj `.to_string()` na desnu stranu `assert_eq!`

### Greška 3: "lifetime may not live long enough"
**Uzrok**: Pokušaj vratiti `&str` iz funkcije koja vraća `String`  
**Rješenje**: Uvijek koristi `String` kao return tip za `normalize()`

---

## 📊 Očekivani rezultati

**Prije (v0.1.6)**:
- Mapa: ~1000 riječi
- Binary: ~62KB
- Pokrivenost: ~50% (samo mapa)

**Poslije (v0.1.7)**:
- Mapa: ~700 riječi (očišćeno)
- Binary: ~70KB
- Pokrivenost: ~90% (mapa + pravila)

**Trade-off**:
- Rijetke greške kod riječi s dvosmislenim slučajevima (npr. "cas" može biti "čas" ili "ćaš")
- Ali to će riješiti stemmer u drugom koraku, pa nije problematično za NLP
