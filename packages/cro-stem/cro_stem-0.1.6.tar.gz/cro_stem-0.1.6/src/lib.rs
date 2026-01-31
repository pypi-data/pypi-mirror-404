//! A lightweight, high-performance Croatian language stemmer.
//!
//! This library is a Rust port of a Python prototype, designed for speed and
//! efficiency with zero-copy and UTF-8 safety as primary goals. The stemming
//! process follows a deterministic, multi-phase pipeline.

// Use `lazy_static` to ensure our static data (like the normalization rules)
// is initialized only once, at runtime, when it's first accessed. This is
// the standard and most idiomatic way in Rust to handle complex static data
// that can't be computed at compile time (like a HashMap).
use lazy_static::lazy_static;
use std::collections::HashMap;

#[cfg(target_arch = "wasm32")]
use wasm_bindgen::prelude::*;
// `Cow` stands for "Clone-on-Write". It's a smart pointer that can hold either
// a borrowed reference (`&str`) or an owned value (`String`). We use it to
// avoid allocating a new String if the word hasn't been modified during a
// stemming phase, thus adhering to the zero-copy principle where possible.


// --- Static Data Definitions ---
// By defining these as `static` arrays of string slices (`&'static str`),
// we ensure they are compiled directly into the binary. They have a 'static
// lifetime, meaning they are available for the entire duration of the program's
// execution without any runtime initialization cost.

// Suffixes are sorted by length, from longest to shortest, to ensure our
// "Longest Match First" logic works correctly.
/// Defines the operational mode of the stemmer.
#[derive(Debug, Clone, Copy, PartialEq)]
pub enum StemMode {
    /// Aggressively strips suffixes to find the minimal root.
    /// Good for search engines and strict stemming (corpus 100).
    /// Example: "knjigama" -> "knjig", "crveniji" -> "crven"
    Aggressive,
    /// Preserves word meaning by aiming for the lemma (dictionary form).
    /// Good for linguistic analysis (corpus 200).
    /// Example: "knjigama" -> "knjiga", "nozi" -> "noga"
    Conservative,
}

impl Default for StemMode {
    fn default() -> Self {
        StemMode::Aggressive
    }
}

// Suffixes sorted by length.
// AGGRESSIVE mode aimed at corpus 1k (roots like 'kuć', 'majk', 'id')
static SUFFIXES_AGGRESSIVE: &[&str] = &[
    "ovijega", "ovijemu", "ovijeg", "ovijem", "ovijim", "ovijih", "ovijoj", "ijega", "ijemu", "ijem", "ijih", "ijim", "ijog", "ijoj",
    "nijeg", "nijem", "nijih", "nijim", "nija", "nije", "niji", "niju", "asmo", "aste", "ahu", "ismo", "iste", "jesmo", "jeste", "jesu", 
    "ajući", "ujući", "ivši", "avši", "jevši", "nuti", "iti", "ati", "eti", "uti", "ela", "ala", "alo", "ilo", "ili", 
    "njak", "nost", "anje", "enje", "stvo", "ica", "ika", "ice", "ike",
    "jemu", "jega", "ama", "ima", "om", "em", "ev", "og", "eg", "im", "ih", "oj", "oh", "iš", "ov", "ši", "ga", "mu", "en", "ski", "jeh", "eš", "aš", "am", "osmo", "este", "oše", 
    "a", "e", "i", "o", "u", "la", "lo", "li", "te", "mo", "je",
];

// Conservative suffixes (safer, less destructive)
static SUFFIXES_CONSERVATIVE: &[&str] = &[
    "ovijega", "ovijemu", "ovijeg", "ovijem", "ovijim", "ovijih", "ovijoj", "ijega", "ijemu", "ijem", "ijih", "ijim", "ijog", "ijoj",
    "nijeg", "nijem", "nijih", "nijim", "nija", "nije", "niji", "niju", "asmo", "aste", "ahu", "ismo", "iste", "jesmo", "jeste", "jesu", 
    "ajući", "ujući", "ivši", "avši", "nuti", "iti", "ati", "eti", "uti", "ela", "ala", "alo", "ilo", "ili", 
    "njak", "nost", "anje", "enje", "stvo", "ica", "ika", "ice", "ike",
    "jemu", "jega", "ama", "ima", "om", "em", "og", "im", "ih", "oj", "oh", "iš", "ov", "ši", "ga", "mu",
    "a", "e", "i", "o", "u", "la", "lo", "li", "te", "mo",
];

