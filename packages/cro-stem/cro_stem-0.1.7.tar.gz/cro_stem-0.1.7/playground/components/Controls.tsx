import React from 'react';
import { StemMode } from '../types';

interface ControlsProps {
  mode: StemMode;
  setMode: (mode: StemMode) => void;
  onPresetClick: (text: string) => void;
  devMode: boolean;
  setDevMode: (enabled: boolean) => void;
  onViewLog: () => void;
  onHelp: () => void;
  logCount: number;
}

export const Controls: React.FC<ControlsProps> = ({ mode, setMode, onPresetClick, devMode, setDevMode, onViewLog, onHelp, logCount }) => {

  const presets = [
    { label: "Šešir žutog...", text: "sesir zutog scapca cuci kraj koscate guscerice sto zdere suseno grozde." },
    { label: "Jučer je ščapavi...", text: "jucer je scapavi ucitelj cesto cackao sljive zvacuci secer i cesce pricajuci o zescim nocnim kisama." },
    { label: "Učenici su...", text: "ucenici su cerupali ceserke s guscerim zbunja dok su suskale jeze i miseve medu cuskijama." },
    { label: "Šenološki stručnjak...", text: "senoloski strucnjak cesce cisti zlicice salice i case koje jucer jos nisu bile ciste." },
    { label: "Često ćemo...", text: "cesto cemo slusati zalosne price o sumskom cudovistu sto zvace zireve i sisarke." },
    { label: "Građevinski...", text: "gradjevinski strucnjaci ocerupali su zbunje čistili zlijebove i cesce provjeravali cvrstocu zice." },
    { label: "Šašavi ženščić...", text: "sasavi zenscic je jucer jos cesce cistio carsaf sivajuci zutim koncem kroz scepanac." },
    { label: "Mlađi učitelj...", text: "mladi ucitelj objasnjava cesce kako se grozde bere zito zanje i secerna repa cupa." },
    { label: "Žalosni mišić...", text: "zalosni scapavi misic je zderao zir i secer sto mu je ucitelj cesto cuvao u scepancu." },
    { label: "Češće ćemo...", text: "cesce cemo cistiti zlicice salice i casice koje zute od secera sto ga jos jucer nismo oprzili." }
  ];

  return (
    <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6 mb-6">

      <div className="flex flex-wrap items-center gap-4">
        {/* Mode Toggle */}
        <div className="flex items-center bg-slate-800/50 p-1 rounded-lg border border-slate-700 backdrop-blur-sm">
          <button
            onClick={() => setMode(StemMode.AGGRESSIVE)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-300 ${mode === StemMode.AGGRESSIVE
              ? 'bg-gradient-to-r from-cyan-500 to-blue-600 text-white shadow-lg shadow-cyan-500/20'
              : 'text-slate-400 hover:text-white'
              }`}
          >
            Agresivni
          </button>
          <button
            onClick={() => setMode(StemMode.CONSERVATIVE)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-all duration-300 ${mode === StemMode.CONSERVATIVE
              ? 'bg-gradient-to-r from-purple-500 to-pink-600 text-white shadow-lg shadow-purple-500/20'
              : 'text-slate-400 hover:text-white'
              }`}
          >
            Konzervativni
          </button>
        </div>

        {/* Dev Mode Controls */}
        <div className="flex items-center gap-2">

          {/* Dev Mode Toggle */}
          <button
            onClick={() => setDevMode(!devMode)}
            className={`flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-mono transition-all border ${devMode
                ? 'bg-amber-500/10 border-amber-500/30 text-amber-400'
                : 'bg-slate-800/50 border-slate-700 text-slate-500 hover:text-slate-300'
              }`}
          >
            <div className={`w-2 h-2 rounded-full ${devMode ? 'bg-amber-400 animate-pulse' : 'bg-slate-600'}`} />
            DEV MODE
          </button>

          {devMode && (
            <>
              <button
                onClick={onViewLog}
                className="flex items-center gap-2 px-3 py-1.5 rounded-md text-xs font-mono transition-all border bg-slate-800/50 border-slate-700 text-slate-400 hover:text-cyan-400 hover:border-cyan-500/30"
              >
                LOG {logCount > 0 && <span className="bg-slate-700 text-white px-1.5 rounded-full text-[10px]">{logCount}</span>}
              </button>
              <button
                onClick={onHelp}
                className="w-8 h-8 flex items-center justify-center rounded-md border bg-slate-800/50 border-slate-700 text-slate-500 hover:text-white hover:border-slate-500 transition-all font-mono text-xs"
                title="Dev Mode Upute"
              >
                ?
              </button>
            </>
          )}
        </div>
      </div>

      {/* Dirty Input Presets */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-semibold text-slate-500 uppercase tracking-wider mr-2">Isprobaj:</span>
        {presets.map((preset) => (
          <button
            key={preset.label}
            onClick={() => onPresetClick(preset.text)}
            className="px-3 py-1.5 rounded-full border border-slate-700 bg-slate-800/30 text-xs text-slate-300 hover:border-cyan-500/50 hover:text-cyan-400 transition-colors"
          >
            {preset.label}
          </button>
        ))}
      </div>
    </div>
  );
};