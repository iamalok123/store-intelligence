from fastapi import FastAPI, Depends, Request, HTTPException
from sqlalchemy.orm import Session
from app.database import init_db, get_db
from app.models import HealthResponse, MetricsResponse, FunnelResponse, HeatmapResponse, AnomaliesResponse, IngestRequest, IngestResponse
from app.ingestion import process_ingestion
from app.metrics import get_store_metrics
from app.funnel import get_store_funnel

# Initialize DB on startup
init_db()

from app.logging_config import setup_logging

app = FastAPI(title="Store Intelligence API")
setup_logging(app)

@app.get("/")
def root():
    return {"message": "Store Intelligence API"}

@app.get("/health", response_model=HealthResponse)
def health(db: Session = Depends(get_db)):
    from app.health import get_health_status
    return get_health_status(db)

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
def get_funnel(store_id: str, db: Session = Depends(get_db)):
    return get_store_funnel(store_id, db)

@app.get("/stores/{store_id}/heatmap", response_model=HeatmapResponse)
def get_heatmap(store_id: str, db: Session = Depends(get_db)):
    from app.heatmap import get_store_heatmap
    return get_store_heatmap(store_id, db)

@app.get("/stores/{store_id}/anomalies", response_model=AnomaliesResponse)
def get_anomalies(store_id: str, db: Session = Depends(get_db)):
    from app.anomalies import get_store_anomalies
    return get_store_anomalies(store_id, db)
