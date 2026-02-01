import React, { useState, useEffect } from 'react';
import { Header } from './components/Header';
import { Controls } from './components/Controls';
import { ResultsTable } from './components/ResultsTable';
import { SessionLogModal } from './components/SessionLogModal';
import { DevInstructionsModal } from './components/DevInstructionsModal';
import { processTextBatch } from './services/croStemService';
import { StemMode, StemResult, ProcessingStats, SessionLogEntry } from './types';

const App: React.FC = () => {
  const [inputText, setInputText] = useState<string>("");
  const [mode, setMode] = useState<StemMode>(StemMode.AGGRESSIVE);
  const [results, setResults] = useState<StemResult[]>([]);
  const [stats, setStats] = useState<ProcessingStats>({ totalTimeUs: 0, wordCount: 0, dirtyCount: 0 });
  const [isProcessing, setIsProcessing] = useState<boolean>(false);
  const [devMode, setDevMode] = useState<boolean>(false);

  // Session Log State
  const [sessionLogs, setSessionLogs] = useState<SessionLogEntry[]>([]);
  const [isLogModalOpen, setIsLogModalOpen] = useState(false);
  const [isHelpModalOpen, setIsHelpModalOpen] = useState(false);

  useEffect(() => {
    const process = async () => {
      if (!inputText.trim()) {
        setResults([]);
        setStats({ totalTimeUs: 0, wordCount: 0, dirtyCount: 0 });
        return;
      }

      setIsProcessing(true);
      try {
        const { results: newResults, stats: newStats } = await processTextBatch(inputText, mode);
        setResults(newResults);
        setStats(newStats);
      } catch (err) {
        console.error("Processing error:", err);
      } finally {
        setIsProcessing(false);
      }
    };

    const timeoutId = setTimeout(process, 100); // Debounce
    return () => clearTimeout(timeoutId);
  }, [inputText, mode]);

  const handleReport = (original: string, stem: string, expected: string, reportMode: StemMode) => {
    const newEntry: SessionLogEntry = {
      original,
      stem,
      expected,
      mode: reportMode,
      timestamp: new Date()
    };
    setSessionLogs(prev => [...prev, newEntry]);
  };

  return (
    <div className="min-h-screen w-full bg-[#0f172a] text-slate-100 p-4 md:p-8 overflow-hidden relative font-sans">

      <SessionLogModal
        isOpen={isLogModalOpen}
        onClose={() => setIsLogModalOpen(false)}
        logs={sessionLogs}
        onClear={() => setSessionLogs([])}
      />

      <DevInstructionsModal
        isOpen={isHelpModalOpen}
        onClose={() => setIsHelpModalOpen(false)}
      />

      {/* Background Decor Elements */}
      <div className="fixed top-[20%] left-[10%] w-96 h-96 bg-blue-600/10 rounded-full blur-3xl pointer-events-none -z-10"></div>
      <div className="fixed bottom-[10%] right-[10%] w-80 h-80 bg-purple-600/10 rounded-full blur-3xl pointer-events-none -z-10"></div>

      <div className="max-w-5xl mx-auto z-10 relative">
        <Header />

        <main className="space-y-8">

          <section>
            <Controls
              mode={mode}
              setMode={setMode}
              onPresetClick={setInputText}
              devMode={devMode}
              setDevMode={setDevMode}
              onViewLog={() => setIsLogModalOpen(true)}
              onHelp={() => setIsHelpModalOpen(true)}
              logCount={sessionLogs.length}
            />

            <div className="relative group">
              <div className={`absolute -inset-0.5 bg-gradient-to-r ${isProcessing ? 'from-cyan-500 via-purple-500 to-blue-600 animate-pulse' : 'from-cyan-500 to-blue-600'} rounded-2xl blur opacity-25 group-hover:opacity-50 transition duration-500`}></div>
              <div className="relative">
                <textarea
                  value={inputText}
                  onChange={(e) => setInputText(e.target.value)}
                  placeholder="Ovdje zalijepite hrvatski tekst (ili odaberite predložak iznad)..."
                  className="w-full min-h-[160px] p-6 rounded-2xl bg-slate-900 border border-slate-700 text-lg text-slate-100 placeholder-slate-600 focus:outline-none focus:ring-2 focus:ring-cyan-500/50 focus:border-transparent transition-all shadow-2xl resize-y font-normal leading-relaxed"
                />
                {inputText.length > 0 && (
                  <button
                    onClick={() => setInputText('')}
                    className="absolute top-4 right-4 text-slate-500 hover:text-white bg-slate-800 hover:bg-red-500/20 hover:text-red-400 p-2 rounded-lg transition-colors text-xs uppercase tracking-wider font-semibold"
                  >
                    Očisti
                  </button>
                )}
                {isProcessing && (
                  <div className="absolute bottom-4 right-4 flex items-center gap-2 text-cyan-500 text-xs font-mono">
                    <span className="w-2 h-2 bg-cyan-500 rounded-full animate-ping"></span>
                    POKREĆEM WASM...
                  </div>
                )}
              </div>
            </div>
          </section>

          <section>
            <ResultsTable
              results={results}
              stats={stats}
              devMode={devMode}
              currentMode={mode}
              onReport={handleReport}
            />
          </section>

        </main>

        <footer className="mt-16 text-center text-slate-600 text-sm">
          <p>© 2026 Cro-Stem Projekt. Interna Verzija 2.0. Izgrađeno s Rust + WASM tehnologijom.</p>
        </footer>
      </div>
    </div>
  );
};

export default App;