import os
import random
from datetime import datetime, timezone
from azure.cosmos import CosmosClient, exceptions

# ============================================================
# RATIOS
# ============================================================
GOOD_RATIO = 0.65
BAD_CONTEXT_RATIO = 0.20
BAD_ANSWER_RATIO = 0.15

# ============================================================
# USERS / TRACE TYPES
# ============================================================
USERS = [f"user-{str(i).zfill(4)}" for i in range(1, 501)]

TRACE_NAMES = [
    "simple-qa",
    "multi-hop-reasoning",
    "tool-use-flow"
]

# ============================================================
# EXPANDED SMART-FACTORY DATASET
# ============================================================
DATA = [
    {
        "input": "Explain valve shutdown procedure",
        "context": (
            "Standard valve shutdown includes isolating flow from both ends and slowly relieving "
            "pressure. Some legacy diagrams mention manual bleed-off valves which may not exist "
            "in newer installations. Incorrect sequencing can cause pressure shock."
        ),
        "output": (
            "Valve shutdown requires isolating upstream and downstream flow and relieving pressure "
            "to reach a zero-energy state."
        )
    },
    {
        "input": "Why does the circuit breaker trip repeatedly?",
        "context": (
            "Repeated tripping usually indicates sustained overload, short circuits, or thermal fatigue. "
            "Humidity inside panels can cause intermittent leakage currents."
        ),
        "output": (
            "Breakers trip due to overloads, thermal fatigue, or moisture-related leakage."
        )
    },
    {
        "input": "What caused the temperature spike in the reactor?",
        "context": (
            "Temperature spikes often arise from cooling-loop imbalance, fouled heat exchangers, "
            "or sensor drift. Flow meters may falsely indicate normal flow."
        ),
        "output": (
            "Cooling-loop failures or faulty sensors commonly cause reactor temperature spikes."
        )
    },
    {
        "input": "How do you stabilize steam pipeline pressure?",
        "context": (
            "Steam pressure instability results from feed variability and clogged steam traps. "
            "Gradual valve modulation prevents water hammer."
        ),
        "output": (
            "Pressure is stabilized by controlled valve modulation and maintaining steam traps."
        )
    },
    {
        "input": "Why did the robotic arm freeze during operation?",
        "context": (
            "Robotic freezes may be caused by encoder desynchronization, PLC communication delays, "
            "or electromagnetic interference from nearby equipment."
        ),
        "output": (
            "Freezing is usually caused by encoder faults or PLC communication delays."
        )
    },
    {
        "input": "How do you detect compressed air leakage?",
        "context": (
            "Leak detection uses ultrasonic sensors or pressure decay testing. "
            "Environmental noise reduces ultrasonic accuracy."
        ),
        "output": (
            "Leaks are detected using ultrasonic scanners or pressure decay analysis."
        )
    },
    {
        "input": "Why is the conveyor belt misaligned?",
        "context": (
            "Misalignment results from uneven loading, worn idlers, warped frames, "
            "or humidity-induced belt expansion."
        ),
        "output": (
            "Uneven load and worn idlers are common causes of belt misalignment."
        )
    },
    {
        "input": "What causes abnormal vibration in motors?",
        "context": (
            "Abnormal vibration originates from shaft imbalance, bearing wear, "
            "loose mounting bolts, or electrical air-gap issues."
        ),
        "output": (
            "Vibration usually indicates imbalance, bearing wear, or mounting problems."
        )
    },
    {
        "input": "How do you handle hydraulic pressure loss?",
        "context": (
            "Pressure loss may occur due to seal leaks, pump cavitation, clogged return lines, "
            "or faulty pressure gauges."
        ),
        "output": (
            "Handling pressure loss involves checking seals, pumps, and return lines."
        )
    },
    {
        "input": "Why did the PLC stop responding?",
        "context": (
            "PLC failures are often caused by I/O bus saturation, firmware corruption, "
            "aging power supplies, or grounding noise."
        ),
        "output": (
            "PLCs stop responding due to firmware faults, power issues, or I/O overload."
        )
    },

    # ---------- SAFETY & OPERATIONS ----------
    {
        "input": "Why did the emergency shutdown trigger unexpectedly?",
        "context": (
            "Emergency shutdowns may trigger due to faulty limit switches, "
            "false positives from vibration sensors, or wiring insulation breakdown."
        ),
        "output": (
            "Unexpected shutdowns often result from sensor faults or wiring issues."
        )
    },
    {
        "input": "How do you test safety interlocks?",
        "context": (
            "Safety interlocks are tested by simulating fault conditions and verifying "
            "that actuators respond within certified time limits."
        ),
        "output": (
            "Interlocks are tested by simulating faults and verifying response times."
        )
    },
    {
        "input": "What causes false fire alarm activation?",
        "context": (
            "False alarms occur due to dust accumulation, steam ingress, "
            "or aging optical sensors."
        ),
        "output": (
            "Dust, steam, or sensor aging can trigger false fire alarms."
        )
    },

    # ---------- ENERGY & UTILITIES ----------
    {
        "input": "Why is energy consumption higher during night shifts?",
        "context": (
            "Higher energy use may result from idle machines left powered, "
            "inefficient lighting systems, or improper shift shutdown procedures."
        ),
        "output": (
            "Night shift energy spikes usually come from idle equipment and lighting."
        )
    },
    {
        "input": "How do you improve power factor in industrial plants?",
        "context": (
            "Power factor is improved using capacitor banks, synchronous condensers, "
            "or VFD tuning."
        ),
        "output": (
            "Capacitor banks and VFD tuning improve power factor."
        )
    },

    # ---------- MAINTENANCE ----------
    {
        "input": "Why do bearings fail prematurely?",
        "context": (
            "Premature bearing failure is caused by contamination, misalignment, "
            "improper lubrication, or overloading."
        ),
        "output": (
            "Bearing failures usually result from contamination or lubrication issues."
        )
    },
    {
        "input": "How do you predict equipment failure?",
        "context": (
            "Predictive maintenance relies on vibration analysis, thermal imaging, "
            "oil analysis, and trend monitoring."
        ),
        "output": (
            "Failure is predicted using vibration, thermal, and oil analysis."
        )
    },

    # ---------- DATA & CONTROL ----------
    {
        "input": "Why are sensor readings inconsistent?",
        "context": (
            "Inconsistent readings may stem from calibration drift, EMI interference, "
            "or loose signal wiring."
        ),
        "output": (
            "Sensor inconsistency is caused by calibration drift or interference."
        )
    },
    {
        "input": "How do you validate SCADA data accuracy?",
        "context": (
            "SCADA data is validated by cross-checking with field instruments, "
            "manual readings, and redundancy logic."
        ),
        "output": (
            "Accuracy is validated through cross-checks and redundancy."
        )
    },

    # ---------- NETWORK & IT ----------
    {
        "input": "Why is industrial Ethernet communication dropping packets?",
        "context": (
            "Packet loss may result from EMI, incorrect switch configuration, "
            "or overloaded control networks."
        ),
        "output": (
            "Packet drops are caused by EMI or overloaded networks."
        )
    },
    {
        "input": "How do you secure PLC networks?",
        "context": (
            "PLC networks are secured using segmentation, firewalls, "
            "role-based access, and firmware updates."
        ),
        "output": (
            "Security is achieved through segmentation and access control."
        )
    }
]

