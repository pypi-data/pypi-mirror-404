use cro_stem::{CroStem, StemMode, normalizer};

fn main() {
    println!("--- Cro-Stem Logic Demo ---");
    let stemmer = CroStem::new(StemMode::Aggressive);

    let test_cases = vec![
        "zivot",   // Šišana latinica
        "cesalj",  // Šišana latinica
        "lepo",    // Ekavica
        "dite",    // Ikavica
        "kucu",    // Šišana latinica + padež
        "majci",   // Sibilarizacija
    ];

    println!("{:<15} | {:<15} | {:<15}", "Original", "Normalized", "Stemmed");
    println!("{:-<15}-|-{:-<15}-|-{:-<15}", "", "", "");

    for word in test_cases {
        let normalized = normalizer::normalize(word);
        let stemmed = stemmer.stem(word); // stem internally calls normalize
        
        println!("{:<15} | {:<15} | {:<15}", word, normalized, stemmed);
    }

    println!("\nTest 2: Rečenica s 'prljavim' inputom");
    let sentence = "Zivot je lep u maloj kuci.";
    let words: Vec<&str> = sentence.split_whitespace().collect();
    
    let processed: Vec<String> = words.iter()
        .map(|w| stemmer.stem(w.trim_matches(|c: char| !c.is_alphabetic())))
        .collect();

    println!("Original: {}", sentence);
    println!("Stemmed:  {}", processed.join(" "));
}
