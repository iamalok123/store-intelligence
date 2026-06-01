# Store Intelligence — Architecture & Submission Guide

## 1. What This Application Does

This project is an end-to-end **Store Intelligence** system built for the Apex Retail engineering challenge. It transforms raw anonymised CCTV footage into actionable retail analytics through a four-stage pipeline:

```
Raw CCTV Clips → Detection Layer → Structured Event Stream → Intelligence API → Live Dashboard
```

**North Star Metric:** Offline Store Conversion Rate

```
Conversion Rate = POS-matched purchasing visitors ÷ Total unique customer visitors
```

The system detects and tracks individuals across store zones, emits structured behavioural events (entries, exits, zone dwells, billing queue activity), correlates those events with POS transaction data, and exposes real-time analytics through a REST API and React dashboard.

---

## 2. Complete Application Flow

```
data/cctv_footage/*.mp4
  → pipeline/detect.py         (YOLOv8 + ByteTrack person detection & tracking)
  → pipeline/state.py          (Visitor state machine: entry/exit/zone/dwell/reentry logic)
  → pipeline/zones.py          (Zone polygon matching from store_layout.json)
  → pipeline/emit.py           (Schema-valid event generation with UUID, timestamps)
  → data/events.jsonl          (Output: structured JSONL event stream)
  → pipeline/replay_events.py  (Batch POST to API in groups of 500)
  → POST /events/ingest        (FastAPI validates, deduplicates, stores in SQLite)
  → SQLite: events + pos_transactions tables
  → GET /metrics, /funnel, /heatmap, /anomalies, /health  (Analytics computed on-demand)
  → React Dashboard at http://localhost:5173  (Real-time polling every 2-5 seconds)
```

---

## 3. Project Structure

```
store-intelligence/
├── app/                          # FastAPI backend
│   ├── main.py                   # FastAPI entrypoint, CORS, exception handlers
│   ├── models.py                 # Pydantic schemas (EventIn, responses)
│   ├── database.py               # SQLAlchemy engine + session factory
│   ├── db_models.py              # SQLAlchemy table definitions (EventDB, PosTransactionDB)
│   ├── ingestion.py              # POST /events/ingest — validate, dedup, store
│   ├── metrics.py                # GET /stores/{id}/metrics — visitors, conversion, dwell
│   ├── funnel.py                 # GET /stores/{id}/funnel — session-based conversion funnel
│   ├── heatmap.py                # GET /stores/{id}/heatmap — zone performance scores
│   ├── anomalies.py              # GET /stores/{id}/anomalies — queue spike, dead zone, etc.
│   ├── health.py                 # GET /health — DB status, stale feed detection
│   ├── pos_matcher.py            # POS CSV loading, billing-zone matching, conversion calc
│   ├── logging_config.py         # Structured JSON logging middleware (trace_id, latency)
│   └── errors.py                 # Error response utilities
│
├── pipeline/                     # Detection pipeline
│   ├── detect.py                 # Main YOLO detection + tracking script
│   ├── state.py                  # VisitorStateTracker — entry/exit/zone state machine
│   ├── zones.py                  # Zone polygons, entry line crossing, direction detection
│   ├── emit.py                   # Event factory + JSONL writer
│   ├── replay_events.py          # Replay events.jsonl into API via HTTP POST
│   ├── run.sh                    # One-command pipeline runner
│   ├── tracker.py                # Tracking utilities (empty, ByteTrack handled by YOLO)
│   ├── staff.py                  # Staff detection heuristics (empty, logic in state.py)
│   └── pos_matcher.py            # POS matcher stub (empty, logic in app/pos_matcher.py)
│
├── dashboard/                    # React + Vite dashboard
│   ├── src/App.tsx               # Main component with polling
│   ├── src/api.ts                # API client functions
│   ├── src/components/           # MetricCard, FunnelChart, HeatmapGrid, AnomalyList, HealthStatus
│   ├── Dockerfile                # Node container for dev server
│   └── package.json              # Dependencies (React, Recharts, Tailwind, Lucide)
│
├── tests/                        # 51 tests across 11 files
│   ├── test_ingest.py            # Ingestion: valid, duplicate, invalid, batch, partial success
│   ├── test_metrics.py           # Metrics: empty store, staff-only, calculation correctness
│   ├── test_funnel.py            # Funnel: empty, repeated events, reentry, staff, POS purchase
│   ├── test_heatmap.py           # Heatmap: empty, low/high confidence, normalization
│   ├── test_anomalies.py         # Anomalies: queue spike, conversion drop, dead zone
│   ├── test_health.py            # Health: empty DB, stale feed, fresh feed, DB failure
│   ├── test_pipeline_emit.py     # Emit: event creation, validation, JSONL writing
│   ├── test_pipeline_state.py    # State: entry/exit, zone, dwell, billing, staff, reentry
│   ├── test_pos.py               # POS: 5-min matching, out-of-window, CSV format parsing
│   ├── test_replay.py            # Replay: batch posting with mocked HTTP
│   └── test_zones.py             # Zones: polygon, bbox, line crossing, direction
│
├── docs/
│   ├── DESIGN.md                 # Architecture + AI-Assisted Decisions section
│   └── CHOICES.md                # 3 key decisions: model, schema, API architecture
│
├── data/
│   ├── store_layout.json         # Zone polygons, camera definitions, store metadata
│   ├── files/                    # POS CSV (Brigade_Bangalore_10_April_26.csv)
│   ├── events_test.jsonl         # Sample test events
│   └── cctv_footage/             # CCTV clips (not committed to git)
│
├── docker-compose.yml            # API + Dashboard orchestration
├── Dockerfile                    # Python 3.11 slim API image
├── requirements-api.txt          # API-only dependencies (FastAPI, SQLAlchemy, Pydantic)
├── requirements-pipeline.txt     # Pipeline dependencies (YOLO, OpenCV, NumPy)
├── requirements-dev.txt          # Dev/test dependencies (pytest, httpx, coverage)
├── requirements.txt              # All dependencies combined
├── .env.example                  # Environment variable template
├── .gitignore                    # Files excluded from git
├── .dockerignore                 # Files excluded from Docker build context
└── README.md                     # Quick start guide
```

