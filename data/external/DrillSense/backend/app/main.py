# app/main.py
import os
import json
import logging
from typing import List

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .rag_retriever import query_rag
from .schemas import AnalysisRequest, AnalysisResponse

from vertexai import init as vertex_init
from vertexai.preview.generative_models import GenerativeModel, Part

PROJECT = os.getenv("GCP_PROJECT", "drillsense-469316")
REGION = os.getenv("VERTEX_REGION", "us-central1")
MODEL_NAME = os.getenv(
    "VERTEX_MODEL_NAME",
    "projects/310665873798/locations/us-central1/endpoints/3458134493657825280",
)

# init VertexAI SDK
vertex_init(project=PROJECT, location=REGION)

app = FastAPI(title="Drilling AI Analysis API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

logger = logging.getLogger("drillsense")
logging.basicConfig(level=logging.INFO)


@app.get("/")
def root():
    return {"status": "ok", "service": "DrillSense Backend"}


def build_rag_prompt(query: str, chunks: List[dict]) -> str:
    context_blocks = []
    for i, c in enumerate(chunks, 1):
        meta = c.get("metadata") or {}
        title = meta.get("title") or meta.get("doc_id") or f"chunk_{i}"
        text = c.get("content", "")[:3000]
        context_blocks.append(f"[{i}] {title}\n{text}")

    context_text = "\n\n".join(context_blocks)
    return f"""
You are a drilling reports domain assistant (Volve/PVT/DDR). Use ONLY the CONTEXT blocks below to answer the query.
If the answer cannot be found in the context, reply with a JSON: {{ "report_id": null, "events": [] }}.

CONTEXT:
{context_text}

QUESTION:
{query}

REPLY (STRICT JSON only): Provide JSON object exactly matching:
{{ "report_id": "<string>", "events": [ {{ "id": "<str>", "type": "<str>", "start_time": "<iso>", "end_time": "<iso>", "depth_m": <number|null>, "severity": "<str|null>", "source": ["doc_id:chunk"], "confidence": <0.0-1.0>, "notes": "<text>" }} ] }}
""".strip()


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze(req: AnalysisRequest):
    try:
        chunks = query_rag(req.query, top_k=8)
        if not chunks:
            raise HTTPException(status_code=404, detail="No context available")

        prompt = build_rag_prompt(req.query, chunks[:5])
        model = GenerativeModel(model_name=MODEL_NAME)

        response = model.generate_content(
            [Part.from_text(prompt)],
            generation_config={
                "temperature": 0.0,
                "top_p": 0.95,
                "max_output_tokens": 1200,
            },
        )

        text = response.text or ""
        try:
            parsed = json.loads(text)
        except Exception:
            import re

            m = re.search(r"(\{.*\})", text, flags=re.S)
            parsed = json.loads(m.group(1)) if m else {"report_id": None, "events": []}

        events = parsed.get("events", [])
        for e in events:
            e.setdefault("id", e.get("id") or "evt")
            e.setdefault("confidence", float(e.get("confidence") or 0.0))
            e.setdefault("source", e.get("source") or [])

        return {
            "report_id": parsed.get("report_id"),
            "events": events,
            "debug": {
                "rag_chunks": chunks,
                "prompt": prompt,
                "raw_response": text,
            },
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Analyze failed")
        raise HTTPException(status_code=500, detail=str(exc))