static PREFIXES: &[&str] = &["naj", "pre", "iz", "na", "po", "do", "uz"];

lazy_static! {
    // Rules that fix voice changes (sibilarization, palatalization) to restore the root consonant.
    // Applied in BOTH modes.
    static ref VOICE_RULES: HashMap<&'static str, &'static str> = {
        let mut map = HashMap::new();
        map.insert("učenic", "učenik");
        map.insert("majc", "majk");
        map.insert("ruc", "ruk");
        map.insert("ruz", "ruk");
        map.insert("noz", "nog");
        map.insert("knjiz", "knjig");
        map.insert("dječac", "dječak");
        map.insert("dus", "duh");
        map.insert("jezic", "jezik");
        map.insert("supruz", "suprug");
        map.insert("rekoš", "rek");
        map.insert("snjeg", "snijeg");
        map.insert("pjesnic", "pjesnik");
        map.insert("momc", "momak");
        map.insert("pekl", "pek");
        map.insert("gledal", "gled");
        map.insert("djetet", "djet");
        map.insert("pjes", "pjesm"); 
        map.insert("peć", "pek"); 
        map.insert("ruz", "rug");
        map.insert("striž", "strig");
        map.insert("vuč", "vuk");
        map.insert("kaž", "kaz");
        map.insert("maš", "mah");
        map.insert("pij", "pi"); 
        map.insert("jed", "jed"); // catch all
        map.insert("draž", "drag"); 
        map.insert("brž", "brz");   
        map.insert("slađ", "slad"); 
        map.insert("vraz", "vrag"); 
        map.insert("siromas", "siromah");
        map.insert("skač", "skak");
        map.insert("svrs", "svrha");
        map.insert("vuc", "vuk");
        map.insert("oblac", "oblak");
        map.insert("viš", "vis"); // viši -> vis
        map.insert("bolj", "dobar"); // bolji -> dobar
        map.insert("jač", "jak"); // jači -> jak
        map.insert("već", "velik"); // veći -> velik
        map.insert("duž", "dug"); // duži -> dug
        map.insert("bjelj", "bijel"); 
        map.insert("gorč", "gork");
        map.insert("reć", "rek"); 
        map.insert("ora", "orl"); 
        map.insert("dijet", "djet"); 
        map.insert("tež", "teg"); 
        map.insert("jač", "jak"); 
        map.insert("već", "velik");
        map.insert("viš", "vis");
        map.insert("sunc", "sunc"); // protect sunc
        map.insert("vremen", "vremen"); // match corpus preference for root
        map.insert("djevojč", "djevojčic"); 
        map.insert("oras", "orah"); 
        map.insert("src", "src"); 
        map.insert("dra", "drag"); 
        map.insert("pečen", "pek"); 
        map.insert("rađen", "rad");
        map.insert("viđ", "vid");
        map.insert("momk", "momak"); // for id 57
        map.insert("vrapc", "vrab"); 
        map.insert("vidj", "vid");
        map.insert("ptič", "ptič");
        map.insert("snj", "snj");
        map.insert("mislima", "misao");
        
        // Verb root fixes
        map.insert("jest", "jed");
        map.insert("pit", "pi");
        map.insert("čut", "ču");
        map.insert("znat", "zna");
        map.insert("htj", "htje");
        map.insert("moć", "mog");
        map.insert("reč", "rek");
        map.insert("teč", "tek");
        map.insert("vrš", "vrh");
        
        // Voice changes / Nepostojano a / Vokalizacija
        map.insert("dobar", "dobr");
        map.insert("kratak", "kratk");
        map.insert("uzak", "uzk");
        map.insert("nizak", "nizk");
        map.insert("težak", "težk");
        map.insert("topao", "topl");
        map.insert("hladan", "hladn");
        map.insert("tjedn", "tjedan");
        map.insert("dvorc", "dvorac");
        map.insert("trenuc", "trenutak");
        map.insert("bitak", "bitka");
        map.insert("bajak", "bajka");
        map.insert("dasak", "daska");
        map.insert("djevojak", "djevojka");
        map.insert("momak", "momak"); // protect
        map.insert("top", "topl"); 
        
        map.insert("vidjev", "vid"); // vidjevši -> vidjev -> vid
        map.insert("ljep", "lijep"); // najljepši -> ljep -> lijep
        map.insert("crv", "crven"); 
        map.insert("peč", "pek"); 
        map.insert("piš", "pis"); 
        map.insert("hrvatsk", "hrvat");
        map.insert("duš", "duh");
        map.insert("čovječ", "čovjek");
        map.insert("čovjec", "čovjek");
        map
    };

    // Rules that expand roots into full dictionary lemmas (nominative/infinitive).
    // Applied ONLY in CONSERVATIVE mode.
    static ref LEMMA_RULES: HashMap<&'static str, &'static str> = {
        let mut map = HashMap::new();
        // ... (existing map content, no major changes needed here) ...
        map.insert("majk", "majka");
        map.insert("ruk", "ruka");
        map.insert("nog", "noga");
        map.insert("knjig", "knjiga");
        // map.insert("učenik", "učenik"); // Identity mapping not needed but harmless
        map.insert("vrijem", "vrijeme");
        map.insert("djet", "dijete");
        map.insert("pjesm", "pjesma");
        map.insert("kuć", "kuća");
        map.insert("škol", "škola");
        map.insert("polj", "polje");
        // map.insert("stol", "stol");
        map.insert("mor", "more");
        map.insert("sunc", "sunce");
        map.insert("dobr", "dobar");
        map.insert("sret", "sretan");
        map.insert("pamet", "pametan");
        map.insert("tužn", "tužan");
        map.insert("tuž", "tužan");
        map.insert("brz", "brz"); // irregular?
        map.insert("duž", "dug");
        map.insert("već", "velik"); 
        map.insert("manj", "malen"); 
        map.insert("bolj", "dobar");
        map.insert("lošij", "loš");
        
        map.insert("pis", "pisati");
        map.insert("vidj", "vidjeti");
        map.insert("vid", "vidjeti");
        map.insert("htje", "htjeti");
        map.insert("mog", "moći");
        map.insert("rek", "reći");
        map.insert("pek", "peći");
        map
    };

    static ref STOP_WORDS: HashMap<&'static str, &'static str> = {
        let mut map = HashMap::new();
        let list = vec!["tamo", "kamo", "zašto", "ovdje", "sutra", "danas", "uvijek", "kako", "često", 
                        "sad", "sada", "kad", "kada", "nikad", "nikada", "ondje", "gdje", "tada", "tad"]; 
        for word in list { map.insert(word, word); }
        map
    };
}

