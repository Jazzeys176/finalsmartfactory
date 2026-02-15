import logging
import random
import time
from datetime import datetime, timezone

from azure.functions import DocumentList
from azure.cosmos import exceptions

from shared.audit import audit_log
from shared.cosmos import evaluators_read, evaluations_write
from Templates.engine import run_evaluator   # 🔥 direct dynamic call


# --------------------------------------------------
# Normalize trace for evaluator templates
# --------------------------------------------------
def normalize_trace(trace: dict) -> dict:
    return {
        "input": trace.get("input") or trace.get("question", ""),
        "context": trace.get("context", ""),
        "response": trace.get("output") or trace.get("answer", ""),
        "output": trace.get("output") or trace.get("answer", ""),
        "_raw": trace
    }


# --------------------------------------------------
# Azure Function Entry
# --------------------------------------------------
def main(documents: DocumentList):
    logging.info("🔥 EvaluatorRunner TRIGGERED 🔥")

    if not documents:
        logging.warning("[EvaluatorRunner] No documents received")
        return

    trace_count = len(documents)
    logging.info(f"[EvaluatorRunner] Processing {trace_count} traces")

    # --------------------------------------------------
    # Load active evaluators
    # --------------------------------------------------
    try:
        evaluators = list(
            evaluators_read.query_items(
                query="SELECT * FROM c WHERE c.status = 'active'",
                enable_cross_partition_query=True,
            )
        )
    except Exception:
        logging.exception("[EvaluatorRunner] Failed to load evaluators")
        return

    if not evaluators:
        logging.warning("[EvaluatorRunner] No active evaluators found")
        return

    # --------------------------------------------------
    # Process each evaluator
    # --------------------------------------------------
    for ev in evaluators:
        evaluator_id = ev.get("id")
        evaluator_name = ev.get("score_name")
        template_id = ev.get("template", {}).get("id")

        if not evaluator_id or not template_id:
            logging.warning(f"[EvaluatorRunner] Invalid evaluator config: {ev}")
            continue

        logging.info(f"[EvaluatorRunner] Running evaluator '{evaluator_id}'")

        executed_count = 0
        exec_cfg = ev.get("execution", {})

        # --------------------------------------------------
        # Iterate traces
        # --------------------------------------------------
        for trace in documents:
            trace_id = trace.get("trace_id") or trace.get("id")
            if not trace_id:
                continue

            # Sampling
            sampling_rate = exec_cfg.get("sampling_rate", 1.0)
            if random.random() > sampling_rate:
                continue

            # Optional delay
            delay_ms = exec_cfg.get("delay_ms", 0)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000)

            eval_id = f"{trace_id}:{evaluator_id}"

            # --------------------------------------------------
            # Idempotency Check
            # --------------------------------------------------
            try:
                evaluations_write.read_item(eval_id, partition_key=trace_id)
                continue
            except exceptions.CosmosResourceNotFoundError:
                pass
            except Exception:
                logging.exception("[EvaluatorRunner] Idempotency check failed")
                continue

            # --------------------------------------------------
            # Run evaluator dynamically
            # --------------------------------------------------
            start_time = time.time()

            try:
                normalized = normalize_trace(trace)

                result = run_evaluator(evaluator_id, normalized)

                score = result.get("score")
                raw_output = result.get("raw_output")
                classification = result.get("classification")

                if isinstance(score, (int, float)):
                    score = round(float(score), 2)

                # 🔥 Status now reflects engine result
                status = "completed" if classification != "failed" else "failed"

            except Exception as e:
                logging.exception(
                    f"[EvaluatorRunner] Evaluator '{evaluator_id}' failed for trace {trace_id}"
                )
                score = None
                raw_output = str(e)
                classification = "failed"
                status = "failed"

            duration_ms = int((time.time() - start_time) * 1000)

            # --------------------------------------------------
            # Save evaluation record
            # --------------------------------------------------
            doc = {
                "id": eval_id,
                "trace_id": trace_id,
                "evaluator": evaluator_name,
                "evaluator_id": evaluator_id,
                "template_id": template_id,
                "score": score,
                "classification": classification,
                "raw_output": raw_output,
                "status": status,
                "duration_ms": duration_ms,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }

            try:
                evaluations_write.upsert_item(doc)
                executed_count += 1
            except Exception:
                logging.exception("[EvaluatorRunner] Failed to persist evaluation")

        # --------------------------------------------------
        # Audit Log
        # --------------------------------------------------
        audit_log(
            action="Evaluator Run Completed",
            type="evaluator",
            user="system",
            details=f"Ran evaluator '{evaluator_id}' on {executed_count}/{trace_count} traces",
        )

        logging.info(
            f"[EvaluatorRunner] Completed evaluator '{evaluator_id}' "
            f"({executed_count}/{trace_count})"
        )
