import math
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

# ✅ Correct shared import
from shared.cosmos import evaluations_read, evaluators_read

router = APIRouter()

# Cache for evaluator names to avoid repeated queries
_evaluator_cache = {}


# -----------------------------
# Helpers
# -----------------------------
def scrub(obj):
    if isinstance(obj, float) and (math.isnan(obj) or math.isinf(obj)):
        return None
    if isinstance(obj, dict):
        return {k: scrub(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [scrub(i) for i in obj]
    return obj


# -----------------------------
# NORMALIZATION
# -----------------------------
ALLOWED_STATUS = {"Completed", "Error", "Timeout"}


def parse_timestamp(ts):
    if isinstance(ts, str):
        return ts
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).isoformat()
    return None


def compute_duration(e: dict):
    for key in ("duration_ms", "duration", "latency_ms", "eval_latency"):
        if isinstance(e.get(key), (int, float)):
            return int(e[key])

    try:
        if e.get("start_time") and e.get("end_time"):
            start = datetime.fromisoformat(e["start_time"])
            end = datetime.fromisoformat(e["end_time"])
            return int((end - start).total_seconds() * 1000)
    except Exception:
        pass

    return 0


def normalize_status(e: dict, score):
    raw = e.get("status")
    if raw in ALLOWED_STATUS:
        return raw

    if isinstance(raw, str):
        rl = raw.lower()
        if "timeout" in rl:
            return "Timeout"
        if "error" in rl or "fail" in rl:
            return "Error"

    return "Completed" if score is not None else "Error"


def get_evaluator_name(evaluator_id: str) -> str:
    """
    Fetch the human-readable name for an evaluator by its ID.
    Uses caching to minimize database queries.
    """
    if not evaluator_id:
        return "Unknown"
    
    # Check cache first
    if evaluator_id in _evaluator_cache:
        return _evaluator_cache[evaluator_id]
    
    try:
        # Query the evaluators container
        evaluator = evaluators_read.read_item(
            item=evaluator_id,
            partition_key=evaluator_id
        )
        name = evaluator.get("name") or evaluator.get("score_name") or evaluator_id
        _evaluator_cache[evaluator_id] = name
        return name
    except Exception:
        # Fallback to evaluator_id if lookup fails
        return evaluator_id


def normalize_eval(e: dict) -> dict:
    score = e.get("score")
    
    # Get evaluator_id from the evaluation record
    evaluator_id = e.get("evaluator_id")
    
    # Fetch the human-readable name
    evaluator_name = get_evaluator_name(evaluator_id)

    return {
        "trace_id": e.get("trace_id"),
        "evaluator_name": evaluator_name,  # Now using the actual name from evaluators table
        "score": score,
        "timestamp": parse_timestamp(
            e.get("timestamp") or e.get("created_at") or e.get("_ts")
        ),
        "duration_ms": compute_duration(e),
        "status": normalize_status(e, score),
    }

# -----------------------------
# Routes
# -----------------------------
@router.get("")
def get_all_evaluations(
    evaluator: str | None = Query(None),
    trace_id: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
):
    try:
        query = "SELECT * FROM c"
        parameters = []
        filters = []

        if evaluator:
            filters.append("c.name = @evaluator")
            parameters.append({"name": "@evaluator", "value": evaluator})

        if trace_id:
            filters.append("c.trace_id = @trace_id")
            parameters.append({"name": "@trace_id", "value": trace_id})

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY c._ts DESC"

        raw = list(
            evaluations_read.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            )
        )

        normalized = [normalize_eval(e) for e in raw[:limit]]
        return scrub(normalized)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