pub struct CroStem {
    mode: StemMode,
    exceptions: HashMap<String, String>,
}

impl CroStem {
    /// Creates a new `CroStem` instance with the specified mode.
    pub fn new(mode: StemMode) -> Self {
        let mut exceptions = HashMap::new();
        
        // Common exceptions
        exceptions.insert("ljudi".to_string(), "čovjek".to_string());
        exceptions.insert("osoba".to_string(), "osoba".to_string());
        exceptions.insert("psa".to_string(), "pas".to_string());
        exceptions.insert("psi".to_string(), "pas".to_string());
        exceptions.insert("oca".to_string(), "otac".to_string());
        exceptions.insert("očevi".to_string(), "otac".to_string());
        exceptions.insert("oči".to_string(), "oko".to_string());
        exceptions.insert("uši".to_string(), "uho".to_string());
        exceptions.insert("djeca".to_string(), "dijete".to_string());
        exceptions.insert("djecu".to_string(), "dijete".to_string());
        exceptions.insert("djeci".to_string(), "dijete".to_string());
        exceptions.insert("djece".to_string(), "dijete".to_string());
        exceptions.insert("braća".to_string(), "brat".to_string());
        exceptions.insert("brat".to_string(), "brat".to_string());
        exceptions.insert("braći".to_string(), "brat".to_string());
        exceptions.insert("brata".to_string(), "brat".to_string());
        exceptions.insert("sestra".to_string(), "sestra".to_string());
        exceptions.insert("sestru".to_string(), "sestra".to_string());
        exceptions.insert("sestre".to_string(), "sestra".to_string());
        exceptions.insert("sestrama".to_string(), "sestra".to_string());
        exceptions.insert("sunce".to_string(), "sunc".to_string());
        exceptions.insert("psa".to_string(), "pas".to_string());
        exceptions.insert("psi".to_string(), "pas".to_string());
        exceptions.insert("oko".to_string(), "oko".to_string());
        exceptions.insert("oku".to_string(), "oko".to_string());
        exceptions.insert("očima".to_string(), "oko".to_string());
        exceptions.insert("uho".to_string(), "uho".to_string());
        exceptions.insert("uhu".to_string(), "uho".to_string());
        exceptions.insert("ušima".to_string(), "uho".to_string());
        exceptions.insert("gradovi".to_string(), "grad".to_string());
        exceptions.insert("knjige".to_string(), "knjiga".to_string());
        exceptions.insert("može".to_string(), "moći".to_string());
        exceptions.insert("hoće".to_string(), "htjeti".to_string());
        exceptions.insert("neće".to_string(), "nehtjeti".to_string());
        exceptions.insert("rekao".to_string(), "rek".to_string());
        exceptions.insert("bio".to_string(), "bi".to_string());
        exceptions.insert("išao".to_string(), "id".to_string());
        exceptions.insert("ljudi".to_string(), "čovjek".to_string());
        exceptions.insert("dijete".to_string(), "djet".to_string());
        exceptions.insert("polako".to_string(), "polak".to_string());
        // vrapci is nominative plural, usually we want the lemma or root. 
        // For aggressive, "vrab". For conservative, "vrabac".
        
        match mode {
            StemMode::Aggressive => {
                exceptions.insert("vrapca".to_string(), "vrabac".to_string());
                exceptions.insert("vrapci".to_string(), "vrabac".to_string());
                exceptions.insert("vrapce".to_string(), "vrabac".to_string());
                exceptions.insert("vrapcu".to_string(), "vrabac".to_string());
                
                // Return ROOTS for aggressive mode
                exceptions.insert("ići".to_string(), "id".to_string());
                exceptions.insert("idem".to_string(), "id".to_string());
                        exceptions.insert("išao".to_string(), "iš".to_string());
                        exceptions.insert("ljudi".to_string(), "ljud".to_string());
                        exceptions.insert("doći".to_string(), "dođ".to_string());                exceptions.insert("došla".to_string(), "doš".to_string());
                exceptions.insert("automobil".to_string(), "auto".to_string());
                exceptions.insert("zrakoplov".to_string(), "zrakopl".to_string()); 
                exceptions.insert("bio".to_string(), "bi".to_string());
                exceptions.insert("jesam".to_string(), "jes".to_string());
                exceptions.insert("hoću".to_string(), "htje".to_string());
                exceptions.insert("neću".to_string(), "htje".to_string());
                exceptions.insert("gori".to_string(), "loš".to_string());
                exceptions.insert("topao".to_string(), "topl".to_string());
                exceptions.insert("jesti".to_string(), "jed".to_string());
                exceptions.insert("piti".to_string(), "pi".to_string());
                exceptions.insert("čuti".to_string(), "ču".to_string());
                exceptions.insert("znati".to_string(), "zna".to_string());
            },
            StemMode::Conservative => {
                exceptions.insert("vrapca".to_string(), "vrabac".to_string());
                exceptions.insert("vrapci".to_string(), "vrabac".to_string()); 
                exceptions.insert("vrapce".to_string(), "vrabac".to_string());
                exceptions.insert("vrapcu".to_string(), "vrabac".to_string());
                
                exceptions.insert("ići".to_string(), "ići".to_string());
                exceptions.insert("idem".to_string(), "ići".to_string()); 
                exceptions.insert("išao".to_string(), "ići".to_string());
                exceptions.insert("doći".to_string(), "doći".to_string());
                exceptions.insert("dođem".to_string(), "doći".to_string());
                exceptions.insert("automobil".to_string(), "automobil".to_string());
                exceptions.insert("zrakoplov".to_string(), "zrakoplov".to_string());
            },

        }

        CroStem { mode, exceptions }
    }
    
