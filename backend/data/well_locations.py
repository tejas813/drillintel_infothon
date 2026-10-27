from pathlib import Path
import csv
import re
import xml.etree.ElementTree as ET

BASE_DIR = Path(__file__).resolve().parents[2]
PROCESSED_DIR = BASE_DIR / "data" / "processed"
OUTPUT_DIR = BASE_DIR / "output"
OUTPUT_FILE = PROCESSED_DIR / "well_locations.csv"
TRAJECTORY_FILE = PROCESSED_DIR / "well_trajectories.csv"
INVENTORY_FILE = PROCESSED_DIR / "well_inventory.csv"
WITSML_DIR = BASE_DIR / "data" / "external" / "volve-drilling" / "witsml"

SODIR_CSV = PROCESSED_DIR / "sodir_wellbores.csv"
if not SODIR_CSV.exists():
    SODIR_CSV = OUTPUT_DIR / "sodir_wellbores.csv"


def normalize_well_name(raw_name: str) -> str:
    """
    Normalize well name or ID into standard SODIR naming convention.
    Examples:
        'Norway-Statoil-NO 15_$47$_9-F-4' -> '15/9-F-4'
        'NO 15/9-F-4' -> '15/9-F-4'
        '15/9-F-4' -> '15/9-F-4'
    """
    if not raw_name:
        return ""
    s = str(raw_name).strip()
    s = s.replace("_$47$_", "/").replace("$47$", "/")
    m = re.search(r"(\d+/\d+-[A-Za-z0-9\-]+(?:\s+[A-Za-z0-9]+)?)", s)
    if m:
        return m.group(1).strip()
    return s


def load_sodir_records() -> dict:
    """
    Load SODIR wellbores keyed by normalized wellbore name, uppercase.
    """
    records = {}
    if not SODIR_CSV.exists():
        return records

    with SODIR_CSV.open("r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        for row in reader:
            wlb_name = row.get("wlbWellboreName") or ""
            clean_name = normalize_well_name(wlb_name).upper()
            if clean_name:
                records[clean_name] = row
            well_name = row.get("wlbWell") or ""
            clean_well = normalize_well_name(well_name).upper()
            if clean_well and clean_well not in records:
                records[clean_well] = row

    return records


def lookup_sodir_well(well_id: str, sodir_records: dict = None) -> dict | None:
    """
    Look up official SODIR record for a given well ID.
    """
    if sodir_records is None:
        sodir_records = load_sodir_records()

    norm = normalize_well_name(well_id).upper()
    if norm in sodir_records:
        return sodir_records[norm]

    # Substring search fallback
    for name, record in sodir_records.items():
        if norm in name or name in norm:
            return record

    return None


def main():
    sodir_records = load_sodir_records()
    print(f"Loaded {len(sodir_records):,} SODIR registry entries.")

    target_wells = set()

    # 1. From trajectories
    if TRAJECTORY_FILE.exists():
        with TRAJECTORY_FILE.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                w = row.get("well_id", "").strip()
                if w:
                    target_wells.add(w)

    # 2. From inventory
    if INVENTORY_FILE.exists():
        with INVENTORY_FILE.open("r", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                w = row.get("well_id", "").strip()
                if w:
                    target_wells.add(w)

    # 3. From WITSML XMLs if present
    if WITSML_DIR.exists():
        files = sorted(WITSML_DIR.rglob("_wellInfo/*.xml"))
        for file in files:
            try:
                root = ET.parse(file).getroot()
                for elem in root.iter():
                    tag = elem.tag.split("}")[-1].lower()
                    if tag == "well":
                        for child in elem:
                            if child.tag.split("}")[-1].lower() == "name" and child.text:
                                target_wells.add(child.text.strip())
            except Exception:
                pass

    print(f"Project wells to resolve: {len(target_wells)}")

    results = []
    for well_id in sorted(target_wells):
        norm = normalize_well_name(well_id)
        sodir = lookup_sodir_well(well_id, sodir_records)

        lat = sodir.get("latitude") if sodir else None
        lon = sodir.get("longitude") if sodir else None
        field = sodir.get("wlbField") if sodir else "VOLVE"
        operator = sodir.get("wlbDrillingOperator") if sodir else "Equinor"
        total_depth = sodir.get("wlbTotalDepth") if sodir else None
        sodir_name = sodir.get("wlbWellboreName") if sodir else norm
        purpose = sodir.get("wlbPurpose") if sodir else None
        status = sodir.get("wlbStatus") if sodir else None

        results.append({
            "well_id": well_id,
            "normalized_name": norm,
            "sodir_wellbore_name": sodir_name,
            "latitude": lat,
            "longitude": lon,
            "field": field,
            "operator": operator,
            "total_depth": total_depth,
            "purpose": purpose,
            "status": status,
            "source": "Norwegian Offshore Directorate (SODIR) FactMaps" if sodir else "WITSML",
        })

        print(
            f"  {well_id} -> {sodir_name} | "
            f"lat={lat} | lon={lon} | "
            f"field={field} | depth={total_depth}"
        )

    # Also add standard Volve well entries for easy lookup
    for well_name in ["15/9-F-4", "15/9-F-7", "15/9-F-9"]:
        if not any(r["well_id"] == well_name for r in results):
            sodir = lookup_sodir_well(well_name, sodir_records)
            if sodir:
                results.append({
                    "well_id": well_name,
                    "normalized_name": well_name,
                    "sodir_wellbore_name": sodir.get("wlbWellboreName"),
                    "latitude": sodir.get("latitude"),
                    "longitude": sodir.get("longitude"),
                    "field": sodir.get("wlbField"),
                    "operator": sodir.get("wlbDrillingOperator"),
                    "total_depth": sodir.get("wlbTotalDepth"),
                    "purpose": sodir.get("wlbPurpose"),
                    "status": sodir.get("wlbStatus"),
                    "source": "Norwegian Offshore Directorate (SODIR) FactMaps",
                })

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "well_id",
        "normalized_name",
        "sodir_wellbore_name",
        "latitude",
        "longitude",
        "field",
        "operator",
        "total_depth",
        "purpose",
        "status",
        "source",
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"Saved: {OUTPUT_FILE} ({len(results)} records with real coordinates)")


if __name__ == "__main__":
    main()
