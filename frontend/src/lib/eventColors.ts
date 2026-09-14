// Central color/label registry for weather event types. Keys must match
// the Title Case strings produced by `titleCase()` in services/api.ts
// (which converts the backend's UPPER_SNAKE_CASE event_type, e.g.
// "STRONG_WIND", into "Strong Wind"). Keeping this in one place avoids
// the map, legend, and charts drifting out of sync with what the
// classifier actually produces.
export const EVENT_COLORS: Record<string, string> = {
  'Flood': '#ef4444',
  'Heavy Rainfall': '#3b82f6',
  'Thunderstorm': '#6366f1',
  'Heatwave': '#f59e0b',
  'Fog': '#a855f7',
  'Dust Storm': '#92400e',
  'Strong Wind': '#14b8a6',
  'Cyclone': '#db2777',
  'Lightning': '#eab308',
  'Hailstorm': '#38bdf8',
  'Other': '#6b7280',
};

export function getEventColor(type: string): string {
  return EVENT_COLORS[type] || EVENT_COLORS['Other'];
}