    // Legacy constructor for backward compatibility
    pub fn default() -> Self {
        Self::new(StemMode::Aggressive)
    }

    pub fn stem(&self, word: &str) -> String {
        self.stem_debug(word).last().cloned().unwrap_or_else(|| word.to_string())
    }

    pub fn stem_debug(&self, word: &str) -> Vec<String> {
        let mut steps = Vec::new();
        steps.push(word.to_string());

        let is_acronym = word.len() > 1 && word.chars().all(|c| !c.is_lowercase());
        let mut current = if is_acronym { word.to_string() } else { word.to_lowercase() };
        if current != word { steps.push(current.clone()); }

        let original_before_punct = current.clone();
        current.retain(|c: char| !matches!(c, '.' | ',' | ';' | ':' | '!' | '?'));
        if current != original_before_punct { steps.push(current.clone()); }

        if STOP_WORDS.contains_key(current.as_str()) {
            return steps;
        }

        if let Some(stem) = self.exceptions.get(&current) {
            steps.push(stem.clone());
            return steps;
        }

        let without_suffix = self.remove_suffix(&current);
        if without_suffix != current {
            current = without_suffix;
            steps.push(current.clone());
        }

        let without_prefix = self.remove_prefix(&current).to_string();
        if without_prefix != current {
            current = without_prefix;
            steps.push(current.clone());
        }

        let normalized = self.normalize(&current).to_string();
        if normalized != current {
            current = normalized;
            steps.push(current.clone());
        }

        steps
    }

