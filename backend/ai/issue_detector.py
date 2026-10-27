"""Issue Notification (IN) and Unknown Scenario Detection Engine for DrillIntel.

Analyzes operational drilling telemetry against historical RAG signatures,
offset well trajectory bounds, and heuristic physical baselines to detect:
1. Operational parameter anomalies (hydraulic imbalance, torque/WOB divergence).
2. Unknown / Out-of-Distribution scenarios (low historical RAG similarity, uncharted depths).
3. Missing sensor evidence and telemetry gaps.
4. Epistemic uncertainty and human review requirements.

Decision support only. Unvalidated thresholds are not confirmed safety limits.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple


def _safe_float(val: Any) -> Optional[float]:
    """Safely cast value to float, ignoring None, NaN, and invalid strings."""
    if val is None or val == "":
        return None
    try:
        f = float(val)
        import math
        return None if math.isnan(f) or math.isinf(f) else f
    except (ValueError, TypeError):
        return None


def evaluate_telemetry_anomalies(condition: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Inspect current telemetry channels for explainable physical discrepancies.
    
    Checks:
    - Delta flow balance (flow_in vs flow_out) indicating potential loss or influx.
    - Pump pressure vs circulating flow (standpipe pressure disconnect).
    - Torque dynamics and WOB anomalies.
    """
    anomalies: List[Dict[str, Any]] = []

    depth = _safe_float(condition.get("depth"))
    wob = _safe_float(condition.get("wob"))
    torque = _safe_float(condition.get("torque"))
    flow_in = _safe_float(condition.get("flow_in"))
    flow_out = _safe_float(condition.get("flow_out"))
    pump = _safe_float(condition.get("pump"))

    # 1. Delta Flow Discrepancy (Circulating loss vs kick influx)
    if flow_in is not None and flow_out is not None:
        if flow_in > 0.005:
            # Significant loss: flow out drops drastically below flow in while pump is active
            if flow_out < 0.20 * flow_in:
                anomalies.append({
                    "parameter": "FLOW_BALANCE",
                    "channel": "FLOWOUT vs FLOWIN",
                    "current_value": f"In: {flow_in:.4f} m³/s, Out: {flow_out:.4f} m³/s",
                    "baseline": "Steady-state circulating balance (Flow Out ≈ Flow In)",
                    "deviation": f"Severe deficit ({((flow_in - flow_out)/flow_in)*100:.1f}% loss of returned flow)",
                    "severity": "HIGH",
                    "status": "ANOMALOUS",
                    "reason": "Returned annular flow is severely lower than pumped flow rate, indicating possible downhole mud loss or sensor error."
                })
            # Potential influx / kick: flow out exceeds pumped flow significantly
            elif flow_out > 1.35 * flow_in:
                anomalies.append({
                    "parameter": "FLOW_BALANCE",
                    "channel": "FLOWOUT vs FLOWIN",
                    "current_value": f"In: {flow_in:.4f} m³/s, Out: {flow_out:.4f} m³/s",
                    "baseline": "Steady-state circulating balance",
                    "deviation": f"Excess returned flow ({((flow_out - flow_in)/flow_in)*100:.1f}% gain)",
                    "severity": "CRITICAL",
                    "status": "ANOMALOUS",
                    "reason": "Returned flow exceeds pumped flow, signaling potential formation fluid influx (kick risk)."
                })
        elif flow_out > 0.005 and flow_in <= 0.001 and pump is not None and pump < 20000:
            # Flowing well with pumps off
            anomalies.append({
                "parameter": "ANNULAR_FLOW_WITH_PUMPS_OFF",
                "channel": "FLOWOUT",
                "current_value": f"{flow_out:.4f} m³/s",
                "baseline": "0.0 m³/s when mud pumps are idle",
                "deviation": "Active flow detected while pumps idle",
                "severity": "CRITICAL",
                "status": "ANOMALOUS",
                "reason": "Positive return flow detected while pumps are disengaged; requires immediate flow check."
            })

    # 2. Standpipe Pressure vs Flow Disconnect
    if pump is not None and flow_in is not None:
        # High pressure with low flow
        if pump > 200000.0 and flow_in < 0.002:
            anomalies.append({
                "parameter": "HYDRAULIC_DISCONNECT",
                "channel": "PUMP vs FLOWIN",
                "current_value": f"Pump: {pump:,.0f} Pa, Flow In: {flow_in:.4f} m³/s",
                "baseline": "Hydraulic curve correlation (pressure builds proportionally with pumped flow)",
                "deviation": "High standpipe pressure without nominal surface flow rate",
                "severity": "HIGH",
                "status": "ANOMALOUS",
                "reason": "High manifold pressure with near-zero flow rate suggests possible nozzle blockage or annular pack-off."
            })

    # 3. Torque / Mechanical Resistance
    if torque is not None:
        if torque > 30.0:
            anomalies.append({
                "parameter": "MECHANICAL_TORQUE",
                "channel": "TORQUE",
                "current_value": f"{torque:.2f} kN·m",
                "baseline": "Nominal drilling range (< 20.0 kN·m)",
                "deviation": f"Elevated mechanical torque (+{torque - 20.0:.1f} kN·m above nominal)",
                "severity": "MEDIUM",
                "status": "ELEVATED",
                "reason": "High rotary torque indicates aggressive formation contact, tight hole, or severe bit-rock interaction."
            })

    return anomalies


