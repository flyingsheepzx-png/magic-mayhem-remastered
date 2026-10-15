"""Offline regression execution against the actual 1.1 compiled modules."""
from pathlib import Path
import sys,types,runpy,json,hashlib
import build_remastered_11 as b

def main():
    # Recover immutable offline map fixtures into this build only.
    backup=b.ROOT/'modernization/backups/development-20260930-remastered-1.0'
    fixture=b.BUILD/'offline-fixture';fixture.mkdir(exist_ok=True)
    for name,h in [('map.bin','a9e2c7c816fe1e7a7fc413eb59ede68bfa14b214fb41189157c42b099c17b9d4'),('tile-types.bin','ecdaad650d5a266a39d0fcf0dc7f90b6cef639331dcdc7e6692df316dda5aaaa')]:
        obj=backup/'objects'/h[:2]/h
        assert b.sha(obj)==h
        (fixture/name).write_bytes(obj.read_bytes())
    import emulate_terrain_diagonal
    emulate_terrain_diagonal.RUN=fixture
    i=types.SimpleNamespace(BUILD=b.BUILD,ROOT=b.ROOT,ENGINE='43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d',sha=b.sha,write=b.write)
    tests=[('install_occluded_body','verify_occluded_units.py'),('install_unit_lifecycle','verify_unit_lifecycle.py'),('install_search_budget','verify_search_budget.py'),('install_group_slots','verify_group_slots.py'),('install_clear_wait','verify_clear_wait.py'),('install_speech_layout','verify_speech_layout.py')]
    results=[]
    for module,script in tests:
        sys.modules[module]=types.SimpleNamespace(installer=i)
        runpy.run_path(str(b.ROOT/'modernization/tools'/script),run_name='__main__')
        results.append(dict(test=script,status='passed',scope='offline compiled x86; no gameplay launch'))
    b.write(b.BUILD/'offline-regressions.json',dict(results=results,repath_sha256=b.sha(b.BUILD/'repath.dll'),qol_sha256=b.sha(b.BUILD/'qol_bindings.dll')))
if __name__=='__main__':main()