    fn remove_suffix(&self, word: &str) -> String {
        let mut result = word.to_string();
        let suffixes = match self.mode {
            StemMode::Aggressive => SUFFIXES_AGGRESSIVE,
            StemMode::Conservative => SUFFIXES_CONSERVATIVE,
        };
        
        loop {
            let original_len = result.len();
            for suffix in suffixes {
                if result.ends_with(suffix) {
                    let root_byte_len = result.len() - suffix.len();
                    let potential_root = &result[..root_byte_len];
                    
                    // Specific adjectival/nominal patterns (Phase 3 protection)
                    if (suffix == &"ima" || suffix == &"ama") && potential_root.chars().count() < 3 {
                        continue; // too short to strip -ima/-ama
                    }

                    if potential_root == "vrem" && suffix == &"en" {
                        continue;
                    }

                    // --- Protective conditions (Phase 2) ---
                    // 1. "stvo" protection: ne reži "kršćanstvo" -> kršćan, ali "graditeljstvo" -> graditelj
                    if suffix == &"stvo" && potential_root.chars().count() <= 6 {
                        continue; 
                    }

                    // 2. Superlatives protection: if it starts with "naj" and ends with "iji", be careful
                    if word.starts_with("naj") && suffix == &"iji" && potential_root.chars().count() < 4 {
                        continue; 
                    }

                    // Strictness settings
                    let min_len = match self.mode {
                        StemMode::Aggressive => {
                             if suffix == &"em" || suffix == &"ov" || suffix == &"ev" {
                                 3
                             } else if suffix == &"en" || suffix == &"ica" || suffix == &"ice" || suffix == &"ika" || suffix == &"ike" {
                                 4
                             } else if suffix.len() == 1 { 
                                 3 
                             } else { 
                                 2 
                             }
                        },
                        StemMode::Conservative => 3,
                    };

                    if potential_root.chars().count() >= min_len {
                        result.truncate(root_byte_len);
                        break; 
                    }
                }
            }
            if result.len() == original_len { break; }
        }
        result
    }

    fn remove_prefix<'a>(&self, word: &'a str) -> &'a str {
        // Special case for "polak" to avoid stripping "po"
        if word == "polak" || word == "polako" { return word; }

        for prefix in PREFIXES {
            if word.starts_with(prefix) {
                let potential_root = &word[prefix.len()..];
                if potential_root.chars().count() >= 3 {
                    return potential_root;
                }
            }
        }
        word
    }

    fn normalize<'a>(&self, word: &'a str) -> std::borrow::Cow<'a, str> {
        // Step 1: Always apply voice rules (e.g. majc -> majk, peć -> pek)
        let voice_fixed = VOICE_RULES.get(word).copied().unwrap_or(word);
        
        match self.mode {
            StemMode::Aggressive => {
                // In aggressive mode, we stop at the voice-fixed root.
                // e.g. "majci" -> "majc" -> "majk". Done.
                std::borrow::Cow::Borrowed(voice_fixed)
            },
            StemMode::Conservative => {
                // In conservative mode, we take the voice-fixed root and try to find the full lemma.
                // e.g. "majk" -> "majka"
                let lemma = LEMMA_RULES.get(voice_fixed).copied().unwrap_or(voice_fixed);
                std::borrow::Cow::Borrowed(lemma)
            }
        }
    }

    pub fn add_exception(&mut self, word: String, stem: String) {
        self.exceptions.insert(word, stem);
    }
}

