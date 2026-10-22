# DrillIntel Agentic MVP integration

1. Copy `backend/agents/` into the existing repository's `backend/` directory.

2. Add this import to `backend/main.py`:
```python
from backend.agents.orchestrator import build_agentic_trace
```

3. Add this route after the existing `/analyze` route:
```python
@app.post("/agentic-analyze")
def agentic_analyze(request: AnalyzeRequest):
    # Reuses the existing analysis function and tools; does not duplicate model/RAG logic.
    analysis = analyze_well(request)
    analysis["agentic"] = build_agentic_trace(analysis)
    return analysis
```

4. Copy `frontend/AgenticPanel.jsx` and `frontend/agentic-panel.css` into `src/`.

5. In `src/App.jsx`, add:
```jsx
import AgenticPanel from "./AgenticPanel";
```
Change the request URL from `${API_URL}/analyze` to `${API_URL}/agentic-analyze`.
Render `<AgenticPanel agentic={analysis?.agentic} />` near the top of the dashboard, ideally above Well intelligence.

6. Restart FastAPI and Vite. Verify `POST /agentic-analyze` in `http://127.0.0.1:8000/docs`.

Important: this is a traceable orchestration MVP, not yet an LLM-powered autonomous multi-agent system. The trace is returned after analysis completes; live streaming requires SSE/WebSocket later.

Risk model correctness: the current predictor hardcodes `predict_proba(X)[0][1]`. Verify that classifier class index 1 is the positive risk label in your dataset before relying on this score. Also validate data paths and labels before adding model caching.
