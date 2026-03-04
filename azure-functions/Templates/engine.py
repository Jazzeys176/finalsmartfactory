import logging
import re
from typing import Optional
from jinja2 import Template

from shared.cosmos import DB_READ
from shared.llm import call_llm


# ----------------------------------------------------
# Cosmos Containers
# ----------------------------------------------------
EVALUATORS_CONTAINER = DB_READ.get_container_client("evaluators")
TEMPLATES_CONTAINER = DB_READ.get_container_client("templates")


# ----------------------------------------------------
# Pricing Table (USD per token)
# ----------------------------------------------------
MODEL_PRICING = {
    "gpt-4o": {"input": 0.000005, "output": 0.000015},
    "gpt-4o-mini": {"input": 0.00000015, "output": 0.0000006},
}


# ----------------------------------------------------
# Fetch Evaluator
# ----------------------------------------------------
def fetch_evaluator(evaluator_id: str):
    try:
        return EVALUATORS_CONTAINER.read_item(
            item=evaluator_id,
            partition_key=evaluator_id
        )
    except Exception as e:
        logging.error(f"[engine] Failed to load evaluator {evaluator_id}: {e}")
        raise


# ----------------------------------------------------
# Fetch Template
# ----------------------------------------------------
def fetch_template(template_id: str):
    try:
        return TEMPLATES_CONTAINER.read_item(
            item=template_id,
            partition_key=template_id
        )
    except Exception as e:
        logging.error(f"[engine] Failed to load template {template_id}: {e}")
        raise


# ----------------------------------------------------
# Render Prompt
# ----------------------------------------------------
def render_prompt(template_str: str, variables: dict) -> str:
    try:
        return Template(template_str).render(**variables)
    except Exception as e:
        logging.error(f"[engine] Failed to render template: {e}")
        raise


# ----------------------------------------------------
# Extract Numeric Score
# ----------------------------------------------------
def parse_numeric_score(raw: Optional[str]) -> Optional[float]:
    try:
        if not raw:
            return None

        match = re.search(r"score[:\s]+(\d+(?:\.\d+)?)", raw, re.IGNORECASE)
        if match:
            return float(match.group(1))

        matches = re.findall(r"\d+(?:\.\d+)?", raw)
        if matches:
            return float(matches[0])

        return None

    except Exception:
        return None


# ----------------------------------------------------
# Cost Calculation
# ----------------------------------------------------
def calculate_cost(model, prompt_tokens, completion_tokens):
    pricing = MODEL_PRICING.get(model)

    if not pricing:
        return 0

    input_cost = prompt_tokens * pricing["input"]
    output_cost = completion_tokens * pricing["output"]

    return input_cost + output_cost


# ----------------------------------------------------
# Main Evaluator Execution
# ----------------------------------------------------
def run_evaluator(
    evaluator_id: str,
    variables: dict,
    deployment: Optional[str] = None
) -> dict:

    logging.info(f"[engine] Starting run_evaluator for {evaluator_id}")

    evaluator_doc = fetch_evaluator(evaluator_id)
    template_id = evaluator_doc["template"]["id"]

    model_override = evaluator_doc.get("template", {}).get("model")

    template_doc = fetch_template(template_id)

    template_model = template_doc.get("model")
    prompt_template = template_doc["template"]
    required_inputs = template_doc.get("inputs", [])

    model = deployment or model_override or template_model

    logging.info(f"[engine] Using model/deployment: {model}")

    template_variables = {}

    for key in required_inputs:
        if key in variables and variables.get(key) is not None:
            template_variables[key] = variables[key]
        elif "_raw" in variables and key in variables["_raw"]:
            template_variables[key] = variables["_raw"][key]
        else:
            raise ValueError(f"Missing required template inputs: [{key}]")

    final_prompt = render_prompt(prompt_template, template_variables)

    # ----------------------------------------------------
    # Call LLM
    # ----------------------------------------------------
    response = call_llm(
        model=model,
        prompt=final_prompt
    )

    if not response:
        return {
            "evaluator_id": evaluator_id,
            "template_id": template_id,
            "model_used": model,
            "score": None,
            "classification": "failed",
            "raw_output": "Empty response",
            "cost_usd": 0
        }

    # Expect response format
    raw_output = response.get("text")
    usage = response.get("usage", {})

    prompt_tokens = usage.get("prompt_tokens", 0)
    completion_tokens = usage.get("completion_tokens", 0)

    cost = calculate_cost(model, prompt_tokens, completion_tokens)

    score = parse_numeric_score(raw_output)

    classification = "completed" if score is not None else "failed"

    return {
        "evaluator_id": evaluator_id,
        "template_id": template_id,
        "model_used": model,
        "score": score,
        "classification": classification,
        "raw_output": raw_output,
        "cost_usd": round(cost, 6)
    }