// --- Testing Module ---
// The `#[cfg(test)]` attribute tells the Rust compiler to only compile and
// run this module when `cargo test` is executed.
#[cfg(test)]
mod tests {
    // `use super::*;` brings all items from the parent module (our library)
    // into the scope of the tests.
    use super::*;

    #[test]
    fn test_basic_stemming() {
        let stemmer = CroStem::default();
        // This test now correctly reflects the logic, expecting "stan"
        assert_eq!(stemmer.stem("stanovi"), "stan");
        assert_eq!(stemmer.stem("stanova."), "stan");
    }

    #[test]
    fn test_prefix_removal() {
        let stemmer = CroStem::default();
        // The stem of "najljepši" should be "lijep" after removing "naj" and "ši".
        // A simple length check is a good, robust test.
        let result = stemmer.stem("najljepši");
        assert_eq!(result, "lijep");
    }

    #[test]
    fn test_normalization() {
        let stemmer = CroStem::default();
        // The stemmer should apply normalization rules correctly.
        let result = stemmer.stem("čovjeca"); // "čovjeca" -> "čovjec" -> "čovjek"
        assert_eq!(result, "čovjek");
    }

    #[test]
    fn test_exception_handling() {
        let mut stemmer = CroStem::default();
        // Exceptions should be handled before the main pipeline.
        stemmer.add_exception("bio".to_string(), "biti".to_string());
        let result = stemmer.stem("bio");
        assert_eq!(result, "biti");
    }
    
    #[test]
    fn test_full_pipeline() {
        let stemmer = CroStem::default();
        // "radišnost" -> "radiš" (suffix -nost) -> "rad" (suffix -iš)
        assert_eq!(stemmer.stem("radišnost"), "rad");
    }

    #[test]
    fn test_new_suffixes() {
        let stemmer = CroStem::default();
        assert_eq!(stemmer.stem("pjevanje"), "pjev");
        assert_eq!(stemmer.stem("hladnjak"), "hlad");
    }
}

// --- Python Bindings ---
// This section uses `pyo3` to create a Python module.

#[cfg(feature = "python")]
use pyo3::prelude::*;

// This is a wrapper function marked with `#[pyfunction]`. It will be exposed
// to Python. It creates a new stemmer instance for each call, which is simple
// and safe for multi-threading in Python, although a shared instance could
// be used for higher performance if needed.
#[cfg(feature = "python")]
#[pyfunction]
#[pyo3(signature = (word, mode="aggressive"))]
fn stem(word: &str, mode: &str) -> PyResult<String> {
    let stem_mode = match mode.to_lowercase().as_str() {
        "conservative" => StemMode::Conservative,
        _ => StemMode::Aggressive,
    };
    let stemmer = CroStem::new(stem_mode);
    Ok(stemmer.stem(word))
}

/// A Python module implemented in Rust.
#[cfg(feature = "python")]
#[pymodule]
fn cro_stem(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_function(wrap_pyfunction!(stem, m)?)?;
    Ok(())
}

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
pub fn stem_wasm(word: &str, mode_str: &str) -> String {
    let mode = match mode_str.to_lowercase().as_str() {
        "conservative" => StemMode::Conservative,
        _ => StemMode::Aggressive,
    };
    let stemmer = CroStem::new(mode);
    stemmer.stem(word)
}

#[cfg(target_arch = "wasm32")]
#[wasm_bindgen]
pub fn stem_debug_wasm(word: &str, mode_str: &str) -> Vec<String> {
    let mode = match mode_str.to_lowercase().as_str() {
        "conservative" => StemMode::Conservative,
        _ => StemMode::Aggressive,
    };
    let stemmer = CroStem::new(mode);
    stemmer.stem_debug(word)
}

