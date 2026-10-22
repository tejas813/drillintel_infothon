from pathlib import Path
import csv
import xml.etree.ElementTree as ET


BASE_DIR = Path("data/external/volve-drilling/witsml")
OUTPUT_FILE = Path("data/processed/well_locations.csv")


def local_name(tag):
    return tag.split("}")[-1]


def text_of(parent, name):
    for elem in parent.iter():
        if local_name(elem.tag).lower() == name.lower():
            text = (elem.text or "").strip()
            if text:
                return text
    return None


def parse_well_info(xml_file):
    root = ET.parse(xml_file).getroot()

    well_name = None
    latitude = None
    longitude = None

    # Find the well object
    for elem in root.iter():
        if local_name(elem.tag) == "well":
            well_name = text_of(elem, "name")
            break

    # Find wellLocation
    for elem in root.iter():
        if local_name(elem.tag) == "wellLocation":
            latitude = text_of(elem, "latitude")
            longitude = text_of(elem, "longitude")
            break

    return {
        "well_id": well_name or xml_file.parent.parent.parent.name,
        "latitude": latitude,
        "longitude": longitude,
        "source_file": str(xml_file),
    }


def main():
    files = sorted(BASE_DIR.rglob("_wellInfo/*.xml"))

    print(f"Well info files found: {len(files)}")

    results = []

    for file in files:
        try:
            result = parse_well_info(file)
            results.append(result)

            print(
                f"{result['well_id']} | "
                f"lat={result['latitude']} | "
                f"lon={result['longitude']}"
            )

        except Exception as exc:
            print(f"ERROR: {file} -> {exc}")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    fieldnames = [
        "well_id",
        "latitude",
        "longitude",
        "source_file",
    ]

    with OUTPUT_FILE.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)

    print()
    print(f"Saved: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
