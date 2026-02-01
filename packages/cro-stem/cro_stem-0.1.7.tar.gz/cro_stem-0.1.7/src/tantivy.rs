use tantivy_tokenizer_api::{Token, TokenFilter, TokenStream, Tokenizer};
use crate::{CroStem, StemMode};

/// A Tantivy `TokenFilter` that applies Croatian stemming to tokens.
#[derive(Clone)]
pub struct CroStemFilter {
    stemmer: CroStem,
}

impl CroStemFilter {
    /// Creates a new `CroStemFilter` with the given stemming mode.
    pub fn new(mode: StemMode) -> Self {
        Self {
            stemmer: CroStem::new(mode),
        }
    }
}

impl TokenFilter for CroStemFilter {
    type Tokenizer<T: Tokenizer> = CroStemTokenizer<T>;

    fn transform<T: Tokenizer>(self, tokenizer: T) -> Self::Tokenizer<T> {
        CroStemTokenizer {
            inner: tokenizer,
            filter: self,
        }
    }
}

/// A wrapper around a Tantivy `Tokenizer`.
#[derive(Clone)]
pub struct CroStemTokenizer<T: Tokenizer> {
    inner: T,
    filter: CroStemFilter,
}

impl<T: Tokenizer> Tokenizer for CroStemTokenizer<T> {
    type TokenStream<'a> = CroStemTokenStream<'a, T::TokenStream<'a>>;

    fn token_stream<'a>(&'a mut self, text: &'a str) -> Self::TokenStream<'a> {
        CroStemTokenStream {
            inner: self.inner.token_stream(text),
            filter: &self.filter,
        }
    }
}

/// A wrapper around a Tantivy `TokenStream` that applies stemming.
pub struct CroStemTokenStream<'a, T: TokenStream> {
    inner: T,
    filter: &'a CroStemFilter,
}

impl<'a, T: TokenStream> TokenStream for CroStemTokenStream<'a, T> {
    fn advance(&mut self) -> bool {
        if !self.inner.advance() {
            return false;
        }
        // Get the text first using an immutable borrow
        let stemmed = self.filter.stemmer.stem(&self.inner.token().text);
        // Then modify it using a mutable borrow
        self.inner.token_mut().text = stemmed;
        true
    }

    fn token(&self) -> &Token {
        self.inner.token()
    }

    fn token_mut(&mut self) -> &mut Token {
        self.inner.token_mut()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use tantivy_tokenizer_api::Tokenizer;
    use crate::StemMode;

    #[test]
    fn test_tantivy_integration() {
        let filter = CroStemFilter::new(StemMode::Aggressive);
        let mut tokenizer = filter.transform(tantivy_tokenizer_api::SimpleTokenizer::default());
        
        // Test "majkama" -> "majk"
        let mut stream = tokenizer.token_stream("majkama");
        assert!(stream.advance());
        assert_eq!(stream.token().text, "majk");
    }

    #[test]
    fn test_tantivy_normalization() {
        let filter = CroStemFilter::new(StemMode::Aggressive);
        let mut tokenizer = filter.transform(tantivy_tokenizer_api::SimpleTokenizer::default());
        
        // Test "zivot" -> "život" -> "život" (stemming doesn't change it further)
        let mut stream = tokenizer.token_stream("zivot");
        assert!(stream.advance());
        assert_eq!(stream.token().text, "život");
    }
}
