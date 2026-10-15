# Remastered 1.0 vs 1.1 background UI comparison

Created 2026-09-30. The user authorized a paired 1.0 baseline then 1.1 UI
capture sequence. This document and `tools/compare_remastered_ui_11.py` form an
independent write set. No engine/module/build/package manifest changes are part
of the harness. Runtime and visual acceptance remain pending the user's run.

Run commands from `D:/Games/Magic&Mayham`. Help and verification never start a
game. An explicit `--run` is required. The initial implementation was checked
only offline; neither game was launched during harness development.

```powershell
python modernization/tools/compare_remastered_ui_11.py --help
python modernization/tools/compare_remastered_ui_11.py --verify-only
python modernization/tools/compare_remastered_ui_11.py --run --seconds 90
```

The last command executes baseline first, closes/restores it, then executes
candidate. It stages separate package copies under a fresh
`modernization/logs/remastered-ui/<timestamp>/package-1.0` and `package-1.1`.
The 1.0 source defaults to the immutable release staging package
`modernization/releases/remastered-1.0/runtime`; the formal distribution is not
used or modified. The candidate source is
`modernization/playtests/remastered-1.1-p1`, with its sibling launcher
`MagicMayhem-Remastered-1.1.exe` and `runtime/` directory. No fixtures are required.
Both launchers run with the staged `runtime/` as their working directory.

## Initial authorized case

The shortest sequence captures five pages/states, without entering battle:

| Capture | Action and evidence |
| --- | --- |
| menu | Wait for verified primary geometry, wrapper handshake and a menu control containing New Game. |
| new-game-map | Click New Game at baseline `(640,396)`; require the known Grimoire toolbar rectangle; record initial region ID and generated save hashes. |
| region-hover | Move privately to baseline `(760,224)`, wait 1.5 seconds, capture without clearing hover; require unchanged initial region ID. |
| grimoire | Click toolbar at baseline `(976,66)`; require the unique Grimoire close control and capture. |
| return-initial-focus | Close at baseline `(1098,330)`; require map toolbar and the original region ID. |

Coordinates derive from the existing comparison harness's verified 1280x720
surface contract. Baseline receives these native coordinates. Candidate receives
coordinates multiplied by two on its 2560x1440 primary. Its 1920x1440 independent
UI content occupies x=320..2239; battle remains a 1280x720 scene/HUD scaled 2x.
The private input channel bypasses client/output scaling; client dimensions are
checked separately. There is no foreground/cursor fallback.

Inputs use `MagicMayhem.Probe.BackgroundMouse.v1`, a handshake and per-message
acknowledgement `0x4D4D4247`. Clicks include move, down and up with the established
hold durations. Captures use private event `0x804d` on the owned window. The
baseline temporarily uses the pinned background diagnostic wrapper **only in
its staged copy**. Candidate uses its manifest-verified mixed wrapper. Inherited
`CaptureSession` methods capture surface pixels, UI controls, fonts, tooltips
and sprite geometry through read-only memory. The telemetry handle uses access
`0x1010`; a separate verified handle permits cleanup of the owned engine.

FMV is explicitly skipped by setting `PlayFMV=FALSE` and `PlayFMVOut=FALSE` in
staged `CFG/prefs.cfg` after backing it up. `MaxFramesPerSec=30` is required and
retained. Original preferences are restored in `finally`. Startup is bounded to
20 seconds for child discovery/window/handshake/menu readiness (a pending private
message can take its 2-second timeout). Each game has a 30..180-second deadline,
90 by default, starting at launch; an independent watchdog closes owned
processes at the deadline. Cleanup has bounded waits. Staging/hash checks take
additional time outside the game lifetime.

Candidate receives `MM_PROBE_BACKGROUND_INPUT=1`, `MM_PROBE_MIXED_RENDER=1`,
`MM_PROBE_MIXED_FONTS=1`, `MM_PROBE_BATTLE_SHARPEN=0`. Baseline receives only the
background flag. Inherited `MM_PROBE_*` values are cleared before constructing
the environment so they cannot silently change the comparison.

## Identity and preservation

The baseline manifest digest is pinned in the script. Candidate digest observed
on disk **after the installed map fix** on 2026-09-30 is:

