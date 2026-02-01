use tantivy::collector::TopDocs;
use tantivy::query::QueryParser;
use tantivy::schema::*;
use tantivy::{Index, ReloadPolicy};
use tantivy::tokenizer::*;
use cro_stem::{CroStemFilter, StemMode};

fn main() -> tantivy::Result<()> {
    println!("--- Cro-Stem + Tantivy Search Demo ---");

    // 1. Definiraj shemu indeksa
    let mut schema_builder = Schema::builder();
    
    // Registriraj naš custom analyzer (CroStem)
    let text_field_indexing = TextFieldIndexing::default()
        .set_tokenizer("croatian") // Koristimo ime koje ćemo registrirati
        .set_index_option(IndexRecordOption::WithFreqsAndPositions);
    let text_options = TextOptions::default().set_indexing_options(text_field_indexing).set_stored();

    let title = schema_builder.add_text_field("title", text_options.clone());
    let body = schema_builder.add_text_field("body", text_options);
    let schema = schema_builder.build();

    // 2. Kreiraj indeks u memoriji
    let index = Index::create_in_ram(schema.clone());

    // 3. Registriraj naš CroStem analizator
    let tokenizer = TextAnalyzer::builder(SimpleTokenizer::default())
        .filter(LowerCaser)
        // OVO JE KLJUČNO: Dodajemo naš stemmer filter
        .filter(CroStemFilter::new(StemMode::Aggressive))
        .build();

    index.tokenizers().register("croatian", tokenizer);

    // 4. Ubaci dokumente (simuliramo loš input sa "šišanom" latinicom)
    let mut index_writer = index.writer(50_000_000)?;
    
    index_writer.add_document(doc!(
        title => "Zivot na selu", // Namjerno "Zivot" (bez kvačice)
        body => "Zivot je lijep kada imas kucu i macku." // "kucu", "macku"
    ))?;

    index_writer.add_document(doc!(
        title => "Programiranje u Rustu",
        body => "Rust je brz i siguran jezik za sistemsko programiranje."
    ))?;

    index_writer.add_document(doc!(
        title => "Recept za kruh",
        body => "Brasno, voda i sol su sve sto ti treba." // "Brasno", "sto"
    ))?;

    index_writer.commit()?;

    // 5. Pretraživanje
    let reader = index.reader()?;
    let searcher = reader.searcher();
    let query_parser = QueryParser::for_index(&index, vec![title, body]);

    // Test 1: Tražimo "život" (s kvačicom), a u tekstu piše "Zivot"
    println!("\nTest 1: Tražim 'život' (s kvačicom) u dokumentima gdje piše 'Zivot'");
    let query = query_parser.parse_query("život")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;
    
    for (_score, doc_address) in top_docs {
        let retrieved_doc = searcher.doc(doc_address)?;
        println!("  FOUND: {}", retrieved_doc.get_first(title).unwrap().as_text().unwrap());
    }

    // Test 2: Tražimo "kuće" (množina s kvačicom), a u tekstu piše "kucu"
    println!("\nTest 2: Tražim 'kuće' (množina) -> očekujem pogodak za 'kucu' (akuzativ bez kvačice)");
    let query = query_parser.parse_query("kuće")?;
    let top_docs = searcher.search(&query, &TopDocs::with_limit(10))?;

    for (_score, doc_address) in top_docs {
        let retrieved_doc = searcher.doc(doc_address)?;
        println!("  FOUND: {}", retrieved_doc.get_first(title).unwrap().as_text().unwrap());
    }

    Ok(())
}
