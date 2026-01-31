
import React, { useState } from 'react';
import { Layout, Code, Play, Github, Book, Terminal, Settings, ExternalLink } from 'lucide-react';
import InteractiveDemo from './components/InteractiveDemo';
import FileViewer from './components/FileViewer';

const App: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'demo' | 'code' | 'setup'>('demo');

  return (
    <div className="min-h-screen bg-[#0d1117] flex flex-col selection:bg-[#58a6ff]/30 selection:text-[#f0f6fc]">
      {/* Header */}
      <header className="border-b border-[#30363d] bg-[#161b22]/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-[#58a6ff] p-2 rounded-xl shadow-lg shadow-[#58a6ff]/10">
              <Terminal className="text-[#0d1117] w-5 h-5" />
            </div>
            <div>
              <h1 className="text-lg font-bold text-[#f0f6fc] tracking-tight">Cro-Stem <span className="text-[#58a6ff]">WASM</span></h1>
              <div className="flex items-center space-x-2">
                <span className="text-[10px] text-[#8b949e] uppercase font-bold tracking-widest">Rust Engine v0.1.4</span>
                <span className="w-1 h-1 rounded-full bg-[#3fb950] animate-pulse"></span>
              </div>
            </div>
          </div>

          <nav className="hidden md:flex space-x-1 bg-[#0d1117] p-1 rounded-xl border border-[#30363d]">
            {(['demo', 'code', 'setup'] as const).map(tab => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-5 py-2 text-xs font-bold uppercase tracking-wider rounded-lg transition-all ${activeTab === tab ? 'bg-[#21262d] text-[#58a6ff] shadow-sm' : 'text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#161b22]'}`}
              >
                {tab === 'demo' ? 'Interactive Demo' : tab === 'code' ? 'Code Explorer' : 'Installation'}
              </button>
            ))}
          </nav>

          <div className="flex items-center space-x-4">
            <a href="https://github.com/Ja1Denis/Cro-Stem" target="_blank" rel="noopener noreferrer" className="p-2 text-[#8b949e] hover:text-[#f0f6fc] hover:bg-[#21262d] rounded-lg transition-all" title="GitHub Repository">
              <Github className="w-5 h-5" />
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-grow">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          <div className="transition-all duration-300">
            {activeTab === 'demo' && <InteractiveDemo />}
            {activeTab === 'code' && <FileViewer />}
            {activeTab === 'setup' && <SetupGuide />}
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="bg-[#161b22] border-t border-[#30363d] py-12 mt-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex flex-col md:flex-row justify-between items-center space-y-6 md:space-y-0">
            <div className="space-y-2 text-center md:text-left">
              <div className="flex items-center justify-center md:justify-start space-x-2">
                <Terminal className="w-4 h-4 text-[#58a6ff]" />
                <span className="text-[#f0f6fc] font-bold">Cro-Stem Project</span>
              </div>
              <p className="text-[#8b949e] text-xs">Optimizirano za WebAssembly i Python. MIT Licensed.</p>
            </div>
            <div className="flex flex-wrap justify-center gap-6 md:gap-8">
              <a href="https://crates.io/crates/cro_stem" target="_blank" rel="noopener" className="flex items-center space-x-1 text-[#8b949e] hover:text-[#58a6ff] text-xs font-bold uppercase tracking-widest transition-colors">
                <span>Crates.io</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <a href="https://pypi.org/project/cro-stem/" target="_blank" rel="noopener" className="flex items-center space-x-1 text-[#8b949e] hover:text-[#58a6ff] text-xs font-bold uppercase tracking-widest transition-colors">
                <span>PyPI</span>
                <ExternalLink className="w-3 h-3" />
              </a>
              <a href="https://github.com/Ja1Denis/Cro-Stem" target="_blank" rel="noopener" className="flex items-center space-x-1 text-[#8b949e] hover:text-[#58a6ff] text-xs font-bold uppercase tracking-widest transition-colors">
                <span>GitHub</span>
                <ExternalLink className="w-3 h-3" />
              </a>
            </div>
          </div>
          <div className="mt-8 pt-8 border-t border-[#30363d]/50 text-center text-[#30363d] text-[10px] uppercase font-bold tracking-[0.3em]">
            Built with Rust • WebAssembly • Python Bindings
          </div>
        </div>
      </footer>
    </div>
  );
};

const SetupGuide: React.FC = () => {
  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
      <div className="bg-[#161b22] border border-[#30363d] rounded-2xl overflow-hidden shadow-2xl">
        <div className="p-6 border-b border-[#30363d] bg-[#21262d]/50">
          <h2 className="text-xl font-bold flex items-center space-x-2">
            <Book className="w-5 h-5 text-[#58a6ff]" />
            <span>WASM Build & Deployment</span>
          </h2>
        </div>
        <div className="p-8 space-y-8">
          <section className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="bg-[#238636]/20 p-2 rounded-lg text-[#3fb950] font-bold text-xs">STEP 1</div>
              <h3 className="text-[#f0f6fc] font-bold">Instalacija Alata</h3>
            </div>
            <p className="text-[#8b949e] text-sm leading-relaxed">Za buildanje Rusta u WASM potreban vam je <code>wasm-pack</code>. On upravlja kompilacijom, optimizacijom i generiranjem JS bindinga.</p>
            <div className="bg-[#0d1117] p-5 rounded-xl font-mono text-xs border border-[#30363d] relative group">
              <span className="text-[#3fb950] mr-2">$</span> curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="bg-[#238636]/20 p-2 rounded-lg text-[#3fb950] font-bold text-xs">STEP 2</div>
              <h3 className="text-[#f0f6fc] font-bold">Buildanje Projekta</h3>
            </div>
            <p className="text-[#8b949e] text-sm leading-relaxed">Pokrenite sljedeću naredbu u korijenu vašeg Rust projekta. Ciljamo <code>web</code> target kako bismo dobili ES module.</p>
            <div className="bg-[#0d1117] p-5 rounded-xl font-mono text-xs border border-[#30363d] relative group">
              <span className="text-[#3fb950] mr-2">$</span> wasm-pack build --target web --out-dir docs/pkg --release
            </div>
            <div className="bg-[#1c2128] border-l-4 border-[#e3b341] p-4 rounded-r-lg">
              <div className="flex items-center space-x-2 text-[#e3b341] mb-1 font-bold text-xs uppercase">
                <Settings className="w-3.5 h-3.5" />
                <span>Optimization Note</span>
              </div>
              <p className="text-[#8b949e] text-[11px]">Korištenjem <code>--release</code> zastavice, Cargo će primijeniti LTO (Link Time Optimization) i smanjiti binarnu datoteku za oko 40%.</p>
            </div>
          </section>

          <section className="space-y-4">
            <div className="flex items-center space-x-3">
              <div className="bg-[#238636]/20 p-2 rounded-lg text-[#3fb950] font-bold text-xs">STEP 3</div>
              <h3 className="text-[#f0f6fc] font-bold">JavaScript Integracija</h3>
            </div>
            <p className="text-[#8b949e] text-sm leading-relaxed">Uvezite inicijalizacijsku funkciju i stemmer metode u svoj frontend kod.</p>
            <div className="bg-[#0d1117] p-5 rounded-xl font-mono text-xs border border-[#30363d] overflow-x-auto">
              <pre className="whitespace-pre text-[#c9d1d9]">
                {`import init, { stem } from './pkg/cro_stem.js';

async function run() {
  // Prvo inicijalizirajte WASM memoriju
  await init();
  
  // Sada možete koristiti stemmer bilo gdje
  const result = stem("programiranje", "aggressive");
  console.log("Stem:", result); // "program"
}`}
              </pre>
            </div>
          </section>

          <section className="pt-6 border-t border-[#30363d]">
            <div className="flex items-center space-x-2 text-[#58a6ff] mb-4">
              <Package className="w-5 h-5" />
              <h3 className="font-bold">Dostupni Paketi</h3>
            </div>
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <a href="https://crates.io/crates/cro_stem" target="_blank" rel="noopener" className="bg-[#161b22] border border-[#30363d] p-4 rounded-xl hover:border-[#58a6ff] transition-all group">
                <div className="text-[#f0f6fc] font-bold mb-1 group-hover:text-[#58a6ff]">Rust / Crates.io</div>
                <div className="text-xs text-[#8b949e]">Službeni Rust crate za backend integracije.</div>
              </a>
              <a href="https://pypi.org/project/cro-stem/" target="_blank" rel="noopener" className="bg-[#161b22] border border-[#30363d] p-4 rounded-xl hover:border-[#58a6ff] transition-all group">
                <div className="text-[#f0f6fc] font-bold mb-1 group-hover:text-[#58a6ff]">Python / PyPI</div>
                <div className="text-xs text-[#8b949e]">Python bindingzi za brzu NLP obradu.</div>
              </a>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};

const Package: React.FC<any> = (props) => (
  <svg {...props} xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="m7.5 4.27 9 5.15" /><path d="M21 8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16Z" /><path d="m3.3 7 8.7 5 8.7-5" /><path d="M12 22V12" /></svg>
);

export default App;
