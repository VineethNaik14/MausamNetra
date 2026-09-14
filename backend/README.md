# MausamNetra — Backend

**AI-Powered Weather Incident Verification & Intelligence Platform**
SIH Problem Statement 26069 · Ministry of Earth Sciences (MoES) / IMD · Disaster Management theme

This is the backend prototype: a FastAPI + PostgreSQL/PostGIS service that ingests weather
reports, runs them through a pluggable AI pipeline (classification → trust scoring → duplicate
detection → incident correlation), stores everything geospatially, and exposes REST + WebSocket
APIs for a React dashboard and an admin verification workflow.

> **Prototype disclaimer:** reliability scores, trust-score thresholds, and severity heuristics
> in this codebase are placeholder values for the hackathon demo. They are **not** official IMD
> policy or ratings.

---

## 1. Architecture

```
DATA SOURCES → INGESTION → NORMALIZATION → EVENT CLASSIFICATION → TRUST/VERIFICATION
→ DUPLICATE DETECTION → INCIDENT CORRELATION → POSTGRESQL + POSTGIS → REST API + WEBSOCKET
→ REACT DASHBOARD → ADMIN VERIFICATION
```

Internally, requests flow through layered separation of concerns:

```
Router (app/api)  →  Service (app/services)  →  Repository (app/repositories)  →  Model (app/models)
```

Routes contain **no** business logic, ML logic, or SQL — they validate input, call a service, and
shape the response envelope. Services own orchestration (e.g. the report ingestion pipeline).
Repositories own all SQLAlchemy query logic.

### Report pipeline (`ReportService`)

```
POST /reports → validate → store raw report (status=PENDING)
              → classify (EventClassifier)
              → duplicate detect (DuplicateDetector)
              → trust evaluate (TrustEngine)
              → incident correlate (IncidentCorrelationService)
              → persist (status=PROCESSED)
              → broadcast over WebSocket
```

If any AI step throws, the exception is caught, logged, and the report is marked `FAILED` —
**the original report is never lost.** It can be retried or manually reviewed later.

---

## 2. Technology stack

- **API**: Python 3.12, FastAPI, Uvicorn, Pydantic v2 / pydantic-settings
- **DB**: PostgreSQL 16 + PostGIS 3.4, SQLAlchemy 2.x, GeoAlchemy2, Alembic
- **Auth**: JWT (python-jose), Argon2 password hashing (passlib)
- **Real-time**: FastAPI native WebSockets
- **Containers**: Docker, Docker Compose
- **Testing**: Pytest, FastAPI TestClient / HTTPX
- **AI-ready** (interfaces only, see §8): scikit-learn, Sentence Transformers, OpenCV, PyTorch/Transformers
- **Future scale-out** (not required for MVP, see §14): Kafka, Spark

---

## 3. Folder structure

```
backend/
├── app/
│   ├── main.py                     # FastAPI app, middleware, exception handlers
│   ├── api/                        # Routers only — no business logic
│   │   ├── router.py  auth.py  reports.py  events.py  analytics.py  admin.py  websocket.py
│   ├── core/                       # config, security, logging, exceptions
│   ├── db/                         # engine/session, declarative base, alembic migrations
│   ├── models/                     # SQLAlchemy ORM models (User, Source, Report, Incident, Verification, Duplicate)
│   ├── schemas/                    # Pydantic request/response schemas + AI integration contracts
│   ├── services/                   # Business logic (ReportService, IncidentService, ...)
│   │   └── integrations/           # AI abstraction layer: classifier, trust_engine, duplicate_detector, incident_correlator
│   ├── repositories/                # All SQL / PostGIS query logic
│   └── dependencies/                # FastAPI DI: auth.py (get_current_user/require_admin), services.py (wiring)
├── tests/                           # Pytest suite (auth, admin, reports, events, geospatial, verification, websocket)
├── scripts/
│   ├── create_admin.py             # ONLY supported way to create an admin account
│   └── seed.py                     # Dev-only sample data
├── uploads/{images,videos}/        # Local media storage (swap for S3/MinIO later)
├── alembic.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── pytest.ini
```

