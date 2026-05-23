"""
main.py
-------
FastAPI application entry point.

To run:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Then open a browser at:
    http://localhost:8000/docs   ← interactive API explorer (Swagger UI)
    http://localhost:8000/redoc  ← alternative documentation
"""

from fastapi import FastAPI
from contextlib import asynccontextmanager

from database import load_all_data
from routers import farms, crops_markets


# ──────────────────────────────────────────────────────────────────────
# Lifespan — runs once at startup before accepting any requests
# This is where we load data from the database into memory
# ──────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load all data from MySQL into memory when the server starts."""
    load_all_data()
    yield  # Server runs here — handling requests
    # (cleanup code would go here if needed)


# ──────────────────────────────────────────────────────────────────────
# Create the FastAPI app
# ──────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Agriculture Database API",
    description="""
## Agriculture DB — Data Scientist Assessment

This API provides two reports over the Bangladesh Agriculture Database:

### Report 1 — Farm Performance
- `GET /farms/summary` — All farms with revenue, cost, profit, loss %
- `GET /farms/{farm_id}/performance` — Single farm detail by crop & market
- `GET /farms/top` — Top N farms ranked by profit / revenue / yield
- `GET /farms/loss-analysis` — Post-harvest loss by region, season, crop

### Report 2 — Crop & Market Intelligence
- `GET /crops/yield-efficiency` — Actual vs benchmark yield per crop
- `GET /crops/seasonal-trend` — Revenue trends by season and year
- `GET /markets/price-comparison` — Price comparison across market channels
- `GET /crops/quality-breakdown` — Grade distribution + pesticide residue

**All endpoints support query filters. Invalid filter values return HTTP 422.**
    """,
    version="1.0.0",
    lifespan=lifespan,
)

# ──────────────────────────────────────────────────────────────────────
# Register routers
# ──────────────────────────────────────────────────────────────────────

app.include_router(farms.router)
app.include_router(crops_markets.router)


# ──────────────────────────────────────────────────────────────────────
# Root endpoint — health check
# ──────────────────────────────────────────────────────────────────────

@app.get("/", tags=["Health"])
def root():
    """Health check — confirms the API is running."""
    return {
        "status": "ok",
        "message": "Agriculture API is running. Visit /docs for the full API explorer.",
        "endpoints": [
            "GET /farms/summary",
            "GET /farms/top",
            "GET /farms/loss-analysis",
            "GET /farms/{farm_id}/performance",
            "GET /crops/yield-efficiency",
            "GET /crops/seasonal-trend",
            "GET /markets/price-comparison",
            "GET /crops/quality-breakdown",
        ]
    }