---

## 4. API Endpoints Reference

### POST /events/ingest
**Purpose:** Accept batches of up to 500 structured events, validate, deduplicate by event_id, and store.

```bash
curl -X POST http://localhost:8000/events/ingest \
  -H "Content-Type: application/json" \
  -d '{"events":[{
    "event_id": "550e8400-e29b-41d4-a716-446655440000",
    "store_id": "STORE_BLR_002",
    "camera_id": "CAM_ENTRY_01",
    "visitor_id": "VIS_001",
    "event_type": "ENTRY",
    "timestamp": "2026-03-03T14:22:10Z",
    "zone_id": null,
    "dwell_ms": 0,
    "is_staff": false,
    "confidence": 0.91,
    "metadata": {"queue_depth": null, "sku_zone": null, "session_seq": 1}
  }]}'
```

**Response:**
```json
{"accepted": 1, "rejected": 0, "duplicates": 0, "errors": null}
```

### GET /stores/{store_id}/metrics
**Purpose:** Real-time store metrics excluding staff events.

```bash
curl http://localhost:8000/stores/STORE_BLR_002/metrics
```

**Response:**
```json
{
  "store_id": "STORE_BLR_002",
  "unique_visitors": 42,
  "conversion_rate": 0.238,
  "avg_dwell_per_zone": {"SKINCARE": 15000.0, "MAKEUP": 8500.0},
  "current_queue_depth": 3,
  "abandonment_rate": 0.15
}
```

### GET /stores/{store_id}/funnel
**Purpose:** Session-based conversion funnel with drop-off percentages.

```bash
curl http://localhost:8000/stores/STORE_BLR_002/funnel
```

**Response:**
```json
{
  "store_id": "STORE_BLR_002",
  "stages": {"entry": 42, "zone_visit": 35, "billing_queue": 12, "purchase": 10},
  "dropoffs": {
    "entry_to_zone": {"count": 7, "percent": 16.67},
    "zone_to_billing": {"count": 23, "percent": 65.71},
    "billing_to_purchase": {"count": 2, "percent": 16.67}
  }
}
```

### GET /stores/{store_id}/heatmap
**Purpose:** Zone visit frequency + avg dwell, normalised 0-100.

```bash
curl http://localhost:8000/stores/STORE_BLR_002/heatmap
```

**Response:**
```json
{
  "store_id": "STORE_BLR_002",
  "zones": [
    {"zone_id": "SKINCARE", "visit_count": 150, "avg_dwell_ms": 12000.0, "normalized_score": 100.0, "data_confidence": "HIGH"},
    {"zone_id": "BILLING", "visit_count": 45, "avg_dwell_ms": 5000.0, "normalized_score": 35.2, "data_confidence": "HIGH"}
  ]
}
```

