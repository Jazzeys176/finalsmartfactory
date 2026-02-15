import math
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

# ✅ Read-only containers
from shared.cosmos import traces_read as traces_container
from shared.cosmos import evaluations_read as evaluations_container

router = APIRouter()


# --------------------------------------------------
# Helpers
# --------------------------------------------------

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


def parse_timestamp(ts):
    if isinstance(ts, str):
        return ts
    if isinstance(ts, (int, float)):
        return datetime.fromtimestamp(ts, tz=timezone.utc).isoformat()
    if isinstance(ts, datetime):
        return ts.astimezone(timezone.utc).isoformat()
    return None


def normalize_trace(t: dict) -> dict:
    return {
        "trace_id": t.get("trace_id") or t.get("id"),
        "session_id": t.get("session_id"),
        "user_id": t.get("user_id"),
        "trace_name": t.get("trace_name"),
        "input": t.get("input"),
        "output": t.get("output"),
        "timestamp": parse_timestamp(
            t.get("timestamp") or t.get("created_at") or t.get("_ts")
        ),
        "latency_ms": t.get("latency_ms") or t.get("latency") or 0,
        "tokens": t.get("tokens"),
        "tokens_in": t.get("tokens_in"),
        "tokens_out": t.get("tokens_out"),
        "cost": t.get("cost"),
        "model": t.get("model"),
    }


# --------------------------------------------------
# Routes
# --------------------------------------------------

@router.get("")
def get_all_traces(
    session_id: str | None = Query(None),
    user_id: str | None = Query(None),
    model: str | None = Query(None),
    limit: int = Query(200, ge=1, le=1000),
):
    try:
        # 🔎 Build query
        query = "SELECT * FROM c"
        parameters = []
        filters = []

        if session_id:
            filters.append("c.session_id = @session_id")
            parameters.append({"name": "@session_id", "value": session_id})

        if user_id:
            filters.append("c.user_id = @user_id")
            parameters.append({"name": "@user_id", "value": user_id})

        if model:
            filters.append("c.model = @model")
            parameters.append({"name": "@model", "value": model})

        if filters:
            query += " WHERE " + " AND ".join(filters)

        query += " ORDER BY c._ts DESC"

        raw_traces = list(
            traces_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True,
            )
        )[:limit]

        # 🔥 Fetch all evaluations once
        evaluations = list(
            evaluations_container.query_items(
                query="SELECT c.trace_id, c.evaluator, c.score FROM c",
                enable_cross_partition_query=True,
            )
        )

        # 🔥 Group evaluations by trace_id
        scores_map = {}
        for e in evaluations:
            trace_id = e.get("trace_id")
            if not trace_id:
                continue

            if trace_id not in scores_map:
                scores_map[trace_id] = {}

            scores_map[trace_id][e.get("evaluator")] = e.get("score")

        # 🔥 Attach scores to each trace
        enriched_traces = []

        for t in raw_traces:
            normalized = normalize_trace(t)
            normalized["scores"] = scores_map.get(normalized["trace_id"], {})
            enriched_traces.append(normalized)

        return scrub(enriched_traces)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{trace_id}")
def get_trace(trace_id: str):
    try:
        # 🔎 Fetch trace
        trace_items = list(
            traces_container.query_items(
                query="SELECT * FROM c WHERE c.trace_id = @trace_id",
                parameters=[{"name": "@trace_id", "value": trace_id}],
                enable_cross_partition_query=True,
            )
        )

        if not trace_items:
            raise HTTPException(status_code=404, detail="Trace not found")

        trace = normalize_trace(trace_items[0])

        # 🔥 Fetch evaluations for this trace only
        eval_items = list(
            evaluations_container.query_items(
                query="SELECT c.evaluator, c.score FROM c WHERE c.trace_id = @trace_id",
                parameters=[{"name": "@trace_id", "value": trace_id}],
                enable_cross_partition_query=True,
            )
        )

        scores = {}
        for e in eval_items:
            scores[e.get("evaluator")] = e.get("score")

        trace["scores"] = scores

        return scrub(trace)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
