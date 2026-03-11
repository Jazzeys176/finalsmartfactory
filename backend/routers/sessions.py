import math
from datetime import datetime, timezone
from collections import defaultdict
from fastapi import APIRouter, HTTPException
from shared.cosmos import traces_container_read as traces_container
from shared.cosmos import evaluations_read as evaluations_container

SESSION_IDLE_TIMEOUT = 5 * 60
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
    if ts is None:
        return None

    ts = float(ts)

    if ts > 1e11:
        return ts / 1000

    return ts


def ts_to_iso(ts):
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

        trace_ids = [t.get("trace_id") for t in traces if t.get("trace_id")]

        evaluations = list(
            evaluations_container.query_items(
                query="SELECT * FROM c WHERE ARRAY_CONTAINS(@trace_ids, c.trace_id)",
                parameters=[{"name": "@trace_ids", "value": trace_ids}],
                enable_cross_partition_query=True,
            )
        )

        trace_eval_cost = defaultdict(float)
        trace_eval_scores = defaultdict(dict)

        for ev in evaluations:

            tid = ev.get("trace_id")
            evaluator = ev.get("evaluator")
            score = ev.get("score")
            cost = ev.get("evaluation_cost_usd", 0.0)

            if tid:
                trace_eval_cost[tid] += cost

            if tid and evaluator and score is not None:
                trace_eval_scores[tid][evaluator] = score

        sessions = defaultdict(
            lambda: {
                "session_id": None,
                "user_id": "unknown",
                "environment": None,
                "trace_count": 0,
                "total_tokens": 0,
                "generation_cost_usd": 0.0,
                "evaluation_cost_usd": 0.0,
                "avg_latency_ms": 0.0,
                "created": None,
                "last_activity": None,
                "eval_sum": defaultdict(float),
                "eval_count": defaultdict(int),
            }
        )

        for t in traces:

            session_obj = t.get("session", {})
            request_obj = t.get("request", {})
            usage_obj = t.get("usage", {})
            cost_obj = t.get("cost", {})
            perf_obj = t.get("performance", {})

            session_id = session_obj.get("session_id")
            trace_id = t.get("trace_id")

            if not session_id:
                continue

            s = sessions[session_id]

            s["session_id"] = session_id
            s["user_id"] = session_obj.get("user_id", "unknown")
            s["environment"] = request_obj.get("environment")

            s["trace_count"] += 1
            s["total_tokens"] += usage_obj.get("total_tokens", 0)

            gen_cost = cost_obj.get("total_cost_usd", 0.0)
            eval_cost = trace_eval_cost.get(trace_id, 0.0)

            s["generation_cost_usd"] += gen_cost
            s["evaluation_cost_usd"] += eval_cost

            s["avg_latency_ms"] += perf_obj.get("latency_ms", 0)

            for ev_name, score in trace_eval_scores.get(trace_id, {}).items():
                s["eval_sum"][ev_name] += score
                s["eval_count"][ev_name] += 1

            ts = normalize_ts(request_obj.get("timestamp"))

            if ts is not None:

                if s["created"] is None or ts < s["created"]:
                    s["created"] = ts

                if s["last_activity"] is None or ts > s["last_activity"]:
                    s["last_activity"] = ts

        now_sec = datetime.now(timezone.utc).timestamp()

        results = []

        for s in sessions.values():

            if s["trace_count"] > 0:
                s["avg_latency_ms"] = safe_round(
                    s["avg_latency_ms"] / s["trace_count"], 2
                )

            avg_scores = {}

            for name, total in s["eval_sum"].items():

                count = s["eval_count"][name]

                if count > 0:
                    avg_scores[name] = safe_round(total / count, 4)

            created = s["created"]
            last = s["last_activity"]

            if created and last:

                if now_sec - last <= SESSION_IDLE_TIMEOUT:
                    effective_end = now_sec
                else:
                    effective_end = last

                s["session_start"] = ts_to_iso(created)
                s["session_end"] = ts_to_iso(effective_end)

                s["session_duration_ms"] = int((effective_end - created) * 1000)

            else:
                s["session_start"] = None
                s["session_end"] = None
                s["session_duration_ms"] = None

            result = {
                "session_id": s["session_id"],
                "user_id": s["user_id"],
                "environment": s["environment"],
                "trace_count": s["trace_count"],
                "total_tokens": s["total_tokens"],
                "generation_cost_usd": safe_round(s["generation_cost_usd"]),
                "evaluation_cost_usd": safe_round(s["evaluation_cost_usd"]),
                "total_cost_usd": safe_round(
                    s["generation_cost_usd"] + s["evaluation_cost_usd"]
                ),
                "avg_latency_ms": s["avg_latency_ms"],
                "session_start": s["session_start"],
                "session_end": s["session_end"],
                "session_duration_ms": s["session_duration_ms"],
                "avg_scores": avg_scores,
            }

            results.append(result)

        return scrub(results)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# GET /sessions/{session_id}
