import React, { useState, useEffect } from "react";
import {
  Globe,
  Database,
  Search,
  Filter,
  MapPin,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  Layers,
  Sparkles,
} from "lucide-react";

export default function SodirRegistryExplorer({ stats, apiUrl }) {
  const [isOpen, setIsOpen] = useState(false);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedField, setSelectedField] = useState("VOLVE");
  const [wellbores, setWellbores] = useState([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(false);

  const endpointBase = (apiUrl || import.meta.env.VITE_API_URL || "/api").replace(/\/$/, "");

  useEffect(() => {
    if (!isOpen) return;

    let active = true;
    const fetchWellbores = async () => {
      setLoading(true);
      try {
        const params = new URLSearchParams();
        if (searchTerm.trim()) params.set("search", searchTerm.trim());
        if (selectedField && selectedField !== "ALL") params.set("field", selectedField);
        params.set("limit", "15");

        const res = await fetch(`${endpointBase}/sodir/wellbores?${params.toString()}`);
        if (!res.ok) throw new Error("Failed to fetch SODIR wellbores");
        const data = await res.json();
        if (active) {
          setWellbores(data.wellbores || []);
          setTotalCount(data.total || 0);
        }
      } catch (err) {
        console.error("SODIR fetch error:", err);
      } finally {
        if (active) setLoading(false);
      }
    };

    const debounce = setTimeout(fetchWellbores, 250);
    return () => {
      active = false;
      clearTimeout(debounce);
    };
  }, [isOpen, searchTerm, selectedField]);

  return (
    <section className="sodir-explorer-container glass-panel">
      {/* Header bar that toggles the explorer */}
      <div
        className="sodir-explorer-header"
        onClick={() => setIsOpen(!isOpen)}
        role="button"
        tabIndex={0}
      >
        <div className="sodir-header-left">
          <div className="sodir-icon-badge">
            <Globe size={18} className="text-cyan spin-slow" />
          </div>
          <div>
            <div className="sodir-eyebrow-row">
              <span className="sodir-eyebrow">OFFICIAL OPEN DATASET</span>
              <span className="sodir-live-tag">MapServer/201 · EPSG:4326</span>
            </div>
            <h3 className="sodir-title">
              Norwegian Offshore Directorate (SODIR) Wellbore Registry
            </h3>
          </div>
        </div>

        <div className="sodir-header-right">
          <div className="sodir-stat-chips">
            <span className="sodir-stat-chip">
              <Database size={13} />
              {stats?.total_wellbores ? `${stats.total_wellbores.toLocaleString()} Records` : "9,869 Records"}
            </span>
            <span className="sodir-stat-chip">
              <Layers size={13} />
              {stats?.unique_fields_count || 138} Fields
            </span>
            <span className="sodir-stat-chip highlight">
              <MapPin size={13} />
              {stats?.volve_field_wellbores_count || 27} Volve Wellbores
            </span>
          </div>

          <button className="sodir-toggle-btn" aria-label="Toggle SODIR Registry">
            {isOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
          </button>
        </div>
      </div>

      {/* Expanded Content Drawer */}
      {isOpen && (
        <div className="sodir-explorer-content">
          {/* Controls Bar */}
          <div className="sodir-controls-bar">
            <div className="sodir-search-box">
              <Search size={15} className="search-icon" />
              <input
                type="text"
                placeholder="Search wellbore name or well (e.g., 15/9-F-4, Troll)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
              {searchTerm && (
                <button className="clear-search-btn" onClick={() => setSearchTerm("")}>
                  ×
                </button>
              )}
            </div>

            <div className="sodir-field-pills">
              <span className="filter-label">
                <Filter size={12} /> Filter Field:
              </span>
              {["VOLVE", "ALL", "TROLL", "EKOFISK", "STATFJORD", "OSEBERG"].map((f) => (
                <button
                  key={f}
                  className={`field-filter-pill ${selectedField === f ? "active" : ""}`}
                  onClick={() => setSelectedField(f)}
                >
                  {f} {f === "VOLVE" && "(27)"}
                </button>
              ))}
            </div>
          </div>

          {/* Results Summary */}
          <div className="sodir-results-info">
            <span>
              Showing {wellbores.length} of {totalCount.toLocaleString()} matching wellbores
              {selectedField !== "ALL" && ` in ${selectedField} field`}
            </span>
            <span className="sodir-crs-info">Official EPSG:4326 WGS84 Coordinates</span>
          </div>

          {/* Table of Wellbores */}
          <div className="sodir-table-wrapper">
            <table className="sodir-table">
              <thead>
                <tr>
                  <th>Wellbore Name</th>
                  <th>Field</th>
                  <th>Drilling Operator</th>
                  <th>Total Depth</th>
                  <th>WGS84 Coordinates</th>
                  <th>Purpose</th>
                  <th>Status</th>
                  <th>Source</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={8} className="sodir-loading-cell">
                      <Sparkles size={16} className="spin text-cyan" /> Loading SODIR FactMaps records…
                    </td>
                  </tr>
                ) : wellbores.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="sodir-empty-cell">
                      No matching wellbores found for current filter criteria.
                    </td>
                  </tr>
                ) : (
                  wellbores.map((wb, idx) => (
                    <tr key={wb.object_id || idx} className="sodir-row">
                      <td className="wellbore-name-cell">
                        <strong>{wb.wellbore_name}</strong>
                        {wb.well && wb.well !== wb.wellbore_name && (
                          <span className="sub-well">{wb.well}</span>
                        )}
                      </td>
                      <td>
                        <span className="field-tag">{wb.field || "—"}</span>
                      </td>
                      <td className="operator-cell">{wb.operator || "—"}</td>
                      <td className="depth-cell">
                        {wb.total_depth != null ? `${Number(wb.total_depth).toLocaleString()} m` : "—"}
                      </td>
                      <td className="coords-cell">
                        {wb.latitude != null && wb.longitude != null ? (
                          <span className="coords-text">
                            {Number(wb.latitude).toFixed(4)}° N, {Number(wb.longitude).toFixed(4)}° E
                          </span>
                        ) : (
                          <span className="coords-missing">Unavailable</span>
                        )}
                      </td>
                      <td>
                        <span className="purpose-pill">{wb.purpose || "GENERAL"}</span>
                      </td>
                      <td>
                        <span className="status-pill">{wb.status || "COMPLETED"}</span>
                      </td>
                      <td>
                        <span className="sodir-source-pill">FactMaps</span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </section>
  );
}