def evaluate_historical_novelty(
    historical_events: List[Dict[str, Any]],
    condition: Dict[str, Any],
    similarity_threshold: float = 0.50
) -> Dict[str, Any]:
    """Compare current scenario with historical RAG retrieval matches.
    
    A scenario is classified as 'unknown' or 'novel' if:
    1. No historical events exist in the knowledge index for the operating condition.
    2. The highest similarity score is strictly below the similarity threshold (< 0.50).
    """
    if not historical_events:
        return {
            "has_precedent": False,
            "precedent_count": 0,
            "top_similarity_score": 0.0,
            "closest_event_type": "None",
            "closest_event_well": "None",
            "novelty_score": 1.0,
            "is_novel": True,
            "assessment": "No historical drilling event records matched the active operational query."
        }

    scores = [_safe_float(e.get("similarity_score")) or 0.0 for e in historical_events]
    top_score = max(scores) if scores else 0.0
    top_event = historical_events[0] if historical_events else {}

    top_type = top_event.get("event_type") or "unknown"
    top_well = top_event.get("well_id") or "unknown"
    top_depth = top_event.get("depth") or top_event.get("event_md") or "unknown"

    # Novelty score: 1.0 = entirely novel, 0.0 = exact match
    novelty_score = round(max(0.0, min(1.0, 1.0 - top_score)), 3)
    is_novel = top_score < similarity_threshold

    if is_novel:
        assessment = (
            f"Low historical similarity (top vector score: {top_score:.3f} < {similarity_threshold:.2f}). "
            f"The nearest logged event was '{top_type}' in {top_well} at {top_depth} m, "
            f"but correlation is weak, indicating an uncharacterized operational state."
        )
    else:
        assessment = (
            f"Known operational precedent identified (top vector similarity: {top_score:.3f}). "
            f"Nearest match is '{top_type}' in well {top_well} at depth {top_depth} m."
        )

    return {
        "has_precedent": not is_novel,
        "precedent_count": len(historical_events),
        "top_similarity_score": round(top_score, 4),
        "closest_event_type": top_type,
        "closest_event_well": top_well,
        "closest_event_depth": top_depth,
        "novelty_score": novelty_score,
        "is_novel": is_novel,
        "assessment": assessment,
    }


def evaluate_offset_coverage(
    offset_wells: List[Dict[str, Any]],
    target_depth: Optional[float]
) -> Dict[str, Any]:
    """Check whether offset reference wells provide spatial and depth coverage."""
    if not offset_wells:
        return {
            "depth_covered": False,
            "max_offset_depth": 0.0,
            "target_depth": target_depth or 0.0,
            "depth_margin": 0.0,
            "top_offset_similarity": 0.0,
            "assessment": "No offset well trajectory reference records are available."
        }

    max_offset_md = max(
        [_safe_float(w.get("offset_max_md")) or 0.0 for w in offset_wells] or [0.0]
    )
    sim_scores = [
        _safe_float(w.get("similarity_score")) or 0.0 for w in offset_wells
    ]
    top_sim = max(sim_scores) if sim_scores else 0.0

    target_d = target_depth or 0.0
    depth_margin = target_d - max_offset_md

    # If target depth exceeds all offset depths by > 50m, it is in deeper frontier
    if depth_margin > 50.0:
        depth_covered = False
        assessment = (
            f"Current depth ({target_d:.1f} m) exceeds maximum offset reference well depth "
            f"({max_offset_md:.1f} m) by {depth_margin:.1f} m. Operating in an unlogged vertical section."
        )
    else:
        depth_covered = True
        assessment = (
            f"Current depth ({target_d:.1f} m) is bounded within reference offset logging interval "
            f"(max offset depth: {max_offset_md:.1f} m, best trajectory match: {top_sim:.1%})."
        )

    return {
        "depth_covered": depth_covered,
        "max_offset_depth": round(max_offset_md, 1),
        "target_depth": round(target_d, 1),
        "depth_margin": round(depth_margin, 1),
        "top_offset_similarity": round(top_sim, 4),
        "assessment": assessment
    }


