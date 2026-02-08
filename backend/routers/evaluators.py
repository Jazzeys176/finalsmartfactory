from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import uuid
from utils.cosmos import evaluators_container

router = APIRouter()

# -----------------------------
# Request Model (updated)
# -----------------------------
class EvaluatorCreate(BaseModel):
    score_name: str
    template: dict            # frontend sends: { id, model, prompt_version }
    status: str
    target: str
    variable_mapping: dict
    execution: dict           # frontend: { sampling_rate, delay_ms }

# -----------------------------
# GET: List evaluators
# -----------------------------
@router.get("")
def get_evaluators():
    try:
        evaluators = list(
            evaluators_container.query_items(
                query="""
                SELECT *
                FROM c
                ORDER BY c.created_at DESC
                """,
                enable_cross_partition_query=True,
            )
        )
        return evaluators

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# -----------------------------
# POST: Create evaluator
# -----------------------------
@router.post("")
def create_evaluator(payload: EvaluatorCreate):
    try:
        evaluator_id = str(uuid.uuid4())

        item = {
            "id": evaluator_id,
            "score_name": payload.score_name,
            "template": payload.template,
            "status": payload.status,
            "target": payload.target,
            "variable_mapping": payload.variable_mapping,
            "execution": payload.execution,
            "created_at": None
        }

        evaluators_container.create_item(
            body=item,
            partition_key=item["status"]  # PK is status
        )

        return {
            "message": "Evaluator created successfully",
            "id": evaluator_id,
            "data": item
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
