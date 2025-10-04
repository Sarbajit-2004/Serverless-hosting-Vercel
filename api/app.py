from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import numpy as np

import json

app = FastAPI()

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST"],
    allow_headers=["*"],
)

# Load telemetry data on startup (replace file path as needed)
with open("q-vercel-latency.json") as f:
    DATA = json.load(f)

@app.post("/api/latency")
async def latency_metrics(request: Request):
    payload = await request.json()
    regions = payload["regions"]
    threshold = payload["threshold_ms"]

    response = {}

    for region in regions:
        # Filter by region
        records = [r for r in DATA if r["region"] == region]
        if not records:
            response[region] = None
            continue
        latencies = np.array([r["latency_ms"] for r in records])
        uptimes = np.array([r["uptime"] for r in records])
        response[region] = {
            "avg_latency": float(np.mean(latencies)),
            "p95_latency": float(np.percentile(latencies, 95)),
            "avg_uptime": float(np.mean(uptimes)),
            "breaches": int(np.sum(latencies > threshold)),
        }
    return response
