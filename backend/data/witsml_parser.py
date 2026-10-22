from pathlib import Path
import csv
import xml.etree.ElementTree as ET

BASE_DIR = Path("data/external/volve-drilling/witsml")
OUTPUT_FILE = Path("data/processed/well_trajectories.csv")


def local_name(tag):
    return tag.split("}")[-1]


def get_text(element, name):
    for child in element.iter():
        if local_name(child.tag) == name:
            value = (child.text or "").strip()
            if value:
                return value
    return None


def get_well_id(xml_file):
    # .../WELL_NAME/trajectory/1.xml
    well_dir = xml_file.parent.parent.parent
    return well_dir.name


def parse_trajectory(xml_file):
    root = ET.parse(xml_file).getroot()
    well_id = get_well_id(xml_file)

    rows = []

    for station in root.iter():
        if local_name(station.tag) != "trajectoryStation":
            continue

        rows.append({
            "well_id": well_id,
            "source_file": str(xml_file),
            "md": get_text(station, "md"),
            "tvd": get_text(station, "tvd"),
            "inclination": get_text(station, "incl"),
            "azimuth": get_text(station, "azi"),
            "dls": get_text(station, "dls"),
            "timestamp": get_text(station, "dtmTrajStation"),
        })

    return rows


def main():
    files = sorted(BASE_DIR.rglob("trajectory/*.xml"))

    print(f"Trajectory files found: {len(files)}")

    all_rows = []

    for file in files:
        rows = parse_trajectory(file)

        print(
            f"{get_well_id(file)} -> "
            f"{len(rows)} trajectory stations"
        )

        all_rows.extend(rows)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fields = [
        "well_id",
        "source_file",
        "md",
        "tvd",
        "inclination",
        "azimuth",
        "dls",
        "timestamp",
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(all_rows)

    print(f"\nTotal stations: {len(all_rows)}")
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