---

## 4. Environment setup

```bash
cd backend
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env    # edit JWT_SECRET_KEY and DATABASE_URL for your machine
```

`.env` is git-ignored. **Never commit real secrets.** Generate a strong `JWT_SECRET_KEY`, e.g.:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

---

## 5. Running with Docker (recommended)

```bash
docker compose up --build
```

This starts:
- `db` — `postgis/postgis:16-3.4` with a healthcheck, volume-backed data
- `backend` — runs `alembic upgrade head` then `uvicorn app.main:app` on port 8000

Then, in a second terminal, create your admin account inside the running container:

```bash
docker compose exec backend python scripts/create_admin.py
```

API docs: http://localhost:8000/api/v1/docs

---

## 6. Running locally without Docker

1. Install PostgreSQL 16 + PostGIS locally, then:
   ```bash
   createdb mausamnetra
   psql -d mausamnetra -c "CREATE EXTENSION IF NOT EXISTS postgis;"
   ```
2. Point `DATABASE_URL` in `.env` at that database.
3. Run migrations:
   ```bash
   alembic upgrade head
   ```
4. Create the admin account (interactive prompts for name/email/password):
   ```bash
   python scripts/create_admin.py
   ```
   Or non-interactively (e.g. CI):
   ```bash
   ADMIN_NAME="Admin" ADMIN_EMAIL="admin@yourdomain.example" ADMIN_PASSWORD="StrongPass123!" \
     python scripts/create_admin.py --non-interactive
   ```
5. (Optional) Load sample data for frontend development:
   ```bash
   python scripts/seed.py
   ```
   This prints a dev-only admin login (`dev-admin@mausamnetra.dev` / see script output) —
   **never use this account or password outside local development.**
6. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 7. Database schema summary

| Table           | Purpose                                                             |
|-----------------|----------------------------------------------------------------------|
| `users`         | `id, name, email, password_hash, role (USER/ADMIN), is_active, timestamps` |
| `sources`       | `id, name, type, reliability_score (prototype heuristic), is_active` |
| `reports`       | Raw incoming report: text, event_type/confidence, `GEOGRAPHY(POINT,4326)` location + lat/lon, city/district/state, media_url, status, `incident_id` FK |
| `incidents`     | Correlated real-world event: event_type, severity, location, report/verified/suspicious/duplicate counters, status |
| `verifications` | 1:1 with report — trust_score (0-100), status, reason, verified_by/at |
| `duplicates`    | 1:1 with report — `master_report_id`, `similarity_score`. Duplicates are never deleted, only linked. |

All geospatial columns use `GEOGRAPHY(POINT, 4326)` with GiST indexes; nearby queries use
`ST_DWithin` / `ST_Distance`. Indexes also cover `timestamp`, `event_type`, `status`, `state`,
`city`, and `source_id` on reports (mirrored on incidents where relevant).

The single migration (`0001_initial_schema`) was verified against the ORM models with
`alembic revision --autogenerate` producing an empty diff (zero drift) — including a full
`upgrade → downgrade → upgrade` cycle — so `alembic downgrade base` is safe to run.

---

## 8. AI integration points — **read this if you're the AI/ML teammate**

The backend never depends on a real AI implementation to run. Each integration point is a Python
`Protocol` + a `Mock*` implementation, wired through one file: **`app/dependencies/services.py`**.

| Integration          | Protocol (in `app/services/integrations/`) | Mock                    | Contract schemas (`app/schemas/ai_integration.py`) |
|-----------------------|--------------------------------------------|--------------------------|------------------------------------------------------|
| Event classification  | `EventClassifier.classify(data)`           | `MockEventClassifier`    | `ClassifierInput` → `ClassifierOutput`               |
| Trust / verification   | `TrustEngine.evaluate(data)`               | `MockTrustEngine`        | `TrustEngineInput` → `TrustEngineOutput`             |
| Duplicate detection    | `DuplicateDetector.detect(data)`           | `MockDuplicateDetector`  | `DuplicateDetectorInput` → `DuplicateDetectorOutput` |
| Incident correlation   | `IncidentCorrelator.correlate(...)`        | *(real rule-based MVP already implemented — not a mock)* | `CorrelationCandidateIncident` → `CorrelationResult` |

