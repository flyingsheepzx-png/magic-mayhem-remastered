import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from display import update_ddraw

class DisplayTests(unittest.TestCase):
    def test_updates_only_global_section(self):
        source = "[ddraw]\nwidth=0\nheight=0\n\n[other]\nwidth=123\n"
        result = update_ddraw(source, {"width": "1920", "height": "1080"})
        self.assertIn("[ddraw]\nwidth=1920\nheight=1080", result)
        self.assertIn("[other]\nwidth=123", result)

    def test_missing_setting_rejected(self):
        with self.assertRaises(ValueError):
            update_ddraw("[ddraw]\nwidth=0\n", {"height": "1080"})

if __name__ == "__main__":
    unittest.main()
