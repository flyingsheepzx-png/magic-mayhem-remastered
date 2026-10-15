"""Regression for full-resolution HD difference localization."""
import sys
import tempfile
import unittest
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from mark_hd_differences import compare


class DifferenceToolTest(unittest.TestCase):
    def test_marks_only_changed_region_at_native_coordinates(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            baseline = Image.new('RGB', (2560, 1440), (60, 55, 50))
            hd = baseline.copy()
            ImageDraw.Draw(hd).rectangle((1300, 50, 1379, 129), fill=(200, 40, 40))
            left, right = root / 'baseline.png', root / 'hd.png'
            baseline.save(left)
            hd.save(right)
            report = compare(left, right, root / 'diff', (1280, 0, 200, 180), 48, 16, 3)
            self.assertEqual(len(report['regions']), 1)
            x0, y0, x1, y1 = report['regions'][0]['box']
            self.assertLessEqual(x0, 1300)
            self.assertLessEqual(y0, 50)
            self.assertGreaterEqual(x1, 1379)
            self.assertGreaterEqual(y1, 128)
            with Image.open(root / 'diff/annotated-compare-5120x1440.png') as annotated:
                self.assertEqual(annotated.size, (5120, 1440))

    def test_known_baseline_defect_can_be_excluded(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            baseline = Image.new('RGB', (2560, 1440), '#202020')
            hd = baseline.copy()
            ImageDraw.Draw(hd).rectangle((2080, 220, 2160, 320), fill='#f0f0f0')
            left, right = root / 'baseline.png', root / 'hd.png'
            baseline.save(left)
            hd.save(right)
            report = compare(left, right, root / 'reviewed', None, 48, 16, 3,
                             [(2070, 200, 110, 140)])
            self.assertEqual(report['regions'], [])
            self.assertEqual(report['ignored_known_baseline_defects'], [[2070, 200, 2180, 340]])


if __name__ == '__main__':
    unittest.main()
