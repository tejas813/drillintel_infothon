import React, { useState } from "react";
import { AnimatePresence, motion } from "motion/react";
import {
  Activity,
  CheckCircle2,
  ChevronDown,
  CircleAlert,
  Clock3,
  Copy,
  Cpu,
  Layers,
  ShieldAlert,
  ShieldCheck,
  Terminal,
  XCircle,
  Zap,
} from "lucide-react";
import "./agentic-panel.css";

const statusConfig = {
  complete: {
    icon: CheckCircle2,
    color: "cyan",
    label: "COMPLETE",
    badgeClass: "badge-complete",
  },
  warning: {
    icon: CircleAlert,
    color: "amber",
    label: "WARNING",
    badgeClass: "badge-warning",
  },
  failed: {
    icon: XCircle,
    color: "rose",
    label: "FAILED",
    badgeClass: "badge-failed",
  },
  unavailable: {
    icon: Clock3,
    color: "muted",
    label: "UNAVAILABLE",
    badgeClass: "badge-unavailable",
  },
};

const formatLabel = (value) =>
  String(value ?? "Unknown").replace(/_/g, " ");

export default function AgenticPanel({ agentic, reduceMotion }) {
  const agents = Array.isArray(agentic?.agents) ? agentic.agents : [];
  const limitations = Array.isArray(agentic?.limitations)
    ? agentic.limitations
    : [];

  // Default first 2 steps expanded if available, or empty
  const [expandedIndices, setExpandedIndices] = useState(new Set([0, 1]));
  const [copiedIndex, setCopiedIndex] = useState(null);

  const toggleStep = (index) => {
    setExpandedIndices((prev) => {
      const next = new Set(prev);
      if (next.has(index)) {
        next.delete(index);
      } else {
        next.add(index);
      }
      return next;
    });
  };

  const expandAll = () => {
    setExpandedIndices(new Set(agents.map((_, i) => i)));
  };

  const collapseAll = () => {
    setExpandedIndices(new Set());
  };

  const copyJson = (data, index) => {
    navigator.clipboard.writeText(JSON.stringify(data, null, 2));
    setCopiedIndex(index);
    setTimeout(() => setCopiedIndex(null), 1800);
  };

  const overallStatus = String(agentic?.overall_status ?? "idle").toLowerCase();

  return (
    <section className="agent-mission-control">
      {/* Top Header */}
      <header className="mission-header">
        <div className="mission-brand">
          <div className="mission-icon">
            <Cpu size={20} />
          </div>
          <div>
            <div className="mission-eyebrow">
              <span className="live-dot" />
              MULTI-STAGE AGENT ORCHESTRATION
            </div>
            <h3>Agent Mission Control</h3>
            <p className="mission-subtitle">
              Bounded evidence verification · Deterministic review pipeline
            </p>
          </div>
        </div>

        <div className="mission-header-actions">
          {agents.length > 0 && (
            <div className="accordion-controls">
              <button
                type="button"
                className="btn-text-ctrl"
                onClick={expandAll}
                title="Expand all agent traces"
              >
                Expand all
              </button>
              <span className="ctrl-divider">/</span>
              <button
                type="button"
                className="btn-text-ctrl"
                onClick={collapseAll}
                title="Collapse all agent traces"
              >
                Collapse all
              </button>
            </div>
          )}

          <div className={`mission-overall-badge ${overallStatus}`}>
            <span className="pulse-indicator" />
            <span>{formatLabel(overallStatus)}</span>
          </div>
        </div>
      </header>

      {/* Empty State */}
      {!agents.length ? (
        <div className="mission-empty-state">
          <div className="empty-icon-wrap">
            <ShieldCheck size={28} />
          </div>
          <div className="empty-copy">
            <strong>Agent Workflow Idle</strong>
            <p>
              Run well analysis to initiate the multi-agent review stages (Risk Review,
              Offset Intelligence, Historical Event Retrieval, and Synthesizer).
            </p>
          </div>
        </div>
      ) : (
        /* Interactive Step Nodes / Accordion List */
        <div className="mission-steplist">
          {agents.map((agent, index) => {
            const rawStatus = String(agent?.status ?? "complete").toLowerCase();
            const config = statusConfig[rawStatus] ?? statusConfig.complete;
            const Icon = config.icon;
            const isExpanded = expandedIndices.has(index);

            const title =
              agent?.name ??
              agent?.title ??
              formatLabel(agent?.agent ?? `Stage ${index + 1}`);

            const toolName = formatLabel(
              agent?.tool ?? agent?.agent ?? agent?.stage ?? "orchestrator"
            );

            const detail =
              agent?.finding ??
              agent?.detail ??
              agent?.summary ??
              "Stage completed successfully.";

            const resultData = agent?.result ?? agent;

            return (
              <motion.div
                key={`${title}-${index}`}
                className={`mission-step-card ${isExpanded ? "expanded" : ""} status-${config.color}`}
                initial={reduceMotion ? false : { opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                {/* Clickable Accordion Header */}
                <button
                  type="button"
                  className="mission-step-header"
                  onClick={() => toggleStep(index)}
                  aria-expanded={isExpanded}
                  aria-controls={`step-content-${index}`}
                >
                  <div className="step-header-left">
                    <span className={`step-status-icon icon-${config.color}`}>
                      <Icon size={16} />
                    </span>
                    <span className="step-num">
                      {String(index + 1).padStart(2, "0")}
                    </span>
                    <div className="step-titles">
                      <strong className="step-title">{title}</strong>
                      <span className="step-tool-badge">{toolName}</span>
                    </div>
                  </div>

                  <div className="step-header-right">
                    <span className={`step-badge ${config.badgeClass}`}>
                      {config.label}
                    </span>
                    <motion.span
                      className="step-chevron"
                      animate={{ rotate: isExpanded ? 180 : 0 }}
                      transition={{ duration: 0.2 }}
                    >
                      <ChevronDown size={17} />
                    </motion.span>
                  </div>
                </button>

                {/* Collapsible Inspection Drawer */}
                <AnimatePresence initial={false}>
                  {isExpanded && (
                    <motion.div
                      id={`step-content-${index}`}
                      className="mission-step-drawer"
                      initial={{ height: 0, opacity: 0 }}
                      animate={{ height: "auto", opacity: 1 }}
                      exit={{ height: 0, opacity: 0 }}
                      transition={{ duration: 0.24, ease: [0.22, 1, 0.36, 1] }}
                    >
                      <div className="drawer-inner">
                        {/* Summary Finding Box */}
                        <div className="drawer-finding-box">
                          <span className="finding-label">VERIFIED FINDING:</span>
                          <p className="finding-text">{detail}</p>
                          {agent?.reason && (
                            <p className="finding-reason">
                              <strong>Context:</strong> {agent.reason}
                            </p>
                          )}
                        </div>

                        {/* Structured Output Tags (if present) */}
                        {(agent?.risk_level || agent?.score !== undefined) && (
                          <div className="drawer-metrics-row">
                            {agent?.risk_level && (
                              <div className="drawer-stat">
                                <span>Output Risk</span>
                                <strong>{agent.risk_level}</strong>
                              </div>
                            )}
                            {agent?.score !== undefined && (
                              <div className="drawer-stat">
                                <span>Model Score</span>
                                <strong>
                                  {typeof agent.score === "number"
                                    ? agent.score.toFixed(1) + "%"
                                    : String(agent.score)}
                                </strong>
                              </div>
                            )}
                            {agent?.valid !== undefined && (
                              <div className="drawer-stat">
                                <span>Schema Validation</span>
                                <strong className="text-cyan">
                                  {agent.valid ? "Verified Pass" : "Flagged"}
                                </strong>
                              </div>
                            )}
                          </div>
                        )}

                        {/* Unknown Scenario / IN Flag Structured Metrics */}
                        {agent?.result?.tool === "unknown_scenario_review" && (
                          <div className="drawer-metrics-row">
                            <div className="drawer-stat">
                              <span>Scenario Type</span>
                              <strong className={agent.result.is_unknown_scenario ? "text-amber" : "text-cyan"}>
                                {agent.result.is_unknown_scenario ? "Unknown / Novel" : "Known Precedent"}
                              </strong>
                            </div>
                            <div className="drawer-stat">
                              <span>Severity</span>
                              <strong className="text-amber">{agent.result.severity}</strong>
                            </div>
                            <div className="drawer-stat">
                              <span>Novelty Score</span>
                              <strong>
                                {agent.result.novelty_score !== undefined
                                  ? `${(agent.result.novelty_score * 100).toFixed(1)}%`
                                  : "0.0%"}
                              </strong>
                            </div>
                            <div className="drawer-stat">
                              <span>Uncertainty</span>
                              <strong>{agent.result.uncertainty}</strong>
                            </div>
                          </div>
                        )}

                        {/* Evidence Items (if array present) */}
                        {Array.isArray(agent?.evidence) && agent.evidence.length > 0 && (
                          <div className="drawer-evidence-section">
                            <span className="evidence-header-label">
                              EVIDENCE ITEMS ({agent.evidence.length})
                            </span>
                            <div className="evidence-pills-list">
                              {agent.evidence.map((ev, evIdx) => (
                                <span key={evIdx} className="evidence-pill">
                                  {typeof ev === "object" ? JSON.stringify(ev) : String(ev)}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Raw JSON Trace Inspector */}
                        <div className="raw-trace-box">
                          <div className="raw-trace-header">
                            <span className="trace-label">
                              <Terminal size={13} />
                              EXECUTION LOG & TRACE
                            </span>
                            <button
                              type="button"
                              className="copy-trace-btn"
                              onClick={(e) => {
                                e.stopPropagation();
                                copyJson(resultData, index);
                              }}
                            >
                              <Copy size={12} />
                              {copiedIndex === index ? "Copied!" : "Copy Trace"}
                            </button>
                          </div>
                          <pre className="trace-code">
                            {JSON.stringify(resultData, null, 2)}
                          </pre>
                        </div>
                      </div>
                    </motion.div>
                  )}
                </AnimatePresence>
              </motion.div>
            );
          })}
        </div>
      )}

      {/* Human In The Loop Advisory Footer */}
      <footer className="mission-footer">
        <div className="footer-left">
          <ShieldAlert size={16} className="text-amber" />
          <span>
            <strong>Human-in-the-Loop Protocol:</strong> Deterministic decision support
            only. All automated suggestions require certified drilling engineer sign-off.
          </span>
        </div>

        {limitations.length > 0 && (
          <details className="limitations-dropdown">
            <summary className="limitations-summary">
              System Limitations ({limitations.length})
              <ChevronDown size={14} className="limitation-chevron" />
            </summary>
            <ul className="limitations-list">
              {limitations.map((lim, i) => (
                <li key={i}>{lim}</li>
              ))}
            </ul>
          </details>
        )}
      </footer>
    </section>
  );
}
