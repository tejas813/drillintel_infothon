from datetime import datetime, timezone

def _stage(agent, title, status, summary, evidence=None):
    return {"agent":agent,"title":title,"status":status,"summary":summary,
            "evidence":evidence or [],"timestamp":datetime.now(timezone.utc).isoformat()}

def build_agentic_trace(analysis: dict) -> dict:
    """Build a trace from actual NWIS outputs; never invent tool success."""
    risk=analysis.get("risk") or {}
    condition=analysis.get("current_condition") or {}
    offsets=analysis.get("offset_wells") or []
    history=analysis.get("historical_events") or []
    recs=analysis.get("recommendations") or []
    missing=[k for k in ("depth","wob","torque","flow_in","flow_out","pump") if condition.get(k) is None]
    stages=[_stage("orchestrator","Plan analysis","complete",
        "Created a bounded plan using existing NWIS analysis tools.",
        ["Risk model","Offset trajectory ranking","Historical RAG search","Recommendation engine"])]
    valid=risk.get("probability") is not None and risk.get("level") in {"LOW","MEDIUM","HIGH"}
    stages.append(_stage("risk_analyst","Assess drilling risk","complete" if valid else "failed",
        "Risk model returned a score and level." if valid else "Risk result missing or invalid; this is not evidence of LOW risk.",
        [f"Risk level: {risk.get('level','unavailable')}",f"Model score: {risk.get('probability','unavailable')}%"]))
    stages.append(_stage("data_quality","Check input completeness","warning" if missing else "complete",
        ("Missing condition fields: "+", ".join(missing)) if missing else "Expected summary condition fields are present.",
        [f"{k}: {condition.get(k,'unavailable')}" for k in ("depth","wob","torque","flow_in","flow_out","pump")]))
    stages.append(_stage("offset_intelligence","Compare offset wells","complete" if offsets else "warning",
        f"Retrieved {len(offsets)} offset comparison(s)." if offsets else "No offset matches returned; comparison evidence unavailable.",
        [f"{x.get('well_id')}: similarity {x.get('similarity_score')}; depth difference {x.get('depth_difference')} m" for x in offsets[:5]]))
    stages.append(_stage("historical_evidence","Retrieve historical events","complete" if history else "warning",
        f"Retrieved {len(history)} historical event match(es)." if history else "No historical matches returned; event-specific conclusions are unsupported.",
        [f"{x.get('event_type')} at {x.get('well_id')} depth {x.get('depth')} m; match {x.get('similarity_score')}" for x in history[:5]]))
    issues=[]
    if not valid: issues.append("Risk assessment unavailable or invalid.")
    if missing: issues.append("Some input summary fields are missing.")
    if not offsets: issues.append("No offset comparison evidence.")
    if not history: issues.append("No historical evidence retrieved.")
    if not recs: issues.append("No recommendations returned.")
    stages.append(_stage("critic_verifier","Verify evidence and limitations","warning" if issues else "complete",
        "Limitations flagged for human review." if issues else "Required outputs are present; this does not certify operational safety.",
        issues or ["Risk, offset, history, and recommendation outputs are present."]))
    stages.append(_stage("decision_brief","Prepare decision brief","complete" if recs else "warning",
        "Compiled backend recommendations for engineering review." if recs else "No recommendations available; specialist review needed.",
        [str(x) for x in recs[:6]]))
    return {"workflow":"DrillIntel bounded multi-agent orchestration","mode":"tool-orchestrated MVP",
        "human_review_required":True,
        "overall_status":"warning" if any(s["status"] in {"warning","failed"} for s in stages) else "complete",
        "agents":stages,"limitations":[
        "This MVP orchestrates existing deterministic/model/RAG tools; roles are not independent LLM agents yet.",
        "The risk score is a model output, not a calibrated incident probability unless validated.",
        "Decision support only; not an automated drilling control system."]}
