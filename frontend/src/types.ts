// The real classifier (app/services/integrations/classifier.py) can return
// event types beyond this original mock set (STORM, CYCLONE, LIGHTNING,
// LANDSLIDE, HAIL, DROUGHT, UNKNOWN, ...), so this is left open. Components
// that key off specific values (e.g. maps/IncidentMap.tsx's colorMap) already
// fall back to an 'Other'-style default for anything unrecognized.
export type EventType = string;
// Options shown in the citizen report form. NOTE: the backend classifies
// event_type itself from the report text server-side - ReportCreate has no
// event_type field, so whatever is picked here is informational only until
// a real classifier is wired in.
export const REPORT_EVENT_TYPE_OPTIONS = ['Flood', 'Heavy Rain', 'Heatwave', 'Thunderstorm', 'Fog', 'Other'] as const;

export type Severity = 'Low' | 'Medium' | 'High' | 'Critical';
// Backend ReportStatus (PENDING/PROCESSED/FAILED) and VerificationStatus
// (VERIFIED/NEEDS_REVIEW/SUSPICIOUS/REJECTED) are combined into this single
// display status by the adapter in services/api.ts.
export type Status = 'Pending' | 'Verified' | 'Rejected' | 'Duplicate' | 'Failed';

export interface Location {
  lat: number;
  lng: number;
  address?: string;
  city?: string;
  district?: string;
  state?: string;
}

export interface IncidentEvent {
  id: string;
  event_type: EventType;
  severity: Severity;
  location: Location;
  confidence: number;
  report_counts: {
    verified: number;
    suspicious: number;
    duplicate: number;
    total: number;
  };
  status: 'Active' | 'Resolved';
  created_at: string;
  updated_at: string;
}

export interface Report {
  id: string;
  event_id?: string;
  event_type: EventType;
  description: string;
  location: Location;
  media_urls: string[];
  severity: Severity;
  status: Status;
  trust_score: number;
  source: 'User' | 'Agency' | 'Sensor';
  // The current backend Report model has no submitted-by-user column (see
  // integration notes) - this is left optional and is not populated yet.
  reporter_id?: string;
  ai_verification_info?: {
    confidence: number;
    reasons: string[];
    is_suspicious: boolean;
  };
  created_at: string;
}

export interface AnalyticsData {
  kpis: {
    active_events: number;
    verified_reports: number;
    suspicious_reports: number;
  };
  event_counts: Record<EventType, number>;
  trend: Array<{ date: string; count: number }>;
}

export interface User {
  id: string;
  role: 'ADMIN' | 'USER';
  name: string;
  email: string;
}

export interface DashboardFilters {
  dateFrom: string | null;   // 'YYYY-MM-DD'
  dateTo: string | null;     // 'YYYY-MM-DD'
  eventType: string;         // 'All' or a specific EventType
  state: string;             // 'All' or a specific state name
  verificationStatus: 'All' | 'Verified' | 'Needs Review' | 'Suspicious' | 'Unverified';
}

// Derives a per-incident verification status from its report_counts,
// since the backend only tracks verification at the Report level, not
// on the Incident itself.
export function getVerificationStatus(event: IncidentEvent): DashboardFilters['verificationStatus'] {
  const { verified, suspicious, total } = event.report_counts;
  if (total === 0) return 'Unverified';
  if (verified > 0) return 'Verified';
  if (suspicious > 0) return 'Suspicious';
  return 'Needs Review';
}