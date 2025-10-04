from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import numpy as np
from collections import defaultdict

app = FastAPI()

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load the telemetry data
try:
    with open("q-vercel-latency.json", "r") as f:
        telemetry_data = json.load(f)
except FileNotFoundError:
    telemetry_data = []

class LatencyRequest(BaseModel):
    regions: list[str]
    threshold_ms: int

@app.post("/api/latency")
async def get_latency_metrics(request: LatencyRequest):
    metrics = {}
    
    for region in request.regions:
        region_data = [item for item in telemetry_data if item["region"] == region]
        
        if not region_data:
            metrics[region] = {
                "avg_latency": 0.0,
                "p95_latency": 0.0,
                "avg_uptime": 0.0,
                "breaches": 0
            }
            continue

        latencies = [item["latency_ms"] for item in region_data]
        uptimes = [item["uptime_pct"] for item in region_data]

        avg_latency = np.mean(latencies)
        p95_latency = np.percentile(latencies, 95)
        avg_uptime = np.mean(uptimes)
        breaches = sum(1 for latency in latencies if latency > request.threshold_ms)

        metrics[region] = {
            "avg_latency": round(float(avg_latency), 2),
            "p95_latency": round(float(p95_latency), 2),
            "avg_uptime": round(float(avg_uptime), 2),
            "breaches": breaches
        }
    
    return metrics
