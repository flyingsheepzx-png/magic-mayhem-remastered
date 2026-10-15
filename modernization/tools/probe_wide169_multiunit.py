"""Compare hero and zombie mid-segment path changes in the isolated test2."""
import json
import os
import sys
import time
from pathlib import Path

from wide169_trial import Session, ROOT
from verify_wide169_input_map import units

os.environ['MM_ALLOW_NATIVE_CLIENT'] = '1'
os.environ['MM_ALLOW_SCALED_CLIENT'] = '1'


def selected(s):
    return [u['index'] for u in units(s) if u['selected']]


def positions(s):
    return {u['index']: u['grid'] for u in units(s) if u['index'] in (0, 9, 10)}


def main():
    with Session() as s:
        s.load('test2')
        observed = []
        # Each pick is confirmed before issuing any orders. The two ground
        # points are inside the clearing and stay clear of the portrait HUD.
        for actor, pick, a, b in (
            (0, (640, 330), (740, 370), (555, 345)),
            (9, (580, 405), (680, 405), (520, 430)),
            (10, (705, 450), (600, 450), (760, 420)),
        ):
            s.click(*pick)
            time.sleep(.15)
            got = selected(s)
            observed.append(dict(actor=actor, pick=pick, selected=got, before=positions(s)))
            if got != [actor]:
                raise RuntimeError(f'Pick {actor} selected {got}')
            for n, target in enumerate((a, b, a, b)):
                s.click(*target, right=True)
                time.sleep(.22)
                observed.append(dict(actor=actor, order=n, target=target,
                                     selected=selected(s), positions=positions(s)))
            time.sleep(.8)
            observed.append(dict(actor=actor, after=positions(s)))
        s.result['movement'] = observed
        print(json.dumps(observed, ensure_ascii=False), flush=True)


if __name__ == '__main__':
    main()
