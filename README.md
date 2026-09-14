# 🌦️ MausamNetra

**AI-Powered Weather Incident Verification & Intelligence Platform**

> Turning fragmented, noisy weather reports from APIs, citizens, and public feeds into **verified, geospatially organized incidents** for disaster-management decision-making.

---

## Table of Contents

- [Overview](#overview)
- [The Problem](#the-problem)
- [Key Innovation The Trust Engine](#key-innovation--the-trust-engine)
- [System Architecture](#system-architecture)
- [Tech Stack](#tech-stack)
- [Repository Structure](#repository-structure)
- [Getting Started](#getting-started)
  - [Option A: Docker Compose (recommended)](#option-a-docker-compose-recommended)
  - [Option B: Manual / Local Development](#option-b-manual--local-development)
- [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Demo Walkthrough](#demo-walkthrough)
- [Project Status & Known Limitations](#project-status--known-limitations)
- [Team](#team)
- [License](#license)

---

## Overview

During floods, cyclones, heatwaves, and other extreme weather events, information arrives simultaneously from weather APIs, public datasets, news, citizen reports, and social feeds often incomplete, duplicated, outdated, or misleading.

**MausamNetra** sits between raw information and disaster-management decision-makers, implementing the pipeline:

```
Collect → Clean → Classify → Verify → Deduplicate → Correlate → Visualize → Alert
```

It ingests heterogeneous weather reports, classifies the event type, assigns an **evidence-based trust score**, groups duplicate reports into a single incident, and displays everything on a real-time geospatial dashboard with an admin verification panel.

This is a hackathon prototype (SIH Problem Statement 26069) built for a small, fully-working end-to-end demo rather than a national-scale production system.

## The Problem

The core question MausamNetra answers is not *"is there enough weather data?"* it's:

> **Which reports are reliable, which describe the same incident, what type of event is occurring, and where is it actually happening?**

Example: during a flood, 20 citizens may report the same event, a news site may cover it, a weather API may show extreme rainfall, and one report may reuse an old photo or the wrong location. Without an intelligence layer these are disconnected data points. MausamNetra turns them into one structured incident record with a report count, source count, duplicate count, event type, severity, and confidence score.

## Key Innovation The Trust Engine

Every incoming report receives an evidence-based reliability score combining:

| Component | Weight |
|---|---|
| Source Reliability | 20% |
| Location Consistency | 20% |
| Temporal Consistency | 15% |
| Cross-Source Agreement | 20% |
| Media/Text Consistency | 15% |
| Metadata Completeness | 10% |

```
80–100  → VERIFIED
60–79   → NEEDS_REVIEW
0–59    → SUSPICIOUS
```

The score is explainable every result includes the specific reasons behind it (e.g. *"GPS does not match reported location"*, *"Image similarity indicates possible reuse"*) and is a **decision-support signal for human admins**, not an automatic replacement for verification.

## System Architecture

MausamNetra is a set of independently deployable services connected over HTTP and Kafka:

![alt text](images/system_arch.png)

**Why separate services?** The classifier and trust engine are independently deployable FastAPI microservices with a stable Pydantic contract (`app/schemas/ai_integration.py`), so the ML team can iterate and redeploy their models without touching backend or frontend code.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React + Vite, TypeScript, Tailwind CSS, Leaflet/MapTiler, Recharts |
| Backend API | Python, FastAPI, SQLAlchemy, Alembic |
| Database | PostgreSQL + PostGIS (geospatial queries) |
| Event Classification | scikit-learn (TF-IDF + Logistic Regression), served via FastAPI |
| Trust / Verification Engine | Custom rules + scikit-learn, TF-IDF text similarity, perceptual image hashing, served via FastAPI |
| Real-time updates | WebSockets |
| Streaming / Big Data | Apache Kafka (ingestion → backend bridge) |
| Auth | JWT (python-jose), Argon2 password hashing |
| Deployment | Docker, Docker Compose |

## Repository Structure

```
MausamNetra/
├── backend/                  # FastAPI core service owns the DB, orchestrates the pipeline
│   └── app/
│       ├── api/               # Route handlers (reports, events, admin, auth, sources, analytics)
│       ├── models/             # SQLAlchemy models
│       ├── schemas/            # Pydantic request/response + AI-service contracts
│       ├── services/           # Business logic (report_service, verification_service, ...)
│       │   └── integrations/    # HTTP adapters to the classifier & verification microservices
│       ├── repositories/       # Data access layer
│       └── dependencies/       # DI: DB session, auth, service wiring
│
├── ml/
│   ├── classification/        # Event classifier microservice (Member 3)
│   │   ├── src/                # train.py, preprocess.py, predict.py, evaluate.py
│   │   ├── api/                 # FastAPI wrapper (/classify)
│   │   └── models/              # Trained model artifacts (.joblib) + eval metrics
│   └── verification/          # Trust engine microservice (Member 4)
│       ├── components/          # Source reliability, location/temporal consistency,
│       │                        #   cross-source agreement, text/image similarity
│       ├── engine/               # Score aggregation + status decision
│       └── api/                  # FastAPI wrapper (/api/v1/verification/verify)
│
├── ingestion/                # Multi-source ingestion (Member 2)
│   ├── weather_api/, dataset/, social_simulator/, citizen_reports/
│   ├── cleaner.py, normalizer.py, dedup.py
│
├── integration/               # Kafka consumer → POSTs normalized reports to backend
│
├── frontend/                  # React dashboard (Member 6)
│   └── src/
│       ├── pages/               # PublicDashboard, ReportSubmission, AdminPanel, Login, ...
│       ├── maps/                 # Live incident map (Leaflet/MapTiler)
│       ├── services/             # api.ts (REST client), ws.ts (WebSocket), AuthContext
│       └── components/
│
├── data/                       # Sample / prototype datasets
├── de_tests/                   # Data-engineering / ingestion test suite
├── docker-compose.yml
├── main.py                     # Standalone ASGI entrypoint (verification service, dev use)
└── requirements.txt
```

## Getting Started

### Option A: Docker Compose (recommended)

This brings up Postgres+PostGIS, Kafka, the ingestion worker, the classifier, the trust engine, the backend (running migrations automatically), and the pipeline-worker bridge.

```bash
# 1. Configure the backend
cp backend/.env.example backend/.env
# edit backend/.env set a real JWT_SECRET_KEY at minimum

# 2. Start everything
docker compose up --build

# 3. Create an admin user (one-time)
docker compose exec backend python scripts/create_admin.py

# 4. (Optional) Seed demo data incidents, reports, verifications
docker compose exec backend python scripts/seed.py
```

| Service | URL |
|---|---|
| Backend API | http://localhost:8000/api/v1 |
| API docs (Swagger) | http://localhost:8000/docs |
| Classifier | http://localhost:8002 |
| Verification engine | http://localhost:8001 |
| PostgreSQL | localhost:5432 |

The **frontend is not containerized** run it separately with `npm run dev` (see below) pointed at `http://localhost:8000/api/v1`.

### Option B: Manual / Local Development

Run each service in its own terminal/virtualenv. Useful when actively developing one component.

**1. Database**
```bash
# Requires PostgreSQL with the PostGIS extension available
createdb mausamnetra
psql -d mausamnetra -c "CREATE EXTENSION IF NOT EXISTS postgis;"
```

**2. Classifier service** (port 8002 locally)
```bash
cd ml/classification
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt fastapi uvicorn
uvicorn api.main:app --app-dir . --host 0.0.0.0 --port 8002
```

**3. Verification / trust-engine service** (port 8001)
```bash
cd MausamNetra   # repo root
python -m venv .venv-verify && source .venv-verify/bin/activate
pip install -r verification_requirements.txt
uvicorn ml.verification.api.main:app --host 0.0.0.0 --port 8001
```
> `sentence-transformers` in `verification_requirements.txt` is optional if it or its model weights aren't available, the trust engine automatically falls back to a TF-IDF similarity backend with no loss of functionality (useful in offline demo environments).

**4. Backend API** (port 8000)
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set DATABASE_URL, JWT_SECRET_KEY, CLASSIFIER_SERVICE_URL=http://localhost:8002,
                        # VERIFICATION_SERVICE_URL=http://localhost:8001

alembic upgrade head
python scripts/create_admin.py
python scripts/seed.py        # optional demo data
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**5. Frontend** (port 3000)
```bash
cd frontend
npm install
cp .env.example .env
# set VITE_API_URL="http://localhost:8000/api/v1"
npm run dev
```

**6. Ingestion + Kafka bridge** *(optional only needed to demo the automated multi-source ingestion path; you can also submit reports directly via the API/UI without this)*
```bash
# Requires a running Kafka broker on localhost:9092
cd ingestion
python -m venv .venv && source .venv/bin/activate
pip install -r ../ingestion_requirements.txt
python demo.py   # or realtime_demo.py for a continuous simulated stream
```

## Environment Variables

**`backend/.env`**

| Variable | Description | Example |
|---|---|---|
| `DATABASE_URL` | Postgres connection string | `postgresql+psycopg://user:pass@localhost:5432/mausamnetra` |
| `JWT_SECRET_KEY` | Secret for signing JWTs **generate a real one** | `python -c "import secrets; print(secrets.token_urlsafe(64))"` |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Token lifetime | `30` |
| `CORS_ORIGINS` | Allowed frontend origins, comma-separated | `http://localhost:3000` |
| `CLASSIFIER_SERVICE_URL` | Base URL of the classifier microservice | `http://localhost:8002` |
| `VERIFICATION_SERVICE_URL` | Base URL of the trust-engine microservice | `http://localhost:8001` |
| `UPLOAD_DIR` / `MAX_UPLOAD_SIZE` | Media upload storage | `uploads` / `10485760` |

**`frontend/.env`**

| Variable | Description |
|---|---|
| `VITE_API_URL` | Backend REST base URL, e.g. `http://localhost:8000/api/v1` (the WebSocket and media URLs are derived from this) |
| `VITE_MAPTILER_API_KEY` | API key for the live map tiles |

## API Reference

Base path: `/api/v1`. Full interactive docs at `/docs` once the backend is running.

| Method | Endpoint | Description | Auth |
|---|---|---|---|
| `POST` | `/reports` | Submit a new weather report (triggers the full classify → verify → dedupe → correlate pipeline) | Public |
| `POST` | `/reports/upload-media` | Upload a photo/video to attach to a report | Public |
| `GET` | `/reports` | List reports with filters (event, state, district, city, status, source) + pagination | Public |
| `GET` | `/reports/{id}` | Get a single report | Public |
| `POST` | `/reports/{id}/verify` | Manually verify a report | Admin |
| `POST` | `/reports/{id}/reject` | Reject a report | Admin |
| `POST` | `/reports/{id}/escalate` | Escalate a report for further review | Admin |
| `GET` | `/events` | List incidents with filters + pagination | Public |
| `GET` | `/events/map` | Lightweight incident points for the live map | Public |
| `GET` | `/events/nearby` | Incidents within a radius (PostGIS `ST_DWithin`) | Public |
| `GET` | `/events/{id}` | Single incident detail | Public |
| `GET` | `/analytics` | Dashboard summary metrics, event/severity distribution, time series | Public |
| `GET` | `/sources` | List active report sources | Public |
| `POST` | `/auth/login` | Obtain a JWT access token | Public |
| `GET` | `/auth/me` | Current authenticated user | User |
| `GET` | `/admin/reports` | All reports including PENDING/FAILED | Admin |
| `GET` | `/admin/reports/{id}` | Full admin detail of any report | Admin |
| `GET` | `/admin/statistics` | Verification pipeline statistics | Admin |
| `WS` | `/ws/incidents` | Real-time incident create/update broadcast | Public |

## Database Schema

Core tables (see `backend/app/models/` and `backend/alembic/`):

![alt text](images/database_schema.png)

## Testing

```bash
# Backend (requires a running Postgres + PostGIS instance)
cd backend
export TEST_DATABASE_URL="postgresql+psycopg://postgres:postgres@localhost:5432/mausamnetra_test"
export PYTHONPATH=.
pytest -q

# Classifier
cd ml/classification && pytest -q

# Verification / trust engine
cd ml/verification && pytest -q

# Ingestion / data-engineering
pytest de_tests/ -q

# Frontend type-check + build
cd frontend
npm run lint     # tsc --noEmit
npm run build
```

## Demo Walkthrough

A good end-to-end demo tells one story:

1. **Citizen submits a report** "Heavy rainfall has caused severe waterlogging" from Hebbal, Bengaluru, with a photo and GPS.
2. **Classifier** tags it `FLOOD` with a confidence score.
3. **Trust engine** scores source reliability, location/temporal consistency, and cross-source agreement into a trust score with an explanation.
4. **Duplicate detector** groups it with similar reports already in the system.
5. **Incident correlation** creates/updates a single `BENGALURU FLOOD INCIDENT` aggregating report count, verified count, suspicious count, severity, and confidence.
6. **Live map** updates over the WebSocket connection in real time.
7. **Admin panel** shows the report queued for review with `[VERIFY] [REJECT] [ESCALATE]` actions.

## Project Status & Known Limitations

This is a hackathon prototype being upfront about its current limits matters more than overselling it:

- **Event classifier is trained on a small (~550-row), templated dataset.** It performs strongly on phrasing close to its training examples but is sensitive to wording it hasn't seen; treat reported accuracy figures as indicative of the current dataset, not general-purpose robustness. Retraining on a larger, more varied corpus is a priority before wider use.
- **The trust score is a prototype decision-support signal, not an official IMD certification.** Thresholds and weights are a configurable starting policy.
- **Public social-media ingestion is simulated** for the prototype rather than pulling from live platform APIs.
- Kafka/Spark are included to demonstrate the scalable architecture; the prototype workload does not require their full scale.

## License

Prototype developed for Smart India Hackathon, Problem Statement 26069. License to be finalized by the team/organization.