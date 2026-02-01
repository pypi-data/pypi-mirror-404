use cro_stem::{CroStem, StemMode};
use serde_json::Value;
use std::fs::File;
use std::io::{BufReader, Write};
use std::collections::HashMap;

#[test]
fn test_corpus_accuracy_10k() {
    let path = "tests/test_data/corpus_10k.json";
    let file = File::open(path).expect("Failed to open corpus_10k.json. Make sure it's in cro_stem/tests/test_data/ folder.");
    let reader = BufReader::new(file);
    let data: Value = serde_json::from_reader(reader).expect("Failed to parse JSON");
    
    let words = data.get("test_corpus")
        .or_else(|| data.get("words"))
        .expect("Could not find 'test_corpus' or 'words' key")
        .as_array()
        .expect("Corpus data is not an array");

    println!("📊 Total words to test: {}", words.len());

    let stemmer_agg = CroStem::new(StemMode::Aggressive);
    let stemmer_cons = CroStem::new(StemMode::Conservative);

    let mut agg_correct = 0;
    let mut cons_correct = 0;
    
    // Statistics for Aggressive Mode
    let mut agg_failures: Vec<String> = Vec::new();
    let mut agg_by_cat: HashMap<String, (i32, i32)> = HashMap::new(); // (correct, total)

    // Statistics for Conservative Mode
    let mut cons_failures: Vec<String> = Vec::new();
    let mut cons_by_cat: HashMap<String, (i32, i32)> = HashMap::new();

    for word_obj in words {
        let original = word_obj["original"].as_str().unwrap();
        let expected = word_obj["expected_stem"].as_str().unwrap();
        let category = word_obj.get("category").and_then(|v| v.as_str()).unwrap_or("unknown");

        // Aggressive Test
        let actual_agg = stemmer_agg.stem(original);
        let agg_entry = agg_by_cat.entry(category.to_string()).or_insert((0, 0));
        agg_entry.1 += 1;
        
        if actual_agg == expected {
            agg_correct += 1;
            agg_entry.0 += 1;
        } else {
            agg_failures.push(format!("AGG: '{}' -> '{}' (expected '{}') [{}]", original, actual_agg, expected, category));
        }

        // Conservative Test
        let actual_cons = stemmer_cons.stem(original);
        let cons_entry = cons_by_cat.entry(category.to_string()).or_insert((0, 0));
        cons_entry.1 += 1;

        if actual_cons == expected {
            cons_correct += 1;
            cons_entry.0 += 1;
        } else {
            cons_failures.push(format!("CONS: '{}' -> '{}' (expected '{}') [{}]", original, actual_cons, expected, category));
        }
    }

    println!("\n=== RESULTS (10k Corpus) ===");
    println!("Aggressive Accuracy: {}/{} ({:.2}%)", agg_correct, words.len(), (agg_correct as f64 / words.len() as f64) * 100.0);
    println!("Conservative Accuracy: {}/{} ({:.2}%)", cons_correct, words.len(), (cons_correct as f64 / words.len() as f64) * 100.0);

    println!("\n=== CATEGORY BREAKDOWN (Aggressive) ===");
    let mut sorted_agg_cats: Vec<_> = agg_by_cat.iter().collect();
    sorted_agg_cats.sort_by(|a, b| a.0.cmp(b.0));
    for (cat, (corr, tot)) in sorted_agg_cats {
        println!("{:<12}: {}/{} ({:.1}%)", cat, corr, tot, (*corr as f64 / *tot as f64) * 100.0);
    }
    
    // Save failures to file for further analysis
    let mut f_log = File::create("failures_10k.txt").expect("Could not create failures_10k.txt");
    writeln!(f_log, "=== AGGRESSIVE FAILURES ===").unwrap();
    for f in &agg_failures {
        writeln!(f_log, "{}", f).unwrap();
    }
    writeln!(f_log, "\n=== CONSERVATIVE FAILURES ===").unwrap();
    for f in &cons_failures {
        writeln!(f_log, "{}", f).unwrap();
    }
    
    println!("\n✅ Failures saved to 'failures_10k.txt'");
}
