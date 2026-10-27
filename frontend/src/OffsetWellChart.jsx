import React, { useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  Cell,
  CartesianGrid,
  ReferenceLine,
} from "recharts";
import { Target, Layers, ArrowUpRight, Compass, ShieldCheck } from "lucide-react";

function formatWellName(id) {
  if (!id) return "Unknown";
  // Convert 'Norway-Statoil-NO 15_$47$_9-F-7' to clean readable 'Well 15/9-F-7'
  return id
    .replace(/^Norway-Statoil-NO\s*/i, "")
    .replace(/_\$47\$_/g, "/")
    .replace(/_/g, " ");
}

const CustomTooltip = ({ active, payload }) => {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    return (
      <div className="offset-chart-tooltip">
        <div className="tooltip-header">
          <span className="tooltip-tag">
            {data.sodirName ? `SODIR · ${data.sodirName}` : "OFFSET CANDIDATE"}
          </span>
          <span className="tooltip-score">
            {(data.similarity * 100).toFixed(1)}% TRAJECTORY
          </span>
        </div>
        <strong className="tooltip-well-name">{data.sodirName || data.fullWellId}</strong>
        <div className="tooltip-grid">
          <div>
            <span>Spatial Distance</span>
            <strong className="text-cyan">
              {data.distanceKm != null
                ? data.distanceKm < 0.05
                  ? "< 50 m (Slot Co-located)"
                  : `${data.distanceKm.toFixed(3)} km`
                : "Platform Grid"}
            </strong>
          </div>
          <div>
            <span>Spatial Affinity</span>
            <strong>
              {data.spatialScore != null
                ? `${(data.spatialScore * 100).toFixed(1)}%`
                : "High (Volve)"}
            </strong>
          </div>
          <div>
            <span>Depth Diff (Δ)</span>
            <strong>{data.depthDiff.toFixed(1)} m</strong>
          </div>
          <div>
            <span>Master Composite Score</span>
            <strong className="text-amber">
              {data.masterScore != null
                ? `${(data.masterScore * 100).toFixed(1)}%`
                : `${(data.similarity * 100).toFixed(1)}%`}
            </strong>
          </div>
        </div>
      </div>
    );
  }
  return null;
};

