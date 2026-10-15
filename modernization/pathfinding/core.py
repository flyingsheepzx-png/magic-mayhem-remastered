"""Deterministic bounded A* prototype for game navigation integration.

Coordinates are integer navigation cells. Callers must supply the game's exact
per-creature passability and terrain costs before any live integration.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
import heapq
import math
from typing import Callable

Cell = tuple[int, int]
Passable = Callable[[Cell], bool]
StepCost = Callable[[Cell, Cell], int]

class Status(Enum):
    REACHED = "reached"
    PARTIAL = "partial"
    UNREACHABLE = "unreachable"
    BUDGET_EXHAUSTED = "budget_exhausted"
    INVALID = "invalid"

@dataclass(frozen=True)
class Route:
    status: Status
    cells: tuple[Cell, ...]
    cost: int
    expansions: int

def _heuristic(a: Cell, b: Cell, minimum_cost: int) -> int:
    return (abs(a[0] - b[0]) + abs(a[1] - b[1])) * minimum_cost

def search(start: Cell, goal: Cell, width: int, height: int,
           passable: Passable, step_cost: StepCost,
           max_expansions: int = 300, minimum_cost: int = 1,
           allow_partial: bool = True) -> Route:
    """Four-way A*. Partial endpoint is the best explored reachable cell.

    The goal's passability is deliberately checked by the caller's rule so a
    closed door or an occupied destination cannot be silently crossed.
    """
    if width <= 0 or height <= 0 or max_expansions <= 0 or minimum_cost <= 0:
        return Route(Status.INVALID, (), 0, 0)
    def valid(p: Cell) -> bool:
        return 0 <= p[0] < width and 0 <= p[1] < height and passable(p)
    if not valid(start):
        return Route(Status.INVALID, (), 0, 0)
    if start == goal:
        return Route(Status.REACHED, (start,), 0, 0)
    if not (0 <= goal[0] < width and 0 <= goal[1] < height):
        return Route(Status.INVALID, (), 0, 0)

    heap: list[tuple[int, int, int, Cell]] = []
    serial = 0
    heapq.heappush(heap, (_heuristic(start, goal, minimum_cost), 0, serial, start))
    best_cost = {start: 0}
    parent: dict[Cell, Cell] = {}
    closed: set[Cell] = set()
    closest = start
    closest_key = (_heuristic(start, goal, 1), 0)
    expansions = 0
    reached = False

    while heap and expansions < max_expansions:
        _, cost, _, current = heapq.heappop(heap)
        if current in closed or cost != best_cost[current]:
            continue
        closed.add(current)
        expansions += 1
        key = (_heuristic(current, goal, 1), cost)
        if key < closest_key:
            closest, closest_key = current, key
        if current == goal:
            reached = True
            break
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0)):
            nxt = (current[0] + dx, current[1] + dy)
            if not valid(nxt) or nxt in closed:
                continue
            weight = step_cost(current, nxt)
            if weight < minimum_cost:
                raise ValueError("step_cost below minimum_cost: heuristic would be invalid")
            candidate = cost + weight
            if candidate >= best_cost.get(nxt, math.inf):
                continue
            best_cost[nxt] = candidate
            parent[nxt] = current
            serial += 1
            heapq.heappush(heap, (candidate + _heuristic(nxt, goal, minimum_cost),
                                  candidate, serial, nxt))

    if reached:
        endpoint, status = goal, Status.REACHED
    elif not heap and closest == start:
        endpoint, status = start, Status.UNREACHABLE
    elif expansions >= max_expansions and heap:
        endpoint, status = closest, Status.BUDGET_EXHAUSTED
    else:
        endpoint, status = closest, Status.PARTIAL
    if status != Status.REACHED and not allow_partial:
        return Route(status, (), 0, expansions)
    route = [endpoint]
    while route[-1] != start:
        route.append(parent[route[-1]])
    route.reverse()
    return Route(status, tuple(route), best_cost[endpoint], expansions)

def prune_visible(cells: tuple[Cell, ...], collision_free: Callable[[Cell, Cell], bool]) -> tuple[Cell, ...]:
    """Remove waypoints only after the engine validates a direct segment."""
    if len(cells) < 3:
        return cells
    result = [cells[0]]
    index = 0
    while index < len(cells) - 1:
        candidate = len(cells) - 1
        while candidate > index + 1 and not collision_free(cells[index], cells[candidate]):
            candidate -= 1
        result.append(cells[candidate])
        index = candidate
    return tuple(result)

@dataclass
class RepathPolicy:
    """Rate-limit replanning while allowing immediate reaction to map changes."""
    min_interval_ticks: int = 5
    stuck_after_ticks: int = 12
    retry_after_failure_ticks: int = 20
    last_plan_tick: int = -10**9
    last_progress_tick: int = 0
    last_goal: Cell | None = None
    last_map_revision: int = -1
    failure_until_tick: int = 0

    def should_replan(self, tick: int, goal: Cell, map_revision: int,
                      has_route: bool) -> bool:
        if tick < self.failure_until_tick:
            return False
        if map_revision != self.last_map_revision:
            return True
        if goal != self.last_goal and tick - self.last_plan_tick >= self.min_interval_ticks:
            return True
        if not has_route and tick - self.last_plan_tick >= self.min_interval_ticks:
            return True
        return tick - self.last_progress_tick >= self.stuck_after_ticks and tick - self.last_plan_tick >= self.min_interval_ticks

    def planned(self, tick: int, goal: Cell, map_revision: int, success: bool) -> None:
        self.last_plan_tick = tick
        self.last_progress_tick = tick
        self.last_goal = goal
        self.last_map_revision = map_revision
        self.failure_until_tick = 0 if success else tick + self.retry_after_failure_ticks

    def progress(self, tick: int) -> None:
        self.last_progress_tick = tick

@dataclass
class SearchBudget:
    """Shared expansion allowance reset once per original logic tick."""
    max_per_tick: int
    remaining: int = field(init=False)

    def __post_init__(self) -> None:
        if self.max_per_tick <= 0:
            raise ValueError("max_per_tick must be positive")
        self.remaining = self.max_per_tick

    def next_tick(self) -> None:
        self.remaining = self.max_per_tick

    def allowance(self, requested: int) -> int:
        return max(0, min(requested, self.remaining))

    def spend(self, expansions: int) -> None:
        if expansions < 0 or expansions > self.remaining:
            raise ValueError("budget exceeded")
        self.remaining -= expansions
