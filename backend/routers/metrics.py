import math
from fastapi import APIRouter, HTTPException

from shared.cosmos import (
    metrics_container_read as metrics_container,
    evaluations_read as evaluations_container,
    traces_read as traces_container
)

router = APIRouter()

METRICS_ID = "metrics_snapshot"
METRICS_PK = "metrics_snapshot"


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


def strip_cosmos_metadata(doc: dict):
    return {k: v for k, v in doc.items() if not k.startswith("_")}


# -----------------------------
# GET /metrics
# -----------------------------
@router.get("/metrics")
def get_metrics():

    try:
        snapshot = metrics_container.read_item(
            item=METRICS_ID,
            partition_key=METRICS_PK,
        )

        return scrub(strip_cosmos_metadata(snapshot))

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# -----------------------------
# GET /metrics/evaluators/{evaluator_id}/traces
# -----------------------------
@router.get("/metrics/evaluators/{evaluator_id}/traces")
def get_traces_for_evaluator(evaluator_id: str):

    try:

        # ------------------------------------
        # Fetch evaluations for evaluator
        # ------------------------------------
        evaluations = list(
            evaluations_container.query_items(
                query="SELECT * FROM c WHERE c.evaluator_id=@eid",
                parameters=[{"name": "@eid", "value": evaluator_id}],
                enable_cross_partition_query=True,
            )
        )

        if not evaluations:
            return []

        trace_ids = [e.get("trace_id") for e in evaluations if e.get("trace_id")]

        # ------------------------------------
        # Fetch corresponding traces
        # ------------------------------------
        traces = []

        for tid in trace_ids:

            items = list(
                traces_container.query_items(
                    query="SELECT * FROM c WHERE c.trace_id=@tid",
                    parameters=[{"name": "@tid", "value": tid}],
                    enable_cross_partition_query=True,
                )
            )

            traces.extend(items)

        # ------------------------------------
        # Map evaluation scores to traces
        # ------------------------------------
        score_map = {}

        for e in evaluations:

            trace_id = e.get("trace_id")

            score_map.setdefault(trace_id, {})[evaluator_id] = {
                "score": e.get("score"),
                "variance": e.get("variance"),
                "unstable": e.get("unstable"),
                "evaluation_cost_usd": e.get("evaluation_cost_usd"),
            }

        for t in traces:

            tid = t.get("trace_id")

            if tid in score_map:
                t["evaluations"] = score_map[tid]

        return scrub([strip_cosmos_metadata(t) for t in traces])

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))