`f9afaf395035f423acd253394542998999024fac763cedd439f9e9c40843ca43`

The earlier `4d4259850045e9e51f4c610625d104b6f7c0bb15eeb04df298a17f58a16239fa`
identifies the pre-map-fix manifest. Both retain engine `42f2aac7...`, but the map
fix changes the launcher and manifest. Engine 1.0 is pinned to `43e12256...`;
engine 1.1 to `42f2aac7...`. An unknown engine is refused even when an explicit
new manifest digest is supplied. Launcher hashes cover embedded module changes.
The current 1.1 PNG loader hash is `48916f6c...`, verified as a static file.

If a later intentional asset installation changes the manifest, review that
manifest and pass its literal digest using `--candidate-manifest-sha256`. This
pins reviewed package contents; it is not an ignore-hashes switch. Do not pass a
digest calculated automatically at launch without first reviewing the change.

Every manifest-listed immutable executable/DLL/asset/static CFG file must match.
AI/*.wbt, static CFG control definitions, winmm.ini and ddraw.dll remain exact
hash guards; backing them up does not exempt them from verification.
Player state may differ only at Save/, CFG/Encrypted/, CFG/prefs.cfg, ddraw.ini,
AI/EXPERIEN.DAT, AI/Brain.dat and modernization/config/qol-hotkeys.json.
These are audited by their **current** hashes, rather than
required to match packaging-time state. `--verify-only` reports mutable hashes
separately. Unmanifested code/assets are rejected. `ss/`, `logs/`, and
`modernization/logs/` are recognized diagnostic directories and omitted from
staging. Reparse points/junctions are rejected. Neither source runtime is edited.

Before launch, every staged Save, CFG, AI, root CFG/INI, QoL config file and
wrapper is backed up with byte hashes and original timestamps under each
session's `mutable-backup/`, with `backup.json`. Existing files are restored in
`finally` after engine exit is confirmed. New saves are retained and archived
in `new-saves/`; unfamiliar saves are never deleted. If cleanup fails, the
report identifies the error and keeps the backups/workspace for recovery.
Original source mutable hashes are checked at the end; concurrent source
changes are reported, never overwritten.

The harness refuses existing Chaos/MagicMayhem game instances. It discovers
only its launcher's child, checks its full path and hash, re-enumerates the
owned window, and closes only owned process handles/Popen instances. A launcher
hash alone is not accepted as engine identity. Ctrl+C follows context cleanup;
forced host termination cannot guarantee `finally`, but installed runtime state
is still isolated from the staged run.

## Output and future cases

Each version writes native captures, 2560x1440 comparison output, and
`capture.json`. Baseline comparison output is exactly nearest-neighbour 2x;
this is labeled reconstructed output, not native HD. Paired PNGs retain full
2560x1440 per-side resolution in a 5120x1440 canvas, baseline left. Difference
images and changed-pixel fractions are evidence, not acceptance thresholds.
`comparison.json` includes identities, cleanup/source audits and paired region
IDs. Successful capture means the bounded sequence and basic page gates passed;
layout/text/sprite/colour-key/interaction acceptance still needs review.

An optional `--fixture PATH.sav --fixture-sha256 EXACT_HASH` stages identical save
bytes/timestamps in both copies and reports the identity. The initial new-game
case does **not** load that save. No absent historical fixture blocks this case.
Do not interpret fixture staging as a paired load/save acceptance result.

Future cases are documented here, not enabled by the initial command:

| Future case | Required paired evidence before implementation/run |
| --- | --- |
| Load | Identical pinned fixture, visible row derived from controls/font height, post-load state gate, page and tooltip captures. |
| Save | Same loaded state; save dialog open/cancel/return; explicit authorization for writing a test save; archive new saves and restore originals. |
| Options | Open/cancel/return; readable Chinese/Latin labels and hit rectangles; snapshot/restore settings before any mutation. |
| Battle | Same pinned save and verified unit state; scene/HUD remains 1280x720 scaled 2x; correct mixed coordinate/font transitions; confirm selection before movement. |

New cases should extend this Remastered session and the shared capture helpers,
retain a finite deadline, and use explicit page/state gates. Do not transplant
address maps onto unknown engine builds or promote visual acceptance from
resolution/hash checks alone.


## Executed checkpoint and expanded cases — 2026-09-30

Main agent executed the scoped authorized runs after module installation.
New-game UI completed at `logs/remastered-ui/map-fix-pair-retry-20260930/`.
Actual campaign map (same pinned test5 save) completed at
`logs/remastered-ui/campaign-map-pair-20260930/`. Both source audits reported
zero changes, owned engines stopped, isolated mutable files restored.
Individual results and full-resolution pairs are in each `comparison.json`.
This is runtime navigation/geometry evidence, not final visual acceptance.

Harness now sets process DPI awareness, records physical client separately
from primary surface, gates page readiness on controls, and preserves/retries
transient black frames. It can reuse only completed/restored/hash-matching
baseline-first capture records using `--baseline-capture`; fixture identity is
also checked for fixture flows. New Game leads to the region-entry difficulty
page; do not conflate it with the campaign map.

`--case realm-loaded --fixture PATH --fixture-sha256 HASH` loads the same
hash-verified save in both isolated labs, prioritizes its visible load row,
captures actual realm, hover, Grimoire and return. Toolbar and close clicks
use verified control identity/order/actual rectangles rather than guessed
sprite dimensions. `--case settings-battle` with a verified battle save adds
settings/load/battle/Esc/save/return and asserts32/22/15 battle font sizes,
64/44/30 candidate independent-save-page sizes. Keep test commands and
fixture hashes in evidence reports rather than treating names alone as proof.


Current1.1 wrapper compositor is path-gated. Use `--candidate-in-place` for
battle/transition acceptance; only the exact isolated candidate path is allowed.
It backs up/restores candidate mutable state, timestamps and prefs, closes only
owned processes and audits source bytes. The baseline remains a staged copy.
Cloned candidate independent UI checks are meaningful, but cloned battle
composition/input is disabled; do not count those as passing battle evidence.
The settings/battle case passed at
`logs/remastered-ui/core-installed-pair-20260930/comparison.json`, including
native UI64/44/30 fonts, battle/Esc/return32/22/15 and save-page cancellation.
Fixture passed, cleanup passed, source_changes=[]; final visual acceptance
and other page cases remain open. DPI awareness and full native capture size
are separate from actual client geometry. Future portability should validate
engine identity instead of using an absolute compositor allowlist.


## Portmanteau case — 2026-09-30

`--case portmanteau` loads pinned test5, opens the fourth campaign toolbar
control derived from native rectangles, dismisses tutorial, captures page and
two talisman hover states. `--case portmanteau-full` adds third hover, three
actual talisman clicks, book navigation and Portmanteau return (12 states).
Independent page/control/font/active-tooltip gates and source cleanup audits
remain required; use `--candidate-in-place` for final current path-gated package.
Evidence before/after: logs/remastered-ui/port-before-20260930/,
port-after-20260930/, port-full-after-20260930/. ui-elements-checks.json
checks active tooltip bounds inside the centered content and roundtrip.
No spell binding/change/cast or new gameplay save is implied by these cases.


2026-09-30 minimap checkpoint: initialization-only repair failed pixel review
although native hit RECT/camera jumps passed. Final module also redirects the
per-frame draw-origin load at0x555b90 (`8b8ee2000000`, resume0x555b96), retaining
the displaced ECX load and the actual primary row stride. Final build
`build/remastered-1.1-minimap-v2/`, module SHA
`0ece558e969d36299f46bbfbd344c6ae1997987e804c67e558cefe4d0ba8a01b`.
Installer/rollback `tools/install_11_minimap_v2.py`; rollback this first, then
`tools/install_11_minimap.py rollback` to restore preceding UI-elements version.
Final paired evidence `logs/remastered-ui/minimap-pair-v2-20260930/`, verified
baseline-first capture reused from `minimap-pair-20260930/1.0/capture.json`.
16,349 interior diamond pixels match baseline exactly; camera clicks1222,46
and1162,46 produce identical66,48→1,33→66,48 jumps in both versions. Seven
page/transition pairs pass, fonts remainUI64/44/30 vsbattle32/22/15; source
changes=[] and mutable state restored.27 scanner +88 UI +89 Realm x86 checks
pass. User final acceptance and other outstanding UI pages remain pending.
