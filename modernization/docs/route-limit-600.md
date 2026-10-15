# Single-player route search allowance: 600

The user selected 600 on 2026-09-27. This increases the allowance for the native
direct route method; it does not replace the shared route scheduler and did not
remove the interrupted-movement delay in A/B tests.

## Launch

Run `D:\Games\Magic&Mayham\Chaos-singleplayer-600.exe` for the 600 allowance.
The same installed assets, localization, wrapper and saves are used. The default
logic preference remains 30. This executable is an opt-in single-player entry.
Use `Chaos.exe` for multiplayer until the modified behavior is separately tested.

Startup memory verification read `0x5e174c = 600`. No save changed during this
verification. Full gameplay validation and the larger pathfinding/60 FPS work
remain unfinished.

## Reproduce and verify

From the game directory:

```powershell
modernization/.venv/Scripts/python.exe modernization/tools/route_600_build.py install
modernization/.venv/Scripts/python.exe modernization/tools/route_600_build.py verify
modernization/.venv/Scripts/python.exe modernization/tools/verify_route_600_runtime.py
```

The builder requires the community executable SHA-256
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
It changes only five bytes in the generated sibling, at VA `0x4e5543`.
The sibling SHA-256 is
`856c0a21f45e4ad41bb90d87416dc9d510e10200381c1c1412b17bc24fd2f9bd`.
The original executable remains unchanged and the immutable baseline is retained.

The game extracts/overwrites plaintext `CFG/chaos.cfg` during startup, so changing
that file did not persist the allowance. The loader patch uses the existing
positive-config branch and sets its parsed value to 600.

## Rollback

```powershell
modernization/.venv/Scripts/python.exe modernization/tools/route_600_build.py rollback
```

This removes only the hash-verified generated sibling. The original executable,
configuration, assets and saves are retained. An unexpectedly changed sibling
is preserved and the command refuses removal.
