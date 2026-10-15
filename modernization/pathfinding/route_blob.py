"""Read-only decoder for the route buffer observed in one community build.

The first five dwords and 18 seven-dword records fit the 0x83-dword copy at
0x51285d. Coordinates and cursor correlate with two controlled routes. The
remaining record fields and all write/ownership semantics are unverified.
Long routes can hold an intermediate segment while the first three dwords
retain the final destination; segment endpoint need not equal destination.
"""
from dataclasses import dataclass
import struct

ROUTE_BYTES = 0x83 * 4
MAX_WAYPOINTS = 18


@dataclass(frozen=True)
class Waypoint:
    x: int
    y: int
    z: int
    metadata: tuple[int, int, int, int]


@dataclass(frozen=True)
class ObservedRoute:
    destination: tuple[int, int, int]
    cursor: int
    count: int
    waypoints: tuple[Waypoint, ...]

    @property
    def segment_reaches_destination(self) -> bool:
        return bool(self.waypoints) and (
            self.waypoints[-1].x, self.waypoints[-1].y,
            self.waypoints[-1].z) == self.destination


def decode(blob: bytes) -> ObservedRoute:
    if len(blob) != ROUTE_BYTES:
        raise ValueError(f"Expected {ROUTE_BYTES} route bytes")
    words = struct.unpack("<131I", blob)
    destination = tuple(words[:3])
    cursor, count = words[3:5]
    if count > MAX_WAYPOINTS or cursor > count:
        raise ValueError("Route cursor/count exceeds observed buffer capacity")
    waypoints = tuple(Waypoint(*words[5 + i * 7:8 + i * 7],
                               tuple(words[8 + i * 7:12 + i * 7]))
                      for i in range(count))
    return ObservedRoute(destination, cursor, count, waypoints)