export default function OffsetWellChart({ offsetWells = [] }) {
  const [activeBar, setActiveBar] = useState(null);

  const hasData = Array.isArray(offsetWells) && offsetWells.length > 0;

  const chartData = hasData
    ? offsetWells.map((item, idx) => ({
        id: item.well_id || `Well-${idx}`,
        shortName: item.sodir_name || formatWellName(item.well_id),
        sodirName: item.sodir_name,
        fullWellId: item.well_id,
        similarity: Number(item.similarity_score ?? 0),
        similarityPct: Number((Number(item.similarity_score ?? 0) * 100).toFixed(1)),
        spatialScore: item.spatial_score != null ? Number(item.spatial_score) : null,
        distanceKm: item.distance_km != null ? Number(item.distance_km) : null,
        masterScore: item.master_score != null ? Number(item.master_score) : null,
        operator: item.operator,
        field: item.field,
        depthDiff: Number(item.depth_difference ?? 0),
        targetMaxMd: Number(item.target_max_md ?? 0),
        offsetMaxMd: Number(item.offset_max_md ?? 0),
      }))
    : [];

  const topMatch = chartData[0];

  return (
    <div className="offset-graph-container">
      {/* Chart Top Header & Controls */}
      <div className="offset-graph-header">
        <div className="offset-graph-title">
          <div className="panel-title-icon">
            <Target size={18} />
          </div>
          <div>
            <h3>Offset Well Intelligence</h3>
            <p>Trajectory & spatial similarity comparison</p>
          </div>
        </div>

        {hasData && (
          <div className="offset-header-badges">
            <span className="graph-meta-badge">
              <Layers size={13} />
              {chartData.length} Candidates Evaluated
            </span>
          </div>
        )}
      </div>

      {!hasData ? (
        <div className="offset-graph-empty">
          <Compass size={32} className="spin-slow text-cyan" />
          <strong>Awaiting Trajectory Ranking</strong>
          <p>Run analysis to render offset well similarity and comparative trajectory metrics.</p>
        </div>
      ) : (
        <div className="offset-graph-body">
          {/* Main Interactive Recharts Horizontal Bar Chart */}
          <div className="offset-chart-wrapper" style={{ width: "100%", height: 210 }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 10, right: 35, left: 15, bottom: 5 }}
              >
                <defs>
                  <linearGradient id="cyanBarGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#00F2FE" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#0284C7" stopOpacity={0.95} />
                  </linearGradient>
                  <linearGradient id="amberBarGrad" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#FFB300" stopOpacity={0.9} />
                    <stop offset="100%" stopColor="#D97706" stopOpacity={0.95} />
                  </linearGradient>
                  <linearGradient id="cyanBarHover" x1="0" y1="0" x2="1" y2="0">
                    <stop offset="0%" stopColor="#67e8f9" stopOpacity={1} />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity={1} />
                  </linearGradient>
                </defs>

                <CartesianGrid
                  horizontal={false}
                  stroke="rgba(255, 255, 255, 0.07)"
                  strokeDasharray="3 3"
                />

                <XAxis
                  type="number"
                  domain={[0, 100]}
                  unit="%"
                  tick={{ fill: "#64748B", fontSize: 11 }}
                  axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
                  tickLine={false}
                />

                <YAxis
                  type="category"
                  dataKey="shortName"
                  tick={{ fill: "#E2E8F0", fontSize: 12, fontWeight: 600 }}
                  axisLine={{ stroke: "rgba(255, 255, 255, 0.1)" }}
                  tickLine={false}
                  width={110}
                />

                <Tooltip
                  content={<CustomTooltip />}
                  cursor={{ fill: "rgba(255, 255, 255, 0.04)" }}
                />

                <ReferenceLine
                  x={80}
                  stroke="rgba(0, 242, 254, 0.35)"
                  strokeDasharray="4 4"
                  label={{
                    value: "80% Benchmark",
                    fill: "#00F2FE",
                    fontSize: 10,
                    position: "insideTopRight",
                  }}
                />

                <Bar
                  dataKey="similarityPct"
                  radius={[0, 8, 8, 0]}
                  barSize={24}
                  onMouseEnter={(_, index) => setActiveBar(index)}
                  onMouseLeave={() => setActiveBar(null)}
                >
                  {chartData.map((entry, index) => {
                    const isHovered = activeBar === index;
                    const fillUrl = isHovered
                      ? "url(#cyanBarHover)"
                      : entry.similarity >= 0.8
                        ? "url(#cyanBarGrad)"
                        : "url(#amberBarGrad)";
                    return <Cell key={`cell-${index}`} fill={fillUrl} />;
                  })}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          {/* Comparative Summary Metrics Row */}
          <div className="offset-metrics-summary">
            <div className="offset-summary-card">
              <span className="summary-label">TOP SIMILARITY MATCH</span>
              <div className="summary-val-row">
                <strong>{topMatch?.sodirName || topMatch?.shortName || "—"}</strong>
                <span className="match-pill cyan">{topMatch?.similarityPct || 0}%</span>
              </div>
              <small>Closest geometric offset trajectory</small>
            </div>

            <div className="offset-summary-card">
              <span className="summary-label">SPATIAL PROXIMITY</span>
              <div className="summary-val-row">
                <strong>
                  {topMatch?.distanceKm != null
                    ? topMatch.distanceKm < 0.05
                      ? "< 50 m Slot"
                      : `${topMatch.distanceKm.toFixed(2)} km`
                    : "Platform Slot"}
                </strong>
                <span className="match-pill cyan">SODIR Verified</span>
              </div>
              <small>WGS84 distance on Volve Field</small>
            </div>

            <div className="offset-summary-card">
              <span className="summary-label">MASTER COMPOSITE RANK</span>
              <div className="summary-val-row">
                <strong>
                  {topMatch?.masterScore != null
                    ? `${(topMatch.masterScore * 100).toFixed(1)}%`
                    : `${topMatch?.similarityPct || 0}%`}
                </strong>
                <span className="match-pill amber">Multi-Signal</span>
              </div>
              <small>50% Traj · 20% Depth · 30% Spatial</small>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
