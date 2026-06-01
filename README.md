# Store Intelligence API

## 1. What this project does
The Store Intelligence system processes raw anonymized CCTV footage to generate a structured event stream (entries, exits, zone dwells, and billing queues). These events are ingested by a FastAPI backend, which aggregates them into live analytics such as unique visitor counts, conversion rates, zone heatmaps, and funnel drop-offs. The analytics are surfaced via a real-time React + Vite dashboard.

## 2. Tech stack
- **Backend**: Python 3.11+, FastAPI, Pydantic v2, SQLAlchemy, SQLite
- **Detection Pipeline**: Python, OpenCV, Ultralytics (YOLOv8), ByteTrack
- **Frontend Dashboard**: React, Vite, TypeScript, Tailwind CSS, Recharts
- **DevOps**: Docker, Docker Compose, Pytest

## 3. Architecture
```
Raw CCTV Clips
   ↓
Detection Layer (YOLO + ByteTrack)
   ↓
Structured Event Stream (JSONL)
   ↓
Intelligence API (FastAPI + SQLite)
   ↓
Database + Analytics
   ↓
Live Dashboard (React + Tailwind)
```

## 4. Quick start
Clone and run — one command is all you need:
```bash
git clone <repo-url>
cd store-intelligence
docker compose up
```

That's it. `docker compose up` automatically:
1. **Builds** both Docker images (API + Dashboard) on first run
2. **Starts** the FastAPI backend on port 8000
3. **Starts** the React dashboard on port 5173
4. **Creates** the SQLite database

No `--build` flag needed. No `.env` file needed (all environment variables have defaults in `docker-compose.yml`).

After Compose starts:
- API: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`
- Dashboard: `http://localhost:5173`
- Health: `http://localhost:8000/health`

> **Optional:** Copy `.env.example` to `.env` if you want to customise configuration:
> ```bash
> cp .env.example .env
> ```

## 5. Run detection pipeline
The challenge CCTV files should live in `data/cctv_footage/`. To process videos and generate events, run:
```bash
python pipeline/detect.py \
  --clips-dir data/cctv_footage \
  --layout data/store_layout.json \
  --pos-data data/files/Brigade_Bangalore_10_April_26.csv \
  --output data/events.jsonl
```

The POS CSV in `data/files/` is used to align generated event timestamps and calculate POS-matched conversion rate. The layout workbook is retained as the source reference; the runnable polygon config is in `data/store_layout.json`.

## 6. Replay events into API
To batch ingest the generated events into the API, run:
```bash
python pipeline/replay_events.py \
  --file data/events.jsonl \
  --api http://localhost:8000/events/ingest
```

## 7. API endpoints
- `POST /events/ingest` - Accepts batch JSON events
- `GET /stores/{id}/metrics` - Top-line store metrics
- `GET /stores/{id}/funnel` - Session-based conversion funnel
- `GET /stores/{id}/heatmap` - Zone performance heatmap
- `GET /stores/{id}/anomalies` - Active operational anomalies
- `GET /health` - System health and stale feed warnings

## 8. Run tests
Tests are written in Pytest with a minimum 70% coverage requirement.
```bash
python -m venv .venv
.venv/Scripts/activate
pip install -r requirements-dev.txt
pytest --cov=app --cov=pipeline --cov-report=term-missing
```

The Docker API image intentionally installs only `requirements-api.txt`. The heavier YOLO/OpenCV stack lives in `requirements-pipeline.txt`, and test-only tools live in `requirements-dev.txt`.

## 9. Dashboard
The dashboard provides a real-time visual interface to the API. To run it locally:
```bash
cd dashboard
npm ci
npm run dev
```
Open `http://localhost:5173` in your browser.

## 10. Known limitations
- **Staff Exclusion Heuristics**: Staff are filtered based on track duration, zones visited, and billing area presence rather than a visual uniform classifier.
- **Camera Overlap**: Re-identification across different cameras uses a time/location heuristic which may fail during extreme crowding.
- **SQLite Concurrency**: SQLite is used for simplicity and speed. A production environment with 40+ stores would require PostgreSQL and a message queue (e.g. Kafka or Redis) for event ingestion.
