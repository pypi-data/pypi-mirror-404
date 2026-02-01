import React, { useMemo } from 'react';
import { SessionLogEntry, StemMode } from '../types';

interface SessionLogModalProps {
    isOpen: boolean;
    onClose: () => void;
    logs: SessionLogEntry[];
    onClear: () => void;
}

export const SessionLogModal: React.FC<SessionLogModalProps> = ({ isOpen, onClose, logs, onClear }) => {
    if (!isOpen) return null;

    const assertions = useMemo(() => {
        return logs.map(log =>
            `assert_eq!(process_one("${log.original}", &StemMode::${log.mode === StemMode.AGGRESSIVE ? 'Aggressive' : 'Conservative'}).stem, "${log.expected}");`
        ).join('\n');
    }, [logs]);

    const jsonExport = useMemo(() => {
        return JSON.stringify(logs.map(({ timestamp, ...rest }) => rest), null, 2);
    }, [logs]);

    const copyToClipboard = (text: string, label: string) => {
        navigator.clipboard.writeText(text).then(() => {
            alert(`Kopirano: ${label}`);
        }).catch(console.error);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn">
            <div className="bg-slate-900 border border-slate-700 w-full max-w-4xl max-h-[90vh] rounded-2xl shadow-2xl flex flex-col animate-scaleIn">

                {/* Header */}
                <div className="flex items-center justify-between p-6 border-b border-slate-800">
                    <div>
                        <h3 className="text-xl font-bold text-white flex items-center gap-3">
                            <span className="w-2 h-2 rounded-full bg-amber-500 animate-pulse"></span>
                            Session Log
                            <span className="px-2 py-0.5 rounded-full bg-slate-800 text-slate-400 text-xs font-mono">{logs.length} items</span>
                        </h3>
                        <p className="text-slate-400 text-sm mt-1">Pregledajte i izvezite prikupljene testne slučajeve.</p>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-slate-800 rounded-lg text-slate-500 hover:text-white transition-colors">
                        <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                        </svg>
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-hidden flex flex-col md:flex-row">

                    {/* List View */}
                    <div className="flex-1 overflow-y-auto p-0 border-r border-slate-800">
                        <table className="w-full text-left text-sm">
                            <thead className="bg-slate-800/50 text-slate-400 sticky top-0 backdrop-blur-sm z-10">
                                <tr>
                                    <th className="px-4 py-3 font-medium text-xs uppercase">Original</th>
                                    <th className="px-4 py-3 font-medium text-xs uppercase">Mode</th>
                                    <th className="px-4 py-3 font-medium text-xs uppercase">Očekivano</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-slate-800">
                                {logs.map((log, i) => (
                                    <tr key={i} className="hover:bg-slate-800/30">
                                        <td className="px-4 py-3 text-slate-300 font-mono">{log.original}</td>
                                        <td className="px-4 py-3 text-slate-500 text-xs">{log.mode}</td>
                                        <td className="px-4 py-3 text-green-400 font-mono font-semibold">{log.expected}</td>
                                    </tr>
                                ))}
                                {logs.length === 0 && (
                                    <tr>
                                        <td colSpan={3} className="px-4 py-12 text-center text-slate-600">Nema zabilježenih stavki.</td>
                                    </tr>
                                )}
                            </tbody>
                        </table>
                    </div>

                    {/* Actions / Preview */}
                    <div className="w-full md:w-80 bg-slate-950 p-6 flex flex-col gap-4 overflow-y-auto">
                        <div>
                            <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-3">Brze Akcije</h4>
                            <div className="space-y-2">
                                <button
                                    onClick={() => copyToClipboard(assertions, "Rust Assertions")}
                                    disabled={logs.length === 0}
                                    className="w-full py-2 px-4 rounded-lg bg-indigo-500/10 border border-indigo-500/20 text-indigo-400 hover:bg-indigo-500/20 hover:text-indigo-300 transition-colors text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <span>📋</span> Kopiraj Rust Assertions
                                </button>
                                <button
                                    onClick={() => copyToClipboard(jsonExport, "JSON Export")}
                                    disabled={logs.length === 0}
                                    className="w-full py-2 px-4 rounded-lg bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 hover:bg-cyan-500/20 hover:text-cyan-300 transition-colors text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <span>{'{ }'}</span> Kopiraj JSON
                                </button>
                                <button
                                    onClick={onClear}
                                    disabled={logs.length === 0}
                                    className="w-full py-2 px-4 rounded-lg bg-red-500/10 border border-red-500/20 text-red-400 hover:bg-red-500/20 hover:text-red-300 transition-colors text-sm font-medium flex items-center justify-center gap-2 disabled:opacity-50 disabled:cursor-not-allowed"
                                >
                                    <span>🗑️</span> Očisti Listu
                                </button>
                            </div>
                        </div>

                        <div className="flex-1 min-h-[200px] bg-black/30 rounded-lg p-3 border border-slate-800">
                            <code className="text-[10px] text-slate-400 font-mono whitespace-pre-wrap break-all block">
                                {assertions || "// Assertions preview..."}
                            </code>
                        </div>
                    </div>

                </div>
            </div>
        </div>
    );
};
