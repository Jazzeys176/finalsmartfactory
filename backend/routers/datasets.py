import os
import math
from fastapi import APIRouter, HTTPException
from azure.cosmos import CosmosClient
from utils.cosmos import COSMOS_DB

router = APIRouter()

# -----------------------------
# Environment + Client
# -----------------------------
COSMOS_CONN_READ = os.getenv("COSMOS_CONN_READ", "").strip()

if not COSMOS_CONN_READ:
    raise RuntimeError("COSMOS_CONN_READ env variable is missing in .env")

try:
    client = CosmosClient.from_connection_string(COSMOS_CONN_READ)
except Exception as e:
    raise RuntimeError(f"Failed to initialize Cosmos Client: {e}")

TRACES_CONTAINER = "traces"
EVALS_CONTAINER = "evaluations"

# -----------------------------
# Helpers
# -----------------------------
def get_cosmos_container(container_name: str):
    db = client.get_database_client(COSMOS_DB)
    return db.get_container_client(container_name)


def scrub(obj):
    """
    Replace NaN / Infinity with None so FastAPI can serialize safely.
    """
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub(i) for i in obj]
    return obj


# -----------------------------
# Routes
# -----------------------------
@router.get("/metrics")
def get_dashboard_metrics():
    """
    Aggregated dashboard metrics (Cosmos-native)
    """
    try:
        traces_container = get_cosmos_container(TRACES_CONTAINER)
        evals_container = get_cosmos_container(EVALS_CONTAINER)

        traces = list(
            traces_container.query_items(
                query="SELECT c.trace_id, c.user_id, c.latency_ms, c.tokens FROM c",
                enable_cross_partition_query=True,
            )
        )

        evals = list(
            evals_container.query_items(
                query="SELECT c.trace_id, c.duration, c.score FROM c",
                enable_cross_partition_query=True,
            )
        )

        # -----------------------------
        # Aggregations
        # -----------------------------
        total_traces = len(traces)
        total_sessions = len(set(t.get("trace_id") for t in traces))
        total_users = len(set(t.get("user_id") for t in traces if t.get("user_id")))

        latencies = [
            t["latency_ms"]
            for t in traces
            if isinstance(t.get("latency_ms"), (int, float))
        ]

        avg_latency_ms = (
            sum(latencies) / len(latencies) if latencies else 0
        )

        total_tokens = sum(
            t.get("tokens", 0)
            for t in traces
            if isinstance(t.get("tokens"), (int, float))
        )

        avg_traces_per_session = (
            total_traces / total_sessions if total_sessions else 0
        )

        metrics = {
            "generated_at": None,  # frontend already handles this
            "total_traces": total_traces,
            "total_sessions": total_sessions,
            "total_users": total_users,
            "avg_traces_per_session": round(avg_traces_per_session, 2),
            "avg_latency_ms": round(avg_latency_ms, 2),
            "total_tokens": total_tokens,
        }

        return scrub(metrics)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
