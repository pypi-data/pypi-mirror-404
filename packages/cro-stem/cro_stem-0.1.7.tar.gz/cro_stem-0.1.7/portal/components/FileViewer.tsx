
import React, { useState } from 'react';
import { Copy, Check, FileCode, Package, FileJson, Cpu } from 'lucide-react';

const FILES = [
  {
    id: 'cargo',
    name: 'Cargo.toml',
    icon: Package,
    language: 'toml',
    content: `[package]
name = "cro_stem"
version = "0.1.4"
edition = "2021"
authors = ["Denis Sakač <sdenis.vr@gmail.com>"]
description = "A lightning-fast, zero-dependency Croatian stemming library written in Rust."
license = "AGPL-3.0"
repository = "https://github.com/Ja1Denis/Cro-Stem"

[dependencies]
lazy_static = "1.4.0"
wasm-bindgen = "0.2"

[profile.release]
opt-level = "z"  # Optimize for size.
lto = true         # Enable Link-Time Optimization.
codegen-units = 1  # Reduce parallelism to allow for better optimization.
panic = "abort"    # Abort on panic for smaller binary.
strip = true       # Strip symbols from the binary.`
  },
  {
    id: 'wasm_rs',
    name: 'src/wasm.rs',
    icon: FileCode,
    language: 'rust',
    content: `use wasm_bindgen::prelude::*;
use crate::CroStem; // Pretpostavljamo da je ovo tvoj glavni struct

#[wasm_bindgen]
pub fn init_panic_hook() {
    // Omogućuje bolje error poruke u browser konzoli
    console_error_panic_hook::set_once();
}

#[wasm_bindgen]
pub fn stem(word: &str, is_aggressive: bool) -> String {
    let stemmer = if is_aggressive {
        CroStem::aggressive()
    } else {
        CroStem::conservative()
    };
    stemmer.stem(word)
}

#[wasm_bindgen]
pub fn stem_batch(text: &str, is_aggressive: bool) -> JsValue {
    let stemmer = if is_aggressive {
        CroStem::aggressive()
    } else {
        CroStem::conservative()
    };

    let results: Vec<String> = text
        .split_whitespace()
        .map(|w| stemmer.stem(w))
        .collect();

    serde_wasm_bindgen::to_value(&results).unwrap_or(JsValue::NULL)
}`
  },
  {
    id: 'lib_rs',
    name: 'src/lib.rs',
    icon: FileCode,
    language: 'rust',
    content: `use lazy_static::lazy_static;
use std::collections::HashMap;
use wasm_bindgen::prelude::*;

#[wasm_bindgen]
pub fn stem_wasm(word: &str, mode_str: &str) -> String {
    let mode = match mode_str.to_lowercase().as_str() {
        "conservative" => StemMode::Conservative,
        _ => StemMode::Aggressive,
    };
    let stemmer = CroStem::new(mode);
    stemmer.stem(word)
}

pub struct CroStem {
    mode: StemMode,
    exceptions: HashMap<String, String>,
}

impl CroStem {
    pub fn new(mode: StemMode) -> Self {
        // ... initialization ...
        Self { mode, exceptions: HashMap::new() }
    }

    pub fn stem(&self, word: &str) -> String {
        // Multi-phase stemming pipeline
        // 1. Sanitize & Normalization
        // 2. Suffix stripping (Longest Match First)
        // 3. Prefix removal (naj-, pre-, iz-...)
        // 4. Voice correction (sibilarizacija/jotacija)
        word.to_string() 
    }
}`
  }
];

const FileViewer: React.FC = () => {
  const [activeFile, setActiveFile] = useState(FILES[0]);
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(activeFile.content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="flex flex-col lg:flex-row gap-6 animate-in slide-in-from-left-4 duration-500">
      <div className="lg:w-64 space-y-1">
        {FILES.map(file => (
          <button
            key={file.id}
            onClick={() => setActiveFile(file)}
            className={`w-full flex items-center space-x-3 px-4 py-3 text-sm rounded-xl transition-all ${activeFile.id === file.id ? 'bg-[#21262d] text-[#58a6ff] border border-[#30363d] shadow-lg' : 'text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#161b22]'}`}
          >
            <file.icon className="w-4 h-4" />
            <span className="font-medium">{file.name}</span>
          </button>
        ))}

        <div className="mt-8 p-4 bg-[#238636]/10 border border-[#238636]/20 rounded-xl">
          <div className="flex items-center space-x-2 text-[#3fb950] mb-2 font-bold text-xs uppercase tracking-wider">
            <Cpu className="w-3 h-3" />
            <span>WASM Ready</span>
          </div>
          <p className="text-[10px] text-[#8b949e] leading-relaxed">
            Kopiraj ove datoteke u svoj projekt i pokreni <code>wasm-pack build</code> za generiranje JS paketa.
          </p>
        </div>
      </div>

      <div className="flex-grow bg-[#161b22] border border-[#30363d] rounded-2xl overflow-hidden flex flex-col min-h-[500px] shadow-2xl">
        <div className="px-6 py-3 bg-[#0d1117] border-b border-[#30363d] flex justify-between items-center">
          <div className="flex items-center space-x-2">
            <div className="w-3 h-3 rounded-full bg-[#ff5f56]"></div>
            <div className="w-3 h-3 rounded-full bg-[#ffbd2e]"></div>
            <div className="w-3 h-3 rounded-full bg-[#27c93f]"></div>
            <span className="ml-4 text-xs text-[#8b949e] font-mono">{activeFile.name}</span>
          </div>
          <button
            onClick={handleCopy}
            className="p-1.5 hover:bg-[#30363d] rounded-lg transition-colors text-[#8b949e] hover:text-[#f0f6fc] flex items-center space-x-2"
          >
            {copied ? <Check className="w-4 h-4 text-[#3fb950]" /> : <Copy className="w-4 h-4" />}
            <span className="text-[10px] uppercase font-extrabold">{copied ? 'Kopirano!' : 'Copy Source'}</span>
          </button>
        </div>
        <div className="p-6 flex-grow overflow-auto bg-[#0d1117]">
          <pre className="font-mono text-sm leading-relaxed whitespace-pre text-[#c9d1d9]">
            {activeFile.content}
          </pre>
        </div>
      </div>
    </div>
  );
};

export default FileViewer;
