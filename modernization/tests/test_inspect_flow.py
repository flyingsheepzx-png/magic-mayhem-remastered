"""Control-flow safety checks using synthetic x86, with no game assets."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
try:
    from inspect_flow import inspect
except ImportError:
    inspect = None


@unittest.skipIf(inspect is None, "pefile/capstone inspection dependencies unavailable")
class FlowTests(unittest.TestCase):
    def test_jump_skips_embedded_fake_call(self):
        data = bytes.fromhex("eb05e80000000090c3")
        result = inspect(data, 0x400000, 0x400000, 0x400009)
        self.assertEqual([r["address"] for r in result["instructions"]],
                         [0x400000, 0x400007, 0x400008])
        self.assertFalse(result["unresolved_edges"])

    def test_conditional_edges_and_import(self):
        data = bytes.fromhex("7406ff1500104000c3")
        result = inspect(data, 0x400000, 0x400000, 0x400009, {0x401000: "TestImport"})
        self.assertEqual(result["instructions"][1]["import"], "TestImport")
        self.assertFalse(result["runtime_semantics_verified"])

    def test_indirect_jump_stops_before_data(self):
        result = inspect(bytes.fromhex("ffe0e800000000"), 0x400000, 0x400000, 0x400007)
        self.assertEqual(len(result["instructions"]), 1)
        self.assertEqual(result["unresolved_edges"][0]["reason"], "indirect branch")

    def test_overlapping_branch_refused(self):
        with self.assertRaisesRegex(ValueError, "instruction|Overlapping"):
            inspect(bytes.fromhex("7401b800000000c3"), 0x400000, 0x400000, 0x400008)


if __name__ == "__main__":
    unittest.main()