### How to plug in your real model

1. Implement a class satisfying the relevant `Protocol` (e.g. `RealEventClassifier` implementing
   `classify(data: ClassifierInput) -> ClassifierOutput`) anywhere convenient — a new module under
   `app/services/integrations/` is the natural home.
2. Open **`app/dependencies/services.py`** and change the one-line factory, e.g.:
   ```python
   def get_event_classifier() -> EventClassifier:
       return RealEventClassifier()   # was: MockEventClassifier()
   ```
3. That's it. No route, schema, or database change needed, as long as your class returns the
   contract's Pydantic output shape.

### Example payloads

**Event Classifier**
```json
// input
{"report_id": "…", "text": "Heavy rainfall has flooded roads", "media_url": null}
// output
{"event_type": "FLOOD", "confidence": 0.94}
```

**Trust Engine**
```json
// output
{"trust_score": 91, "status": "VERIFIED", "reasons": ["Strong location consistency", "Multiple corroborating reports"]}
```

**Duplicate Detector**
```json
// output
{"is_duplicate": true, "master_report_id": "…", "similarity_score": 0.93}
```

The mocks are intentionally simple and transparent (keyword matching, a scored heuristic,
`difflib` text similarity) — good enough to exercise the full pipeline end-to-end, but they must
never be presented as real AI/ML results.

---

## 9. Authentication & authorization flow

1. `POST /api/v1/auth/login` — email + password → JWT access token (short-lived, see
   `ACCESS_TOKEN_EXPIRE_MINUTES`). Same generic error for "no such user" and "wrong password" to
   avoid leaking which emails are registered.
2. Every protected route depends on `get_current_user` (`app/dependencies/auth.py`), which:
   validates the JWT signature/expiry → loads the user from the DB → checks `is_active`.
3. Admin-only routes additionally depend on `require_admin`, which checks `role == ADMIN` and
   raises `403 Forbidden` otherwise. An unauthenticated request gets `401 Unauthorized`.
4. **There is no public registration endpoint, and no endpoint accepts a `role` field from the
   client.** The only way to create an ADMIN account is `scripts/create_admin.py`, run directly
   against the database — a normal user has no code path to self-promote.

---

## 10. API endpoint summary

All routes are versioned under `/api/v1`.

| Method | Path | Auth | Purpose |
|---|---|---|---|
| POST | `/auth/login` | — | Obtain JWT |
| GET | `/auth/me` | user | Current user info |
| POST | `/auth/logout` | user | Stateless logout (client discards token) |
| POST | `/reports/upload-media` | user | Upload photo/video, get back a media URL |
| POST | `/reports` | user | Submit a report (runs the full AI pipeline) |
| GET | `/reports` | user | List + filter (`event,state,district,city,status,source_id`) + paginate |
| GET | `/reports/{id}` | user | Get one report |
| POST | `/reports/{id}/verify` | **admin** | Manually verify |
| POST | `/reports/{id}/reject` | **admin** | Reject with reason |
| POST | `/reports/{id}/escalate` | **admin** | Escalate to NEEDS_REVIEW |
| GET | `/events` | user | List incidents, filter + paginate |
| GET | `/events/map` | user | Lightweight incident points for Leaflet |
| GET | `/events/nearby` | user | `ST_DWithin` radius search (`latitude, longitude, radius_km`, + event/state/district/city) |
| GET | `/events/{id}` | user | Get one incident |
| GET | `/analytics` | user | Dashboard metrics (see §11) |
| GET | `/admin/reports` | **admin** | All reports incl. PENDING/FAILED |
| GET | `/admin/reports/{id}` | **admin** | Full report detail |
| GET | `/admin/statistics` | **admin** | Verification pipeline counts |
| WS | `/ws/incidents` | — | Real-time incident/verification feed |

