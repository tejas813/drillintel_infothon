from __future__ import annotations

from pathlib import Path
import math
import pandas as pd
from typing import Optional, Dict, Any, List

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "output"

SODIR_CSV = PROCESSED_DIR / "sodir_wellbores.csv"
if not SODIR_CSV.exists():
    SODIR_CSV = OUTPUT_DIR / "sodir_wellbores.csv"

_DF_CACHE: Optional[pd.DataFrame] = None


def get_sodir_df() -> pd.DataFrame:
    global _DF_CACHE
    if _DF_CACHE is not None:
        return _DF_CACHE

    if not SODIR_CSV.exists():
        raise FileNotFoundError(f"SODIR dataset not found at {SODIR_CSV}")

    df = pd.read_csv(SODIR_CSV, low_memory=False)
    # Ensure string types for common query columns to avoid nan issues
    for col in ["wlbWellboreName", "wlbWell", "wlbField", "wlbDrillingOperator", "wlbPurpose", "wlbStatus", "wlbContent"]:
        if col in df.columns:
            df[col] = df[col].fillna("").astype(str)

    _DF_CACHE = df
    return _DF_CACHE


def get_sodir_stats() -> Dict[str, Any]:
    df = get_sodir_df()

    total_records = len(df)
    valid_coords = int(df[["latitude", "longitude"]].dropna().shape[0]) if "latitude" in df.columns and "longitude" in df.columns else 0

    fields = [f for f in df["wlbField"].dropna().unique() if f.strip()]
    operators = [o for o in df["wlbDrillingOperator"].dropna().unique() if o.strip()]

    # Top fields
    top_fields = df[df["wlbField"] != ""]["wlbField"].value_counts().head(10).to_dict()
    # Top operators
    top_operators = df[df["wlbDrillingOperator"] != ""]["wlbDrillingOperator"].value_counts().head(10).to_dict()

    min_depth = float(df["wlbTotalDepth"].dropna().min()) if "wlbTotalDepth" in df.columns and not df["wlbTotalDepth"].dropna().empty else None
    max_depth = float(df["wlbTotalDepth"].dropna().max()) if "wlbTotalDepth" in df.columns and not df["wlbTotalDepth"].dropna().empty else None

    # Count Volve wells
    volve_count = int((df["wlbField"].str.upper() == "VOLVE").sum())

    return {
        "dataset_name": "Norwegian Offshore Directorate (SODIR) FactMaps Wellbores Layer",
        "source": "Factmaps/FactMapsWGS84/MapServer/201",
        "total_wellbores": total_records,
        "valid_coordinates_count": valid_coords,
        "unique_fields_count": len(fields),
        "unique_operators_count": len(operators),
        "min_depth_m": min_depth,
        "max_depth_m": max_depth,
        "top_fields": top_fields,
        "top_operators": top_operators,
        "volve_field_wellbores_count": volve_count,
        "is_incident_dataset": False,
        "description": "Official open-data point layer of all exploration and production wellbores on the Norwegian Continental Shelf.",
    }


import numpy as np

def clean_val(val: Any) -> Any:
    if val is None:
        return None
    try:
        if pd.isna(val):
            return None
    except Exception:
        pass
    if isinstance(val, (np.integer, int)):
        return int(val)
    if isinstance(val, (np.floating, float)):
        if math.isnan(val) or math.isinf(val):
            return None
        return float(val)
    if isinstance(val, np.generic):
        return val.item()
    return val


def format_wellbore_item(row: pd.Series) -> Dict[str, Any]:
    return {
        "object_id": clean_val(row.get("OBJECTID")),
        "wellbore_name": str(row.get("wlbWellboreName", "")).strip(),
        "well": str(row.get("wlbWell", "")).strip(),
        "field": str(row.get("wlbField", "")).strip() or None,
        "operator": str(row.get("wlbDrillingOperator", "")).strip() or None,
        "total_depth": clean_val(row.get("wlbTotalDepth")),
        "water_depth": clean_val(row.get("wlbWaterDepth")),
        "final_vertical_depth": clean_val(row.get("wlbFinalVerticalDepth")),
        "max_inclination": clean_val(row.get("wlbMaxInclation")),
        "purpose": str(row.get("wlbPurpose", "")).strip() or None,
        "status": str(row.get("wlbStatus", "")).strip() or None,
        "content": str(row.get("wlbContent", "")).strip() or None,
        "well_type": str(row.get("wlbWellType", "")).strip() or None,
        "latitude": clean_val(row.get("latitude")),
        "longitude": clean_val(row.get("longitude")),
        "entry_date": clean_val(row.get("wlbEntryDate")),
        "completion_date": clean_val(row.get("wlbCompletionDate")),
        "main_area": str(row.get("wlbMainArea", "")).strip() or None,
        "drilling_facility": str(row.get("wlbDrillingFacility", "")).strip() or None,
        "fact_page_url": str(row.get("cmpFactPageUrl", "")).strip() or None,
        "record_type": "wellbore",
        "source": "Norwegian Offshore Directorate (SODIR) FactMaps",
    }


def search_sodir_wellbores(
    search: Optional[str] = None,
    field: Optional[str] = None,
    operator: Optional[str] = None,
    purpose: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> Dict[str, Any]:
    df = get_sodir_df()
    filtered = df

    if search:
        s = search.strip().lower()
        filtered = filtered[
            filtered["wlbWellboreName"].str.lower().str.contains(s, na=False)
            | filtered["wlbWell"].str.lower().str.contains(s, na=False)
        ]

    if field:
        f = field.strip().lower()
        filtered = filtered[filtered["wlbField"].str.lower() == f]

    if operator:
        o = operator.strip().lower()
        filtered = filtered[filtered["wlbDrillingOperator"].str.lower().str.contains(o, na=False)]

    if purpose:
        p = purpose.strip().lower()
        filtered = filtered[filtered["wlbPurpose"].str.lower() == p]

    total_matched = len(filtered)
    limit = max(1, min(limit, 500))
    offset = max(0, offset)

    sliced = filtered.iloc[offset : offset + limit]
    items = [format_wellbore_item(row) for _, row in sliced.iterrows()]

    return {
        "total": total_matched,
        "limit": limit,
        "offset": offset,
        "returned": len(items),
        "wellbores": items,
    }


def get_sodir_wellbore(wellbore_name: str) -> Optional[Dict[str, Any]]:
    df = get_sodir_df()
    target = wellbore_name.strip().lower()

    # Exact match on wlbWellboreName
    matches = df[df["wlbWellboreName"].str.lower() == target]
    if matches.empty:
        # Match normalized
        from backend.data.well_locations import normalize_well_name
        norm = normalize_well_name(wellbore_name).lower()
        matches = df[df["wlbWellboreName"].str.lower() == norm]

    if matches.empty:
        matches = df[df["wlbWellboreName"].str.lower().str.contains(target, na=False)]

    if matches.empty:
        return None

    return format_wellbore_item(matches.iloc[0])