### GET /stores/{store_id}/anomalies
**Purpose:** Active operational anomalies with severity and suggested actions.

```bash
curl http://localhost:8000/stores/STORE_BLR_002/anomalies
```

**Response:**
```json
{
  "store_id": "STORE_BLR_002",
  "anomalies": [
    {
      "type": "BILLING_QUEUE_SPIKE",
      "severity": "WARN",
      "message": "Billing queue depth (7) is above normal threshold.",
      "suggested_action": "Open another billing counter or assign staff to billing area.",
      "detected_at": "2026-03-03T14:35:00Z"
    }
  ]
}
```

### GET /health
**Purpose:** System health, database status, last event timestamps, stale feed warnings.

```bash
curl http://localhost:8000/health
```

**Response:**
```json
{
  "status": "ok",
  "database": "ok",
  "last_event_timestamp_per_store": {"STORE_BLR_002": "2026-03-03T14:45:00Z"},
  "warnings": []
}
```

---

## 5. Event Schema

Every event emitted by the detection pipeline follows this schema:

| Field | Type | Description |
|-------|------|-------------|
| event_id | UUID v4 | Globally unique event identifier |
| store_id | String | Store identifier (e.g., "STORE_BLR_002") |
| camera_id | String | Camera that produced this event |
| visitor_id | String | Unique per-visit session token |
| event_type | Enum | ENTRY, EXIT, ZONE_ENTER, ZONE_EXIT, ZONE_DWELL, BILLING_QUEUE_JOIN, BILLING_QUEUE_ABANDON, REENTRY |
| timestamp | ISO-8601 | UTC timestamp derived from clip + frame offset |
| zone_id | String/null | Zone name from store_layout.json (null for ENTRY/EXIT) |
| dwell_ms | Integer ≥ 0 | Duration in milliseconds (0 for instantaneous events) |
| is_staff | Boolean | Whether the detected person is classified as staff |
| confidence | Float 0-1 | YOLO detection confidence score |
| metadata | Object | queue_depth (int/null), sku_zone (string/null), session_seq (int/null) |

---

## 6. Detection Pipeline Details

### Model & Tracker
- **YOLOv8n** (Ultralytics) for person detection (class 0)
- **ByteTrack** for multi-object tracking (integrated via Ultralytics `model.track()`)
- Processes every 5th frame for speed

### Entry/Exit Detection
- Uses a horizontal entry line at the vertical center of the frame
- Line crossing is detected via segment intersection algorithm
- Direction is determined by vertical movement (y-axis increase = ENTRY)

### Zone Assignment
- Bottom-center of bounding box is tested against zone polygons from `store_layout.json`
- Ray casting algorithm for point-in-polygon tests
- Zones: ENTRY, SKINCARE, MAKEUP, FRAGRANCE, BILLING

### Staff Detection
A heuristic scoring system flags staff based on:
- Duration visible > 8 minutes (+2 points)
- Visited ≥ 4 different zones (+1 point)
- Visited billing area ≥ 5 times (+1 point)
- ≥ 3 entry/exit transitions (+1 point)
- Score ≥ 3 → classified as staff

### Re-entry Handling
When a visitor crosses the entry line inbound, the system checks recent exits (within 5 minutes). If a match is found, a REENTRY event is emitted instead of ENTRY, and the new track is aliased to the original visitor_id.

### Confidence Propagation
YOLO confidence scores are passed through to every emitted event. Low-confidence detections are NOT suppressed — they are flagged with their actual confidence value.

---

## 7. POS Transaction Matching

The system correlates POS transactions with visitor sessions:

1. **CSV Loading:** Reads the POS CSV (`Brigade_Bangalore_10_April_26.csv`) with support for multiple date/time formats
2. **Store Code Normalization:** Maps the POS store code (`ST1008`) to `STORE_BLR_002` using `store_layout.json` aliases
3. **Line Item Grouping:** Groups CSV rows by transaction_id and sums basket values
4. **5-Minute Window Matching:** For each POS transaction, finds visitors who were in the billing zone within 5 minutes before the transaction timestamp
5. **Conversion Rate:** `converted_visitors / unique_customer_visitors`

---

## 8. Database Design

