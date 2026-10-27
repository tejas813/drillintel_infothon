import React from "react";
import { motion } from "motion/react";
import { Activity, Gauge, MapPin, TrendingUp, Waves, Zap } from "lucide-react";

function formatNumber(value, decimals = 1, fallback = "—") {
  const number = Number(value);
  if (value === null || value === undefined || !Number.isFinite(number)) {
    return fallback;
  }
  return number.toLocaleString(undefined, {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  });
}

export default function OperationalSignals({ condition, loading, reduceMotion }) {
  const hasData = Boolean(condition && Object.keys(condition).length > 0);

  const signals = [
    {
      id: "depth",
      label: "CURRENT DEPTH",
      subLabel: "Measured Depth (MD)",
      value: formatNumber(condition?.depth, 1),
      unit: "m",
      secondary: condition?.depth ? `Bit Depth: ${formatNumber(condition.depth, 1)} m` : "Sensor nominal",
      icon: <MapPin size={19} />,
      accent: "cyan",
    },
    {
      id: "wob",
      label: "WEIGHT ON BIT",
      subLabel: "API Drilling Load",
      value: formatNumber(condition?.wob, 1),
      unit: "daN",
      secondary: condition?.wob ? "Steady bit engagement" : "Awaiting sensor",
      icon: <Activity size={19} />,
      accent: "amber",
    },
    {
      id: "torque",
      label: "ROTARY TORQUE",
      subLabel: "Drive Resistance",
      value: formatNumber(condition?.torque, 2),
      unit: "kN·m",
      secondary: condition?.torque ? "Nominal string rotation" : "Awaiting telemetry",
      icon: <TrendingUp size={19} />,
      accent: "cyan",
    },
    {
      id: "pump",
      label: "PUMP RATE / STROKE",
      subLabel: "Hydraulic Pressure",
      value: formatNumber(condition?.pump, 1),
      unit: "kPa",
      secondary: condition?.pump ? "Continuous mud loop" : "Circulation idle",
      icon: <Waves size={19} />,
      accent: "amber",
    },
  ];

  return (
    <motion.section
      className="unified-signals-container"
      initial={reduceMotion ? false : { opacity: 0, y: 14 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.45 }}
    >
      {/* Header Bar */}
      <div className="signals-header-bar">
        <div className="signals-header-title">
          <div className="signals-header-icon">
            <Zap size={18} />
          </div>
          <div>
            <h4>OPERATIONAL SIGNALS</h4>
            <p>Unified real-time drilling telemetry & hydraulic parameters</p>
          </div>
        </div>

        <div className="signals-header-meta">
          <div className={`telemetry-badge ${hasData ? "active" : "standby"}`}>
            <span className="telemetry-pulse" />
            <span>{hasData ? "STREAM ACTIVE" : "AWAITING TELEMETRY"}</span>
          </div>
          {hasData && condition?.depth && (
            <span className="telemetry-depth-pill">
              Logged @ {formatNumber(condition.depth, 0)} m
            </span>
          )}
        </div>
      </div>

      {/* Unified 4-Column Grid with Sleek Dividers */}
      <div className="signals-quad-grid">
        {signals.map((signal, idx) => (
          <motion.div
            key={signal.id}
            className={`signal-cell accent-${signal.accent}`}
            whileHover={reduceMotion ? {} : { y: -2, backgroundColor: "rgba(255, 255, 255, 0.03)" }}
            transition={{ duration: 0.2 }}
          >
            <div className="signal-cell-top">
              <div className={`signal-cell-icon icon-${signal.accent}`}>
                {signal.icon}
              </div>
              <div className="signal-label-group">
                <span className="signal-label">{signal.label}</span>
                <span className="signal-sublabel">{signal.subLabel}</span>
              </div>
            </div>

            <div className="signal-value-row">
              <span className="signal-value">{signal.value}</span>
              {signal.unit && signal.value !== "—" && (
                <span className="signal-unit">{signal.unit}</span>
              )}
            </div>

            <div className="signal-cell-footer">
              <span className="signal-secondary-text">{signal.secondary}</span>
            </div>
          </motion.div>
        ))}
      </div>
    </motion.section>
  );
}
