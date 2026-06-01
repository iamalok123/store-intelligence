# CHOICES.md

## Decision 1: Detection Model

### Options considered
- YOLOv8
- YOLOv11
- RT-DETR
- MediaPipe

### What AI suggested
The AI suggested RT-DETR for superior accuracy and Transformer-based global context understanding, which helps in crowded retail environments, or DeepSORT if focusing purely on re-identification strength.

### What I chose
I chose YOLOv8 combined with ByteTrack.

### Why I chose it
Given the 48-hour challenge window, YOLOv8 provides the best speed-to-implementation trade-off. It is widely supported, extremely fast, and natively integrates with ByteTrack within the `ultralytics` package. This allowed me to immediately focus on the event schema logic and API correctness rather than debugging model deployment.

### Trade-offs
YOLOv8 may struggle with severe occlusions compared to Transformer-based models, and ByteTrack can lose track identities when a subject leaves the frame entirely. I mitigated the track-loss issue by implementing a rudimentary re-entry time/location heuristic.

### What I would improve with more time
With more time, I would deploy a dedicated Re-ID model (e.g., OSNet) to extract appearance embeddings for every track. This would solve identity switches across disparate camera feeds far better than my current time/location heuristic.

---

## Decision 2: Event Schema Design Rationale

### Options considered
- Coarse-grained events (only storing `SESSION_START` and `SESSION_END`)
- Highly granular frame-by-frame state dumps
- Standardized lifecycle events (`ENTRY`, `ZONE_ENTER`, `ZONE_DWELL`, `EXIT`)

### What AI suggested
The AI initially recommended a highly granular schema that dumps bounding boxes and coordinates into a timeseries database like InfluxDB for infinite replayability and spatial analytics.

### What I chose
I chose a standardized lifecycle event stream (`ENTRY`, `EXIT`, `ZONE_ENTER`, `ZONE_DWELL`, `BILLING_QUEUE_JOIN`, `BILLING_QUEUE_ABANDON`).

### Why I chose it
This schema directly aligns with the business metrics we need to compute (conversion rate, dwell time, abandonment rate). It reduces the payload size significantly compared to frame-by-frame dumps, while preserving enough data to generate heatmaps and funnels. It complies perfectly with the API ingestion validation requirements.

### Trade-offs
We lose exact spatial paths. We know which zone a person visited and for how long, but we cannot reconstruct their exact walking trajectory (e.g., stopping at a specific endcap inside the zone) without querying the raw video again.

### What I would improve with more time
I would add an `x, y` coordinate array to the `metadata` payload of `ZONE_DWELL` events to retain a compressed trajectory for more advanced spatial heatmapping.

---

## Decision 3: API Architecture Choice

### Options considered
- Flask + SQLAlchemy
- Django + Django REST Framework
- FastAPI + Pydantic

### What AI suggested
The AI suggested FastAPI due to its async capabilities and native Pydantic integration, noting that it is quickly becoming the industry standard for Python microservices.

### What I chose
FastAPI + Pydantic v2 + SQLite.

### Why I chose it
FastAPI and Pydantic provide out-of-the-box validation for our strict event schema, automatically rejecting malformed events and generating Swagger documentation. SQLite was chosen over PostgreSQL simply to ensure the project runs seamlessly in a container without requiring a heavy database orchestration setup, fulfilling the "containerisation" and "testability" constraints of the challenge.

### Trade-offs
SQLite handles concurrent reads well but struggles with concurrent writes. If multiple detection pipelines from 10+ cameras are POSTing events simultaneously, SQLite will likely lock and throw `OperationalError`s.

### What I would improve with more time
I would migrate the storage backend to PostgreSQL for concurrent writes. Furthermore, I would place a Redis queue in front of the ingestion endpoint to buffer incoming events so the API never drops a payload during traffic spikes.
