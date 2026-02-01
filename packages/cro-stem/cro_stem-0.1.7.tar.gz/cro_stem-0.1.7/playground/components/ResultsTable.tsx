import React, { useState } from 'react';
import { StemResult, ProcessingStats, StemMode } from '../types';
import { FeedbackModal } from './FeedbackModal';

interface ResultsTableProps {
  results: StemResult[];
  stats: ProcessingStats;
  devMode: boolean;
  currentMode: StemMode;
  onReport: (original: string, stem: string, expected: string, mode: StemMode) => void;
}

export const ResultsTable: React.FC<ResultsTableProps> = ({ results, stats, devMode, currentMode, onReport }) => {
  const [selectedItem, setSelectedItem] = useState<StemResult | null>(null);
  const [showToast, setShowToast] = useState(false);
  const [toastMessage, setToastMessage] = useState("");

  const handleReportClick = (item: StemResult) => {
    setSelectedItem(item);
  };

  const handleModalSubmit = (expected: string) => {
    if (selectedItem) {
      // Add to main log
      onReport(selectedItem.original, selectedItem.stem, expected, currentMode);

      // Also copy specific assertion to clipboard for convenience
      const modeStr = currentMode === StemMode.AGGRESSIVE ? 'Aggressive' : 'Conservative';
      const snippet = `assert_eq!(process_one("${selectedItem.original}", &StemMode::${modeStr}).stem, "${expected}");`;

      navigator.clipboard.writeText(snippet).then(() => {
        setToastMessage(`Prijavljeno i kopirano!`);
        setShowToast(true);
        setTimeout(() => setShowToast(false), 3000);
      });
    }
    setSelectedItem(null);
  };

  if (results.length === 0) {
    return (
      <div className="w-full h-64 flex flex-col items-center justify-center border-2 border-dashed border-slate-700 rounded-xl bg-slate-800/20 text-slate-500">
        <svg xmlns="http://www.w3.org/2000/svg" className="h-12 w-12 mb-4 opacity-50" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M19.428 15.428a2 2 0 00-1.022-.547l-2.384-.477a6 6 0 00-3.86.517l-.318.158a6 6 0 01-3.86.517L6.05 15.21a2 2 0 00-1.806.547M8 4h8l-1 1v5.172a2 2 0 00.586 1.414l5 5c1.26 1.26.367 3.414-1.415 3.414H4.828c-1.782 0-2.674-2.154-1.414-3.414l5-5A2 2 0 009 10.172V5L8 4z" />
        </svg>
        <p>Unesite tekst iznad da vidite stemmer na djelu</p>
      </div>
    );
  }

  return (
    <div className="space-y-4 animate-fadeIn relative">
      {/* Toast Notification - Moved higher to avoid footer collision */}
      <div className={`fixed bottom-24 left-1/2 -translate-x-1/2 z-[100] transition-all duration-500 transform ${showToast ? 'translate-y-0 opacity-100' : 'translate-y-12 opacity-0 pointer-events-none'}`}>
        <div className="bg-slate-900 border border-cyan-500/50 text-cyan-400 px-6 py-3 rounded-full shadow-[0_0_30px_rgba(6,182,212,0.2)] flex items-center gap-3 backdrop-blur-xl">
          <div className="w-2 h-2 bg-cyan-500 rounded-full animate-pulse" />
          <span className="text-sm font-mono truncate max-w-xs md:max-w-md">{toastMessage}</span>
        </div>
      </div>

      <FeedbackModal
        isOpen={selectedItem !== null}
        onClose={() => setSelectedItem(null)}
        onSubmit={handleModalSubmit}
        word={selectedItem?.original || ""}
        currentStem={selectedItem?.stem || ""}
      />

      {/* Metrics Header */}
      <div className="flex flex-wrap items-center justify-between gap-4 p-4 rounded-xl bg-slate-800/40 border border-slate-700/50 backdrop-blur-md">
        <div className="flex items-center gap-6">
          <div>
            <span className="block text-xs text-slate-500 uppercase">Riječi</span>
            <span className="text-xl font-mono font-bold text-white">{stats.wordCount}</span>
          </div>
          <div>
            <span className="block text-xs text-slate-500 uppercase">Izmjene</span>
            <span className="text-xl font-mono font-bold text-amber-400">{stats.dirtyCount}</span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <span className="text-xs text-slate-400">Ukupno vrijeme:</span>
          <div className="px-3 py-1 rounded bg-black/40 border border-cyan-900/50 text-cyan-400 font-mono text-sm shadow-[0_0_15px_rgba(34,211,238,0.15)]">
            {stats.totalTimeUs} μs
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto rounded-xl border border-slate-700/50 shadow-2xl bg-slate-900/50 backdrop-blur-xl">
        <table className="w-full text-left text-sm">
          <thead>
            <tr className="bg-slate-800/80 text-slate-400 border-b border-slate-700">
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Original</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Normalizirano</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs">Korijen</th>
              <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs text-right">Vrijeme (μs)</th>
              {devMode && (
                <th className="px-6 py-4 font-medium uppercase tracking-wider text-xs text-right text-amber-500">Dev Akcije</th>
              )}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-800">
            {results.map((item, index) => (
              <tr
                key={index}
                className="hover:bg-slate-800/40 transition-colors duration-150 group"
              >
                <td className="px-6 py-3 font-medium text-slate-300">
                  {item.original}
                </td>
                <td className="px-6 py-3">
                  <span className={`inline-block transition-colors ${item.isDirty ? 'text-amber-400 font-medium' : 'text-slate-500'}`}>
                    {item.normalized}
                  </span>
                  {item.isDirty && (
                    <span className="ml-2 text-[10px] px-1.5 py-0.5 rounded bg-amber-500/10 border border-amber-500/20 text-amber-500">
                      MOD
                    </span>
                  )}
                </td>
                <td className="px-6 py-3">
                  <span className="font-mono text-cyan-300 font-medium bg-cyan-950/30 px-2 py-1 rounded border border-cyan-900/50">
                    {item.stem}
                  </span>
                </td>
                <td className="px-6 py-3 text-right font-mono text-slate-500 group-hover:text-white transition-colors">
                  {item.executionTimeUs}
                </td>
                {devMode && (
                  <td className="px-6 py-3 text-right">
                    <button
                      onClick={() => handleReportClick(item)}
                      className="text-[10px] px-2 py-1 rounded border border-red-500/30 text-red-400 hover:bg-red-500/10 hover:text-red-300 transition-colors uppercase tracking-wider font-semibold"
                    >
                      Prijavi
                    </button>
                  </td>
                )}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};