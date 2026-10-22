# Define Pydantic Schemas

from pydantic import BaseModel
from typing import List, Optional


class AnalysisRequest(BaseModel):
    query: str


class Event(BaseModel):
    id: str
    type: str
    start_time: str
    end_time: str
    depth_m: Optional[float]
    severity: Optional[str]
    source: List[str]
    confidence: float
    notes: Optional[str]


class AnalysisResponse(BaseModel):
    report_id: str
    events: List[Event]


class DebugInfo(BaseModel):
    rag_chunks: List[dict]
    prompt: str
    raw_response: str


class AnalysisResponse(BaseModel):
    report_id: str
    events: List[Event]
    debug: Optional[DebugInfo] = None