# -----------------------------
@router.get("/{session_id}")
def get_session(session_id: str):

    try:

        traces = list(
            traces_container.query_items(
                query="SELECT * FROM c WHERE c.session.session_id=@sid",
                parameters=[{"name": "@sid", "value": session_id}],
                enable_cross_partition_query=True,
            )
        )

        if not traces:
            raise HTTPException(status_code=404, detail="Session not found")

        trace_ids = [t.get("trace_id") for t in traces if t.get("trace_id")]

        evaluations = list(
            evaluations_container.query_items(
                query="SELECT * FROM c WHERE ARRAY_CONTAINS(@trace_ids, c.trace_id)",
                parameters=[{"name": "@trace_ids", "value": trace_ids}],
                enable_cross_partition_query=True,
            )
        )

        trace_eval_cost = defaultdict(float)
        trace_eval_scores = defaultdict(dict)

        eval_sum = defaultdict(float)
        eval_count = defaultdict(int)

        for ev in evaluations:

            trace_id = ev.get("trace_id")
            evaluator = ev.get("evaluator")
            score = ev.get("score")
            cost = ev.get("evaluation_cost_usd", 0.0)

            if trace_id:
                trace_eval_cost[trace_id] += cost

            if trace_id and evaluator and score is not None:
                trace_eval_scores[trace_id][evaluator] = score
                eval_sum[evaluator] += score
                eval_count[evaluator] += 1

        generation_cost = sum(
            t.get("cost", {}).get("total_cost_usd", 0.0) for t in traces
        )

        evaluation_cost = sum(trace_eval_cost.values())

        timestamps = [
            normalize_ts(t.get("request", {}).get("timestamp")) for t in traces
        ]

        timestamps = [t for t in timestamps if t is not None]

        created = min(timestamps) if timestamps else None
        last_activity = max(timestamps) if timestamps else None

        now_sec = datetime.now(timezone.utc).timestamp()

        if created and last_activity:

            if now_sec - last_activity <= SESSION_IDLE_TIMEOUT:
                effective_end = now_sec
            else:
                effective_end = last_activity

        else:
            effective_end = None

        avg_scores = {}

        for name, total in eval_sum.items():

            count = eval_count[name]

            if count > 0:
                avg_scores[name] = safe_round(total / count, 4)

        for t in traces:

            tid = t.get("trace_id")

            t["evaluation_cost_usd"] = safe_round(trace_eval_cost.get(tid, 0))
            t["evaluator_scores"] = trace_eval_scores.get(tid, {})

        session = {
            "session_id": session_id,
            "user_id": traces[0].get("session", {}).get("user_id", "unknown"),
            "environment": traces[0].get("request", {}).get("environment"),
            "trace_count": len(traces),
            "total_tokens": sum(
                t.get("usage", {}).get("total_tokens", 0) for t in traces
            ),
            "generation_cost_usd": safe_round(generation_cost),
            "evaluation_cost_usd": safe_round(evaluation_cost),
            "total_cost_usd": safe_round(generation_cost + evaluation_cost),
            "avg_latency_ms": safe_round(
                sum(t.get("performance", {}).get("latency_ms", 0) for t in traces)
                / len(traces),
                2,
            ),
            "session_start": ts_to_iso(created),
            "session_end": ts_to_iso(effective_end),
            "session_duration_ms": (
                int((effective_end - created) * 1000)
                if created and effective_end
                else None
            ),
            "avg_scores": avg_scores,
            "traces": traces,
        }

        return scrub(session)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))