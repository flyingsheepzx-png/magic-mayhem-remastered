"""Read-only bounded AI scheduling review using native bytes and existing traces."""
import hashlib
import json
import struct
from collections import Counter, defaultdict
from pathlib import Path

from unicorn import UC_HOOK_CODE
from unicorn.x86_const import UC_X86_REG_EAX, UC_X86_REG_EBX, UC_X86_REG_ECX, UC_X86_REG_EDI, UC_X86_REG_EIP, UC_X86_REG_ESP
from verify_ai_training_math import machine, put
from verify_ai_action_primitives import call
from verify_ai_model_native import ROOT, SHA
from read_ai_diagnostics_11 import decode


def quantiles(values):
    values = sorted(values)
    return {name: values[min(len(values)-1, int(len(values)*fraction))] if values else None
            for name, fraction in [('median', .5), ('p95', .95), ('max', 1)]}


def native_budget_checks():
    rows = []
    for total in [0, 1, 2, 3, 15, 30, 60, 120, 240, 480]:
        u = machine()
        put(u, 0x5e15f4, 'i', total)
        sp = 0x23f0000
        u.reg_write(UC_X86_REG_ESP, sp)
        captured = []
        def scheduler_stub(uc, address, size, _):
            if address != 0x415c40:
                return
            esp = uc.reg_read(UC_X86_REG_ESP)
            ret, allowance = struct.unpack('<II', uc.mem_read(esp, 8))
            captured.append((uc.reg_read(UC_X86_REG_ECX), allowance))
            uc.reg_write(UC_X86_REG_ESP, esp+8)
            uc.reg_write(UC_X86_REG_EIP, ret)
        u.hook_add(UC_HOOK_CODE, scheduler_stub)
        u.emu_start(0x46b5be, 0x46b5e8, count=100)
        assert captured == [(0x690600, total//2), (0x644550, total//2)]
        # Native scheduler's first split; stop before budget initializer call.
        u.reg_write(UC_X86_REG_EBX, total//2)
        u.emu_start(0x415ca0, 0x415cad, count=20)
        planning = u.reg_read(UC_X86_REG_EDI)
        assert planning == (total//2)//2
        u.reg_write(UC_X86_REG_EBX, total//2)
        u.reg_write(UC_X86_REG_EDI, planning)
        u.emu_start(0x416384, 0x416386, count=5)
        execution = u.reg_read(UC_X86_REG_EBX)
        assert execution == total//2-planning
        obj = 0x2010000
        put(u, 0x6e1f64, 'I', 0)
        for allowance in (planning, execution):
            put(u, obj, 'III', 0x12345678, 0xabcdef01, 0x87654321)
            call(u, 0x4075b0, obj, [allowance])
            assert struct.unpack('<III', u.mem_read(obj, 12)) == (allowance, 0xabcdef01, allowance)
            assert call(u, 0x407600, obj, []) == allowance
        rows.append({'total': total, 'each_scheduler': total//2,
                     'planning_each': planning, 'execution_each': execution})
    return rows


def trace_review(fixture):
    folder = ROOT/'modernization/logs/ai-review'/fixture/'isolated-package/runtime/AI/diagnostics'
    paths = list(folder.glob('session-*/trace.bin'))
    assert len(paths) == 1, (fixture, paths)
    path = paths[0]
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    events = list(decode(path))
    active = {}
    rows = defaultdict(list)
    counts = Counter()
    commits = Counter()
    orphan = 0
    for event in events:
        kind, scheduler = event['kind'], event['scheduler']
        counts[kind] += 1
        if kind == 1:
            assert scheduler not in active
            active[scheduler] = {'budget': event['budget'], 'tick': event['tick'],
                                 'start_phase': event['phase'], 'yield_count': 0, 'evaluations': 0}
        elif kind == 2:
            row = active.pop(scheduler)
            row.update(elapsed_us=event['elapsed_us'], end_phase=event['phase'])
            rows[scheduler].append(row)
        elif kind in (5, 6, 9):
            if scheduler not in active:
                orphan += 1
                continue
            if kind == 9:
                active[scheduler]['yield_count'] += 1
            else:
                active[scheduler]['evaluations'] += 1
        elif kind == 10:
            commits[event['id']] += 1
    assert not active and not orphan
    result = {}
    for scheduler, calls in rows.items():
        ticks = [r['tick'] for r in calls]
        normal = [r for r in calls if r['budget'] == 15]
        yielded = sum(r['yield_count'] > 0 for r in calls)
        streak = best = 0
        for row in calls:
            streak = streak+1 if row['yield_count'] else 0
            best = max(best, streak)
        result[hex(scheduler)] = {
            'calls': len(calls), 'budgets': dict(Counter(r['budget'] for r in calls)),
            'normal_calls': len(normal),
            'normal_calls_with_candidate_budget_yield': sum(r['yield_count'] > 0 for r in normal),
            'normal_yield_fraction': sum(r['yield_count'] > 0 for r in normal)/len(normal),
            'normal_duration_us': quantiles([r['elapsed_us'] for r in normal]),
            'calls_with_candidate_budget_yield': yielded,
            'fraction_calls_with_candidate_budget_yield': yielded/len(calls),
            'max_consecutive_calls_with_candidate_budget_yield': best,
            'scheduler_tick_deltas': dict(Counter(b-a for a, b in zip(ticks, ticks[1:]))),
            'observed_duration_us': quantiles([r['elapsed_us'] for r in calls]),
            'candidate_evaluations_per_call': quantiles([r['evaluations'] for r in calls]),
            'end_phases': dict(Counter(r['end_phase'] for r in calls))}
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    return {'trace': str(path), 'sha256': before, 'schedulers': result,
            'commits': dict(commits), 'total_events': len(events),
            'limitations': 'Historical instrumented baseline only. Yields are evaluator continuation, not proof of idle units. Duration includes observer overhead. No increased-budget gameplay or wall-time prediction.'}


def main():
    report = {'engine_sha256': SHA, 'result': 'passed',
              'native_budget_splits': native_budget_checks(),
              'traces': [trace_review(name) for name in ['isolated-test18-v1', 'isolated-test7-v1']],
              'scope': 'No game launched or patched. Native caller and split instruction slices, whole NOTIONAL budget init/query; scheduler callback explicitly doubled. Existing traces read only.'}
    output = ROOT/'modernization/docs/ai-budget-opportunity-verification.json'
    output.write_text(json.dumps(report, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
