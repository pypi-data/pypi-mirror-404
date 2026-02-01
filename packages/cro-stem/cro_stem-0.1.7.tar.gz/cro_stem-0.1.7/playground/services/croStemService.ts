import { StemMode, StemResult, ProcessingStats } from '../types';
import init, { stem_wasm, normalize_wasm } from '../cro_stem/cro_stem.js';

let wasmInitialized = false;

/**
 * Ensures the WASM module is initialized before use.
 */
const ensureWasm = async () => {
  if (!wasmInitialized) {
    try {
      await init();
      wasmInitialized = true;
      console.log('Cro-Stem WASM Initialized successfully');
    } catch (err) {
      console.error('Failed to initialize Cro-Stem WASM:', err);
    }
  }
};

/**
 * Batched processing of text.
 * Note: Since WASM init is async, the first call might be slightly slower or we should await it.
 * Real-time responsiveness is achieved by ensuring init is called.
 */
export const processTextBatch = async (text: string, mode: StemMode): Promise<{ results: StemResult[], stats: ProcessingStats }> => {
  await ensureWasm();

  const startTotal = performance.now();

  // Split by whitespace and punctuation, keeping meaningful words
  const rawWords = text.split(/[\s,.;:!?()"]+/).filter(w => w.length > 0);

  const results: StemResult[] = rawWords.map(word => {
    const startWord = performance.now();

    // The Rust WASM 'stem_wasm' now handles both normalization and stemming internally
    // but the API expects a mode string.
    const modeStr = mode === StemMode.AGGRESSIVE ? "Aggressive" : "Conservative";

    // In our new version, stem_wasm applies normalization BEFORE stemming.
    // However, to show the "Normalized" column in the UI, we might need a separate call
    // or just show the same if the stemmer doesn't distinguish.
    // Actually, Cro-Stem 0.1.6's stem_wasm returns the STEM.
    // To get the "Normalized" version separately, we'd need another export, 
    // but we can simulate it for the UI since the stemmer is so fast.

    // Call our NEW normalize_wasm to get the middle step for the UI
    const normalized = normalize_wasm(word);
    const stemmed = stem_wasm(word, modeStr);

    const endWord = performance.now();

    // Duration in Microseconds
    const durationUs = Math.floor((endWord - startWord) * 1000);

    return {
      original: word,
      normalized: normalized,
      stem: stemmed,
      executionTimeUs: Math.max(1, durationUs),
      isDirty: normalized.toLowerCase() !== word.toLowerCase()
    };
  });

  const endTotal = performance.now();
  const totalTimeUs = Math.floor((endTotal - startTotal) * 1000);

  return {
    results,
    stats: {
      totalTimeUs,
      wordCount: results.length,
      dirtyCount: results.filter(r => r.isDirty).length
    }
  };
};