def detect_issue_notification(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Synthesizes all drilling evidence to construct the Issue Notification object.
    
    Evaluates:
    - Physical parameter discrepancies.
    - Historical RAG similarity / novelty.
    - Offset spatial depth coverage.
    - Missing sensor channels.
    - Severity and epistemic uncertainty.
    """
    condition = analysis.get("current_condition") or {}
    risk = analysis.get("risk") or {}
    offset_wells = analysis.get("offset_wells") or []
    historical_events = analysis.get("historical_events") or []
    target_well = analysis.get("target_well") or "Unknown Well"

    target_depth = _safe_float(condition.get("depth"))
    risk_level = str(risk.get("level", "LOW")).upper()
    risk_prob = _safe_float(risk.get("probability")) or 0.0

    # 1. Telemetry anomalies
    anomalies = evaluate_telemetry_anomalies(condition)

    # 2. Historical novelty
    novelty = evaluate_historical_novelty(historical_events, condition, similarity_threshold=0.50)

    # 3. Offset depth coverage
    coverage = evaluate_offset_coverage(offset_wells, target_depth)

    # 4. Check for missing critical sensor channels
    required_channels = ["depth", "wob", "torque", "flow_in", "flow_out", "pump"]
    missing_channels = [
        ch for ch in required_channels if _safe_float(condition.get(ch)) is None
    ]

    # Additional mud / formation logging check
    missing_evidence: List[str] = []
    if missing_channels:
        missing_evidence.append(f"Primary telemetry channels unrecorded or null: {', '.join(missing_channels)}")
    if not offset_wells:
        missing_evidence.append("No offset trajectory similarity data available for spatial comparison")
    if not historical_events:
        missing_evidence.append("No historical incident logs matched the search query in vector index")

    # 5. Determine Unknown Scenario Flag
    # A scenario is unknown if:
    # a) Novelty is high (historical RAG similarity < 0.50 or empty), OR
    # b) Operating at uncharted depth interval beyond all offset wells, OR
    # c) Parameter anomalies exist with no precedent.
    is_unknown_scenario = bool(
        novelty["is_novel"] or (not coverage["depth_covered"] and (coverage.get("depth_margin") or 0) > 50)
    )

    # 6. Determine Severity & Flagging Status
    explainable_reasons: List[str] = []
    has_critical_anomaly = any(a["severity"] == "CRITICAL" for a in anomalies)
    has_high_anomaly = any(a["severity"] == "HIGH" for a in anomalies)

    for anom in anomalies:
        explainable_reasons.append(f"[{anom['parameter']}] {anom['reason']}")

    if is_unknown_scenario:
        if novelty["is_novel"]:
            explainable_reasons.append(
                f"Historical RAG similarity is low (score {novelty['top_similarity_score']:.3f} < 0.50), "
                "indicating the current operational conditions are under-represented in past well incident records."
            )
        if not coverage["depth_covered"]:
            depth_desc = f"{target_depth:.1f} m" if target_depth is not None else "depth unrecorded"
            explainable_reasons.append(
                f"Target depth ({depth_desc}) exceeds maximum reference offset well depth "
                f"({coverage['max_offset_depth']:.1f} m). No direct offset logging available at this horizon."
            )

    # Epistemic Uncertainty
    if is_unknown_scenario or len(missing_channels) >= 2 or not historical_events:
        uncertainty = "HIGH"
    elif len(anomalies) > 0 or risk_level in {"MEDIUM", "HIGH"}:
        uncertainty = "MEDIUM"
    else:
        uncertainty = "LOW"

    # Severity Synthesis
    if has_critical_anomaly or (is_unknown_scenario and risk_level == "HIGH"):
        severity = "CRITICAL"
        flagged = True
        status = "CRITICAL_ISSUE_NOTIFICATION"
        title = "CRITICAL ISSUE NOTIFICATION: Immediate Parameter Discrepancy"
    elif has_high_anomaly or (is_unknown_scenario and len(anomalies) > 0) or (risk_level == "HIGH"):
        severity = "HIGH"
        flagged = True
        status = "HIGH_ISSUE_NOTIFICATION"
        title = "IN-FLAG: Anomalous Drilling Signatures & Low Historical Precedent"
    elif is_unknown_scenario:
        severity = "MEDIUM"
        flagged = True
        status = "UNKNOWN_SCENARIO_DETECTED"
        title = "UNKNOWN SCENARIO: Novel Drilling State with Under-Represented Precedent"
    elif len(anomalies) > 0:
        severity = "MEDIUM"
        flagged = True
        status = "ANOMALY_NOTIFIED"
        title = "IN-FLAG: Operational Parameter Divergence"
    elif missing_channels:
        severity = "INFO"
        flagged = True
        status = "INCOMPLETE_TELEMETRY"
        title = "IN-FLAG: Missing Sensor Evidence"
    else:
        severity = "LOW"
        flagged = False
        status = "NORMAL_MONITORING"
        title = "IN-FLAG: Nominal Operations"

    # Executive Summary
    if flagged:
        if is_unknown_scenario and anomalies:
            summary = (
                f"Potential drilling issue flagged for {target_well} (Severity: {severity}). "
                f"Detected {len(anomalies)} parameter anomal{'y' if len(anomalies)==1 else 'ies'} "
                "operating in an uncharacterized operational scenario with low historical precedent."
            )
        elif is_unknown_scenario:
            summary = (
                f"Unknown / novel scenario detected for {target_well} (Severity: {severity}). "
                "Current operations exhibit low correlation with historical offset event signatures. "
                "Heightened vigilance and human verification required."
            )
        else:
            summary = (
                f"Operational issue notification flagged for {target_well} (Severity: {severity}). "
                f"Detected {len(anomalies)} parameter discrepancies requiring inspection."
            )
    else:
        summary = (
            f"Nominal monitoring state for {target_well}. Operational measurements correlate with "
            "established historical parameters and remain within standard bounds."
        )

    # Uncertainty Warnings (Never treat unvalidated heuristic limits as absolute structural safety bounds)
    uncertainty_warnings = [
        "Uncertainty flag: Detection relies on heuristic empirical correlations and offset trajectory projections.",
        "Model scores and anomaly flags are decision-support indicators, not calibrated mechanical safety bounds.",
        "Human review protocol: Certified drilling engineer sign-off is mandatory before initiating corrective actions."
    ]
    if is_unknown_scenario:
        uncertainty_warnings.insert(
            0,
            "Novel Scenario Warning: The machine learning model and RAG database have limited historical representation for this operational state."
        )

    # Recommended Actions
    recommended_actions: List[str] = []
    if has_critical_anomaly:
        recommended_actions.append("Perform immediate flow check and verify pit volume totalizers (PVT).")
        recommended_actions.append("Disengage rotary table / top drive and evaluate standpipe pressure trend.")
    elif is_unknown_scenario and anomalies:
        recommended_actions.append("Verify mud return sensors and inspect cuttings returns at shaker screens.")
        recommended_actions.append("Cross-reference drillstring hydraulic model with real-time pressure data.")
    elif is_unknown_scenario:
        recommended_actions.append("Review nearest offset formation tops and mud weight schedules for upcoming interval.")
        recommended_actions.append("Maintain enhanced real-time telemetry monitoring for unexpected formation transitions.")
    else:
        recommended_actions.append("Continue regular parameter monitoring and trend tracking against offset baseline.")

    return {
        "flagged": flagged,
        "status": status,
        "severity": severity,
        "is_unknown_scenario": is_unknown_scenario,
        "confidence": round(0.90 if len(missing_channels) == 0 else max(0.40, 0.90 - len(missing_channels) * 0.12), 2),
        "uncertainty": uncertainty,
        "novelty_score": novelty["novelty_score"],
        "title": title,
        "summary": summary,
        "triggering_measurements": anomalies,
        "explainable_reasons": explainable_reasons,
        "historical_evidence_comparison": novelty,
        "offset_coverage": coverage,
        "missing_evidence": missing_evidence,
        "uncertainty_warnings": uncertainty_warnings,
        "human_review_required": True,
        "human_review_status": "PENDING_SIGN_OFF",
        "recommended_actions": recommended_actions,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
