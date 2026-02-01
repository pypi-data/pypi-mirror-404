import React from 'react';

export const Header: React.FC = () => {
  return (
    <header className="mb-8 text-center sm:text-left relative">
      <div className="absolute top-0 right-0 -z-10 opacity-20 blur-3xl">
        <div className="w-64 h-64 bg-cyan-500 rounded-full mix-blend-multiply filter opacity-50 animate-pulse"></div>
      </div>

      <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
        <div>
          <h1 className="text-4xl md:text-5xl font-extrabold tracking-tight text-white mb-2">
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-blue-500">
              Cro-Stem
            </span>
            <span className="ml-2 text-slate-500 font-light">2.0</span>
          </h1>
          <p className="text-slate-400 max-w-md text-sm md:text-base">
            Visokoučinkoviti Rust stemmer preveden u WASM.
            Sadrži hibridnu normalizaciju i mapiranje dijalekata.
          </p>
        </div>

        <div className="hidden sm:block">
          <div className="px-4 py-2 rounded-full border border-emerald-500/30 bg-emerald-500/10 text-emerald-400 text-xs font-mono uppercase tracking-widest flex items-center gap-2">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-emerald-500"></span>
            </span>
            WASM Učitan
          </div>
        </div>
      </div>
    </header>
  );
};