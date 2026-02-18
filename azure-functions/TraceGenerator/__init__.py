import os
import time
import random
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, exceptions
from groq import Groq

from shared.secrets import get_secret


# ============================================================
# CONFIG (COST OPTIMIZED)
# ============================================================

DEFAULT_MODEL = "llama-3.1-8b-instant"  

GOOD_RATIO = 0.6
PARTIAL_CONTEXT_RATIO = 0.25
DEGRADED_CONTEXT_RATIO = 0.15


# ============================================================
# USERS / TRACE TYPES
# ============================================================

USERS = [f"user-{str(i).zfill(4)}" for i in range(1, 150)]

TRACE_NAMES = [
    "simple-qa",
    "multi-hop-reasoning",
    "tool-use-flow"
]


# ============================================================
# DATASET
# ============================================================

DATA = [
    {
        "input": "What causes pump cavitation?",
        "context": "Pump cavitation occurs when suction pressure drops below vapor pressure causing vapor bubble collapse."
    },
    {
        "input": "Why is the motor overheating?",
        "context": "Motor overheating may result from overload, blocked ventilation, or insulation degradation."
    },
    {
        "input": "Why did the compressor fail?",
        "context": "Compressor failure may occur due to lubrication issues, electrical faults, or overheating."
    },
    {
        "input": "Why did the turbine shut down?",
        "context": "Turbine shutdown occurs when vibration exceeds threshold or lubrication pressure drops."
    },
    {
        "input": "What should be done after detecting a gas leak?",
        "context": "Gas leaks require evacuation and ignition source isolation."
    },
    {
        "input": "Why did vibration increase after bearing replacement?",
        "context": "Improper alignment after bearing replacement can increase vibration."
    }
]

ALL_CONTEXTS = [d["context"] for d in DATA]


# ============================================================
# COST CALCULATION
# ============================================================

def calculate_cost(model, tokens_in, tokens_out):
    pricing_per_token = {
        "llama-3.1-8b-instant": 0.000001  # lower assumed price
    }
    price = pricing_per_token.get(model, 0.000001)
    return round((tokens_in + tokens_out) * price, 6)


# ============================================================
# LLM WRAPPER (COST OPTIMIZED)
# ============================================================

class GroqWrapper:

    def __init__(self, api_key):
        self.client = Groq(api_key=api_key)

    def generate(self, prompt, context, model_name):

        start = time.time()

        # Trim context length to avoid large input tokens
        context = context[:500]

        system_instruction = (
            "You are a Smart Factory assistant. "
            "Answer concisely using the context provided."
        )

        response = self.client.chat.completions.create(
            model=model_name,
            temperature=0.3,
            max_tokens=120,
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": f"Context: {context}\n\nQuestion: {prompt}"}
            ]
        )

        latency = (time.time() - start) * 1000

        tokens_in = response.usage.prompt_tokens
        tokens_out = response.usage.completion_tokens

        return {
            "output": response.choices[0].message.content,
            "tokens_input": tokens_in,
            "tokens_output": tokens_out,
            "latency_ms": latency,
            "cost": calculate_cost(model_name, tokens_in, tokens_out),
            "model": model_name
        }


def get_llm_provider(model_name):
    api_key = get_secret("GROK-API-KEY")
    return GroqWrapper(api_key)


# ============================================================
# TRACE COUNTER
# ============================================================

def get_next_trace_number(counter_container):
    try:
        doc = counter_container.read_item(
            item="trace_counter",
            partition_key="trace_counter"
        )
        next_no = doc["value"] + 1
    except exceptions.CosmosResourceNotFoundError:
        next_no = 1
        doc = {
            "id": "trace_counter",
            "partitionKey": "trace_counter",
            "value": 0
        }

    doc["value"] = next_no
    counter_container.upsert_item(doc)
    return next_no


# ============================================================
# TRACE BUILDER
# ============================================================

def make_trace(trace_no, session_id, user_id, trace_name,
               input_text, context_text, llm_response):

    trace_id = f"trace-{str(trace_no).zfill(4)}"

    tokens_in = llm_response["tokens_input"]
    tokens_out = llm_response["tokens_output"]

    return {
        "id": trace_id,
        "partitionKey": trace_id,
        "trace_id": trace_id,
        "session_id": session_id,
        "user_id": user_id,
        "trace_name": trace_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "input": input_text,
        "context": context_text,
        "output": llm_response["output"],
        "latency_ms": llm_response["latency_ms"],
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens": tokens_in + tokens_out,
        "cost": llm_response["cost"],
        "model": llm_response["model"],
    }


# ============================================================
# TIMER FUNCTION ENTRY (REDUCED LOAD)
# ============================================================

def main(mytimer):

    COSMOS_CONN_WRITE = get_secret("COSMOS-CONN-WRITE")

    cosmos = CosmosClient.from_connection_string(COSMOS_CONN_WRITE)
    db = cosmos.get_database_client("llmops-data")
    traces_container = db.get_container_client("traces")
    counter_container = db.get_container_client("metrics")

    provider = get_llm_provider(DEFAULT_MODEL)

    # Only 1–2 traces per trigger (reduce cost)
    for _ in range(random.randint(1, 2)):

        base = random.choice(DATA)
        input_text = base["input"]
        context_text = base["context"]

        r = random.random()

        if r < GOOD_RATIO:
            pass
        elif r < GOOD_RATIO + PARTIAL_CONTEXT_RATIO:
            context_text += " Minor unrelated maintenance note."
        else:
            context_text = context_text[: int(len(context_text) * 0.7)]

        llm_response = provider.generate(
            prompt=input_text,
            context=context_text,
            model_name=DEFAULT_MODEL
        )

        trace_no = get_next_trace_number(counter_container)

        trace = make_trace(
            trace_no=trace_no,
            session_id=f"session-{random.randint(1, 150)}",
            user_id=random.choice(USERS),
            trace_name=random.choice(TRACE_NAMES),
            input_text=input_text,
            context_text=context_text,
            llm_response=llm_response
        )

        traces_container.create_item(trace)
