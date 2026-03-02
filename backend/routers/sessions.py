import math
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from shared.cosmos import traces_container_read as traces_container

SESSION_IDLE_TIMEOUT = 5 * 60  # 5 minutes
router = APIRouter()

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


def safe_round(value: float, decimals: int = 6):
    return round(float(value), decimals)


def normalize_ts(ts):
    """Normalize Cosmos timestamps (ms or sec) → seconds."""
    if ts is None:
        return None
    if ts > 1e12:  # ms
        return ts / 1000
    return ts


def ts_to_iso(ts):
    """Convert seconds timestamp → ISO."""
    if ts is None:
        return None
    return datetime.utcfromtimestamp(ts).isoformat() + "Z"


# -----------------------------
# GET /sessions
# -----------------------------
@router.get("")
def list_sessions():
    try:
        traces = list(
            traces_container.query_items(
                query="SELECT * FROM c",
                enable_cross_partition_query=True,
            )
        )

        if not traces:
            return []

        sessions = defaultdict(
            lambda: {
                "session_id": None,
                "user_id": "unknown",
                "environment": None,
                "trace_count": 0,
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "total_cost_micro_usd": 0,
                "avg_latency_ms": 0.0,
                "created": None,
                "last_activity": None,
            }
        )

        # Aggregate sessions
        for t in traces:
            # Get session info from nested object or flat structure
            session_data = t.get("session", {}) or {}
            session_id = session_data.get("session_id") or t.get("session_id")
            if not session_id:
                continue

            s = sessions[session_id]

            s["session_id"] = session_id
            s["user_id"] = session_data.get("user_id") or t.get("user_id", "unknown")
            
            # Environment from request
            request_obj = t.get("request", {}) or {}
            s["environment"] = request_obj.get("environment")

            s["trace_count"] += 1
            
            # Tokens
            usage = t.get("usage", {}) or {}
            s["total_tokens"] += usage.get("total_tokens", 0) or t.get("tokens", 0)

            # Cost
            cost_obj = t.get("cost", {}) or {}
            cost_usd = cost_obj.get("total_cost_usd", 0.0) or t.get("cost", 0.0)
            s["total_cost_usd"] += cost_usd
            s["total_cost_micro_usd"] += int(cost_usd * 1_000_000)

            # Latency
            perf_obj = t.get("performance", {}) or {}
            s["avg_latency_ms"] += perf_obj.get("latency_ms", 0)

            # Timestamps
            ts = normalize_ts(request_obj.get("timestamp") or t.get("timestamp"))
            if ts:
                if s["created"] is None or ts < s["created"]:
                    s["created"] = ts
                if s["last_activity"] is None or ts > s["last_activity"]:
                    s["last_activity"] = ts

        return scrub(list(sessions.values()))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# GET /sessions/{session_id}
# -----------------------------
@router.get("/{session_id}")
def get_session(session_id: str):
    try:
        # Try both nested and flat session_id fields
        traces = list(
            traces_container.query_items(
                query="SELECT * FROM c WHERE c.session.session_id=@sid OR c.session_id=@sid",
                parameters=[{"name": "@sid", "value": session_id}],
                enable_cross_partition_query=True,
            )
        )

        if not traces:
            raise HTTPException(status_code=404, detail="Session not found")

        first_session = traces[0].get("session", {}) or {}
        first_request = traces[0].get("request", {}) or {}

        # Get user_id from nested structure
        user_id = first_session.get("user_id") or traces[0].get("user_id", "unknown")

        total_cost_usd = 0.0
        total_tokens = 0
        total_latency_ms = 0

        timestamps = []

        for t in traces:
            usage = t.get("usage", {}) or {}
            total_tokens += usage.get("total_tokens", 0) or t.get("tokens", 0)
            
            cost_obj = t.get("cost", {}) or {}
            total_cost_usd += cost_obj.get("total_cost_usd", 0.0) or t.get("cost", 0.0)

            perf_obj = t.get("performance", {}) or {}
            total_latency_ms += perf_obj.get("latency_ms", 0) or 0

            request = t.get("request", {}) or {}
            # Normalize timestamps
            ts = normalize_ts(request.get("timestamp") or t.get("timestamp"))
            if ts:
                timestamps.append(ts)

        created = min(timestamps) if timestamps else None
        last_activity = max(timestamps) if timestamps else None

        now_sec = datetime.now(timezone.utc).timestamp()

        # Active session?
        if last_activity and (now_sec - last_activity <= SESSION_IDLE_TIMEOUT):
            effective_end = now_sec
        else:
            effective_end = last_activity

        session = {
            "session_id": session_id,
            "user_id": user_id,
            "environment": first_request.get("environment"),
            "trace_count": len(traces),
            "total_tokens": total_tokens,
            "total_cost_usd": safe_round(total_cost_usd, 6),
            "total_cost_micro_usd": int(total_cost_usd * 1_000_000),
            "avg_latency_ms": safe_round(total_latency_ms / len(traces), 2) if len(traces) > 0 else 0,
            "created": created,
            "last_activity": last_activity,
            "session_start": ts_to_iso(created) if created else None,
            "session_end": ts_to_iso(effective_end) if effective_end else None,
            "session_duration_ms": int((effective_end - created) * 1000) if created and effective_end else None,
            "traces": traces,
        }

        return scrub(session)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))