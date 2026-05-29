from fastapi import FastAPI
from app.database import init_db
from app.models import HealthResponse, MetricsResponse, FunnelResponse, HeatmapResponse, AnomaliesResponse, IngestRequest, IngestResponse

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
def ingest_events(request: IngestRequest):
    return {
        "accepted": len(request.events),
        "rejected": 0,
        "duplicates": 0,
        "errors": []
    }

@app.get("/stores/{store_id}/metrics", response_model=MetricsResponse)
def get_metrics(store_id: str):
    return {
        "store_id": store_id,
        "unique_visitors": 0,
        "conversion_rate": 0,
        "avg_dwell_per_zone": {},
        "current_queue_depth": 0,
        "abandonment_rate": 0
    }

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
