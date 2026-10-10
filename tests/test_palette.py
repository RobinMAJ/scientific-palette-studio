import importlib.util
import json
import os
from pathlib import Path
import tempfile
import unittest
import xml.etree.ElementTree as ET
import zipfile

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("palette", ROOT/"scripts/palette.py")
palette = importlib.util.module_from_spec(spec)
spec.loader.exec_module(palette)


class PaletteTests(unittest.TestCase):
    def setUp(self):
        self.p = palette.build_palette(palette.DEMO_COLORS, "Test palette", {"basis": "manual"})

    def test_oklab_roundtrip(self):
        for rgb in [(0,0,0), (255,255,255), (255,0,0), (0,255,0), (0,0,255), (73,156,201)]:
            self.assertEqual(rgb, palette.lab_to_rgb(palette.rgb_to_lab(rgb)))

    def test_known_lightness(self):
        self.assertAlmostEqual(palette.rgb_to_lab((255,0,0))[0], .62795536, places=6)
        self.assertAlmostEqual(palette.contrast((0,0,0), (255,255,255)), 21)

    def test_main_anchors_and_lightness(self):
        for c,g in zip(palette.DEMO_COLORS, self.p["gradients"]):
            self.assertEqual(c, g["colors"][128])
            self.assertEqual(257, len(g["colors"]))
            self.assertTrue(g["lightness"]["monotonic_with_tolerance"])
            self.assertTrue(all(0 <= x <= 255 for v in g["colors"] for x in palette.hex_rgb(v)))

    def test_neutral_diverging_center(self):
        g = self.p["gradients"][-1]
        rgb = palette.hex_rgb(g["colors"][128])
        self.assertEqual(rgb[0], rgb[1])
        self.assertEqual(rgb[1], rgb[2])
        self.assertTrue(g["lightness"]["monotonic_with_tolerance"])
        self.assertGreater(palette.rgb_to_lab(rgb)[0], .95)

    def test_sequential_order(self):
        self.assertTrue(self.p["gradients"][-2]["lightness"]["monotonic_with_tolerance"])

    def test_native_pal_roundtrip(self):
        for colors in [palette.DEMO_COLORS, palette.gradient_256(self.p["gradients"][-1]["colors"])]:
            lines = palette.pal_text(colors).splitlines()
            self.assertEqual(["JASC-PAL", "0100", str(len(colors))], lines[:3])
            loaded = [tuple(map(int, x.split())) for x in lines[3:]]
            self.assertEqual([palette.hex_rgb(c) for c in colors], loaded)

    def test_observed_colors_ignore_white_text(self):
        pixels = np.array([(255,255,255)]*20000 + [(0,0,0)]*10000 +
                          [palette.hex_rgb(c) for c in palette.DEMO_COLORS for _ in range(600)], dtype=np.uint8)
        actual, report = palette.extract_colors(pixels, 6)
        self.assertEqual(set(palette.DEMO_COLORS), set(actual))
        self.assertEqual(3600, report["retained_pixels"])

    def test_sparse_lines_recovered(self):
        im = Image.new("RGB", (1200,800), "white")
        d = ImageDraw.Draw(im)
        for i,c in enumerate(palette.DEMO_COLORS):
            d.line((80,120+i*70,1100,200+i*70), fill=c, width=3)
        actual,_ = palette.extract_colors(np.asarray(im).reshape(-1,3)[::3],6)
        self.assertEqual(set(actual), set(palette.DEMO_COLORS))

    def test_do_not_invent_source_hues(self):
        pixels=np.array([palette.hex_rgb(palette.DEMO_COLORS[0])]*100 +
                        [palette.hex_rgb(palette.DEMO_COLORS[1])]*100, dtype=np.uint8)
        actual,report=palette.extract_colors(pixels,6)
        self.assertEqual(2,len(actual))
        self.assertEqual(6,report["requested_main_count"])

    def test_grayscale_requires_opt_in(self):
        pixels=np.array([(55,55,55)]*100+[(170,170,170)]*100,dtype=np.uint8)
        with self.assertRaises(ValueError):palette.extract_colors(pixels)
        colors,_=palette.extract_colors(pixels,2,True)
        self.assertEqual({"#373737","#AAAAAA"},set(colors))

    def test_transparency_not_black(self):
        with tempfile.TemporaryDirectory() as t:
            im=Image.new("RGBA",(12,12),(12,34,56,0));p=Path(t)/"alpha.png";im.save(p)
            self.assertEqual((255,255,255),palette.normalized_image(p).getpixel((0,0)))

    def test_page_selection_and_bounds(self):
        self.assertEqual([2,4,5],palette.parse_pages("2,4-5",9))
        self.assertEqual(list(range(1,7)),palette.parse_pages(None,100))
        for bad in ["0","1-13","3-2","99","2;whoami","nan"]:
            with self.assertRaises(ValueError):palette.parse_pages(bad,20)

    def test_crop_bounds(self):
        im=Image.new("RGB",(100,100));self.assertEqual((50,50),palette.crop_image(im,"0.25,0.25,0.75,0.75").size)
        for bad in ["-0.1,0,1,1","0,0,0,1","0,0,1,2","nan,0,1,1"]:
            with self.assertRaises(ValueError):palette.crop_image(im,bad)

    def test_invalid_manual_colors(self):
        for colors in [["#FFFFFF"],["#FFFFFF","#FFFFFF"],["#GGFFFF","#28669B"],["#fff","#28669B"]]:
            with self.assertRaises(ValueError):palette.build_palette(colors,"test",{})

    def test_theme_six_slots_preserve_extra_colors(self):
        p=palette.build_palette(palette.DEMO_COLORS+["#12AA99","#DA9878"],"Eight",{})
        self.assertEqual(6,len(p["powerpoint"]["accent_colors"]))
        self.assertEqual(2,len(p["powerpoint"]["extra_colors"]))
        p=palette.build_palette(palette.DEMO_COLORS[:2],"Two",{})
        self.assertEqual(6,len(p["powerpoint"]["accent_colors"]))

    def test_native_pptx_gradients_and_values(self):
        parts=palette.pptx_parts(self.p)
        gradients=0
        for name,data in parts.items():
            if name.endswith((".xml",".rels")):ET.fromstring(data)
            if name.startswith("ppt/slides/slide") and name.endswith(".xml"):
                node=ET.fromstring(data)
                gs=node.findall(".//a:gradFill",palette.NS)
                gradients+=len(gs)
                for g in gs:self.assertEqual(17,len(g.findall("a:gsLst/a:gs",palette.NS)))
        self.assertEqual(8,gradients)
        self.assertIn(b"28669B",parts["ppt/slides/slide1.xml"])
        self.assertNotIn(b"MAIN-6",parts["ppt/slides/slide1.xml"])

    def test_theme_relationships(self):
        parts=palette.theme_parts(self.p)
        for data in parts.values():ET.fromstring(data)
        self.assertIn(b"28669B",parts["theme/theme1.xml"])
        root=ET.fromstring(parts["_rels/.rels"])
        self.assertIn(root[0].get("Target"),parts)

    def test_export_no_overwrite_hashes_and_script_injection(self):
        with tempfile.TemporaryDirectory() as t:
            self.p["title"]="Text </script><script>alert(1)</script>"
            out=palette.export_bundle(self.p,Path(t)/"kit")
            self.assertIn("\\u003c/script",(out/"palette-workbench.html").read_text())
            self.assertNotIn("__PALETTE_PAYLOAD__",(out/"palette-workbench.html").read_text())
            manifest=json.loads((out/"manifest.json").read_text())
            for name,sha in manifest["files"].items():
                self.assertEqual(sha,palette.hashlib.sha256((out/name).read_bytes()).hexdigest())
            with self.assertRaises(ValueError):palette.export_bundle(self.p,out)
            with zipfile.ZipFile(out/"powerpoint/palette-toolkit.pptx") as z:self.assertIsNone(z.testzip())

    def test_reexport_updates_all_gradient_anchors(self):
        with tempfile.TemporaryDirectory() as t:
            self.p["main"][0]["hex"]="#AA3344"
            f=Path(t)/"edited.json";f.write_text(json.dumps(self.p));p=palette.load_palette(f)
            self.assertEqual("#AA3344",p["gradients"][0]["colors"][128])
            self.assertIn("reexported_from_sha256",p["provenance"])
            self.assertEqual("user-edited",p["provenance"]["basis"])

    @unittest.skipUnless(os.environ.get("PALETTE_TEST_PDF"),"Optional synthetic PDF fixture not configured")
    def test_pdf_input_fixture(self):
        pixels,sources=palette.load_sources([os.environ["PALETTE_TEST_PDF"]],"2")
        actual,_=palette.extract_colors(pixels,6)
        self.assertEqual(set(actual),set(palette.DEMO_COLORS))
        self.assertEqual([2],sources[0]["pages"])
        self.assertEqual(64,len(sources[0]["sha256"]))


if __name__ == "__main__":unittest.main()
