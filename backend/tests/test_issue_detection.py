"""Unit and integration test suite for Issue Notification (IN) and Unknown Scenario Detection.

Covers:
- Unknown scenario detection (low RAG similarity, empty historical records, uncharted depth).
- Telemetry anomaly detection (flow deficit/loss, flow influx/kick, hydraulic disconnect).
- Missing evidence and telemetry gaps handling.
- Null and NaN resilience.
- Ollama timeout and connection failure resilience.
- API compatibility for /analyze and /agentic-analyze endpoints.
"""

import math
import os
import sys
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
import urllib.error

# Ensure backend is on sys.path
BASE_DIR = Path(__file__).resolve().parents[2]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR / "backend") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "backend"))

from backend.ai.issue_detector import (
    detect_issue_notification,
    evaluate_historical_novelty,
    evaluate_offset_coverage,
    evaluate_telemetry_anomalies,
)
from backend.agents.agent_runtime import (
    _llm_synthesis,
    _unknown_scenario_review,
    run_agentic_workflow,
)


class TestIssueNotificationAndUnknownScenario(unittest.TestCase):

    def test_unknown_scenario_low_rag_similarity(self):
        """Low historical RAG similarity (< 0.50) must flag an Unknown Scenario."""
        analysis = {
            "target_well": "Well-Test-Novelty",
            "current_condition": {
                "depth": 2100.0,
                "wob": 15000.0,
                "torque": 12.0,
                "flow_in": 0.035,
                "flow_out": 0.035,
                "pump": 120000.0,
            },
            "risk": {"level": "LOW", "probability": 1.5},
            "offset_wells": [
                {"offset_well": "Offset-A", "offset_max_md": 2500.0, "similarity_score": 0.85}
            ],
            "historical_events": [
                {
                    "similarity_score": 0.38,
                    "event_type": "tight_hole",
                    "well_id": "Past-Well-X",
                    "event_md": 2050.0,
                    "description": "Minor tight hole during trip",
                }
            ],
        }

        result = detect_issue_notification(analysis)

        self.assertTrue(result["flagged"])
        self.assertTrue(result["is_unknown_scenario"])
        self.assertEqual(result["uncertainty"], "HIGH")
        self.assertGreater(result["novelty_score"], 0.50)
        self.assertIn("UNKNOWN", result["status"])
        self.assertTrue(any("Historical RAG similarity is low" in r for r in result["explainable_reasons"]))
        self.assertTrue(result["human_review_required"])
        self.assertEqual(result["human_review_status"], "PENDING_SIGN_OFF")

    def test_unknown_scenario_empty_history(self):
        """Empty historical records must flag an Unknown Scenario with high novelty."""
        analysis = {
            "target_well": "Well-Test-EmptyHistory",
            "current_condition": {
                "depth": 1500.0,
                "wob": 12000.0,
                "torque": 10.0,
                "flow_in": 0.03,
                "flow_out": 0.03,
                "pump": 110000.0,
            },
            "risk": {"level": "LOW", "probability": 0.8},
            "offset_wells": [{"offset_max_md": 1800.0, "similarity_score": 0.90}],
            "historical_events": [],
        }

        result = detect_issue_notification(analysis)

        self.assertTrue(result["is_unknown_scenario"])
        self.assertEqual(result["novelty_score"], 1.0)
        self.assertFalse(result["historical_evidence_comparison"]["has_precedent"])
        self.assertEqual(result["historical_evidence_comparison"]["precedent_count"], 0)
        self.assertIn("No historical incident logs matched", str(result["missing_evidence"]))

    def test_known_scenario_nominal_drilling(self):
        """Known scenario with strong historical and offset matches should be nominal."""
        analysis = {
            "target_well": "Well-Test-Nominal",
            "current_condition": {
                "depth": 1100.0,
                "wob": 14000.0,
                "torque": 8.5,
                "flow_in": 0.04,
                "flow_out": 0.039,
                "pump": 130000.0,
            },
            "risk": {"level": "LOW", "probability": 2.0},
            "offset_wells": [
                {"offset_well": "Offset-B", "offset_max_md": 1250.0, "similarity_score": 0.92}
            ],
            "historical_events": [
                {
                    "similarity_score": 0.82,
                    "event_type": "drilling_event",
                    "well_id": "Offset-B",
                    "event_md": 1083.0,
                    "description": "Normal rotary drilling progress",
                }
            ],
        }

        result = detect_issue_notification(analysis)

        self.assertFalse(result["flagged"])
        self.assertFalse(result["is_unknown_scenario"])
        self.assertEqual(result["severity"], "LOW")
        self.assertEqual(result["status"], "NORMAL_MONITORING")
        self.assertEqual(len(result["triggering_measurements"]), 0)
        self.assertTrue(result["historical_evidence_comparison"]["has_precedent"])

    def test_anomalous_flow_deficit_lost_circulation(self):
        """Severe flow return deficit must trigger high severity issue notification."""
        anomalies = evaluate_telemetry_anomalies({
            "flow_in": 0.050,
            "flow_out": 0.005,  # 90% deficit while pumping
            "pump": 140000.0,
            "torque": 10.0,
            "wob": 12000.0,
        })

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["parameter"], "FLOW_BALANCE")
        self.assertEqual(anomalies[0]["severity"], "HIGH")
        self.assertIn("deficit", anomalies[0]["deviation"].lower())

    def test_anomalous_flow_gain_kick_risk(self):
        """Flow out exceeding flow in by > 35% must trigger CRITICAL anomaly."""
        anomalies = evaluate_telemetry_anomalies({
            "flow_in": 0.030,
            "flow_out": 0.055,  # 83% excess return flow
            "pump": 135000.0,
        })

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["parameter"], "FLOW_BALANCE")
        self.assertEqual(anomalies[0]["severity"], "CRITICAL")
        self.assertIn("kick", anomalies[0]["reason"].lower())

    def test_hydraulic_disconnect_packoff(self):
        """High standpipe pressure without nominal surface flow must trigger anomaly."""
        anomalies = evaluate_telemetry_anomalies({
            "pump": 260000.0,
            "flow_in": 0.0005,
        })

        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0]["parameter"], "HYDRAULIC_DISCONNECT")
        self.assertIn("pack-off", anomalies[0]["reason"].lower())

    def test_uncharted_depth_interval(self):
        """Operating deeper than all offset wells must trigger depth coverage warning."""
        coverage = evaluate_offset_coverage(
            offset_wells=[
                {"offset_well": "Offset-1", "offset_max_md": 1206.0, "similarity_score": 0.74},
                {"offset_well": "Offset-2", "offset_max_md": 1083.0, "similarity_score": 0.73},
            ],
            target_depth=3510.0,
        )

        self.assertFalse(coverage["depth_covered"])
        self.assertEqual(coverage["max_offset_depth"], 1206.0)
        self.assertEqual(coverage["target_depth"], 3510.0)
        self.assertGreater(coverage["depth_margin"], 2300.0)
        self.assertIn("exceeds maximum offset reference", coverage["assessment"])

    def test_missing_sensor_evidence_and_uncertainty(self):
        """Missing essential channels must be logged under missing evidence with HIGH uncertainty."""
        analysis = {
            "target_well": "Well-Test-MissingTelemetry",
            "current_condition": {
                "depth": 1800.0,
                "wob": None,
                "torque": None,
                "flow_in": None,
                "flow_out": None,
                "pump": None,
            },
            "risk": {"level": "LOW", "probability": 1.0},
            "offset_wells": [],
            "historical_events": [],
        }

        result = detect_issue_notification(analysis)

        self.assertTrue(result["flagged"])
        self.assertEqual(result["uncertainty"], "HIGH")
        self.assertLess(result["confidence"], 0.60)
        self.assertTrue(len(result["missing_evidence"]) >= 2)

    def test_null_and_nan_resilience(self):
        """Engine must handle float('nan'), float('inf'), None, and strings gracefully without crashing."""
        analysis = {
            "target_well": "Well-Test-Corrupted",
            "current_condition": {
                "depth": float("nan"),
                "wob": float("inf"),
                "torque": "corrupt_data",
                "flow_in": None,
                "flow_out": -1.0,
                "pump": "",
            },
            "risk": None,
            "offset_wells": None,
            "historical_events": None,
        }

        # Must not raise an unhandled exception
        result = detect_issue_notification(analysis)

        self.assertIsInstance(result, dict)
        self.assertIn("flagged", result)
        self.assertIn("severity", result)
        self.assertIn("uncertainty_warnings", result)
        self.assertEqual(result["uncertainty"], "HIGH")

    def test_agent_workflow_integration(self):
        """run_agentic_workflow must include unknown_scenario_review stage in agents list."""
        analysis = {
            "target_well": "Well-Workflow-Integration",
            "current_condition": {
                "depth": 1500.0,
                "wob": 14000.0,
                "torque": 8.0,
                "flow_in": 0.04,
                "flow_out": 0.04,
                "pump": 130000.0,
            },
            "risk": {"level": "LOW", "probability": 2.5},
            "offset_wells": [{"similarity_score": 0.85, "offset_max_md": 1600.0}],
            "historical_events": [{"similarity_score": 0.45, "event_type": "pressure_event", "event_md": 1500.0}],
            "recommendations": ["Review pump parameters."],
        }

        workflow = run_agentic_workflow(analysis)

        stages = [step["stage"] for step in workflow.get("agents", [])]
        self.assertIn("unknown_scenario_review", stages)
        self.assertIn("issue_notification", workflow)
        self.assertIn("issue_notification", analysis)

        unknown_step = next(s for s in workflow["agents"] if s["stage"] == "unknown_scenario_review")
        self.assertEqual(unknown_step["status"], "complete")
        self.assertIn("issue_notification", unknown_step["result"])

    @patch("urllib.request.urlopen")
    def test_ollama_timeout_resilience(self, mock_urlopen):
        """Ollama timeout must fall back gracefully without losing deterministic findings."""
        mock_urlopen.side_effect = TimeoutError("Connection timed out after 10.0 seconds")

        findings = {
            "risk_review": {"valid": True, "finding": "Risk valid"},
            "unknown_scenario_review": {
                "flagged": True,
                "is_unknown_scenario": True,
                "severity": "HIGH",
                "finding": "Unknown scenario detected",
            },
        }
        analysis = {
            "target_well": "Well-Timeout-Test",
            "risk": {"level": "HIGH", "probability": 75.0},
        }

        result = _llm_synthesis(analysis, findings)

        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["content"])
        self.assertTrue(result["human_review_required"])
        self.assertIn("timed out", result["error"].lower())

    @patch("urllib.request.urlopen")
    def test_ollama_connection_refused_resilience(self, mock_urlopen):
        """Ollama connection refusal must not crash and must preserve deterministic outputs."""
        mock_urlopen.side_effect = urllib.error.URLError("Connection refused [Errno 111]")

        findings = {"risk_review": {"valid": True, "finding": "Deterministic OK"}}
        analysis = {"target_well": "Well-ConnRefused-Test"}

        result = _llm_synthesis(analysis, findings)

        self.assertEqual(result["status"], "unavailable")
        self.assertIsNone(result["content"])
        self.assertIn("refused", result["error"].lower())

    def test_api_endpoints_return_issue_notification(self):
        """Both /analyze and /agentic-analyze must return a valid issue_notification object."""
        from fastapi.testclient import TestClient
        from backend.main import app

        client = TestClient(app)
        wells_resp = client.get("/wells")
        self.assertEqual(wells_resp.status_code, 200)
        wells = wells_resp.json().get("wells", [])
        self.assertTrue(len(wells) > 0)
        target_well = wells[0]

        # Test /analyze
        analyze_resp = client.post("/analyze", json={"well_id": target_well})
        self.assertEqual(analyze_resp.status_code, 200)
        data = analyze_resp.json()
        self.assertIn("issue_notification", data)
        self.assertIsNotNone(data["issue_notification"])
        self.assertIn("flagged", data["issue_notification"])
        self.assertIn("severity", data["issue_notification"])
        self.assertIn("is_unknown_scenario", data["issue_notification"])

        # Test /agentic-analyze
        agentic_resp = client.post("/agentic-analyze", json={"well_id": target_well})
        self.assertEqual(agentic_resp.status_code, 200)
        agentic_data = agentic_resp.json()
        self.assertIn("issue_notification", agentic_data)
        self.assertIn("agentic", agentic_data)
        stages = [s["stage"] for s in agentic_data["agentic"].get("agents", [])]
        self.assertIn("unknown_scenario_review", stages)


if __name__ == "__main__":
    unittest.main()
