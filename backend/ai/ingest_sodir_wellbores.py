"""
Ingest the Norwegian Offshore Directorate wellbore-point shapefile into a SEPARATE
FAISS collection. This does not overwrite events_index.faiss or events_metadata.json.

Run from repository root:
    python backend/ai/ingest_sodir_wellbores.py

Dependencies (install into the same environment as DrillIntel):
    pip install geopandas sentence-transformers faiss-cpu pandas numpy
"""
from __future__ import annotations

import json
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

import faiss
import geopandas as gpd
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parents[2]
SOURCE_URL = "https://factpages.sodir.no/downloads/shape/wlbPoint.zip"
DATA_DIR = BASE_DIR / "data" / "external" / "sodir_wellbores"
RAG_DIR = BASE_DIR / "data" / "processed" / "rag"
ZIP_FILE = DATA_DIR / "wlbPoint.zip"
EXTRACT_DIR = DATA_DIR / "shapefile"
CSV_FILE = DATA_DIR / "sodir_wellbores.csv"
METADATA_FILE = RAG_DIR / "wellbores_metadata.json"
INDEX_FILE = RAG_DIR / "wellbores_index.faiss"
MODEL_NAME = "all-MiniLM-L6-v2"


def download_zip() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    request = Request(SOURCE_URL, headers={"User-Agent": "DrillIntel dataset ingestion"})
    with urlopen(request, timeout=120) as response, ZIP_FILE.open("wb") as target:
        shutil.copyfileobj(response, target)
    if not zipfile.is_zipfile(ZIP_FILE):
        ZIP_FILE.unlink(missing_ok=True)
        raise RuntimeError("The download was not a valid ZIP file; no index was changed.")


def extract_shapefile() -> Path:
    EXTRACT_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(ZIP_FILE) as archive:
        archive.extractall(EXTRACT_DIR)
    candidates = list(EXTRACT_DIR.rglob("*.shp"))
    if not candidates:
        raise FileNotFoundError("No .shp file found in downloaded ZIP.")
    # Prefer the wellbore point layer by filename when possible.
    return next((p for p in candidates if "wlbpoint" in p.name.lower()), candidates[0])


def clean_value(value):
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "isoformat"):
        try:
            return value.isoformat()
        except Exception:
            pass
    if isinstance(value, np.generic):
        return value.item()
    return value


def main() -> None:
    print("Downloading official SODIR wellbore-point dataset...")
    download_zip()
    shp_path = extract_shapefile()
    print(f"Reading {shp_path.name}")
    gdf = gpd.read_file(shp_path)
    if gdf.empty:
        raise RuntimeError("The shapefile contains no records; existing RAG files were not changed.")

    # Preserve source attributes, and derive coordinates in WGS84 when possible.
    if gdf.crs is not None:
        try:
            geo = gdf.to_crs("EPSG:4326")
            gdf["longitude"] = geo.geometry.x
            gdf["latitude"] = geo.geometry.y
        except Exception:
            gdf["longitude"] = None
            gdf["latitude"] = None
    else:
        gdf["longitude"] = None
        gdf["latitude"] = None

    # CSV keeps all original attributes; geometry is represented as WKT.
    export = gdf.copy()
    export["geometry_wkt"] = export.geometry.to_wkt() if "geometry" in export else None
    if "geometry" in export.columns:
        export = export.drop(columns=["geometry"])
    export.to_csv(CSV_FILE, index=False)

    records = []
    for _, row in gdf.iterrows():
        attrs = {str(k): clean_value(v) for k, v in row.items() if k != gdf.geometry.name}
        geom = row.geometry
        if geom is not None and not geom.is_empty:
            attrs["longitude"] = clean_value(attrs.get("longitude"))
            attrs["latitude"] = clean_value(attrs.get("latitude"))
        # Identify records using the source's stable wellbore ID when present.
        id_key = next((k for k in attrs if k.lower() in {
            "wlbnpdidwellbore", "npdidwellbore", "wellbore_id", "objectid"
        }), None)
        name_key = next((k for k in attrs if k.lower() in {
            "wlbwellborename", "wlbname", "wellbore_name", "wellname"
        }), None)
        well_id = attrs.get(id_key) if id_key else None
        well_name = attrs.get(name_key) if name_key else None

        # Build search text from source attributes without inventing incident labels.
        useful = []
        for key, value in attrs.items():
            if value is not None and str(value).strip():
                useful.append(f"{key}: {value}")
        text = (
            "Source: Norwegian Offshore Directorate (SODIR) wellbore-point dataset. "
            f"Record type: wellbore metadata (not a drilling incident). "
            f"Wellbore ID: {well_id if well_id is not None else 'Unknown'}. "
            f"Wellbore name: {well_name if well_name is not None else 'Unknown'}. "
            + "Attributes: " + "; ".join(useful)
        )
        records.append({
            "record_type": "wellbore",
            "source": "Norwegian Offshore Directorate (SODIR) wlbPoint",
            "source_url": SOURCE_URL,
            "well_id": str(well_id) if well_id is not None else "Unknown",
            "well_name": str(well_name) if well_name is not None else "Unknown",
            "event_type": "unknown",
            "attributes": attrs,
            "text": text,
        })

    # Create a new independent index. Existing drilling-event files are untouched.
    RAG_DIR.mkdir(parents=True, exist_ok=True)
    model = SentenceTransformer(MODEL_NAME)
    texts = [r["text"] for r in records]
    vectors = np.asarray(
        model.encode(texts, convert_to_numpy=True, show_progress_bar=True),
        dtype=np.float32,
    )
    if vectors.ndim != 2 or len(vectors) != len(records):
        raise RuntimeError("Embedding count mismatch; no index written.")
    faiss.normalize_L2(vectors)
    index = faiss.IndexFlatIP(vectors.shape[1])
    index.add(vectors)

    # Write to temporary paths first, then atomically replace only the new collection.
    tmp_index = INDEX_FILE.with_suffix(".faiss.tmp")
    tmp_meta = METADATA_FILE.with_suffix(".json.tmp")
    faiss.write_index(index, str(tmp_index))
    payload = {
        "dataset": "SODIR wlbPoint",
        "source_url": SOURCE_URL,
        "ingested_at_utc": datetime.now(timezone.utc).isoformat(),
        "record_count": len(records),
        "embedding_model": MODEL_NAME,
        "records": records,
    }
    with tmp_meta.open("w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2, default=str)
    tmp_index.replace(INDEX_FILE)
    tmp_meta.replace(METADATA_FILE)

    print(f"Rows imported: {len(records):,}")
    print(f"CSV: {CSV_FILE}")
    print(f"Separate FAISS index: {INDEX_FILE}")
    print(f"Separate metadata: {METADATA_FILE}")
    print("Existing drilling-event FAISS index and metadata were not modified.")


if __name__ == "__main__":
    main()