Full interactive documentation (request/response schemas, try-it-out): **`/api/v1/docs`**
(Swagger) and **`/api/v1/redoc`**.

---

## 11. Analytics response shape

```json
{
  "success": true,
  "data": {
    "summary": {"active_events": 2, "total_reports": 4, "verified_reports": 2,
                "suspicious_reports": 1, "pending_verification": 1, "rejected_reports": 0},
    "event_distribution": [{"key": "FLOOD", "count": 3}, {"key": "HEATWAVE", "count": 1}],
    "severity_distribution": [{"key": "LOW", "count": 1}, {"key": "MODERATE", "count": 1}],
    "source_distribution": [{"key": "Citizen App", "count": 1}, ...],
    "geographic_distribution": [{"key": "Karnataka", "count": 3}, ...],
    "time_series": [{"date": "2026-09-11", "count": 3}, {"date": "2026-09-12", "count": 1}]
  }
}
```

---

## 12. WebSocket usage

Connect to `ws://<host>/ws/incidents`. No auth handshake is required for the prototype (the feed
is read-only, non-sensitive aggregate data); add a token-based upgrade path before any real
deployment. The server pushes JSON messages such as:

```json
{"type": "NEW_INCIDENT", "incident": {"id": "…", "event": "FLOOD", "severity": "HIGH", "latitude": 13.0358, "longitude": 77.597}}
{"type": "INCIDENT_UPDATED", "incident": {...}}
{"type": "REPORT_VERIFIED", "report_id": "…", "incident_id": "…"}
{"type": "REPORT_REJECTED", "report_id": "…"}
```

---

## 13. PostGIS queries used

- **Storage**: `location GEOGRAPHY(POINT, 4326)` on both `reports` and `incidents`, built via
  `ST_SetSRID(ST_MakePoint(lon, lat), 4326)::geography`, with a GiST index.
- **Nearby search**: `ST_DWithin(location, origin, radius_metres)` filters, ordered by
  `ST_Distance(location, origin)` (returned to the client in km).
- Example: *"flood incidents within 10km of Bengaluru"* →
  `GET /api/v1/events/nearby?latitude=12.9716&longitude=77.5946&radius_km=10&event=flood`

---

## 14. Frontend integration notes

- All responses use one of two envelopes:
  ```json
  {"success": true, "data": {...}, "message": "..."}
  {"success": true, "data": [...], "pagination": {"page":1,"page_size":20,"total":100,"total_pages":5}}
  ```
  Errors: `{"success": false, "error": {"code": "...", "message": "..."}}`.
- Store the JWT client-side and send `Authorization: Bearer <token>` on every request.
- `/events/map` is intentionally minimal (id, event_type, severity, status, lat/lon, report_count)
  — fetch `/events/{id}` for full detail on marker click.
- CORS origins are controlled by `CORS_ORIGINS` in `.env` (comma-separated).

---

## 15. Sample requests

```bash
# Login
curl -X POST localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@yourdomain.example","password":"..."}'

# Create a report
curl -X POST localhost:8000/api/v1/reports \
  -H "Authorization: Bearer $TOKEN" -H "Content-Type: application/json" \
  -d '{"source_id":"<uuid>","text":"Heavy rainfall has flooded roads","latitude":12.9716,"longitude":77.5946,"city":"Bengaluru","state":"Karnataka"}'

# Nearby incidents
curl "localhost:8000/api/v1/events/nearby?latitude=12.97&longitude=77.59&radius_km=10&event=flood" \
  -H "Authorization: Bearer $TOKEN"
```

---

## 16. Security considerations

- Argon2 password hashing (`passlib[argon2]`); passwords are never logged or returned in any
  response schema.
- Short-lived JWTs signed with `JWT_SECRET_KEY` (from environment only — never hardcoded).
- `require_admin` enforces role checks **server-side**; the frontend hiding a button is never
  relied upon.
- File uploads: extension allow-list, MIME-agnostic size cap (`MAX_UPLOAD_SIZE`), server-generated
  UUID filenames (client filenames are never trusted), and a resolved-path check defending against
  traversal even though generated names can't contain path separators.
