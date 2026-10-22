from pathlib import Path
import csv
from collections import defaultdict


INPUT_FILE = Path("data/processed/well_trajectories.csv")
OUTPUT_FILE = Path("data/processed/well_inventory.csv")


def to_float(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def main():
    wells = defaultdict(list)

    with INPUT_FILE.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            wells[row["well_id"]].append(row)

    inventory = []

    for well_id, rows in wells.items():
        md_values = [
            to_float(r["md"])
            for r in rows
            if to_float(r["md"]) is not None
        ]

        tvd_values = [
            to_float(r["tvd"])
            for r in rows
            if to_float(r["tvd"]) is not None
        ]

        inclination_values = [
            to_float(r["inclination"])
            for r in rows
            if to_float(r["inclination"]) is not None
        ]

        azimuth_values = [
            to_float(r["azimuth"])
            for r in rows
            if to_float(r["azimuth"]) is not None
        ]

        inventory.append({
            "well_id": well_id,
            "trajectory_stations": len(rows),
            "max_md": max(md_values) if md_values else None,
            "max_tvd": max(tvd_values) if tvd_values else None,
            "max_inclination": max(inclination_values)
            if inclination_values else None,
            "max_azimuth": max(azimuth_values)
            if azimuth_values else None,
        })

    fieldnames = [
        "well_id",
        "trajectory_stations",
        "max_md",
        "max_tvd",
        "max_inclination",
        "max_azimuth",
    ]

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(inventory)

    print(f"Wells found: {len(inventory)}")
    print(f"Output: {OUTPUT_FILE}")

    for well in inventory:
        print(
            f"{well['well_id']} | "
            f"stations={well['trajectory_stations']} | "
            f"max MD={well['max_md']} | "
            f"max TVD={well['max_tvd']}"
        )


if __name__ == "__main__":
    main()
