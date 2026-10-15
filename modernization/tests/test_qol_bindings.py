import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from qol_bindings import KEYS, Layout


class LayoutTests(unittest.TestCase):
    def test_every_key_transfers_and_each_slot_has_one_key(self):
        layout = Layout()
        for index, key in enumerate(KEYS):
            self.assertTrue(layout.bind(key, index // 7, index % 7))
        self.assertEqual(len(layout.bindings), 12)
        self.assertTrue(layout.bind("Q", 2, 4))
        self.assertEqual(layout.key_for(0, 0), None)
        self.assertEqual(layout.key_for(2, 4), "Q")
        self.assertTrue(layout.bind("W", 2, 4))
        self.assertEqual(layout.key_for(2, 4), "W")
        self.assertNotIn("Q", layout.bindings)
        self.assertFalse(layout.bind("W", 2, 4))
        self.assertTrue(layout.clear(2, 4))
        self.assertFalse(layout.clear(2, 4))

    def test_empty_slot_retains_layout_and_replacement_reactivates(self):
        layout = Layout()
        layout.bind("E", 1, 3)
        self.assertIsNone(layout.active_slot("E", set()))
        self.assertEqual(layout.active_slot("E", {(1, 3)}), (1, 3))
        self.assertEqual(layout.key_for(1, 3), "E")

    def test_reload_is_shared_and_rejects_invalid_config(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "qol-hotkeys.json"
            self.assertEqual(Layout.load(path).bindings, {})
            layout = Layout()
            layout.bind("V", 2, 20)
            layout.save(path)
            self.assertEqual(Layout.load(path).bindings, {"V": (2, 20)})
            data = json.loads(path.read_text(encoding="utf-8"))
            data["bindings"]["C"] = {"tray": 2, "slot": 20}
            path.write_text(json.dumps(data), encoding="utf-8")
            with self.assertRaises(ValueError):
                Layout.load(path)

    def test_invalid_ids_and_keys_are_rejected(self):
        layout = Layout()
        for args in (("T", 0, 0), ("Q", -1, 0), ("Q", 0, 21)):
            with self.assertRaises(ValueError):
                layout.bind(*args)
        self.assertEqual(layout.bindings, {})


if __name__ == "__main__":
    unittest.main()
