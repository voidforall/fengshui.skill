"""City map generation: real coordinates, portable packaging and safe annotations."""

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

    def test_examples_have_all_five_elements_and_realistic_city_locations(self):
        for slug, lat_range, lon_range in (
            ("london", (51.4, 51.7), (-0.4, 0.1)),
            ("new-york", (40.6, 40.9), (-74.1, -73.8)),
        ):
            with self.subTest(city=slug):
                data = json.loads((SKILL / "examples" / (slug + ".json")).read_text(encoding="utf-8"))
                generator.validate(data)
                self.assertEqual(set(generator.ELEMENTS), {p["element"] for p in data["places"]})
                for place in data["places"]:
                    self.assertTrue(lat_range[0] <= place["lat"] <= lat_range[1])
                    self.assertTrue(lon_range[0] <= place["lon"] <= lon_range[1])

    def test_rejects_bad_coordinates_elements_and_untraceable_facts(self):
        for field, value in (("lat", 91), ("lat", float("nan")), ("lat", True),
                             ("lon", -181), ("lon", "-0.1"), ("element", "旺财"),
                             ("element", ""), ("basis", "客观结论"), ("sources", []),
                             ("sources", [{"title": "bad", "url": "javascript:alert(1)"}])):
            with self.subTest(field=field, value=value):
                data = copy.deepcopy(self.data)
                data["places"][0][field] = value
                with self.assertRaises(ValueError):
                    generator.validate(data)

    def test_duplicate_ids_and_empty_city_are_errors(self):
        self.data["places"][1]["id"] = self.data["places"][0]["id"]
        with self.assertRaises(ValueError):
            generator.validate(self.data)
        self.data["places"] = self.data["places"][:1]
        self.data["city"] = ""
        with self.assertRaises(ValueError):
            generator.validate(self.data)

    def test_data_cannot_escape_json_script_or_page_title(self):
        payload = '</script><script>alert("injected")</script>'
        self.data["city"] = payload
        self.data["places"][0]["reading"] = payload
        result = generator.render(self.data)
        self.assertNotIn(payload, result)
        start = result.index('<script id="city-data" type="application/json">')
        content = result[start:].split('>', 1)[1].split('</script>', 1)[0]
        embedded = json.loads(content)
        self.assertEqual(payload, embedded["places"][0]["reading"])
        self.assertEqual(payload, embedded["city"])

    def test_custom_city_runs_as_an_installed_standalone_skill(self):
        with tempfile.TemporaryDirectory() as directory:
            temp = Path(directory)
            installed = temp / "city-wuxing-map"
            shutil.copytree(SKILL, installed, ignore=shutil.ignore_patterns("__pycache__"))
            self.data["city"] = "测试城市"
            self.data["places"] = self.data["places"][:1]
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
