# Dashboard Metrics Temporary Workaround

We have implemented a temporary workaround to provide live, accurate aggregated metrics (and a Daily Active Users chart) on the Dashboard, **without** modifying the Azure Function `Aggregator` script.

## Changes Made

1. **Backend ([backend/routers/metrics.py](file:///home/sigmoid/Desktop/Final_SmartAILLMOps/backend/routers/metrics.py))**: 
   - A new `@router.get("/live_metrics")` endpoint was added. 
   - This endpoint queries the Cosmos DB `traces` and `evaluations` containers directly to correctly parse the nested JSON log structures (`latency_ms`, `total_tokens`, `total_cost_usd`, model usage, etc.) and calculate daily active users dynamically without waiting for the azure function.

2. **Frontend ([frontend/src/pages/Dashboard.tsx](file:///home/sigmoid/Desktop/Final_SmartAILLMOps/frontend/src/pages/Dashboard.tsx))**:
   - The data fetch block was updated to call the new `/live_metrics` endpoint.
   - The old fetching code (`api.get("/dashboard/metrics")`) was left in the codebase and **commented out**.
   - A Recharts `LineChart` was added to map the `metrics.daily_active_users` array.

## How to Restore Default Functionality

Once you receive manager approval to fix the Azure Function ([Aggregator/__init__.py](file:///home/sigmoid/Desktop/Final_SmartAILLMOps/azure-functions/Aggregator/__init__.py)), follow these steps to restore the system to its intended architectural flow:

1. **Update the Azure Function ([azure-functions/Aggregator/__init__.py](file:///home/sigmoid/Desktop/Final_SmartAILLMOps/azure-functions/Aggregator/__init__.py))**:
   - Implement the nested key parsing fixes here so it accurately aggregates the raw trace inputs and uploads them to the [metrics](file:///home/sigmoid/Desktop/Final_SmartAILLMOps/backend/routers/metrics.py#39-55) Cosmos container.
   - Specifically, ensure values are derived from `performance.latency_ms`, `usage.total_tokens`, `cost.total_cost_usd`, `model_info.model`, and that `session.user_id` is extracted for DAU calculations.

2. **Uncomment the Default Frontend API Call ([frontend/src/pages/Dashboard.tsx](file:///home/sigmoid/Desktop/Final_SmartAILLMOps/frontend/src/pages/Dashboard.tsx))**:
   Locate the `useEffect` block fetching the metrics (around line 48):
   ```tsx
     useEffect(() => {
       // TEMPORARY WORKAROUND: Bypassing the frozen metrics document.
       // Uncomment this line to restore default Azure Functions aggregation:
       // api.get("/dashboard/metrics")
       api
         .get("/dashboard/live_metrics")
         .then((res) => setMetrics(res.data))
         .catch(() => setMetrics(null))
         .finally(() => setLoading(false));
     }, []);
   ```
   **Change it back to:**
   ```tsx
     useEffect(() => {
       api
         .get("/dashboard/metrics")
         .then((res) => setMetrics(res.data))
         .catch(() => setMetrics(null))
         .finally(() => setLoading(false));
     }, []);
   ```

3. **Cleanup Backend ([backend/routers/metrics.py](file:///home/sigmoid/Desktop/Final_SmartAILLMOps/backend/routers/metrics.py))**:
   - You may safely delete the `@router.get("/live_metrics")` endpoint to keep the codebase clean.

The dashboard will now correctly reflect data parsed and pushed periodically by the Azure Functions aggregator.
