"""Capture the reported dialog and non-intro Grimoire tab in an owned session."""
import json
import time

from wide169_trial import Session


with Session() as s:
    s.load('test8')
    s.click(1040, 25)
    time.sleep(.6)
    s.capture('test8-grimoire-intro')
    s.click(195, 132)
    time.sleep(.6)
    s.capture('test8-grimoire-realm-tab')
    s.result['realm_tab_controls'] = s.controls()
    s.click(1088, 286)
    time.sleep(.4)
    s.key(0x1b)
    time.sleep(.5)
    s.capture('esc')
    s.result['esc_controls'] = s.controls()
    s.click(640, 420)
    time.sleep(.5)
    s.capture('confirmation')
    s.result['confirmation_controls'] = s.controls()
    print(json.dumps({'run': str(s.run), 'confirmation_controls': s.result['confirmation_controls']}, indent=2))
