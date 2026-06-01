# Store Intelligence API

## 1. What this project does
The Store Intelligence system processes raw anonymized CCTV clips to generate a structured event stream (entries, exits, zone dwells, and billing queues). These events are ingested by a FastAPI backend, which aggregates them into live analytics such as unique visitor counts, conversion rates, zone heatmaps, and funnel drop-offs. The analytics are surfaced via a real-time React + Vite dashboard.

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
You can run the entire system using the following 5 commands:
```bash
git clone <repo-url>
cd store-intelligence
cp .env.example .env
docker compose up --build
curl http://localhost:8000/health
```

## 5. Run detection pipeline
To process videos and generate events, run:
```bash
python pipeline/detect.py \
  --clips-dir data/clips \
  --layout data/store_layout.json \
  --output data/events.jsonl
```

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
pip install -r requirements.txt
pytest --cov=app --cov=pipeline --cov-report=term-missing
```

## 9. Dashboard
The dashboard provides a real-time visual interface to the API. To run it locally:
```bash
cd dashboard
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.

## 10. Known limitations
- **Staff Exclusion Heuristics**: Staff are filtered based on track duration, zones visited, and billing area presence rather than a visual uniform classifier.
- **Camera Overlap**: Re-identification across different cameras uses a time/location heuristic which may fail during extreme crowding.
- **SQLite Concurrency**: SQLite is used for simplicity and speed. A production environment with 40+ stores would require PostgreSQL and a message queue (e.g. Kafka or Redis) for event ingestion.
