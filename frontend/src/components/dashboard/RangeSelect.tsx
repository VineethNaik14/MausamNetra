import React from 'react';

export type ChartRange = '7d' | '30d' | '1y' | 'all';

const RANGE_LABELS: Record<ChartRange, string> = {
  '7d': 'Last 7 days',
  '30d': 'Last 30 days',
  '1y': 'Last year',
  all: 'All time',
};

// 'all' maps to a large-but-finite window rather than an unbounded query,
// since the backend's time_series_days expects a number either way.
export function rangeToDays(range: ChartRange): number {
  switch (range) {
    case '7d': return 7;
    case '30d': return 30;
    case '1y': return 365;
    case 'all': return 3650;
  }
}

interface RangeSelectProps {
  value: ChartRange;
  onChange: (value: ChartRange) => void;
}

export function RangeSelect({ value, onChange }: RangeSelectProps) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value as ChartRange)}
      className="bg-[#24313D] border border-[#34C759]/20 text-[#F4F6F6] text-xs rounded-md px-2 py-1.5 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-[#34C759] appearance-none cursor-pointer"
      aria-label="Chart time range"
    >
      {(Object.keys(RANGE_LABELS) as ChartRange[]).map((r) => (
        <option key={r} value={r}>{RANGE_LABELS[r]}</option>
      ))}
    </select>
  );
}