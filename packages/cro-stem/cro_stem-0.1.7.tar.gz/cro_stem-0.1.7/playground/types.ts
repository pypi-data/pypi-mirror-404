export enum StemMode {
  AGGRESSIVE = 'Aggressive',
  CONSERVATIVE = 'Conservative'
}

export interface StemResult {
  original: string;
  normalized: string;
  stem: string;
  executionTimeUs: number; // Microseconds
  isDirty: boolean; // True if normalized != original
}

export interface ProcessingStats {
  totalTimeUs: number;
  wordCount: number;
  dirtyCount: number;
}

export interface SessionLogEntry {
  original: string;
  stem: string;
  expected: string;
  mode: StemMode;
  timestamp: Date;
}