# api/latency.py
from pathlib import Path
from typing import List, Dict, Any, Optional
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import json

app = FastAPI()

# CORS (include OPTIONS for preflight)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "OPTIONS"],
    allow_headers=["*"],
)

# Load telemetry from repo root (works locally and on Vercel)
DATA_PATH = Path(__file__).resolve().parent.parent / "q-vercel-latency.json"
with DATA_PATH.open("r", encoding="utf-8") as f:
    DATA: List[Dict[str, Any]] = json.load(f)

def get_latency(row: Dict[str, Any]) -> Optional[float]:
    for k in ("latency_ms", "ms", "latency"):
        if k in row:
            try:
                return float(row[k])
            except Exception:
                return None
    return None

def get_uptime(row: Dict[str, Any]) -> Optional[float]:
    for k in ("uptime", "up", "is_up"):
        if k in row:
            v = row[k]
            if isinstance(v, bool):
                return 1.0 if v else 0.0
            try:
                return float(v)
            except Exception:
                return None
    return None

def p95(values: List[float]) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = max(0, min(len(s) - 1, int(round(0.95 * (len(s) - 1)))))
    return s[idx]

@app.post("/api/latency")
async def latency_metrics(request: Request):
    body = await request.json()
    regions: List[str] = body["regions"]
    threshold: float = float(body["threshold_ms"])

    results = []
    for region in regions:
        rows = [r for r in DATA if str(r.get("region", "")).lower() == region.lower()]
        latencies = [x for x in (get_latency(r) for r in rows) if x is not None]
        uptimes   = [x for x in (get_uptime(r)  for r in rows) if x is not None]

        avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
        p95_latency = p95(latencies)
        avg_uptime  = sum(uptimes) / len(uptimes)   if uptimes   else 0.0
        breaches    = sum(1 for v in latencies if v > threshold)

        results.append({
            "region": region,
            "avg_latency": avg_latency,
            "p95_latency": p95_latency,
            "avg_uptime":  avg_uptime,
            "breaches":    breaches,
        })

    # Order doesn't matter per the assignment
    return {"regions": results}
