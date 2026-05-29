from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import init_db, get_db
from app.models import HealthResponse, MetricsResponse, FunnelResponse, HeatmapResponse, AnomaliesResponse, IngestRequest, IngestResponse
from app.ingestion import process_ingestion
from app.metrics import get_store_metrics

# Initialize DB on startup
init_db()

app = FastAPI(title="Store Intelligence API")

@app.get("/")
def root():
    return {"message": "Store Intelligence API"}

@app.get("/health", response_model=HealthResponse)
def health():
    return {
        "status": "ok",
        "database": "ok",
        "last_event_timestamp_per_store": {},
        "warnings": []
    }

@app.post("/events/ingest", response_model=IngestResponse)
async def ingest_events(request: Request, db: Session = Depends(get_db)):
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    return process_ingestion(payload, db)

@app.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
def get_metrics(store_id: str, db: Session = Depends(get_db)):
    return get_store_metrics(store_id, db)

@app.get("/stores/{store_id}/funnel", response_model=FunnelResponse)
def get_funnel(store_id: str):
    return {
        "store_id": store_id,
        "stages": {"entry": 0, "zone_visit": 0, "billing_queue": 0, "purchase": 0},
        "dropoffs": {}
    }

@app.get("/stores/{store_id}/heatmap", response_model=HeatmapResponse)
def get_heatmap(store_id: str):
    return {
        "store_id": store_id,
        "zones": []
    }

@app.get("/stores/{store_id}/anomalies", response_model=AnomaliesResponse)
def get_anomalies(store_id: str):
    return {
        "store_id": store_id,
        "anomalies": []
    }
