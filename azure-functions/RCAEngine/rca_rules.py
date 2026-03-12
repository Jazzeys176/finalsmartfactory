THRESHOLDS = {
    "weak_retrieval": 0.6,
    "moderate_retrieval_low": 0.6,
    "moderate_retrieval_high": 0.75,
    "context_ignore": 0.45,
    "hallucination": 0.5,
    "weak_retrieval_hallucination": 0.65,
    "ungrounded_context": 0.3,
    "low_context_utilization": 0.5,
    "context_tokens_utilization": 200,
    "context_tokens_min": 100,
    "context_tokens_max": 3000,
    "temperature": 0.7,
    "conciseness": 0.45,
    "completion_tokens": 450
}


def analyze_trace(trace, evals):

    findings = []
    evidence = []
    suggestions = []

    # ------------------------------------------------------------
    # Extract telemetry (normalized schema)
    # ------------------------------------------------------------

    retrieval = trace.get("retrieval", {}) or {}

    retrieval_executed = retrieval.get(
        "executed",
        trace.get("retrieval_executed", False)
    )

    documents_found = retrieval.get(
        "documents_found",
        trace.get("documents_found", 0)
    )

    retrieval_confidence = retrieval.get(
        "retrieval_confidence",
        trace.get("retrieval_confidence", 0.0)
    )

    documents_found = int(documents_found or 0)
    retrieval_confidence = float(retrieval_confidence or 0.0)

    spans = trace.get("spans", [])

    usage = trace.get("usage", {})
    completion_tokens = int(usage.get("completion_tokens", 0))

    output = trace.get("output_text")

    # ------------------------------------------------------------
    # Extract LLM span telemetry
    # ------------------------------------------------------------

    llm_span = next((s for s in spans if s.get("type") == "llm"), {})

    temperature = llm_span.get("temperature")
    context_tokens = llm_span.get("context_tokens", 0)

    evidence.append(f"documents_found={documents_found}")
    evidence.append(f"retrieval_confidence={retrieval_confidence}")

    if temperature is not None:
        evidence.append(f"temperature={temperature}")

    if context_tokens:
        evidence.append(f"context_tokens={context_tokens}")

    # ------------------------------------------------------------
    # Track evaluator states + extract scores dynamically
    # ------------------------------------------------------------

    completed_evaluators = []
    skipped_evaluators = []
    failed_evaluators = []

    scores = {}

    for e in evals:

        name = e.get("evaluator")
        status = e.get("status")
        score = e.get("score")

        if not name:
            continue

        if status == "completed":

            completed_evaluators.append(name)

            try:
                scores[name] = float(score)
                evidence.append(f"{name}_score={scores[name]}")
            except:
                pass

        elif status == "skipped":

            skipped_evaluators.append(name)

            evidence.append(f"{name}_evaluator_skipped")

            reason = "dependency_condition_not_met"

            if documents_found == 0:
                reason = "no_retrieved_documents"

            elif not retrieval_executed:
                reason = "retrieval_not_executed"

            elif not output:
                reason = "no_model_output"

            evidence.append(f"{name}_skip_reason={reason}")

        elif status == "failed":

            failed_evaluators.append(name)
            evidence.append(f"{name}_evaluator_failed")

    context_score = scores.get("context_relevance")
    halluc_score = scores.get("hallucination")
    concise_score = scores.get("conciseness")

    # ------------------------------------------------------------
    # 1 Retrieval Failure
    # ------------------------------------------------------------

    if retrieval_executed and documents_found == 0:

        findings.append("retrieval_failed")

        evidence.append("documents_found=0")

        suggestions.append(
            "Improve embeddings, chunking strategy, or increase top_k."
        )

    # ------------------------------------------------------------
    # 2 Weak Retrieval
    # ------------------------------------------------------------

    if documents_found > 0 and retrieval_confidence < THRESHOLDS["weak_retrieval"]:

        findings.append("weak_retrieval_quality")

        suggestions.append(
            "Improve embedding quality, chunk size, or increase retrieval_k."
        )

    # ------------------------------------------------------------
    # 3 Moderate Retrieval
    # ------------------------------------------------------------

    if (
        THRESHOLDS["moderate_retrieval_low"]
        <= retrieval_confidence
        < THRESHOLDS["moderate_retrieval_high"]
    ):

        findings.append("moderate_retrieval_confidence")

        suggestions.append(
            "Consider reranking retrieved documents or improving semantic chunking."
        )

    # ------------------------------------------------------------
    # 4 Context Ignored
    # ------------------------------------------------------------

    if (
        context_score is not None
        and context_score < THRESHOLDS["context_ignore"]
        and documents_found > 0
        and retrieval_confidence >= THRESHOLDS["moderate_retrieval_high"]
    ):

        findings.append("generation_ignored_context")

        suggestions.append(
            "Strengthen grounding instructions or enforce citation-based answering."
        )

    # ------------------------------------------------------------
    # 5 Hallucination
    # ------------------------------------------------------------

    if halluc_score is not None and halluc_score < THRESHOLDS["hallucination"]:

        if documents_found == 0:

            findings.append("hallucination_due_to_no_context")

            suggestions.append(
                "Force refusal when no documents are retrieved."
            )

        elif retrieval_confidence < THRESHOLDS["weak_retrieval_hallucination"]:

            findings.append("hallucination_due_to_weak_retrieval")

            suggestions.append(
                "Improve retrieval relevance or apply reranking."
            )

        elif context_score is not None and context_score < THRESHOLDS["ungrounded_context"]:

            findings.append("ungrounded_answer")

            suggestions.append(
                "Model relied on prior knowledge instead of retrieved context."
            )

        else:

            findings.append("generation_overreach")

            suggestions.append(
                "Reduce model temperature or enforce stricter grounding."
            )

    # ------------------------------------------------------------
    # 6 Low Context Utilization
    # ------------------------------------------------------------

    if (
        context_score is not None
        and context_score < THRESHOLDS["low_context_utilization"]
        and context_tokens > THRESHOLDS["context_tokens_utilization"]
    ):

        findings.append("low_context_utilization")

        suggestions.append(
            "Model received context but did not properly use it."
        )

    # ------------------------------------------------------------
    # 7 Context Too Small
    # ------------------------------------------------------------

    if retrieval_executed and documents_found > 0 and context_tokens < THRESHOLDS["context_tokens_min"]:

        findings.append("low_context_provided")

        suggestions.append(
            "Increase chunk size or top_k to provide richer context."
        )

    # ------------------------------------------------------------
    # 8 Context Overload
    # ------------------------------------------------------------

    if context_tokens > THRESHOLDS["context_tokens_max"]:

        findings.append("context_overload")

        suggestions.append(
            "Reduce chunk size or apply reranking to limit context tokens."
        )

    # ------------------------------------------------------------
    # 9 High Temperature Generation
    # ------------------------------------------------------------

    if temperature is not None and temperature > THRESHOLDS["temperature"]:

        findings.append("high_temperature_generation")

        suggestions.append(
            "Lower temperature for factual QA tasks."
        )

    # ------------------------------------------------------------
    # 10 Over Verbose
    # ------------------------------------------------------------

    if concise_score is not None and concise_score < THRESHOLDS["conciseness"]:

        findings.append("over_verbose_answer")

        suggestions.append(
            "Add stricter brevity constraints or reduce max_tokens."
        )

    # ------------------------------------------------------------
    # 11 Excessive Generation
    # ------------------------------------------------------------

    if completion_tokens > THRESHOLDS["completion_tokens"]:

        findings.append("excessive_generation_length")

        suggestions.append(
            "Limit max_tokens or enforce concise response style."
        )

    # ------------------------------------------------------------
    # 12 Retrieval Executed But Not Needed
    # ------------------------------------------------------------

    if retrieval_executed and documents_found > 0 and not context_score:

        findings.append("retrieval_executed_but_unused")

        suggestions.append(
            "Consider routing logic improvements to avoid unnecessary retrieval."
        )

    # ------------------------------------------------------------
    # 13 Generation Without Retrieval
    # ------------------------------------------------------------

    if not retrieval_executed and output:

        findings.append("generation_without_retrieval")

        suggestions.append(
            "Ensure retrieval is triggered for knowledge queries."
        )

    # ------------------------------------------------------------
    # 14 Intent mismatch
    # ------------------------------------------------------------

    span_int = next(
        (s for s in spans if s.get("type") == "intent-classification"),
        None
    )

    if span_int:

        span_intent = span_int.get("metadata", {}).get("intent")
        trace_intent = trace.get("request", {}).get("intent")

        if span_intent and trace_intent and trace_intent != span_intent:

            findings.append("intent_mismatch")

            suggestions.append(
                "Investigate intent classifier consistency."
            )

    # ------------------------------------------------------------
    # RCA completeness
    # ------------------------------------------------------------

    if skipped_evaluators and completed_evaluators:

        findings.append("rca_partial_analysis")

        evidence.append(f"skipped_evaluators={','.join(skipped_evaluators)}")

    elif skipped_evaluators and not completed_evaluators:

        findings.append("rca_not_applicable")

        evidence.append(f"all_evaluators_skipped={','.join(skipped_evaluators)}")

    # ------------------------------------------------------------
    # Remove duplicates
    # ------------------------------------------------------------

    findings = list(dict.fromkeys(findings))
    evidence = list(dict.fromkeys(evidence))
    suggestions = list(dict.fromkeys(suggestions))

    # ------------------------------------------------------------
    # Healthy case
    # ------------------------------------------------------------

    if not findings:

        findings.append("no_anomaly_detected")

        evidence.append("All evaluator thresholds satisfied")

        suggestions.append("No action required")

    return findings, evidence, suggestions