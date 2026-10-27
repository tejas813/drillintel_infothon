import React, { useState } from "react";
import { motion, AnimatePresence } from "motion/react";
import {
  AlertTriangle,
  ShieldAlert,
  ShieldCheck,
  Compass,
  Radar,
  HelpCircle,
  Activity,
  Layers,
  ChevronDown,
  Info,
  Clock,
  CheckCircle2,
  FileWarning,
  Flame,
} from "lucide-react";

export default function IssueNotificationPanel({
  issueNotification,
  loading,
  reduceMotion,
}) {
  const [showDetails, setShowDetails] = useState(true);

  if (loading) {
    return (
      <div className="in-panel in-loading glass-panel">
        <div className="in-loading-inner">
          <Radar className="spin-slow text-amber" size={22} />
          <span>Evaluating operational telemetry for issue notifications & unknown scenarios…</span>
        </div>
      </div>
    );
  }

  if (!issueNotification) {
    return (
      <div className="in-panel in-idle glass-panel">
        <div className="in-idle-inner">
          <div className="in-idle-icon">
            <Compass size={20} />
          </div>
          <div className="in-idle-text">
            <strong>Issue Notification & Unknown Scenario System Standby</strong>
            <p>
              Run well analysis to initiate real-time telemetry screening, offset trajectory depth
              checks, and historical RAG novelty classification.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const {
    flagged = false,
    status = "NORMAL_MONITORING",
    severity = "LOW",
    is_unknown_scenario = false,
    confidence = 0.9,
    uncertainty = "LOW",
    novelty_score = 0.0,
    title = "Issue Notification",
    summary = "No active notifications.",
    triggering_measurements = [],
    explainable_reasons = [],
    historical_evidence_comparison = {},
    offset_coverage = {},
    missing_evidence = [],
    uncertainty_warnings = [],
    human_review_required = true,
    human_review_status = "PENDING_SIGN_OFF",
    recommended_actions = [],
  } = issueNotification;

  const sevLower = String(severity || "low").toLowerCase();
  const uncertLower = String(uncertainty || "low").toLowerCase();

  const getSeverityBadgeClass = (sev) => {
    switch (sev.toLowerCase()) {
      case "critical":
        return "badge-in-critical";
      case "high":
        return "badge-in-high";
      case "medium":
        return "badge-in-medium";
      default:
        return "badge-in-low";
    }
  };

  return (
    <motion.section
      className={`in-panel glass-panel sev-${sevLower} ${
        flagged ? "in-flagged" : "in-nominal"
      }`}
      initial={reduceMotion ? false : { opacity: 0, y: 15 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
    >
      {/* 1. Header Bar */}
      <header className="in-header">
        <div className="in-header-left">
          <div className={`in-alert-beacon ${sevLower}`}>
            {is_unknown_scenario ? (
              <Radar className="beacon-icon" size={20} />
            ) : flagged ? (
              <AlertTriangle className="beacon-icon" size={20} />
            ) : (
              <CheckCircle2 className="beacon-icon" size={20} />
            )}
            <span className="beacon-pulse" />
          </div>

          <div className="in-title-block">
            <div className="in-eyebrow-row">
              <span className="in-eyebrow">
                {is_unknown_scenario
                  ? "OUT-OF-DISTRIBUTION DETECTION"
                  : "OPERATIONAL SUPERVISORY PROTOCOL"}
              </span>
              <span className="in-protocol-tag">RTOC-IN-2026</span>
            </div>
            <h3 className="in-main-title">{title}</h3>
          </div>
        </div>

        <div className="in-header-badges">
          {/* IN Flag Indicator */}
          <div className={`in-flag-pill ${flagged ? "flagged" : "clear"}`}>
            <span className="flag-dot" />
            <span>
              {flagged
                ? is_unknown_scenario
                  ? "IN: UNKNOWN SCENARIO"
                  : "IN FLAG: ACTIVE"
                : "IN: MONITORING CLEAR"}
            </span>
          </div>

          {/* Severity Badge */}
          <span className={`in-severity-pill ${getSeverityBadgeClass(severity)}`}>
            {severity} SEVERITY
          </span>

          {/* Uncertainty Badge */}
          <span className={`in-uncert-pill uncert-${uncertLower}`}>
            <HelpCircle size={13} />
            UNCERTAINTY: {uncertainty}
          </span>

          {/* Human Review Sign-Off Status */}
          <div className="in-signoff-pill">
            <ShieldAlert size={14} className="text-amber" />
            <span>{human_review_status.replace(/_/g, " ")}</span>
          </div>

          {/* Toggle Details Button */}
          <button
            type="button"
            className="in-toggle-btn"
            onClick={() => setShowDetails(!showDetails)}
            title={showDetails ? "Collapse alert details" : "Expand alert details"}
            aria-expanded={showDetails}
          >
            <span>{showDetails ? "Collapse" : "Inspect"}</span>
            <motion.span
              animate={{ rotate: showDetails ? 180 : 0 }}
              transition={{ duration: 0.2 }}
            >
              <ChevronDown size={15} />
            </motion.span>
          </button>
        </div>
      </header>

      {/* 2. Executive Summary Callout */}
      <div className={`in-summary-box ${sevLower}`}>
        <div className="summary-indicator-stripe" />
        <p className="in-summary-text">{summary}</p>
      </div>

      <AnimatePresence>
        {showDetails && (
          <motion.div
            className="in-details-container"
            initial={reduceMotion ? false : { opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: "auto" }}
            exit={reduceMotion ? false : { opacity: 0, height: 0 }}
            transition={{ duration: 0.25 }}
          >
            {/* 3. Operational Evidence Matrix (Triggering Measurements & Novelty) */}
            <div className="in-matrix-grid">
              {/* Triggering Measurements Card */}
              <div className="in-subcard">
                <div className="in-subcard-header">
                  <Activity size={16} className="text-cyan" />
                  <h4>Triggering Measurements & Divergence</h4>
                  <span className="subcard-count">
                    {triggering_measurements.length} Anomaly
                    {triggering_measurements.length === 1 ? "" : "ies"}
                  </span>
                </div>

                {!triggering_measurements.length ? (
                  <div className="in-nominal-box">
                    <CheckCircle2 size={16} className="text-cyan" />
                    <span>
                      All primary telemetry channels (WOB, Torque, Flow, Pump) are operating within
                      standard mechanical corridors.
                    </span>
                  </div>
                ) : (
                  <div className="triggering-list">
                    {triggering_measurements.map((meas, idx) => (
                      <div key={idx} className={`trigger-item status-${meas.severity?.toLowerCase()}`}>
                        <div className="trigger-top">
                          <span className="trigger-param">{meas.channel || meas.parameter}</span>
                          <span className={`trigger-tag ${meas.severity?.toLowerCase()}`}>
                            {meas.status || "ANOMALOUS"}
                          </span>
                        </div>
                        <div className="trigger-values">
                          <div className="val-row">
                            <span className="val-lbl">Observed:</span>
                            <strong className="val-current">{meas.current_value}</strong>
                          </div>
                          <div className="val-row">
                            <span className="val-lbl">Baseline:</span>
                            <span className="val-base">{meas.baseline}</span>
                          </div>
                          <div className="val-row">
                            <span className="val-lbl">Deviation:</span>
                            <span className="val-dev text-amber">{meas.deviation}</span>
                          </div>
                        </div>
                        {meas.reason && <p className="trigger-reason">{meas.reason}</p>}
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Historical Precedent & Offset Coverage Card */}
              <div className="in-subcard">
                <div className="in-subcard-header">
                  <Layers size={16} className="text-amber" />
                  <h4>Historical Precedent & Offset Coverage</h4>
                  <span className="subcard-count">
                    Novelty: {(novelty_score * 100).toFixed(1)}%
                  </span>
                </div>

                <div className="comparison-content">
                  {/* Historical RAG comparison */}
                  <div className="comparison-row">
                    <span className="comp-label">Historical Precedent:</span>
                    <span
                      className={`comp-value ${
                        historical_evidence_comparison?.has_precedent ? "text-cyan" : "text-amber"
                      }`}
                    >
                      {historical_evidence_comparison?.has_precedent
                        ? "Known Case Match"
                        : "Low Correlation / Novel Scenario"}
                    </span>
                  </div>

                  <div className="comparison-row">
                    <span className="comp-label">Top Vector Similarity:</span>
                    <strong className="comp-value score">
                      {historical_evidence_comparison?.top_similarity_score !== undefined
                        ? `${(historical_evidence_comparison.top_similarity_score * 100).toFixed(1)}%`
                        : "0.0%"}
                    </strong>
                  </div>

                  {historical_evidence_comparison?.closest_event_type && (
                    <div className="comparison-row">
                      <span className="comp-label">Closest Event Type:</span>
                      <span className="comp-value">
                        {historical_evidence_comparison.closest_event_type} (
                        {historical_evidence_comparison.closest_event_well || "offset"} @{" "}
                        {historical_evidence_comparison.closest_event_depth} m)
                      </span>
                    </div>
                  )}

                  <p className="comp-assessment">
                    {historical_evidence_comparison?.assessment ||
                      "Historical event comparison unavailable."}
                  </p>

                  <div className="comp-divider" />

                  {/* Offset Depth Boundary */}
                  <div className="comparison-row">
                    <span className="comp-label">Offset Depth Horizon:</span>
                    <span
                      className={`comp-value ${
                        offset_coverage?.depth_covered ? "text-cyan" : "text-amber"
                      }`}
                    >
                      {offset_coverage?.depth_covered
                        ? "Depth Bounded by Offsets"
                        : "Unlogged Deeper Section"}
                    </span>
                  </div>

                  <div className="comparison-row">
                    <span className="comp-label">Max Offset Depth:</span>
                    <span className="comp-value">
                      {offset_coverage?.max_offset_depth
                        ? `${offset_coverage.max_offset_depth} m`
                        : "—"}
                    </span>
                  </div>

                  <p className="comp-assessment">
                    {offset_coverage?.assessment || "Offset coverage assessment pending."}
                  </p>
                </div>
              </div>
            </div>

            {/* 4. Explainable Reasons & Missing Evidence Row */}
            <div className="in-rationale-row">
              {/* Explainable Reasons */}
              <div className="in-reasons-block">
                <h5 className="block-subheading">
                  <Info size={14} className="text-cyan" />
                  Explainable Diagnostic Reasons
                </h5>
                <ul className="reasons-list">
                  {explainable_reasons.length ? (
                    explainable_reasons.map((reason, idx) => (
                      <li key={idx} className="reason-item">
                        <span className="bullet-chevron">›</span>
                        <span>{reason}</span>
                      </li>
                    ))
                  ) : (
                    <li className="reason-item text-muted">
                      No anomalous justifications flagged for the current condition.
                    </li>
                  )}
                </ul>
              </div>

              {/* Missing Evidence / Sensor Gaps */}
              <div className="in-missing-block">
                <h5 className="block-subheading">
                  <FileWarning size={14} className="text-amber" />
                  Missing Evidence & Telemetry Gaps
                </h5>
                {missing_evidence.length ? (
                  <div className="missing-tags-wrap">
                    {missing_evidence.map((gap, idx) => (
                      <span key={idx} className="missing-gap-tag">
                        {gap}
                      </span>
                    ))}
                  </div>
                ) : (
                  <div className="all-evidence-present">
                    <CheckCircle2 size={14} className="text-cyan" />
                    <span>All primary sensor telemetry and offset datasets are available.</span>
                  </div>
                )}

                {/* Recommended Mitigation Steps */}
                {recommended_actions.length > 0 && (
                  <div className="actions-section mt-3">
                    <h6 className="actions-subheading">Recommended Mitigation Actions:</h6>
                    <ul className="actions-list">
                      {recommended_actions.map((act, i) => (
                        <li key={i} className="action-item">
                          <span className="action-num">0{i + 1}</span>
                          <span>{act}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            </div>

            {/* 5. Uncertainty & Safety Disclaimers */}
            <div className="in-safety-disclaimer">
              <ShieldAlert size={16} className="disclaimer-icon text-amber" />
              <div className="disclaimer-content">
                <strong>Supervisory Decision Support & Verification Protocol</strong>
                <p>
                  This Issue Notification engine generates empirical anomaly flags based on
                  available surface sensors and historical offset correlation. Thresholds are not
                  certified structural limits. Autonomous drilling operations are strictly
                  prohibited; a certified drilling supervisor or petrotechnical engineer must verify
                  all findings before altering drilling parameters.
                </p>
                {uncertainty_warnings.length > 0 && (
                  <ul className="uncertainty-bullets">
                    {uncertainty_warnings.map((w, idx) => (
                      <li key={idx}>{w}</li>
                    ))}
                  </ul>
                )}
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </motion.section>
  );
}