### events table
| Column | Type | Notes |
|--------|------|-------|
| event_id | TEXT PK | UUID, indexed |
| store_id | TEXT | Indexed |
| camera_id | TEXT | |
| visitor_id | TEXT | Indexed |
| event_type | TEXT | |
| timestamp | DATETIME | Indexed |
| zone_id | TEXT | Nullable |
| dwell_ms | INTEGER | |
| is_staff | BOOLEAN | |
| confidence | FLOAT | |
| metadata_json | TEXT | JSON string |
| created_at | DATETIME | |

### pos_transactions table
| Column | Type | Notes |
|--------|------|-------|
| transaction_id | TEXT PK | |
| store_id | TEXT | Indexed |
| timestamp | DATETIME | Indexed |
| basket_value_inr | FLOAT | |
| matched_visitor_id | TEXT | Nullable, set by POS matcher |

---

## 9. Dashboard Components

| Component | What It Shows | Polling |
|-----------|--------------|---------|
| MetricCard | Unique visitors, conversion rate, queue depth, abandonment rate | 2s |
| FunnelChart | Entry → Zone Visit → Billing → Purchase with drop-off % | 5s |
| HeatmapGrid | Zone performance scores normalised 0-100, color-coded | 5s |
| AnomalyList | Active anomalies with severity badges and suggested actions | 2s |
| HealthStatus | System OK/degraded status, stale feed warnings | 2s |

---

## 10. Production Readiness Features

- **Containerised:** `docker compose up` starts everything. No manual steps beyond `git clone`.
- **Structured Logging:** Every request logs `trace_id`, `store_id`, `endpoint`, `latency_ms`, `event_count`, `status_code` as JSON.
- **Idempotency:** `POST /events/ingest` deduplicates by `event_id`. Safe to call twice.
- **Graceful Degradation:** Database errors → HTTP 503 with structured JSON body. Generic errors → structured 500 with trace_id. No raw stack traces.
- **Partial Success:** Malformed events don't block valid ones in the same batch.
- **Test Coverage:** 51 tests across 11 files, covering edge cases: empty store, all-staff clip, zero purchases, re-entry in funnel.
- **CORS:** Configurable via environment variable.

---

## 11. How To Run

### Quick Start (Docker)
```bash
git clone <repo-url>
cd store-intelligence
cp .env.example .env
docker compose up --build
```

### Verify
- API: http://localhost:8000/docs
- Dashboard: http://localhost:5173
- Health: http://localhost:8000/health

### Run Detection Pipeline (requires Python + YOLO locally)
```bash
pip install -r requirements-pipeline.txt
python pipeline/detect.py \
  --clips-dir data/cctv_footage \
  --layout data/store_layout.json \
  --pos-data data/files/Brigade_Bangalore_10_April_26.csv \
  --output data/events.jsonl
```

### Replay Events Into API
```bash
python pipeline/replay_events.py \
  --file data/events.jsonl \
  --api http://localhost:8000/events/ingest
```

### Run Tests
```bash
pip install -r requirements-dev.txt
pytest tests/ -v --cov=app --cov=pipeline --cov-report=term-missing
```

---

## 12. Manual Verification Checklist

Use this checklist to verify everything works before submitting:

### Acceptance Gate (MUST PASS)
- [ ] `docker compose up` starts API without errors
- [ ] `docker compose up` starts dashboard without errors
- [ ] `curl http://localhost:8000/health` returns valid JSON with `"status": "ok"`
- [ ] `curl http://localhost:8000/stores/STORE_BLR_002/metrics` returns valid JSON
- [ ] `docs/DESIGN.md` exists and is >250 words
- [ ] `docs/CHOICES.md` exists and is >250 words

### API Correctness
- [ ] POST /events/ingest accepts a valid event → `accepted: 1`
- [ ] POST /events/ingest with same event_id → `duplicates: 1` (idempotent)
- [ ] POST /events/ingest with invalid confidence (>1) → `rejected: 1`
- [ ] POST /events/ingest with >500 events → HTTP 400
- [ ] GET /stores/STORE_BLR_002/metrics → returns `unique_visitors`, `conversion_rate`, `avg_dwell_per_zone`
- [ ] GET /stores/STORE_BLR_002/funnel → returns stages and dropoffs with purchase count
- [ ] GET /stores/STORE_BLR_002/heatmap → returns zones with normalized_score 0-100
- [ ] GET /stores/STORE_BLR_002/anomalies → returns anomaly list with severity and suggested_action
- [ ] Metrics exclude is_staff=true events
- [ ] Funnel uses distinct visitor_id (no double-counting)
- [ ] Heatmap shows data_confidence=LOW when <20 sessions

