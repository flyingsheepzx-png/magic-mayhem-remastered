"""Check mid-edge trial events against world-position telemetry."""
import argparse
import csv
from collections import Counter
import json
import math
from pathlib import Path


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("report",type=Path)
    ap.add_argument("events",type=Path)
    args=ap.parse_args()
    report=json.loads(args.report.read_text(encoding="utf-8"))
    rows=list(csv.DictReader(Path(report["unit_csv"]).open(newline="")))
    events=list(csv.reader(args.events.open(newline="")))
    frequency=report["qpc_frequency"]
    changes=[(int(b["qpc"]),int(b["pixel_x_candidate"]),int(b["pixel_y_candidate"]))
             for a,b in zip(rows,rows[1:]) if (a["pixel_x_candidate"],a["pixel_y_candidate"])!=
                                              (b["pixel_x_candidate"],b["pixel_y_candidate"])]
    jumps=[{"qpc":b[0],"from":[a[1],a[2]],"to":[b[1],b[2]],
            "distance":math.hypot(b[1]-a[1],b[2]-a[2])}
           for a,b in zip(changes,changes[1:]) if math.hypot(b[1]-a[1],b[2]-a[2])>12]
    event_qpcs=[int(e[0]) for e in events if e[1] in ("redirect","reverse_layer")]
    motion_gaps=[]
    for left,right in zip(event_qpcs,event_qpcs[1:]):
        window=[q for q,_,_ in changes if left<=q<right]
        motion_gaps.extend((b-a)/frequency for a,b in zip(window,window[1:]))
    result=[]
    last_order=None
    for event in events:
        q=int(event[0]);kind=event[1]
        if kind=="order_mid_segment":last_order=q
        if kind not in ("redirect","reverse_layer"):continue
        x,y=int(event[5]),int(event[6])
        first=next((c for c in changes if c[0]>q),None)
        result.append({"kind":kind,"qpc":q,"position_at_handoff":[x,y],
                       "off_cell_boundary":bool(x%32 or y%32),
                       "planning_and_handoff_ms":(q-last_order)*1000/frequency if last_order else None,
                       "first_position_change_ms":(first[0]-q)*1000/frequency if first else None,
                       "first_position_change_pixels":math.hypot(first[1]-x,first[2]-y) if first else None})
    counts=Counter(e[1] for e in events)
    output={"source":str(args.report),"event_counts":dict(counts),"handoffs":result,
            "large_position_jumps":jumps,
            "max_between_handoff_position_change_gap_seconds":max(motion_gaps) if motion_gaps else None,
            "occupancy_check_failures":counts["occupancy_mismatch"],
            "visual_duplicate_absence_verified":False,"native_navigation_equivalence_verified":False}
    print(json.dumps(output,indent=2))


if __name__=="__main__":main()
