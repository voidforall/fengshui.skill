"""Regional maps: geometry, evidence, method separation and standalone generation."""

import copy
import importlib.util
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills/city-wuxing-map"
SPEC = importlib.util.spec_from_file_location("city_map_generator", SKILL / "scripts/generate.py")
generator = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(generator)


class TestCityMap(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((SKILL / "examples/london.json").read_text(encoding="utf-8"))

    def test_examples_cover_five_elements_with_regional_evidence(self):
        for slug, lat_range, lon_range in (
            ("london", (51.4, 51.7), (-0.4, 0.1)),
            ("new-york", (40.6, 40.9), (-74.1, -73.8)),
        ):
            with self.subTest(city=slug):
                data = json.loads((SKILL / "examples" / (slug + ".json")).read_text(encoding="utf-8"))
                generator.validate(data)
                self.assertEqual(set(generator.ELEMENTS), {
                    r["analyses"][r["preferred_method"]]["primary"] for r in data["regions"]})
                for region in data["regions"]:
                    self.assertEqual("解释性概化", region["boundary"]["kind"])
                    self.assertTrue(region["boundary"]["sources"])
                    for ring in region["geometry"]["coordinates"]:
                        for lon, lat in ring:
                            self.assertTrue(lat_range[0] <= lat <= lat_range[1])
                            self.assertTrue(lon_range[0] <= lon <= lon_range[1])

    def test_same_region_preserves_distinct_method_conclusions(self):
        region = next(r for r in self.data["regions"] if r["id"] == "canary-wharf")
        self.assertEqual("金", region["analyses"]["function"]["primary"])
        self.assertEqual("水", region["analyses"]["landscape"]["primary"])
        city = next(r for r in self.data["regions"] if r["id"] == "city-finance")
        self.assertNotIn("landscape", city["analyses"])

    def test_old_point_data_is_rejected_instead_of_fabricating_regions(self):
        with self.assertRaisesRegex(ValueError, "旧 places"):
            generator.validate({"city": "London", "places": [{"lat": 51.5, "lon": 0}]})

    def test_region_can_remain_unanalysed_without_an_invented_element(self):
        region = self.data["regions"][0]
        region["analyses"] = {}
        region["preferred_method"] = None
        generator.validate(self.data)
        self.assertIn('"analyses": {}', generator.render(self.data))

    def test_invalid_geometry_is_rejected(self):
        invalid = [
            {"type": "Point", "coordinates": [0, 51]},
            {"type": "Polygon", "coordinates": []},
            {"type": "MultiPolygon", "coordinates": []},
            {"type": "Polygon", "coordinates": [[[0, 51], [1, 51], [1, 52], [0, 52]]]},
            {"type": "Polygon", "coordinates": [[[0, 51], [1, 51], [2, 51], [0, 51]]]},
            {"type": "Polygon", "coordinates": [[[0, 91], [1, 51], [1, 52], [0, 91]]]},
            {"type": "Polygon", "coordinates": [[[float("nan"), 51], [1, 51], [1, 52], [0, 51]]]},
        ]
        for geometry in invalid:
            with self.subTest(geometry=geometry):
                self.data["regions"][0]["geometry"] = geometry
                with self.assertRaises(ValueError):
                    generator.validate(self.data)

    def test_multipolygon_and_holes_keep_geojson_coordinate_order(self):
        outer = [[0, 50], [2, 50], [2, 52], [0, 52], [0, 50]]
        hole = [[.5, 50.5], [.5, 51.5], [1.5, 51.5], [1.5, 50.5], [.5, 50.5]]
        self.data["regions"][0]["geometry"] = {"type": "MultiPolygon", "coordinates": [[outer, hole]]}
        generator.validate(self.data)
        result = generator.render(self.data)
        self.assertIn('"type": "MultiPolygon"', result)
        self.assertEqual([0, 50], self.data["regions"][0]["geometry"]["coordinates"][0][0][0])

    def test_analysis_and_boundary_require_traceable_evidence(self):
        for field, value in (("primary", "旺财"), ("secondary", ["水"]),
                             ("secondary", ["木", "木"]), ("facts", []),
                             ("sources", []), ("reason", ""), ("limitations", ""),
                             ("sources", [{"title": "bad", "url": "javascript:alert(1)"}])):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["regions"][0]["analyses"]["landscape"][field] = value
                with self.assertRaises(ValueError):
                    generator.validate(data)
        for change in (lambda r: r.update(preferred_method="function"),
                       lambda r: r["boundary"].update(sources=[]),
                       lambda r: r["boundary"].update(kind="能量精确边界")):
            data = copy.deepcopy(self.data)
            change(data["regions"][0])
            with self.assertRaises(ValueError):
                generator.validate(data)

    def test_duplicate_ids_and_empty_city_are_errors(self):
        self.data["regions"][1]["id"] = self.data["regions"][0]["id"]
        with self.assertRaises(ValueError):
            generator.validate(self.data)
        self.data["regions"] = self.data["regions"][:1]
        self.data["city"] = ""
        with self.assertRaises(ValueError):
            generator.validate(self.data)

    def test_data_cannot_escape_json_script_or_page_title(self):
        payload = '</script><script>alert("injected")</script>'
        self.data["city"] = payload
        self.data["regions"][0]["analyses"]["landscape"]["reason"] = payload
        result = generator.render(self.data)
        self.assertNotIn(payload, result)
        start = result.index('<script id="city-data" type="application/json">')
        content = result[start:].split('>', 1)[1].split('</script>', 1)[0]
        embedded = json.loads(content)
        self.assertEqual(payload, embedded["regions"][0]["analyses"]["landscape"]["reason"])
        self.assertEqual(payload, embedded["city"])

    def test_custom_city_runs_as_an_installed_standalone_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            installed = temp / "city-wuxing-map"
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns("__pycache__"))
            self.data["city"] = "测试城市"
            self.data["regions"] = self.data["regions"][:1]
            source, output = temp / "city.json", temp / "output/map.html"
            source.write_text(json.dumps(self.data), encoding="utf-8")
            result = subprocess.run([sys.executable, str(installed / "scripts/generate.py"),
                                     "--input", str(source), "--output", str(output)],
                                    cwd=temp, capture_output=True, text=True)
            self.assertEqual(0, result.returncode, result.stderr)
            rendered = output.read_text(encoding="utf-8")
            self.assertIn("测试城市", rendered)
            self.assertIn("Leaflet 1.9.4", rendered)
            self.assertIn("OpenStreetMap contributors", rendered)
            self.assertNotIn('src="https://unpkg.com', rendered)

    def test_cli_failure_does_not_write_output_or_overwrite_input(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "bad.json"
            output = Path(directory) / "map.html"
            source.write_text('{"city":"bad"}', encoding="utf-8")
            command = [sys.executable, str(SKILL / "scripts/generate.py"), "--input", str(source)]
            result = subprocess.run(command + ["--output", str(output)], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertFalse(output.exists())
            source.write_text(json.dumps(self.data), encoding="utf-8")
            original = source.read_bytes()
            result = subprocess.run(command + ["--output", str(source)], capture_output=True, text=True)
            self.assertEqual(2, result.returncode)
            self.assertEqual(original, source.read_bytes())

    def test_custom_basemap_requires_template_and_attribution(self):
        self.data["basemap"] = dict(generator.DEFAULT_BASEMAP, url="https://example.com/{z}/{x}/{y}.png")
        generator.validate(self.data)
        del self.data["basemap"]["attribution"]
        with self.assertRaises(ValueError):
            generator.validate(self.data)
        self.data["basemap"] = dict(generator.DEFAULT_BASEMAP, url="https://example.com/static.png")
        with self.assertRaises(ValueError):
            generator.validate(self.data)

    def test_committed_maps_match_current_template_and_data(self):
        for slug in ("london", "new-york"):
            with self.subTest(city=slug):
                data = json.loads((SKILL / "examples" / (slug + ".json")).read_text(encoding="utf-8"))
                expected = generator.render(data)
                actual = (ROOT / "docs/examples" / (slug + "-wuxing.html")).read_text(encoding="utf-8")
                self.assertEqual(expected, actual, "请重新生成城市地图示例")


if __name__ == "__main__":
    unittest.main()
