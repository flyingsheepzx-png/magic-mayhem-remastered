"""Read-only structural inspection of native AI data; never writes runtime files.

Layout recovered from engine SHA256
42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da:
0x479a10/0x476240/0x475e60/0x475cf0 and 0x4764d0.
Names such as component/matrix are structural, not recovered semantic types.
"""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import struct


class Reader:
    def __init__(self, path):
        self.data = path.read_bytes()  # immutable snapshot even if game appends later
        self.pos = 0

    def read(self, fmt):
        size = struct.calcsize('<' + fmt)
        if self.pos + size > len(self.data):
            raise ValueError(f'truncated record at {self.pos}')
        values = struct.unpack_from('<' + fmt, self.data, self.pos)
        self.pos += size
        return values

    def dimension(self):
        n, = self.read('I')
        if not 0 < n <= 1024:
            raise ValueError(f'invalid dimension {n} at {self.pos - 4}')
        return n

    def metadata(self):
        return {'bytes': len(self.data), 'sha256': hashlib.sha256(self.data).hexdigest()}


def brain(path):
    r = Reader(path)
    models = []
    while r.pos < len(r.data):
        offset = r.pos
        action, = r.read('I')
        dimension = r.dimension()
        count = r.dimension()
        if count > 32:
            raise ValueError('unsupported component count')
        components = []
        for _ in range(count):
            coefficient, = r.read('f')
            n = r.dimension()
            feature_records = r.read('f' * (12 * n))
            scalar, = r.read('f')
            matrix = r.read('f' * (n * n))
            if n != dimension:
                raise ValueError('component/model dimensions differ')
            if not all(map(math.isfinite, (coefficient, scalar, *feature_records, *matrix))):
                raise ValueError('nonfinite data')
            components.append({
                'coefficient': coefficient, 'scalar': scalar, 'dimension': n,
                'matrix_asymmetry_max': max(abs(matrix[i*n+j] - matrix[j*n+i])
                                             for i in range(n) for j in range(n)),
            })
        models.append({'action_id': action, 'dimension': dimension, 'offset': offset,
                       'coefficient_sum': sum(c['coefficient'] for c in components),
                       'components': components})
    return {**r.metadata(), 'models': models, 'complete': r.pos == len(r.data)}


def experience(path):
    r = Reader(path)
    counts = Counter()
    labels = Counter()
    while r.pos < len(r.data):
        action, = r.read('I')
        n = r.dimension()
        r.read('i' * n)
        classes, label = r.read('II')
        if not 0 < classes <= 32 or label >= classes:
            raise ValueError('invalid outcome class count/label')
        counts[action, n] += 1
        labels[action, classes, label] += 1
    return {**r.metadata(), 'records': sum(counts.values()), 'groups': [
        {'action_id': k[0], 'dimension': k[1], 'records': v}
        for k, v in sorted(counts.items())], 'labels': [
        {'action_id': k[0], 'class_count': k[1], 'label': k[2], 'records': v}
        for k,v in sorted(labels.items())], 'complete': r.pos == len(r.data)}


if __name__ == '__main__':
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('directory', type=Path)
    args = ap.parse_args()
    print(json.dumps({'brain': brain(args.directory / 'Brain.dat'),
                      'experience': experience(args.directory / 'EXPERIEN.DAT')}, indent=2))
