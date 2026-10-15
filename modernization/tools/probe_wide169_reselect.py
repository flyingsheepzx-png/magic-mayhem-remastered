"""Reproduce single selection following same-type double selection."""
import json
import time

from wide169_trial import Session
from verify_wide169_input_map import state

with Session() as s:
    s.load('test9')
    s.click(480,340)
    s.click(480,340)
    before=state(s)
    s.click(540,340)
    after=state(s)
    s.result['selection_repro']={'before':before,'after':after}
    s.capture('reselect')
    print(json.dumps({'before_count':before['selected_count'], 'after_count':after['selected_count'],
                      'after_indices':[u['index'] for u in after['selected']], 'run':str(s.run)}))
