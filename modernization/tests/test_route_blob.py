import struct
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathfinding.route_blob import ROUTE_BYTES, decode


def fixture(goal=(2, 1, 0), cursor=0, points=((1, 1, 0), (2, 1, 0))):
    words = [0] * (ROUTE_BYTES // 4)
    words[:5] = [*goal, cursor, len(points)]
    for index, point in enumerate(points):
        words[5 + 7 * index:8 + 7 * index] = point
    return struct.pack("<131I", *words)


class RouteBlobTests(unittest.TestCase):
    def test_observed_layout_capacity_and_cursor(self):
        route = decode(fixture(cursor=1))
        self.assertEqual(route.destination, (2, 1, 0))
        self.assertEqual(route.cursor, 1)
        self.assertEqual(route.count, 2)
        self.assertEqual([(p.x, p.y, p.z) for p in route.waypoints],
                         [(1, 1, 0), (2, 1, 0)])

    def test_partial_segment_keeps_final_destination(self):
        route = decode(fixture(goal=(9, 9, 9)))
        self.assertEqual(route.destination, (9, 9, 9))
        self.assertFalse(route.segment_reaches_destination)

    def test_rejects_invalid_shapes(self):
        with self.assertRaises(ValueError):
            decode(b"\0" * 100)
        with self.assertRaises(ValueError):
            decode(fixture(cursor=3))


if __name__ == "__main__":
    unittest.main()
