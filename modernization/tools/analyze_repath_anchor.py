"""Compare player draw steps with static terrain to remove camera movement.

Read-only diagnostic for the disposable repath sprite log. The terrain median is
only accepted when at least three identical tile/frame keys occur in both draws.
"""
import argparse
import csv
import json
from pathlib import Path
from statistics import median


def frames(path):
    with path.open(newline="", encoding="utf-8", errors="replace") as stream:
        yield from _frames(stream)


def _frames(stream):
    scenery = {}
    height = 0
    projection = None
    for row in csv.reader(stream):
        if len(row) > 12 and row[1] == "sprite_any" and row[2] in {"4f8bf5", "4f8d2c", "4f9257"}:
            key = (row[2], row[9], row[10])
            scenery[key] = (int(row[11]), int(row[12]))
        elif len(row) > 2 and row[1] == "height_state":
            height = int(row[2])
        elif len(row) >= 18 and row[1] == "projection_state":
            projection = list(map(int, row[2:]))
        elif len(row) >= 21 and row[1] == "sprite1":
            yield {"qpc": int(row[0]), "grid": [int(row[2]), int(row[3]), int(row[4])],
                   "world": [int(row[5]), int(row[6])],
                   "screen": [int(row[9]), int(row[10])], "scenery": scenery,
                   "height": height, "origin": [int(row[18]), int(row[19])],
                   "projection": projection}
            scenery = {}


def analyze(path):
    old = None
    steps = []
    total_steps = 0
    scene_steps = []
    def project(x, y, rotation):
        return ((x-y, (x+y)//2), (x+y, (y-x)//2),
                (y-x, -(x+y)//2), (-x-y, (x-y)//2))[rotation]
    def scene_origin(frame):
        p = frame["projection"]
        if p is None or not 0 <= p[5] < 4:
            return None
        # Native footprint locals can select a periodic image of a map cell.
        # Derive that image from the exact grid/local relation; canonical
        # scene indices alone introduce a whole-map jump at the seam.
        x, y = project(frame["grid"][0]*32-p[6],
                       frame["grid"][1]*32-p[7], p[5])
        return (p[3]-x, p[4]+p[2]*16-y)
    for frame in frames(path):
        if old:
            total_steps += 1
            new_origin, old_origin = scene_origin(frame), scene_origin(old)
            if new_origin is not None and old_origin is not None:
                current = project(*frame["world"], frame["projection"][5])
                previous = project(*old["world"], old["projection"][5])
                camera = [new_origin[i]-old_origin[i] for i in range(2)]
                raw = [frame["screen"][i]-old["screen"][i] for i in range(2)]
                expected = [camera[i]+current[i]-previous[i]+
                            frame["origin"][i]-old["origin"][i] for i in range(2)]
                expected[1] += old["height"]-frame["height"]
                scene_steps.append({"qpc": frame["qpc"], "grid": frame["grid"],
                                    "residual": [raw[i]-expected[i] for i in range(2)],
                                    "camera_step": camera,
                                    "action": frame["projection"][13],
                                    "previous_action": old["projection"][13]})
            common = old["scenery"].keys() & frame["scenery"].keys()
            motion = [(frame["scenery"][key][0] - old["scenery"][key][0],
                       frame["scenery"][key][1] - old["scenery"][key][1]) for key in common]
            if len(motion) >= 3:
                camera = [round(median(d[0] for d in motion)), round(median(d[1] for d in motion))]
                raw = [frame["screen"][i] - old["screen"][i] for i in range(2)]
                world = [frame["world"][i] - old["world"][i] for i in range(2)]
                origin = [frame["origin"][i] - old["origin"][i] for i in range(2)]
                expected = [world[0] - world[1] + origin[0],
                            (world[0] + world[1]) // 2 - frame["height"] +
                            old["height"] + origin[1]]
                residual = [raw[i] - camera[i] - expected[i] for i in range(2)]
                steps.append({"qpc": frame["qpc"], "grid": frame["grid"],
                              "screen_step": raw, "camera_step": camera,
                              "actor_step": [raw[i] - camera[i] for i in range(2)],
                              "world_step": world, "terrain_matches": len(motion),
                              "anchor_residual": residual})
        old = frame
    jumps = [s for s in steps if max(map(abs, s["actor_step"])) > 15 and
             max(map(abs, s["world_step"])) <= 10]
    return {"frames_with_camera_estimate": len(steps), "jumps": jumps,
            "total_draw_steps": total_steps,
            "camera_estimate_coverage": len(steps) / total_steps if total_steps else 0,
            "max_actor_step": max((max(map(abs, s["actor_step"])) for s in steps), default=None),
            "max_anchor_residual": max((max(map(abs, s["anchor_residual"])) for s in steps), default=None),
            "scene_projection_steps": len(scene_steps),
            "max_scene_projection_residual": max((max(map(abs, s["residual"])) for s in scene_steps), default=None),
            "large_scene_projection_residuals": [s for s in scene_steps if max(map(abs, s["residual"])) > 15],
            "large_anchor_residuals": [s for s in steps if max(map(abs, s["anchor_residual"])) > 15]}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("events", type=Path)
    args = parser.parse_args()
    print(json.dumps(analyze(args.events), indent=2))
