import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from backend.main import app
from backend.data.sodir_service import (
    get_sodir_stats,
    search_sodir_wellbores,
    get_sodir_wellbore,
)
from backend.data.well_locations import normalize_well_name, lookup_sodir_well
from backend.offset.spatial import spatial_similarity, haversine_distance_km

BASE_DIR = Path(__file__).resolve().parents[2]


class TestSodirDatasetIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_01_dataset_files_exist(self):
        csv_path = BASE_DIR / "data" / "processed" / "sodir_wellbores.csv"
        geo_path = BASE_DIR / "data" / "processed" / "sodir_wellbores.geojson"
        out_csv = BASE_DIR / "output" / "sodir_wellbores.csv"
        out_geo = BASE_DIR / "output" / "sodir_wellbores.geojson"

        self.assertTrue(csv_path.exists() or out_csv.exists(), "sodir_wellbores.csv should exist")
        self.assertTrue(geo_path.exists() or out_geo.exists(), "sodir_wellbores.geojson should exist")

    def test_02_sodir_stats(self):
        stats = get_sodir_stats()
        self.assertGreaterEqual(stats["total_wellbores"], 9800)
        self.assertGreaterEqual(stats["valid_coordinates_count"], 9700)
        self.assertGreaterEqual(stats["unique_fields_count"], 100)
        self.assertGreaterEqual(stats["unique_operators_count"], 50)
        self.assertEqual(stats["volve_field_wellbores_count"], 27)
        self.assertFalse(stats["is_incident_dataset"])

    def test_03_well_name_normalization(self):
        self.assertEqual(normalize_well_name("Norway-Statoil-NO 15_$47$_9-F-4"), "15/9-F-4")
        self.assertEqual(normalize_well_name("Norway-Statoil-NO 15_$47$_9-F-7"), "15/9-F-7")
        self.assertEqual(normalize_well_name("Norway-Statoil-NO 15_$47$_9-F-9"), "15/9-F-9")
        self.assertEqual(normalize_well_name("NO 15/9-F-4"), "15/9-F-4")

    def test_04_lookup_sodir_wellbore(self):
        wb4 = get_sodir_wellbore("15/9-F-4")
        self.assertIsNotNone(wb4)
        self.assertEqual(wb4["wellbore_name"], "15/9-F-4")
        self.assertEqual(wb4["field"], "VOLVE")
        self.assertAlmostEqual(float(wb4["latitude"]), 58.44098, places=3)
        self.assertAlmostEqual(float(wb4["longitude"]), 1.88588, places=3)
        self.assertEqual(wb4["record_type"], "wellbore")

        wb7 = get_sodir_wellbore("Norway-Statoil-NO 15_$47$_9-F-7")
        self.assertIsNotNone(wb7)
        self.assertEqual(wb7["wellbore_name"], "15/9-F-7")
        self.assertEqual(wb7["field"], "VOLVE")

    def test_05_spatial_distance_between_platform_wells(self):
        wb4 = get_sodir_wellbore("15/9-F-4")
        wb7 = get_sodir_wellbore("15/9-F-7")

        res = spatial_similarity(
            wb4["latitude"],
            wb4["longitude"],
            wb7["latitude"],
            wb7["longitude"],
        )
        self.assertTrue(res["available"])
        self.assertIsNotNone(res["distance_km"])
        # Platform wells are within 50 meters (0.05 km)
        self.assertLess(res["distance_km"], 0.1)
        self.assertGreater(res["score"], 0.9)

    def test_06_api_sodir_stats(self):
        res = self.client.get("/sodir/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("total_wellbores", data)
        self.assertGreaterEqual(data["total_wellbores"], 9800)
        self.assertEqual(data["volve_field_wellbores_count"], 27)

    def test_07_api_sodir_search(self):
        res = self.client.get("/sodir/wellbores?field=VOLVE&limit=10")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["total"], 27)
        self.assertEqual(len(data["wellbores"]), 10)
        names = [w["wellbore_name"] for w in data["wellbores"]]
        self.assertTrue(any("15/9" in n for n in names))

    def test_08_api_sodir_single_wellbore(self):
        res = self.client.get("/sodir/wellbores/15/9-F-4")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["wellbore_name"], "15/9-F-4")
        self.assertEqual(data["field"], "VOLVE")
        self.assertIn("latitude", data)
        self.assertIn("longitude", data)

    def test_09_api_analyze_sodir_enrichment(self):
        target_id = "Norway-Statoil-NO 15_$47$_9-F-4"
        res = self.client.post("/analyze", json={"well_id": target_id})
        self.assertEqual(res.status_code, 200)
        data = res.json()

        # Check SODIR metadata attached
        self.assertTrue(data.get("sodir_verified"))
        self.assertIn("sodir_metadata", data)
        sodir_meta = data["sodir_metadata"]
        self.assertIsNotNone(sodir_meta)
        self.assertEqual(sodir_meta["wellbore_name"], "15/9-F-4")
        self.assertEqual(sodir_meta["field"], "VOLVE")
        self.assertAlmostEqual(float(sodir_meta["latitude"]), 58.44098, places=3)
        self.assertAlmostEqual(float(sodir_meta["longitude"]), 1.88588, places=3)

        # Check offset wells include spatial scores
        offsets = data.get("offset_wells", [])
        self.assertGreater(len(offsets), 0)
        for off in offsets:
            self.assertIn("spatial_score", off)
            self.assertIn("distance_km", off)
            self.assertIn("master_score", off)
            self.assertIn("sodir_name", off)
            self.assertIsNotNone(off["spatial_score"])
            self.assertIsNotNone(off["distance_km"])
            self.assertLess(off["distance_km"], 0.5)


if __name__ == "__main__":
    unittest.main()