- All DB access goes through SQLAlchemy Core/ORM (no raw string-interpolated SQL) — standard
  injection protection.
- Centralized exception handling (`app/main.py`) guarantees stack traces, SQL text, and internal
  paths are never returned to a client; unexpected errors become a generic `500` with a log entry
  server-side.
- `.env` is git-ignored; `.env.example` documents required variables without real values.

---

## 17. Testing

Tests run against a **real PostgreSQL + PostGIS** database (SQLite cannot support the geography
types/functions this app relies on), mirroring the Docker Compose setup.

```bash
createdb mausamnetra_test
psql -d mausamnetra_test -c "CREATE EXTENSION IF NOT EXISTS postgis;"
export TEST_DATABASE_URL=postgresql+psycopg://postgres:postgres@localhost:5432/mausamnetra_test
pytest
```

Each test runs inside a transaction + SAVEPOINT that is rolled back afterwards, so tests never
leak state into one another even though the application code under test calls `session.commit()`.

Coverage includes: login (valid/invalid/inactive), JWT (missing/invalid/expired), admin vs user
authorization (403/401), report CRUD + coordinate validation + filtering + pagination, incident
listing + map + nearby (PostGIS `ST_DWithin`), manual verify/reject/escalate, password-never-leaked
checks, and WebSocket connect/broadcast/disconnect.

---

## 18. Future Kafka/Spark integration (not required for MVP)

The report ingestion pipeline (`ReportService._run_pipeline`) is already isolated behind clean
interfaces, so a future high-throughput version could:
- Publish incoming reports to a Kafka topic instead of running the pipeline inline in the request
  path, with a consumer worker calling the same `EventClassifier` / `TrustEngine` /
  `DuplicateDetector` / `IncidentCorrelator` abstractions.
- Use Spark (Structured Streaming) for large-scale duplicate/correlation batch jobs feeding back
  into the same `incidents` / `duplicates` tables.

None of this is wired up, and it should not be until the MVP demonstrates the need — the current
architecture does not block it later.

---

## 19. Remaining TODOs

- [ ] Replace `MockEventClassifier`, `MockTrustEngine`, `MockDuplicateDetector` with real
      implementations (see §8).
- [ ] Add a token revocation/blocklist if immediate server-side logout becomes a requirement.
- [ ] Add authentication to the `/ws/incidents` WebSocket before any non-prototype deployment.
- [ ] Swap local `uploads/` storage for S3/MinIO (only `app/services/media_service.py` needs to
      change).
- [ ] Add rate limiting middleware (e.g. `slowapi`) in front of `/auth/login` and `/reports`.
- [ ] Kafka/Spark integration for scale (see §18) — intentionally out of scope for the MVP.

---

## 20. Final checklist

- [x] Backend starts (`uvicorn app.main:app`)
- [x] PostgreSQL/PostGIS connects
- [x] Alembic migration (`0001_initial_schema`) applies cleanly
- [x] Admin created via `scripts/create_admin.py`, cannot be self-assigned via any API
- [x] JWT login/verification works; expired/invalid tokens rejected
- [x] Normal users get `403` on admin routes; unauthenticated get `401`
- [x] Reports: create/retrieve/filter/paginate, invalid lat/lon rejected (422)
- [x] Incidents: list/map/nearby (`ST_DWithin`) all verified against a live PostGIS DB
- [x] Analytics endpoint returns dashboard-ready aggregates
- [x] Admin verify/reject/escalate flows tested
- [x] Duplicate relationships stored (never deletes the duplicate report)
- [x] AI interfaces + mocks exist and are swappable via one file
- [x] AI pipeline failures leave the report `FAILED`, never lost
- [x] WebSocket connect/broadcast/disconnect tested
- [x] Media upload validated (extension allow-list, size cap, safe filenames)
- [x] Centralized, secret-free error handling
- [x] 46 tests passing against a live Postgres+PostGIS instance
- [x] Docker Compose boots db + backend together
- [x] No secrets committed (`.env` git-ignored, `.env.example` provided)