### Detection Pipeline
- [ ] `python pipeline/detect.py --help` shows usage
- [ ] Detection pipeline generates data/events.jsonl
- [ ] Events in JSONL are schema-valid (UUID event_id, valid event_type, confidence 0-1)
- [ ] ENTRY/EXIT events have zone_id=null
- [ ] REENTRY events are generated for re-entering visitors
- [ ] is_staff=true for long-duration visitors
- [ ] confidence field contains actual YOLO detection confidence

### Tests
- [ ] `pytest tests/ -v` — all tests pass
- [ ] `pytest tests/ --cov=app --cov=pipeline` — coverage >70%
- [ ] Every test file has `# PROMPT:` and `# CHANGES MADE:` comment blocks

### Documentation
- [ ] README.md has 5-command quick start
- [ ] DESIGN.md has "AI-Assisted Decisions" section with 3 decisions
- [ ] CHOICES.md covers: model selection, schema design, API architecture choice
- [ ] Each decision includes: options considered, what AI suggested, what you chose, why

### Git Cleanliness
- [ ] No `.env` file committed
- [ ] No `__pycache__/` directories committed
- [ ] No `store_intelligence.db` committed
- [ ] No `yolov8n.pt` committed
- [ ] No `data/cctv_footage/` committed
- [ ] No `node_modules/` committed
- [ ] No `.coverage` committed
- [ ] No `dashboard/dist/` committed

---

## 13. How To Explain The Project

### 30-Second Pitch
> I built an end-to-end store intelligence system that converts raw CCTV footage into business-actionable retail analytics. The detection pipeline uses YOLOv8 and ByteTrack to track visitors, maps their positions to store zones using polygon geometry, and emits structured events. The FastAPI backend ingests these events, correlates billing-zone activity with POS transactions, and computes conversion rate, funnel drop-offs, zone heatmaps, queue depth, and operational anomalies. Everything runs with `docker compose up` and displays on a real-time React dashboard.

### Key Trade-Offs
> I prioritised a reliable end-to-end system over perfect computer vision. YOLOv8 and ByteTrack gave a fast baseline, while rule-based zones made the behaviour explainable and testable. SQLite keeps Docker setup simple for the challenge, but I documented that PostgreSQL plus a message queue would be needed for 40 live stores. Staff detection uses behavioural heuristics rather than visual uniform classification — this is documented as a known limitation.

### On Follow-Up Questions
The system is designed so you can confidently answer questions about:
- **Detection choices:** Why YOLOv8 over RT-DETR, why ByteTrack over DeepSORT
- **Entry/exit logic:** Horizontal line crossing with y-direction heuristic
- **Scalability limits:** SQLite write locking, in-memory POS matching
- **Re-entry handling:** 5-minute exit window with visitor_id aliasing
- **Confidence:** YOLO confidence propagated to all events, never suppressed

---

## 14. Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| APP_ENV | development | Application environment |
| DATABASE_URL | sqlite:///./data/store_intelligence.db | SQLAlchemy database URL |
| API_HOST | 0.0.0.0 | API bind host |
| API_PORT | 8000 | API bind port |
| CORS_ORIGINS | http://localhost:5173 | Comma-separated allowed origins |
| STALE_FEED_MINUTES | 10 | Minutes before a store feed is flagged stale |
| POS_DATA_PATH | data/files/Brigade_Bangalore_10_April_26.csv | Path to POS CSV |
| VITE_API_BASE | http://localhost:8000 | Dashboard API base URL |
| CCTV_BASE_TIME | (auto) | Optional ISO timestamp for first clip |

---

## 15. Files NOT To Push To GitHub

These are generated at runtime and excluded via `.gitignore`:

| File/Directory | Why Excluded |
|----------------|-------------|
| `.env` | Contains local environment secrets |
| `.venv/` / `venv/` | Python virtual environment |
| `__pycache__/` | Python bytecode cache |
| `.pytest_cache/` | Pytest cache |
| `.coverage` | Test coverage data |
| `htmlcov/` | Coverage HTML report |
| `store_intelligence.db` | SQLite database (generated on startup) |
| `data/events.jsonl` | Generated by detection pipeline |
| `data/cctv_footage/` | CCTV clips (challenge data, not redistributable) |
| `yolov8n.pt` | YOLO model weights (auto-downloaded by Ultralytics) |
| `node_modules/` | npm dependencies (installed by `npm ci`) |
| `dashboard/dist/` | Built dashboard (generated by `npm run build`) |
| `IMPLEMENTATION.md` | Internal implementation notes |
