"""Reproduce the v22 disk patch from its audited, hash-gated byte spans."""
import argparse
import hashlib
import json
from pathlib import Path
import pefile

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_SHA = '84d201637ce3ccebf49b8c9f930c1e5d41083ecc40015d342e19e6ef9b232448'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build(engine, launcher, output):
    spec = json.loads((ROOT/'modernization/config/wide169-timer-progress-patch.json').read_text())
    raw = engine.read_bytes()
    if sha(raw) != spec['parent_engine'] or sha(launcher.read_bytes()) != LAUNCHER_SHA:
        raise ValueError('Unknown engine or launcher; refusing address patch')
    pe = pefile.PE(data=raw)
    if pe.OPTIONAL_HEADER.ImageBase != 0x400000:
        raise ValueError('Unexpected image base')
    data = bytearray(raw)
    for row in spec['changes']:
        offset = pe.get_offset_from_rva(int(row['va'],16)-0x400000)
        before, after = bytes.fromhex(row['old']), bytes.fromhex(row['new'])
        if len(before) != len(after) or data[offset:offset+len(before)] != before:
            raise ValueError('Unexpected patch bytes at '+row['va'])
        data[offset:offset+len(before)] = after
    if sha(data) != spec['engine_sha256']:
        raise ValueError('Unexpected output engine')
    launch = launcher.read_bytes()
    needle = spec['parent_engine'].encode('utf-16le')
    if launch.count(needle) != 1:
        raise ValueError('Engine identity literal is not unique')
    launch = launch.replace(needle,spec['engine_sha256'].encode('utf-16le'))
    output.mkdir(parents=True, exist_ok=False)
    (output/engine.name).write_bytes(data)
    (output/launcher.name).write_bytes(launch)
    print(json.dumps({'engine':sha(data),'launcher':sha(launch)},indent=2))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('engine',type=Path)
    parser.add_argument('launcher',type=Path)
    parser.add_argument('output',type=Path)
    args=parser.parse_args()
    build(args.engine,args.launcher,args.output)
