from pathlib import Path
import csv
import math


BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data" / "processed"

INVENTORY_FILE = DATA_DIR / "well_inventory.csv"
TRAJECTORY_FILE = DATA_DIR / "well_trajectories.csv"


def load_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def normalize(value, min_value, max_value):
    if max_value == min_value:
        return 1.0

    return (value - min_value) / (max_value - min_value)


def trajectory_similarity(target, candidate):
    """
    Compare two wells using trajectory characteristics.
    Returns a score between 0 and 1.
    """

    target_md = float(target["max_md"])
    candidate_md = float(candidate["max_md"])

    target_inc = float(target["max_inclination"])
    candidate_inc = float(candidate["max_inclination"])

    target_azi = float(target["max_azimuth"])
    candidate_azi = float(candidate["max_azimuth"])

    # Depth similarity
    depth_difference = abs(target_md - candidate_md)
    depth_similarity = math.exp(-depth_difference / max(target_md, 1))

    # Inclination similarity
    inc_difference = abs(target_inc - candidate_inc)
    inclination_similarity = math.exp(-inc_difference)

    # Azimuth is circular: 0° and 360° are close
    azi_difference = abs(target_azi - candidate_azi)
    azi_difference = min(azi_difference, 360 - azi_difference)

    azimuth_similarity = math.exp(-azi_difference / 45.0)

    # Weighted score
    score = (
        0.50 * depth_similarity
        + 0.30 * inclination_similarity
        + 0.20 * azimuth_similarity
    )

    return round(score, 4)


def rank_offsets(target_well_id, top_k=5):
    inventory = load_csv(INVENTORY_FILE)

    target = None
    candidates = []

    for well in inventory:
        if well["well_id"] == target_well_id:
            target = well
        else:
            candidates.append(well)

    if target is None:
        raise ValueError(f"Target well not found: {target_well_id}")

    results = []

    for candidate in candidates:

        score = trajectory_similarity(target, candidate)

        results.append({
            "target_well": target_well_id,
            "offset_well": candidate["well_id"],
            "similarity_score": score,
            "target_md": float(target["max_md"]),
            "offset_md": float(candidate["max_md"]),
            "target_inclination": float(target["max_inclination"]),
            "offset_inclination": float(candidate["max_inclination"]),
            "target_azimuth": float(target["max_azimuth"]),
            "offset_azimuth": float(candidate["max_azimuth"]),
        })

    results.sort(
        key=lambda x: x["similarity_score"],
        reverse=True
    )

    return results[:top_k]


def main():

    inventory = load_csv(INVENTORY_FILE)

    if not inventory:
        raise RuntimeError("No well inventory found.")

    print("\n=== eRTMAC-NWIS Offset Well Ranking ===\n")

    # Use first well as demonstration target
    target_well = inventory[0]["well_id"]

    print(f"Target Well: {target_well}\n")

    results = rank_offsets(target_well)

    if not results:
        print("No offset wells available.")
        return

    print("Rank | Offset Well | Similarity")
    print("-" * 60)

    for rank, result in enumerate(results, start=1):

        print(
            f"{rank:>4} | "
            f"{result['offset_well']} | "
            f"{result['similarity_score']:.4f}"
        )


if __name__ == "__main__":
    main()
