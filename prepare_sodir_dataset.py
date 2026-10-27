#!/usr/bin/env python3
"""
Download the live SODIR/FactMaps wellbore point layer and export:
  - sodir_wellbores.csv
  - sodir_wellbores.geojson

This uses the official ArcGIS REST API, pages through the complete layer, asks
for WGS84 (EPSG:4326) geometry, preserves source attributes, and does NOT
classify wellbores as drilling incidents.

Run:
    python -m pip install requests
    python prepare_sodir_dataset.py
"""
from __future__ import annotations

import csv
import json
import sys
import time
from pathlib import Path

import requests

LAYER_URL = (
    "https://factmaps.sodir.no/api/rest/services/"
    "Factmaps/FactMapsWGS84/MapServer/201"
)
QUERY_URL = f"{LAYER_URL}/query"
BASE_DIR = Path(__file__).resolve().parent
OUT_DIR = BASE_DIR / "output"
PROCESSED_DIR = BASE_DIR / "data" / "processed"
CSV_PATH = OUT_DIR / "sodir_wellbores.csv"
GEOJSON_PATH = OUT_DIR / "sodir_wellbores.geojson"
PAGE_SIZE = 1000
TIMEOUT = 90


def request_json(session: requests.Session, params: dict) -> dict:
    response = session.get(QUERY_URL, params=params, timeout=TIMEOUT)
    response.raise_for_status()
    payload = response.json()
    if "error" in payload:
        raise RuntimeError(f"SODIR API error: {payload['error']}")
    return payload


def main() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    session = requests.Session()
    session.headers.update({"User-Agent": "DrillIntel SODIR open-data export/1.0"})

    # Count records first so the export can verify pagination completeness.
    info = request_json(session, {
        "where": "1=1",
        "returnCountOnly": "true",
        "f": "json",
    })
    expected = int(info.get("count", 0))
    if expected <= 0:
        raise RuntimeError(f"API returned an unexpected feature count: {info}")

    print(f"Official SODIR layer reports {expected:,} wellbore records.")
    features = []
    offset = 0
    while offset < expected:
        payload = request_json(session, {
            "where": "1=1",
            "outFields": "*",
            "returnGeometry": "true",
            "outSR": "4326",
            "f": "geojson",
            "resultOffset": offset,
            "resultRecordCount": PAGE_SIZE,
            "orderByFields": "OBJECTID",
        })
        batch = payload.get("features", [])
        if not batch:
            # Fallback: some ArcGIS layers ignore resultOffset. Try standard JSON
            # pagination with object IDs if GeoJSON pagination returned no rows.
            id_payload = request_json(session, {
                "where": "1=1",
                "returnIdsOnly": "true",
                "f": "json",
            })
            ids = id_payload.get("objectIds", [])
            if not ids:
                raise RuntimeError(f"No features returned at offset {offset}.")
            wanted = ids[offset:offset + PAGE_SIZE]
            if not wanted:
                break
            fallback = request_json(session, {
                "objectIds": ",".join(map(str, wanted)),
                "outFields": "*",
                "returnGeometry": "true",
                "outSR": "4326",
                "f": "geojson",
            })
            batch = fallback.get("features", [])
        if not batch:
            raise RuntimeError(f"Pagination stopped early at {offset} of {expected}.")
        features.extend(batch)
        offset += len(batch)
        print(f"Retrieved {len(features):,} / {expected:,}")
        if len(batch) < PAGE_SIZE and len(features) < expected:
            # Offset-based pagination may return a short final page.
            time.sleep(0.1)

    # De-duplicate by source OBJECTID if pagination fallback overlapped.
    unique = {}
    for feature in features:
        props = feature.get("properties") or {}
        oid = props.get("OBJECTID")
        key = str(oid) if oid is not None else json.dumps(feature, sort_keys=True)
        unique[key] = feature
    features = list(unique.values())
    if len(features) != expected:
        raise RuntimeError(
            f"Completeness check failed: expected {expected:,}, got {len(features):,}. "
            "No final exports written; retry later or check the official service."
        )

    # Ensure each GeoJSON feature has source attributes plus explicit coordinates.
    # GeoJSON point coordinate order is [longitude, latitude].
    all_fields = []
    seen = set()
    for feature in features:
        props = feature.get("properties") or {}
        for key in props:
            if key not in seen:
                seen.add(key)
                all_fields.append(key)

    for feature in features:
        props = feature.setdefault("properties", {})
        geom = feature.get("geometry")
        lon = lat = None
        if geom and geom.get("type") == "Point" and geom.get("coordinates"):
            coords = geom["coordinates"]
            if len(coords) >= 2:
                lon, lat = coords[0], coords[1]
        # Keep all original properties; append explicit WGS84 coordinate columns.
        props["longitude"] = lon
        props["latitude"] = lat
        props["record_type"] = "wellbore"
        props["source"] = "Norwegian Offshore Directorate (SODIR) FactMaps"
        props["source_layer"] = "Wellbores, all (MapServer layer 201)"
        props["source_url"] = LAYER_URL
        props["event_type"] = "unknown"  # neutral placeholder, not an incident classification

    for key in ("longitude", "latitude", "record_type", "source", "source_layer", "source_url", "event_type"):
        if key not in seen:
            all_fields.append(key)

    geojson = {
        "type": "FeatureCollection",
        "name": "sodir_wellbores",
        "source": "Norwegian Offshore Directorate (SODIR) FactMaps",
        "source_url": LAYER_URL,
        "crs": {"type": "name", "properties": {"name": "urn:ogc:def:crs:OGC:1.3:CRS84"}},
        "features": features,
    }

    # Write temporary files first, so incomplete downloads cannot masquerade as exports.
    tmp_geo = GEOJSON_PATH.with_suffix(".geojson.tmp")
    tmp_csv = CSV_PATH.with_suffix(".csv.tmp")
    tmp_geo.write_text(json.dumps(geojson, ensure_ascii=False, indent=2), encoding="utf-8")

    with tmp_csv.open("w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields, extrasaction="ignore")
        writer.writeheader()
        for feature in features:
            props = dict(feature.get("properties") or {})
            # Keep coordinates as explicit columns; geometry remains in GeoJSON.
            writer.writerow({k: props.get(k) for k in all_fields})

    tmp_geo.replace(GEOJSON_PATH)
    tmp_csv.replace(CSV_PATH)

    # Also sync copy to data/processed for immediate consumption by DrillIntel backend
    processed_csv = PROCESSED_DIR / "sodir_wellbores.csv"
    processed_geo = PROCESSED_DIR / "sodir_wellbores.geojson"
    import shutil
    shutil.copy2(CSV_PATH, processed_csv)
    shutil.copy2(GEOJSON_PATH, processed_geo)

    print("\nExport complete:")
    print(f"  Records: {len(features):,}")
    print(f"  CSV:     {CSV_PATH} and {processed_csv}")
    print(f"  GeoJSON: {GEOJSON_PATH} and {processed_geo}")
    print("Source attributes are preserved. Geometry is WGS84; GeoJSON points use [longitude, latitude].")
    print("Records are wellbore metadata, not drilling incidents.")


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
