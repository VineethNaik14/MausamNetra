import { IncidentEvent } from "../types";
import { API_URL } from "./api";

type WebSocketEvent =
  | { type: 'NEW_INCIDENT'; payload: IncidentEvent }
  | { type: 'INCIDENT_UPDATED'; payload: IncidentEvent }
  | { type: 'REPORT_VERIFIED'; payload: { report_id: string; event_id: string } }
  | { type: 'REPORT_REJECTED'; payload: { report_id: string } };

type Listener = (event: WebSocketEvent) => void;

const SEVERITY_MAP: Record<string, IncidentEvent['severity']> = {
  LOW: 'Low',
  MODERATE: 'Medium',
  HIGH: 'High',
  SEVERE: 'Critical',
};

function titleCase(s: string): string {
  return s
    .toLowerCase()
    .split(/[_\s]+/)
    .map((w) => (w ? w[0].toUpperCase() + w.slice(1) : w))
    .join(' ');
}

// Backend broadcast shapes (see app/services/websocket_service.py):
//   {"type": "NEW_INCIDENT", "incident": {...}}
//   {"type": "INCIDENT_UPDATED", "incident": {...}}
//   {"type": "REPORT_VERIFIED", "report_id": "...", "incident_id": "..."}
//   {"type": "REPORT_REJECTED", "report_id": "..."}
// NOTE: the NEW_INCIDENT payload only carries a subset of Incident fields
// (id, event_type, severity, status, latitude, longitude, city, state,
// confidence, report_count, verified_count, suspicious_count,
// duplicate_count) - not the full IncidentRead shape. Missing fields below
// are filled with safe defaults; refetch the incident/dashboard for the
// complete record when precision matters.
function adaptIncidentPayload(raw: any): IncidentEvent {
  return {
    id: raw.id,
    event_type: raw.event_type ? titleCase(raw.event_type) : 'Other',
    severity: SEVERITY_MAP[raw.severity] || 'Medium',
    location: {
      lat: raw.latitude,
      lng: raw.longitude,
      city: raw.city || undefined,
      state: raw.state || undefined,
    },
    confidence: raw.confidence ?? 0,
    report_counts: {
      verified: raw.verified_count ?? 0,
      suspicious: raw.suspicious_count ?? 0,
      duplicate: raw.duplicate_count ?? 0,
      total: raw.report_count ?? 1,
    },
    status: raw.status === 'RESOLVED' || raw.status === 'DISMISSED' ? 'Resolved' : 'Active',
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };
}

class WebSocketService {
  private ws: WebSocket | null = null;
  private listeners: Set<Listener> = new Set();
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null;
  private manuallyDisconnected = false;

  connect() {
    this.manuallyDisconnected = false;
    const wsUrl = API_URL.replace(/^http/, 'ws').replace(/\/api\/v1\/?$/, '') + '/ws/incidents';

    try {
      this.ws = new WebSocket(wsUrl);
    } catch (err) {
      console.error('[WebSocket] Failed to construct connection', err);
      this.scheduleReconnect();
      return;
    }

    this.ws.onopen = () => {
      console.log('[WebSocket] Connected to', wsUrl);
    };

    this.ws.onmessage = (event) => {
      try {
        const msg = JSON.parse(event.data);
        if (msg.type === 'NEW_INCIDENT' && msg.incident) {
          this.notifyListeners({ type: 'NEW_INCIDENT', payload: adaptIncidentPayload(msg.incident) });
        } else if (msg.type === 'INCIDENT_UPDATED' && msg.incident) {
          this.notifyListeners({ type: 'INCIDENT_UPDATED', payload: adaptIncidentPayload(msg.incident) });
        } else if (msg.type === 'REPORT_VERIFIED') {
          this.notifyListeners({
            type: 'REPORT_VERIFIED',
            payload: { report_id: msg.report_id, event_id: msg.incident_id },
          });
        } else if (msg.type === 'REPORT_REJECTED') {
          this.notifyListeners({ type: 'REPORT_REJECTED', payload: { report_id: msg.report_id } });
        }
      } catch (err) {
        console.error('[WebSocket] Failed to parse message', err);
      }
    };

    this.ws.onclose = () => {
      console.log('[WebSocket] Disconnected');
      if (!this.manuallyDisconnected) {
        this.scheduleReconnect();
      }
    };

    this.ws.onerror = (err) => {
      console.error('[WebSocket] Error', err);
    };
  }

  private scheduleReconnect() {
    if (this.reconnectTimer) return;
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null;
      if (!this.manuallyDisconnected) this.connect();
    }, 5000);
  }

  subscribe(listener: Listener) {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  private notifyListeners(event: WebSocketEvent) {
    this.listeners.forEach((l) => l(event));
  }

  disconnect() {
    this.manuallyDisconnected = true;
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer);
      this.reconnectTimer = null;
    }
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }
}

export const wsService = new WebSocketService();
