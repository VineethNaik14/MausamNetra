import axios from "axios";
import {
  AnalyticsData,
  EventType,
  IncidentEvent,
  Report,
  Severity,
  Status,
  User,
} from "../types";

// ==========================================
// CONFIG
// ==========================================
// VITE_API_URL should point at the FastAPI app's versioned prefix, e.g.
// http://localhost:8000/api/v1 (see backend/.env.example API_V1_PREFIX).
export const API_URL =
  import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";
// The origin (no /api/v1 suffix) is needed to resolve relative media URLs
// returned by the backend (it serves uploads from `${ORIGIN}/uploads/...`).
export const API_ORIGIN = API_URL.replace(/\/api\/v1\/?$/, "");

export const api = axios.create({
  baseURL: API_URL,
});

// Attach the JWT token to every request.
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("jwt_token");
  if (token && config.headers) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// If a token is present but the backend says it's invalid/expired, clear it
// so the app doesn't keep sending a dead token on every request.
api.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error?.response?.status === 401) {
      localStorage.removeItem("jwt_token");
    }
    return Promise.reject(error);
  },
);

export function resolveMediaUrl(
  path: string | null | undefined,
): string | null {
  if (!path) return null;
  if (/^https?:\/\//i.test(path)) return path;
  return `${API_ORIGIN}/${path.replace(/^\/+/, "")}`;
}

// ==========================================
// BACKEND ENVELOPE TYPES
// (mirrors app/schemas/common.py - every route wraps its payload this way)
// ==========================================
interface ApiResponse<T> {
  success: boolean;
  data: T;
  message?: string | null;
}

interface PaginationMeta {
  page: number;
  page_size: number;
  total: number;
  total_pages: number;
}

interface PaginatedResponse<T> {
  success: boolean;
  data: T[];
  pagination: PaginationMeta;
}

// --- Raw backend shapes (mirrors app/schemas/*.py) ---
interface BackendUser {
  id: string;
  name: string;
  email: string;
  role: "ADMIN" | "USER";
  is_active: boolean;
  created_at: string;
}

interface BackendTokenResponse {
  access_token: string;
  token_type: string;
  expires_in_minutes: number;
  user: BackendUser;
}

interface BackendVerification {
  id: string;
  report_id: string;
  trust_score: number; // 0-100
  status: "VERIFIED" | "NEEDS_REVIEW" | "SUSPICIOUS" | "REJECTED";
  reason: string | null;
  verified_by: string | null;
  verified_at: string | null;
  created_at: string;
  updated_at: string;
}

interface BackendReport {
  id: string;
  source_id: string;
  text: string;
  event_type: string | null;
  event_confidence: number | null;
  timestamp: string;
  latitude: number;
  longitude: number;
  city: string | null;
  district: string | null;
  state: string | null;
  media_url: string | null;
  report_metadata: Record<string, unknown> | null;
  status: "PENDING" | "PROCESSED" | "FAILED";
  incident_id: string | null;
  created_at: string;
  updated_at: string;
  verification?: BackendVerification | null;
}

interface BackendIncident {
  id: string;
  event_type: string;
  severity: "LOW" | "MODERATE" | "HIGH" | "SEVERE";
  latitude: number;
  longitude: number;
  state: string | null;
  district: string | null;
  city: string | null;
  start_time: string;
  end_time: string | null;
  confidence: number | null;
  status: "ACTIVE" | "MONITORING" | "RESOLVED" | "DISMISSED";
  report_count: number;
  verified_count: number;
  suspicious_count: number;
  duplicate_count: number;
  created_at: string;
  updated_at: string;
}

interface BackendAnalytics {
  summary: {
    active_events: number;
    total_reports: number;
    verified_reports: number;
    suspicious_reports: number;
    pending_verification: number;
    rejected_reports: number;
  };
  event_distribution: { key: string; count: number }[];
  severity_distribution: { key: string; count: number }[];
  source_distribution: { key: string; count: number }[];
  geographic_distribution: { key: string; count: number }[];
  time_series: { date: string; count: number }[];
}

export interface BackendSource {
  id: string;
  name: string;
  type: string;
  reliability_score: number;
  is_active: boolean;
  created_at: string;
}

// ==========================================
// ADAPTERS: backend shape -> existing frontend types
// ==========================================
const SEVERITY_MAP: Record<string, Severity> = {
  LOW: "Low",
  MODERATE: "Medium",
  HIGH: "High",
  SEVERE: "Critical",
};

function adaptSeverity(s: string): Severity {
  return SEVERITY_MAP[s] || "Medium";
}

function adaptIncidentStatus(
  s: BackendIncident["status"],
): "Active" | "Resolved" {
  return s === "RESOLVED" || s === "DISMISSED" ? "Resolved" : "Active";
}

function titleCase(s: string): string {
  return s
    .toLowerCase()
    .split(/[_\s]+/)
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(" ");
}

function adaptEventType(t: string | null): EventType {
  if (!t || t === "UNKNOWN") return "Other";
  return titleCase(t);
}

function adaptUser(u: BackendUser): User {
  return { id: u.id, role: u.role, name: u.name, email: u.email };
}

function adaptIncident(i: BackendIncident): IncidentEvent {
  return {
    id: i.id,
    event_type: adaptEventType(i.event_type),
    severity: adaptSeverity(i.severity),
    location: {
      lat: i.latitude,
      lng: i.longitude,
      city: i.city || undefined,
      district: i.district || undefined,
      state: i.state || undefined,
    },
    confidence: i.confidence ?? 0,
    report_counts: {
      verified: i.verified_count,
      suspicious: i.suspicious_count,
      duplicate: i.duplicate_count,
      total: i.report_count,
    },
    status: adaptIncidentStatus(i.status),
    created_at: i.created_at,
    updated_at: i.updated_at,
  };
}

// Combines Report.status (pipeline stage) + Verification.status (human/AI
// verdict) into the single display status the frontend components expect.
function adaptReportStatus(r: BackendReport): Status {
  if (r.status === "PENDING") return "Pending";
  if (r.status === "FAILED") return "Failed";
  const v = r.verification?.status;
  if (v === "VERIFIED") return "Verified";
  if (v === "REJECTED") return "Rejected";
  // NEEDS_REVIEW / SUSPICIOUS / no verification yet all still need admin eyes.
  return "Pending";
}

function adaptReport(r: BackendReport): Report {
  const mediaUrl = resolveMediaUrl(r.media_url);
  return {
    id: r.id,
    event_id: r.incident_id || undefined,
    event_type: adaptEventType(r.event_type),
    description: r.text,
    location: {
      lat: r.latitude,
      lng: r.longitude,
      city: r.city || undefined,
      district: r.district || undefined,
      state: r.state || undefined,
    },
    media_urls: mediaUrl ? [mediaUrl] : [],
    severity: "Medium", // Report model doesn't carry a severity - only Incident does.
    status: adaptReportStatus(r),
    trust_score: r.verification ? r.verification.trust_score / 100 : 0,
    source: "User",
    reporter_id: undefined,
    ai_verification_info: r.verification
      ? {
          confidence: r.verification.trust_score / 100,
          reasons: r.verification.reason
            ? r.verification.reason.split("; ").filter(Boolean)
            : [],
          is_suspicious: r.verification.status === "SUSPICIOUS",
        }
      : undefined,
    created_at: r.created_at,
  };
}

function adaptAnalytics(a: BackendAnalytics): AnalyticsData {
  const event_counts: Record<string, number> = {};
  for (const { key, count } of a.event_distribution) {
    event_counts[adaptEventType(key)] = count;
  }
  return {
    kpis: {
      active_events: a.summary.active_events,
      verified_reports: a.summary.verified_reports,
      suspicious_reports: a.summary.suspicious_reports,
    },
    event_counts: event_counts as AnalyticsData["event_counts"],
    trend: a.time_series.map((t) => ({
      date: new Date(t.date).toLocaleDateString("en-US", { weekday: "short" }),
      count: t.count,
    })),
  };
}

// ==========================================
// API MODULES
// ==========================================
export const authApi = {
  login: async (credentials: { email: string; password: string }) => {
    const res = await api.post<ApiResponse<BackendTokenResponse>>(
      "/auth/login",
      credentials,
    );
    return {
      data: {
        token: res.data.data.access_token,
        user: adaptUser(res.data.data.user),
      },
    };
  },
  getMe: async () => {
    const res = await api.get<ApiResponse<BackendUser>>("/auth/me");
    return { data: adaptUser(res.data.data) };
  },
  logout: async () => {
    await api.post("/auth/logout");
  },
};

export const sourcesApi = {
  getSources: async (): Promise<{ data: BackendSource[] }> => {
    const res = await api.get<ApiResponse<BackendSource[]>>("/sources");
    return { data: res.data.data };
  },
};

export const reportsApi = {
  uploadMedia: async (file: File): Promise<{ data: { media_url: string } }> => {
    const form = new FormData();
    form.append("file", file);
    const res = await api.post<ApiResponse<{ media_url: string }>>(
      "/reports/upload-media",
      form,
      {
        headers: { "Content-Type": "multipart/form-data" },
      },
    );
    return { data: res.data.data };
  },
  // `data` mirrors app/schemas/report.py::ReportCreate. source_id is required
  // by the backend - callers should look one up via sourcesApi.getSources().
  submitReport: async (data: {
    source_id: string;
    text: string;
    latitude: number;
    longitude: number;
    city?: string;
    district?: string;
    state?: string;
    media_url?: string;
    timestamp?: string;
    event_type_hint?: string;
  }) => {
    const res = await api.post<ApiResponse<BackendReport>>("/reports", data);
    return { data: adaptReport(res.data.data) };
  },
  getReports: async (
    filters: { status?: string; page?: number; page_size?: number } = {},
  ) => {
    const res = await api.get<PaginatedResponse<BackendReport>>("/reports", {
      params: { page: filters.page ?? 1, page_size: filters.page_size ?? 100 },
    });
    let items = res.data.data.map(adaptReport);
    // The backend only filters by pipeline status (PENDING/PROCESSED/FAILED),
    // not by the human-facing Verified/Rejected/Pending status shown in the
    // UI, so that filter is applied client-side against the adapted status.
    if (filters.status && filters.status !== "All") {
      items = items.filter((r) => r.status === filters.status);
    }
    return {
      data: {
        items,
        total: res.data.pagination.total,
        page: res.data.pagination.page,
        total_pages: res.data.pagination.total_pages,
      },
    };
  },
  getReportById: async (id: string) => {
    const res = await api.get<ApiResponse<BackendReport>>(`/reports/${id}`);
    return { data: adaptReport(res.data.data) };
  },
  adminAction: async (
    id: string,
    action: "verify" | "reject" | "escalate",
    reason?: string,
  ) => {
    if (action === "verify") {
      await api.post(`/reports/${id}/verify`, { reason: reason || null });
    } else if (action === "reject") {
      await api.post(`/reports/${id}/reject`, {
        reason: reason || "Rejected by admin",
      });
    } else {
      await api.post(`/reports/${id}/escalate`, {
        reason: reason || "Escalated by admin",
      });
    }
    return { data: { success: true, action } };
  },
};

export const eventsApi = {
  getEvents: async () => {
    const res = await api.get<PaginatedResponse<BackendIncident>>("/events", {
      params: { page: 1, page_size: 100 },
    });
    return {
      data: {
        items: res.data.data.map(adaptIncident),
        total: res.data.pagination.total,
      },
    };
  },
  getEventById: async (id: string) => {
    const res = await api.get<ApiResponse<BackendIncident>>(`/events/${id}`);
    return { data: adaptIncident(res.data.data) };
  },
  getMapData: async () => {
    const res =
      await api.get<
        ApiResponse<
          Omit<
            BackendIncident,
            | "state"
            | "district"
            | "city"
            | "start_time"
            | "end_time"
            | "confidence"
            | "created_at"
            | "updated_at"
            | "verified_count"
            | "suspicious_count"
            | "duplicate_count"
          >[]
        >
      >("/events/map");
    return {
      data: res.data.data.map((p) => ({
        id: p.id,
        lat: p.latitude,
        lng: p.longitude,
        event_type: adaptEventType(p.event_type),
        severity: adaptSeverity(p.severity),
        confidence: 0,
      })),
    };
  },
};

export const analyticsApi = {
  getAnalytics: async (
    timeSeriesDays: number = 7,
  ): Promise<{ data: AnalyticsData }> => {
    const res = await api.get<ApiResponse<BackendAnalytics>>("/analytics", {
      params: { time_series_days: timeSeriesDays },
    });
    return { data: adaptAnalytics(res.data.data) };
  },
};
