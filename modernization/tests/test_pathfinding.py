import heapq
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from pathfinding.core import RepathPolicy, SearchBudget, Status, prune_visible, search

def oracle(start, goal, width, height, passable, cost):
    queue = [(0, start)]
    best = {start: 0}
    while queue:
        distance, cell = heapq.heappop(queue)
        if distance != best[cell]:
            continue
        if cell == goal:
            return distance
        for dx, dy in ((0, 1), (1, 0), (0, -1), (-1, 0)):
            nxt = (cell[0] + dx, cell[1] + dy)
            if 0 <= nxt[0] < width and 0 <= nxt[1] < height and passable(nxt):
                candidate = distance + cost(cell, nxt)
                if candidate < best.get(nxt, 10**9):
                    best[nxt] = candidate
                    heapq.heappush(queue, (candidate, nxt))
    return None

class PathfindingTests(unittest.TestCase):
    def test_detours_around_wall(self):
        blocked = {(2, y) for y in range(4)}
        route = search((0, 0), (4, 0), 5, 5, lambda p: p not in blocked,
                       lambda _a, _b: 1)
        self.assertEqual(route.status, Status.REACHED)
        self.assertEqual(route.cost, 12)
        self.assertTrue(all(p not in blocked for p in route.cells))

    def test_unreachable_is_bounded(self):
        blocked = {(2, y) for y in range(5)}
        route = search((0, 0), (4, 0), 5, 5, lambda p: p not in blocked,
                       lambda _a, _b: 1, max_expansions=300)
        self.assertEqual(route.status, Status.PARTIAL)
        self.assertLessEqual(route.expansions, 300)
        self.assertEqual(route.cells[-1], (1, 0))

    def test_budget_and_backoff(self):
        route = search((0, 0), (19, 19), 20, 20, lambda _p: True,
                       lambda _a, _b: 1, max_expansions=4)
        self.assertEqual(route.status, Status.BUDGET_EXHAUSTED)
        budget = SearchBudget(5)
        budget.spend(route.expansions)
        self.assertEqual(budget.allowance(20), 1)
        policy = RepathPolicy()
        policy.planned(0, (4, 4), 1, False)
        self.assertFalse(policy.should_replan(10, (4, 4), 1, False))
        self.assertTrue(policy.should_replan(20, (4, 4), 1, False))

    def test_smoothing_requires_collision_check(self):
        route = ((0, 0), (1, 0), (2, 0))
        self.assertEqual(prune_visible(route, lambda _a, _b: False), route)
        self.assertEqual(prune_visible(route, lambda _a, _b: True), ((0, 0), (2, 0)))

    def test_narrow_door_and_map_change(self):
        blocked = {(3, y) for y in range(7) if y != 3}
        route = search((0, 0), (6, 0), 7, 7, lambda p: p not in blocked,
                       lambda _a, _b: 1)
        self.assertEqual(route.status, Status.REACHED)
        self.assertIn((3, 3), route.cells)
        blocked.add((3, 3))
        self.assertNotEqual(search((0, 0), (6, 0), 7, 7,
                                   lambda p: p not in blocked,
                                   lambda _a, _b: 1).status, Status.REACHED)

    def test_moving_target_replans_at_interval(self):
        policy = RepathPolicy(min_interval_ticks=5)
        policy.planned(0, (3, 3), 1, True)
        self.assertFalse(policy.should_replan(1, (4, 3), 1, True))
        self.assertTrue(policy.should_replan(5, (4, 3), 1, True))
        policy.planned(5, (4, 3), 1, True)
        self.assertTrue(policy.should_replan(6, (4, 3), 2, True))

    def test_no_movement_progress_triggers_replan(self):
        policy = RepathPolicy(min_interval_ticks=5, stuck_after_ticks=12)
        policy.planned(0, (4, 4), 1, True)
        policy.progress(6)
        self.assertFalse(policy.should_replan(12, (4, 4), 1, True))
        self.assertTrue(policy.should_replan(18, (4, 4), 1, True))

    def test_random_maps_match_dijkstra(self):
        rng = random.Random(1998)
        for _ in range(150):
            width = height = 12
            blocked = {(x, y) for x in range(width) for y in range(height)
                       if rng.random() < 0.22}
            blocked.discard((0, 0))
            blocked.discard((11, 11))
            passable = lambda p: p not in blocked
            cost = lambda _a, b: 1 + (b[0] * 7 + b[1] * 3) % 5
            expected = oracle((0, 0), (11, 11), width, height, passable, cost)
            route = search((0, 0), (11, 11), width, height, passable, cost,
                           max_expansions=width * height)
            if expected is None:
                self.assertIn(route.status, (Status.PARTIAL, Status.UNREACHABLE))
            else:
                self.assertEqual(route.status, Status.REACHED)
                self.assertEqual(route.cost, expected)

if __name__ == "__main__":
    unittest.main()
