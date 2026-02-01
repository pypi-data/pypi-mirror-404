import React from 'react';

interface DevInstructionsModalProps {
    isOpen: boolean;
    onClose: () => void;
}

export const DevInstructionsModal: React.FC<DevInstructionsModalProps> = ({ isOpen, onClose }) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 bg-black/80 backdrop-blur-md animate-fadeIn" onClick={onClose}>
            <div className="bg-slate-900 border border-slate-700 w-full max-w-2xl rounded-2xl shadow-2xl p-8 animate-scaleIn relative" onClick={e => e.stopPropagation()}>

                <button
                    onClick={onClose}
                    className="absolute top-4 right-4 p-2 text-slate-500 hover:text-white transition-colors hover:bg-slate-800 rounded-lg"
                >
                    <svg xmlns="http://www.w3.org/2000/svg" className="h-6 w-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                </button>

                <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-3">
                    <span className="text-amber-400">⚡</span>
                    Developer Mode Upute
                </h2>

                <div className="space-y-8 text-slate-300">

                    <section>
                        <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-cyan-500"></span>
                            Osnovni Workflow
                        </h3>
                        <p className="text-sm leading-relaxed mb-3">
                            Kada je <strong className="text-amber-400">DEV MODE</strong> uključen, dobit ćete dodatne kontrole za brzo prikupljanje testnih slučajeva (Test Cases) izravno iz sučelja.
                        </p>
                        <ol className="list-decimal list-inside space-y-2 text-sm ml-2 marker:text-slate-500">
                            <li>Uočite netočan korijen u tablici rezultata.</li>
                            <li>Kliknite gumb <kbd className="px-1.5 py-0.5 rounded bg-slate-800 border border-slate-700 text-red-400 font-mono text-xs">PRIJAVI</kbd> desno od rezultata.</li>
                            <li>Upišite <strong>očekivani korijen</strong> u prozor koji se otvori i potvrdite.</li>
                        </ol>
                    </section>

                    <section>
                        <h3 className="text-lg font-semibold text-white mb-3 flex items-center gap-2">
                            <span className="w-1.5 h-1.5 rounded-full bg-indigo-500"></span>
                            Funkcije Gumba
                        </h3>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="px-2 py-1 rounded border border-red-500/30 text-red-400 bg-red-500/10 text-xs font-bold uppercase tracking-wider">PRIJAVI</span>
                                </div>
                                <p className="text-xs text-slate-400">
                                    Otvara modal za ispravak. Odmah kopira pojedinačni <code className="text-cyan-400">assert_eq!</code> u međuspremnik i dodaje stavku u sesijski log.
                                </p>
                            </div>

                            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="px-2 py-1 rounded border border-slate-700 text-slate-400 bg-slate-800 text-xs font-bold uppercase tracking-wider">LOG [N]</span>
                                </div>
                                <p className="text-xs text-slate-400">
                                    Otvara pregled svih prikupljenih ispravaka u ovoj sesiji. Omogućuje masovni izvoz.
                                </p>
                            </div>

                            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-indigo-400 text-xs font-bold uppercase tracking-wider">📋 Kopiraj Rust Assertions</span>
                                </div>
                                <p className="text-xs text-slate-400">
                                    (Unutar Log prozora) Generira i kopira blok koda sa svim vašim ispravcima, spreman za lijepljenje u <code className="text-slate-300">src/lib.rs</code> testove.
                                </p>
                            </div>

                            <div className="bg-slate-800/50 p-4 rounded-xl border border-slate-700/50">
                                <div className="flex items-center gap-2 mb-2">
                                    <span className="text-cyan-400 text-xs font-bold uppercase tracking-wider">{'{ }'} Kopiraj JSON</span>
                                </div>
                                <p className="text-xs text-slate-400">
                                    (Unutar Log prozora) Izvozi podatke u JSON formatu za arhiviranje ili dijeljenje s timom.
                                </p>
                            </div>
                        </div>
                    </section>

                </div>

                <div className="mt-8 pt-6 border-t border-slate-800 flex justify-end">
                    <button
                        onClick={onClose}
                        className="px-6 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors text-sm font-medium"
                    >
                        Razumijem
                    </button>
                </div>

            </div>
        </div>
    );
};
