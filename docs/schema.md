/trace
        trace_id STRING            -- unique trace identifier
        session_id STRING          -- conversation/session grouping
        timestamp TIMESTAMP        -- when the response was generated

        question STRING            -- user query
        context STRING             -- retrieved context (RAG output)
        answer STRING              -- assistant response

        latency_ms INT             -- response latency
        tokens_in INT              -- input token count
        tokens_out INT             -- output token count

        prompt_version STRING      -- prompt version used
        model STRING               -- model name (e.g., gpt-4o-mini)


/sessions
        session_id STRING
        created_at TIMESTAMP
        updated_at TIMESTAMP
        trace_count INT
        total_tokens INT
        total_cost DOUBLE

        
/evaluations
        eval_id STRING             -- unique evaluation id
        trace_id STRING            -- FK to traces.trace_id

        evaluator_name STRING      -- hallucination | relevance | conciseness | correctness
        score DOUBLE               -- value between 0 and 1
        explanation STRING         -- optional evaluator explanation

        timestamp TIMESTAMP        -- evaluation time


/evaluator_version
        evaluator_name STRING      -- hallucination, relevance, etc.
        version STRING             -- evaluator version (v1, v2)
        template STRING            -- evaluator prompt template

        threshold DOUBLE           -- alert threshold
        baseline DOUBLE            -- rolling baseline (7d / 30d)
        active BOOLEAN             -- whether evaluator is active

        created_at TIMESTAMP

/prompt_version
        prompt_name STRING
        version STRING
        template STRING
        variables ARRAY<STRING>

        environment STRING         -- dev | prod
        created_by STRING
        created_at TIMESTAMP

/datasets
        dataset_id STRING
        name STRING

        input STRING               -- question/input
        expected_output STRING     -- ground truth answer

        verification_status STRING -- verified | unverified
        created_at TIMESTAMP

/dataset_eval_results
        dataset_id STRING
        evaluation_run_id STRING

        pass_rate DOUBLE
        avg_score DOUBLE
        avg_latency DOUBLE
        total_cost DOUBLE

        evaluated_at TIMESTAMP

/annotations
        annotation_id STRING
        trace_id STRING

        status STRING              -- pending | reviewed | resolved
        issue_category STRING      -- hallucination | incorrect | unsafe | irrelevant

        created_at TIMESTAMP
        reviewed_at TIMESTAMP

/alerts
        alert_id STRING
        trace_id STRING            -- nullable for drift alerts

        type STRING                -- hallucination | drift | latency | safety
        severity STRING            -- low | medium | high | critical
        metric STRING              -- hallucination_score, relevance_score, etc.
        value DOUBLE               -- score or drift %

        timestamp TIMESTAMP
        rca_summary STRING         -- AI-generated RCA explanation

/audit_logs
        audit_id STRING
        timestamp TIMESTAMP

        actor STRING               -- user | system | admin
        action STRING              -- create | update | delete
        object_type STRING         -- setting | prompt | evaluator | alert
        object_id STRING

        details STRING

/settings
        category STRING            -- retrieval | embedding | generation | guardrails | project
        key STRING                 -- setting name
        value STRING               -- setting value (stored as string)
        updated_at TIMESTAMP

/feedback
        feedback_id STRING
        trace_id STRING

        rating STRING              -- thumbs_up | thumbs_down
        comment STRING             -- free-text feedback

        timestamp TIMESTAMP

/feedback_kpi_daily
        date DATE

        total_feedback INT
        positive_feedback INT
        negative_feedback INT

        top_issue_category STRING