BAD_ANSWERS = [
    "This issue is caused by gravitational anomalies in the facility.",
    "The machine stopped because it was tired after long usage.",
    "Cosmic radiation interfered with the control system.",
    "The reactor overheated due to internet connectivity issues.",
    "A software bug in the login system caused the pressure spike."
]

ALL_CONTEXTS = [d["context"] for d in DATA]

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
def make_trace(trace_no, session_id, user_id, trace_name, input_text, context_text, output_text):

    tokens_in = random.randint(200, 3500)
    tokens_out = random.randint(50, 1500)

    trace_id = f"trace-{str(trace_no).zfill(4)}"

    return {
        "id": trace_id,
        "partitionKey": trace_id,      # 🔥 PK = trace_id
        "trace_id": trace_id,

        "session_id": session_id,
        "user_id": user_id,
        "trace_name": trace_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),

        "input": input_text,
        "output": output_text,

        "latency_ms": random.randint(200, 8000),
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "tokens": tokens_in + tokens_out,
        "cost": round((tokens_in + tokens_out) * random.uniform(0.00008, 0.00025), 5),

        "model": random.choice(["gpt-4o", "gpt-4o-mini", "llama-3.3-70b"]),
    }

# ============================================================
# TIMER FUNCTION
# ============================================================
def main(mytimer):

    cosmos = CosmosClient.from_connection_string(
        os.environ["COSMOS_CONN_WRITE"]
    )
    db = cosmos.get_database_client("llmops-data")

    traces_container = db.get_container_client("traces")
    counter_container = db.get_container_client("metrics")

    # 🔥 HIGH VOLUME GENERATION
    for _ in range(random.randint(2, 5)):
        base = random.choice(DATA)

        input_text = base["input"]
        context_text = base["context"]
        output_text = base["output"]

        r = random.random()
        if GOOD_RATIO <= r < GOOD_RATIO + BAD_CONTEXT_RATIO:
            context_text = random.choice([c for c in ALL_CONTEXTS if c != context_text])
        elif r >= GOOD_RATIO + BAD_CONTEXT_RATIO:
            output_text = random.choice(BAD_ANSWERS)

        trace_no = get_next_trace_number(counter_container)

        trace = make_trace(
            trace_no=trace_no,
            session_id=f"session-{random.randint(1, 200)}",
            user_id=random.choice(USERS),
            trace_name=random.choice(TRACE_NAMES),
            input_text=input_text,
            context_text=context_text,
            output_text=output_text
        )

        # ✅ MUST use create_item for Cosmos trigger
        traces_container.create_item(trace)
