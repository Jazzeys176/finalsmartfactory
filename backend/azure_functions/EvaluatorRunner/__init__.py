import os
import logging
import random
import time
from datetime import datetime, timezone

from azure.functions import DocumentList
from azure.cosmos import CosmosClient, exceptions

from evaluators.registry import EVALUATORS


# --------------------------------------------------
# Validate environment variables
# --------------------------------------------------

COSMOS_CONN_READ = os.getenv("COSMOS_CONN_READ")
COSMOS_CONN_WRITE = os.getenv("COSMOS_CONN_WRITE")

if not COSMOS_CONN_READ:
    raise RuntimeError("❌ Missing environment variable: COSMOS_CONN_READ")

if not COSMOS_CONN_WRITE:
    raise RuntimeError("❌ Missing environment variable: COSMOS_CONN_WRITE")


# --------------------------------------------------
# Cosmos Clients
# --------------------------------------------------

COSMOS_READ = CosmosClient.from_connection_string(COSMOS_CONN_READ)
COSMOS_WRITE = CosmosClient.from_connection_string(COSMOS_CONN_WRITE)

DB_READ = COSMOS_READ.get_database_client("llmops-data")
DB_WRITE = COSMOS_WRITE.get_database_client("llmops-data")

EVALUATORS_CONTAINER = DB_READ.get_container_client("evaluators")
EVALS_CONTAINER = DB_WRITE.get_container_client("evaluations")


# --------------------------------------------------
# Azure Function Entry
# --------------------------------------------------

def main(documents: DocumentList):
    logging.error("🔥 EvaluatorRunner TRIGGERED 🔥")

    if not documents:
        logging.warning("[EvaluatorRunner] No documents received")
        return

    logging.info(f"[EvaluatorRunner] Processing {len(documents)} traces")

    # --------------------------------------------------
    # Load enabled evaluators
    # --------------------------------------------------
    try:
        evaluators = list(
            EVALUATORS_CONTAINER.query_items(
                query="SELECT * FROM c WHERE c.status = 'enabled'",
                enable_cross_partition_query=True,
            )
        )
    except Exception:
        logging.exception("Failed to load evaluators")
        return

    if not evaluators:
        logging.warning("[EvaluatorRunner] No enabled evaluators found")
        return

    # --------------------------------------------------
    # Process each trace
    # --------------------------------------------------
    for trace in documents:
        trace_id = trace.get("trace_id") or trace.get("id")

        if not trace_id:
            logging.warning("Trace missing trace_id and id — skipping")
            continue

        for ev in evaluators:
            evaluator_name = ev.get("score_name")
            execution_cfg = ev.get("execution", {})

            if not evaluator_name:
                continue

            # --------------------------------------------------
            # 1️⃣ SAMPLING RATE
            # --------------------------------------------------
            sampling_rate = execution_cfg.get("sampling_rate", 1.0)  # default: 100%
            if sampling_rate < 0 or sampling_rate > 1:
                sampling_rate = 1.0  # safety fallback

            if random.random() > sampling_rate:
                logging.info(
                    f"[EvaluatorRunner] Skipped {evaluator_name} due to sampling ({sampling_rate})"
                )
                continue

            # --------------------------------------------------
            # 2️⃣ OPTIONAL DELAY BEFORE RUNNING EVALUATOR
            # --------------------------------------------------
            delay_ms = execution_cfg.get("delay_ms", 0)
            if delay_ms > 0:
                logging.info(
                    f"[EvaluatorRunner] Delay {delay_ms}ms for evaluator {evaluator_name}"
                )
                time.sleep(delay_ms / 1000)

            # --------------------------------------------------
            # Get evaluator template function
            # --------------------------------------------------
            template_id = ev.get("template", {}).get("id")
            evaluator_fn = EVALUATORS.get(template_id)

            if not evaluator_fn:
                logging.warning(
                    f"No evaluator function registered for template {template_id}"
                )
                continue

            eval_id = f"{trace_id}:{evaluator_name}"

            # --------------------------------------------------
            # 3️⃣ Idempotency check
            # --------------------------------------------------
            try:
                EVALS_CONTAINER.read_item(item=eval_id, partition_key=trace_id)
                logging.info(f"[EvaluatorRunner] Skipping existing eval {eval_id}")
                continue
            except exceptions.CosmosResourceNotFoundError:
                pass
            except Exception:
                logging.exception("Failed during idempotency check")
                continue

            # --------------------------------------------------
            # 4️⃣ Run evaluator with duration measurement
            # --------------------------------------------------
            start_time = time.time()

            try:
                result = evaluator_fn(trace)
                status = "completed"
            except Exception as e:
                logging.exception(
                    f"Evaluator {evaluator_name} failed for trace {trace_id}"
                )
                result = {
                    "score": None,
                    "explanation": str(e),
                }
                status = "failed"

            duration_ms = int((time.time() - start_time) * 1000)

            # --------------------------------------------------
            # 5️⃣ Persist evaluation
            # --------------------------------------------------
            doc = {
                "id": eval_id,
                "trace_id": trace_id,  # partition key
                "evaluator_name": evaluator_name,
                "score": result.get("score"),
                "explanation": result.get("explanation", ""),
                "status": status,
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                EVALS_CONTAINER.upsert_item(doc)
                logging.info(
                    f"[EvaluatorRunner] Stored {evaluator_name} for trace {trace_id} "
                    f"(duration={duration_ms}ms)"
                )
            except Exception:
                logging.exception("Failed to persist evaluation")
