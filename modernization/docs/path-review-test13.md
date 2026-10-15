# Pathfinding review / test13 — 2026-09-30

## 1.1 short direct routes — 2026-10-01

### test18 corrective investigation (user-authorized runtime)

Short-direct did not satisfy user reproduction. Updated save SHA256:
91967472e1d061bf30b11bd15d15fad12102246e3876768453e11df3727ee304.
Owned background replay and read-only captures:
logs/remastered-ui/test18-path-before-v1/{samples.json,unit0.bin,map.bin,tile-types.bin,unit-type.bin}.
Origin63,39,9; goal63,20,9. Active saved macro route first goes64,38,9 then65,37,9,
climbs to65,33,13 and returns through64,27,10 to63,26,9. Complete baseline reaches
goal in approximately13.1s from first sample. No new move orders sent.

Actual native0x514360 and occupancy0x522f50 on captured100x100x28 terrain accept
a unique x63 corridor, heights9,9,10,11,12,13,13,13,13,12,11,10,9 then9 to goal.
Extra flat-space predicate0x4f13f0 rejects valid descending ramp at63,29,12 whereas
the complete native transition accepts walkingkind0. Corridor implementation
therefore uses complete transition plus occupancy, not flattened ground tests.

Candidate runtime/hd11/corridor_route.inc uses bounded<=64 axis/diagonal corridor,
unique supported next height z-1..z+1, native adjacent route generator for exact
metadata, and maximum16 output points. Entire corridor is validated before prefix
acceptance. Original goal retained. Deserialize marks a one-shot pending record;
first on_motion uses existing transactional redirect and native movement start to
refresh loaded path only if corridor passes. Failure retains original route.
The saved unit is already moving, so normal inactive short-direct alone cannot
address it. Source and build chain remain isolated1.1, preserving currentUI.

9 offline cases execute actual compiled/native routines on captured test18,
including ramps, inserted solid obstruction, scope exclusions, wrong endpoint
height and deserialize register/stack contract. Report:
build/remastered-1.1-corridor/verification.json. ModuleSHA:
9bfaf72a703a72fba05c25ccdb96051479e2b7dc322dd42ddfcb3312298d2d6a.
NOT installed at this checkpoint: unrelated running FMV diagnostic game blocks
global idle gate. Do not terminate it. Installation and updated paired runtime
probe remain required. First roof click used incorrect coordinates; corrected
probe uses main portrait1217,640 logical battle and must verify resulting view.

Follow-up: user confirmed closure; installed via build_11_corridor.py, then actual
owned test18 replay completed at logs/remastered-ui/test18-path-corridor-v3.
225 snapshots: all grid x63, worldx2016..2018 (initial saved subcell offset), goal
63,20,9 reached. Prior run gridx63..65. Prefix16 then final3 native nodes preserved
the same final destination and valid ramp heights. Baseline goal ~13.12s vs new
~11.93s from first sample; these runs include capture/portrait interactions and
are not a controlled performance benchmark. Paired report in that folder.
Some multi-field snapshots overlap native transactional updates (brief zeroed
next node/restored origin); do not interpret those torn reads as stable movement
regressions. Stable grid trace and endpoint confirm the reported sideways detour
removed. Correct portrait1217,640 double click executed; resulting surface captured.
User saves/settings restored, cleanup_errors empty; all5882 runtime hashes pass.
Broader path gameplay acceptance pending user feedback. No further optimization.

Installed candidate backup: modernization/backups/remastered-1.1-corridor.
Close game then rollback from root:
`C:/Python314/python.exe modernization/tools/build_11_corridor.py rollback`.
Roof-display persistence in saves recorded as separate TODO, preserving old saves;
Alt+F4 hang remains queued after this path iteration.

User reported test18 protagonist takes two southeast then two northwest steps
before approaching a northeast portal. No runtime reproduction performed: current
project rules require installing one change then stopping for user testing. Static
analysis identifies a plausible source: 0x5128a0 can select macro waypoint targets
before its low-level search/direct path; more search budget does not bypass those
targets. This is a bounded improvement, not a verified diagnosis of test18.

Native 0x513370 constructs at most 16 adjacent line waypoints, checks transitions
through 0x4f3990, and writes original direction/movement metadata. New detour at
0x51292f, signature `8b 8c 24 c4 02 00 00`, tries this native generator on the
original request target before macro navigation rewrites it. EBP is unit, original
ESP+0x2c0/+0x2c4/+0x2c8 are request XYZ. Successful bounded full flat route goes
to native copy/apply branch 0x5132ac with EDX=0. Clears unit+0xd03 so native macro
destination override/three-waypoint truncation cannot corrupt the direct result.
Failure replays `mov ecx,[esp+0x2c4]` and resumes 0x512936 with flags/registers
preserved. No custom waypoint metadata, motion or reservations synthesized.

Scope: single-player, no search continuation, active unit object, ordinary move
command2, currently inactive motion, width-one normal walking type, no special
flags or movement profile; valid in-map target, same layer, distance1..16 cells,
no shorter toroidal wrap required. Every generated point must have flat ordinary
walking metadata and pass existing walking_edge (native space/headroom, occupancy,
transition and movement-kind0). Blocked/slope/large/multiplayer/special/long paths
retain macro/search fallback. Test short portal approaches and obstacle avoidance.

Engine identity remains
`42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`, image base0x400000.
Read-only Ghidra export: D:/Tools/magic-mayhem-re/projects/path18-20261001-export.
Hook signature checked against current engine. Latest installed resource101 was
byte-identical to build/remastered-1.1-p1/repath.dll before rebuilding that source;
render/clock/game-time code preserved. Resource102 is exact installed minimap-center
DLL, retaining all current UI fixes. Only isolated launcher and manifest replaced.

Source: runtime/hd11/short_direct_route.inc. Build/installation:
tools/build_11_short_direct.py. Verification: tools/verify_11_short_direct.py,
build/remastered-1.1-short-direct/verification.json. 29 Unicorn cases execute
compiled adapter plus actual native line generator/direction construction, testing
12 direction/length combinations, 15 scope exclusions and 2 failure paths. External
terrain/occupancy predicates are stubbed; missing historical captured terrain
files prevented reuse of old test10 terrain fixtures. No claim of actual test18
terrain clearance or measured performance. User gameplay acceptance pending.

Installed resource101 SHA256:
`49bb7663934a16e7fb53fac37df3e96f52aa2e82e0ce1ee481e3f046142674b2`.
5882 runtime hashes passed; formal v38/1.0, assets, engine, saves/config unchanged.
Backup: modernization/backups/remastered-1.1-short-direct.
Rollback with game closed from project root:
`C:/Python314/python.exe modernization/tools/build_11_short_direct.py rollback`.
Stop for test18 user feedback. Alt+F4 unresponsive exit remains queued next.

## Follow-up optimization 6: wake cleared occupancy waits (v33)

User accepted this iteration on 2026-09-30 before requesting rendering work.

Native `0x510e80` calls blocker handling `0x511c40`. A result of 1 enters
action 15 with timer 7 at `0x511bdd`. Native `0x50f7c0` decrements the timer
and invokes the existing retry callback. Separately, `0x51a600` can replan,
and `0x51b7f0` orders blockers aside using size/type/ID priority and a six-tick
wait. Globally reducing waits could disturb that ordering, so v33 only records
the first specific seven-tick occupancy-wait site.

Each recorded unit must remain a single-player, active, width-one normal
walker on ordinary move command 2, waiting action 15, without active motion or
special movement flags. The unit pointer/ID, origin, route cursor/next cell and
goal must match; timer must decrease monotonically. Invalidated records are
discarded, including on native reset/deserialization. If the original adjacent
edge passes native space/headroom, occupancy and transition checks with walking
kind 0, set the timer to 1 so the original decrement/retry executes this update.
No new route, destination or reservation is written. Remaining blocked waits,
larger units, special modes, combat orders and multiplayer keep native behavior.

Hooks: `0x511bdd` replays `c7 86 6c 06 00 00 07 00 00 00`, resumes `0x511be7`;
`0x50f823` replays `8b 86 6c 06 00 00`, resumes `0x50f829`. Signatures are
verified before patch installation. Source: `runtime/wide169/repath_multiunit_trial.cpp`.
Read-only Ghidra evidence: `D:/Tools/magic-mayhem-re/projects/path-review-export/`.

Build and 28 offline checks passed (`tools/verify_clear_wait.py`, report
`build/clear-wait-v1/wait-verification.json`). Compiled hooks preserve register,
flags and stack contracts. Predicate-stub cases cover wait tracking, blocked
then cleared edges, scope exclusions, changed routes/identity/timers and both
lifecycle detours. Two cases execute actual native validators against captured
test10 map cells: a clear edge wakes; a solid destination does not. These are
offline checks, not gameplay acceptance or a measured performance gain.

Installed package: `build/wide169/package-v33-clear-wait`.
Launcher SHA-256: `211f731a94be48d4adfe1240408c195be7f7d9ebd54a331d0761b739a7a852a1`.
Embedded resource101: `14f26593d6e6eb00651593d7b1a3365fd72dfa99fcbe0a59274f4a089657769c`.
Engine, terrain DLL, other launcher resources, saves and configuration are
preserved. Backup: `backups/wide169/path-review-1790709035649636700`.
Rollback: `python modernization/tools/install_clear_wait.py rollback` restores
the exact v32 entry and manifests. No game was launched. User should test
test13 group crossings and narrow passages for reduced residual pauses without
new oscillation, overlap or failure to resume; stop until their feedback.

## Follow-up optimization 5: extend native group slots (v32)

The initial review's implication that group orders simply share one target was
incomplete. Static analysis of viewport command handling `0x4fdad0` found native
destination allocation `0x517a50`, with shared per-order cursor `0x6e985c` and 17
candidates: centre, four diagonal neighbours, four axial distance-two positions,
four diagonal distance-two positions and four axial distance-four positions.
Once the cursor exceeds 16, the allocator returns the common clicked target.
Its first-caller flag resets the cursor for each group order. A separate allocator
`0x517e80` handles other behavior; it remains unchanged.

v32 retains the original first 17 candidates and adds the 32 previously omitted
integer XY positions within squared radius 16, shortest distance first, with a
total bounded limit of 49. The native maximum distance from the click stays four
cells. Extra candidates only apply when the allocator return address is
`0x4fefd0` (call at `0x4fefcb`, normal ground move construction), single-player,
valid unit slot, width-one walker, ordinary movement profile and map dimensions
at least 9x9. Attack/unit interaction branch `0x4fe73b`, special target branch
`0x4feb20`, alternate/queued-repeat branch `0x4ff0e0`, special movement modes,
large units and multiplayer retain native fallback. The normal caller may itself
construct a Shift-queued movement order after allocation; this shares its
ordinary ground allocation semantics. First selected unit always keeps native
centre behavior. No group command serialization or unit order application changed.

Hook `0x517a81`, expected `83 f8 10 0f 8f ff 02 00 00`, replaces only the original
index upper-bound branch. EBP holds the unit; original ESP+0x14 is return address,
+0x18/+0x1c origin XY, +0x28/+0x2c output XY pointers. Added candidates rejoin at
`0x517b64`, before original height selection, space/headroom (`0x414940` ->
`0x4f46b0`), support (`0x414890` -> `0x4f4330`) and native transition checks
(`0x517db0`). Unsuccessful candidates advance the original cursor and retry;
exhaustion at 49 still uses native fallback. Coordinate wrapping matches native
toroidal convention. This changes available destinations, not route/collision
rules; it does not guarantee congestion-free travel or reserve destinations.

Original/installed engine identities and image base remain those below. Ghidra
read-only exports in `D:/Tools/magic-mayhem-re/projects/path-review-export/`.
An initial export from interior address `0x4fdad6` failed decompilation; exporting
verified entry `0x4fdad0` succeeded. Relevant allocator/caller/helper spans compared
byte-for-byte between known original and installed engine before the build.

`tools/verify_group_slots.py` runs actual compiled hook plus native allocator and
terrain validation in Unicorn on the captured test10 map: 165 checks pass.
Includes original successful slots, 17/49 boundaries, multiplayer/width/movement/
caller exclusions, actual solid-cell rejection, and 49 unique candidate offsets
within the unchanged radius across normal and map-edge centres. At the real
map target (54,74,5), original exhausted cursor 17 returns the shared target;
new code instead accepts supported (54,73,6). This is offline allocation evidence,
not end-to-end unit movement or gameplay acceptance. No game launched.

Build/manifest/report: `build/group-slots-v1/`. Installer:
`tools/install_group_slots.py` actions build/install/rollback. Rollback restores
exact v31 entry/manifests with game closed. All other embedded resources,
launcher non-resource sections, external terrain DLL, engine, saves and config
preserved by integrity checks. User test target: ordinary multi-unit moves toward
open/obstructed ground, particularly enough units/blocked candidates to exceed
the original slots; ensure interaction/portal behavior remains normal. Await
feedback before another optimization.

## Follow-up optimization 4: opt-in terrain trace (v31)

User requested continuation after v30. Cost/benefit reassessment selected a
small low-risk change before gameplay-changing group destination behavior:
terrain exception diagnostics no longer open/write/close a file by default.
Only the DLL initialization of its logging flag changes. Explicit environment
`MM_TERRAIN_DIAGONAL_TRACE=1` restores the existing bounded diagnostic behavior;
unset, 0 and 10 leave it off. Previously the first 4000 accepted exceptions
could open a file per search edge. Benefit is removal of avoidable file I/O;
no measured FPS improvement or movement behavior change is claimed.

New terrain DLL SHA: `3791b8eabf83428b43c21d95d44d43996fd1f2275fbd1b882c803c4fa456ad41`.
Parent launcher: `aca872718155d51b39c8c74ab41cb7801dc7fc1ff7807ab05acf8b559839ade1`.
Exact launcher hash and pinned-string offset in `build/terrain-trace-v1/manifest.json`.
Installer checks the known v30 launcher/engine/terrain hashes and replaces only
the one UTF-16 terrain hash string in launcher .rdata. Reversing that replacement
reproduces the complete original launcher byte-for-byte. All resources retained,
including v30 repath/replay and QoL. Runtime data/configuration and engine unchanged.

`tools/verify_terrain_trace.py` runs native terrain functions plus old/new compiled
hooks offline against the existing captured test10 map. 80 comparisons match
across single/multiplayer, unit widths/heights, starting solid obstacle and
portal-side slopes/both directions. Four emulated DLL attach cases verify
the environment switch, with native patching disabled for that initialization
test. Build and installation integrity passed; no game launched.

Build/install/rollback: `tools/install_terrain_trace.py` with the corresponding
action. Rollback restores exact v30 launcher, external terrain DLL and manifests
(close game first). User testing pending: ordinary group movement in test13,
optionally the previously accepted test10 portal-side diagonal. This is one
isolated optimization; wait for feedback before continuing.

## Follow-up optimization 3: ordinary search allowance (v30)

User requested the next step after v29; no detailed v29 runtime results were
provided. Ordinary requests used 70/210 expansions even after v27 removed the
cross-unit budget throttle. v30 raises those single-player requests to 600,
matching the existing direct/redirect allowance, while retaining v27's shared
601 per-request grant. No change to direct searches or custom redirects.
Both player and AI requests use the same native path. Early success exits
unchanged; hard/unreachable cases can consume more CPU. More search opportunity
does not prove every route shorter or eliminate occupancy waits. No runtime
route-quality/performance measurement was made; user acceptance remains pending.

Evidence (same hash-verified engine/original and 0x400000 image base below):
`0x54b800` performs the native search and retains frontier state when budget
runs out, then reconstructs the best available partial route. Neighbor expansion
`0x4ebae0` checks a positive allowance and decrements it once at the end.
Search neighbor storage and reconstructed path vector grow through native
allocations (including `0x440260`). The fixed output route is independent:
`0x54bd5b` compares its count to 16 and `0x54bd5f` exits before writing when
count >=16. Increasing the expansion allowance does not expand that buffer.
Container growth and partial-path behavior were inspected in read-only Ghidra
exports under `D:/Tools/magic-mayhem-re/projects/path-review-export/`.

Hook at `0x513162`, expected bytes `8b 35 88 f1 6d 00`, sets remaining request
budget `0x6df18c` to 600 only when player count `0x6e1f0c` <=1, replays the
original shared-budget load to ESI, resumes at `0x513168`. Native minimum and
debit logic remain. For multiplayer the original budget passes through exactly.
Runtime verifies signature before applying; build compares the request/search/
neighbor/vector code spans between original and installed engine.

`tools/verify_search_budget.py` executes compiled request and budget detours,
native minimum and native output-cap branches offline in Unicorn. 29 cases
passed: single/multiplayer, 0/1/70/210 request budgets, 0/53/601 shared budgets,
and output counts 0/15/16/17/600. Registers/stack and retained single-player
shared remainder verified. This validates plumbing and bounds, not route quality.
Reports, exact source/launcher/module identities: `build/search-budget-v1/`.

Installed with `tools/install_search_budget.py install`. Rollback action restores
exact v29 entry and manifests with game closed. Installer verifies unchanged
other resources/non-resource sections, saves, configuration, engine and terrain
DLL. No game launched. Test complex/long routes and simultaneous multi-unit
requests for route behavior and stalls, then provide feedback before next item.

## Follow-up optimization 2: lifecycle invalidation (v29)

User accepted v28 and requested the next item. v29 clears the specific unit's
redirect state before native reset `0x5060a0` or deserialize `0x527310`. It also
clears its current/previous replay actor records and invalidates the captured
frame, tags and bars until the next native capture. No native unit/save bytes
are changed by these callbacks; no per-frame scanning is introduced. Other
units' redirect/actor records remain intact. This is preventive reliability
work, not a measured speedup or a claim of reproducing a user-visible defect.

Static evidence (same original/installed engine hashes listed below; image base
0x400000): `0x5060a0` frees owned auxiliary objects, zeroes all 0xe4b unit bytes,
and restores the slot ID from its argument. Manager reset calls it per slot at
`0x52a5d3`. `0x52c160` loads the unit pool in place by calling `0x527310` for each
slot; the latter reads unit ID, active flag, coordinates and subsequent fields
from the save. Pointer+ID can therefore match across lifetimes. Read-only Ghidra
exports remain in `D:/Tools/magic-mayhem-re/projects/path-review-export/`.

Both hooks receive the unit in ECX. Reset signature `6a ff 68 1b 24 5c 00` is
replayed as the original two pushes before continuing at `0x5060a7` (before SEH
registration); deserialize signature `81 ec 48 01 00 00` is replayed as original
stack allocation before continuing at `0x527316`. Build checks original/current
code spans and hashes; DLL attach checks both hook signatures before mutation.
Invalid/out-of-pool pointers are ignored. Reset occurs even on a later failed
deserialize, since native code may already have partially replaced the object.

`tools/verify_unit_lifecycle.py` executes the actual compiled hooks/callbacks
offline in Unicorn. Eight cases cover first/middle/last slots and misaligned
pointers for both entries, target-only cache clearing, captured-frame
invalidation, unchanged native unit bytes, register preservation, stack balance
and reset's original exception-handler pushes. All passed. Report and exact
source/module hashes: `build/unit-lifecycle-v1/`. No game launched.

Install/rollback tool: `python modernization/tools/install_unit_lifecycle.py`
with action `build`, `install` or `rollback`. Rollback restores exact v28 entry
and manifests; close game first. Saves/configuration/engine/terrain and all
other launcher resources remain unchanged, verified by installer. Gameplay
acceptance pending. Test loading test13 repeatedly after moving/redirecting,
then continue group movement; if practical, check newly summoned/replaced units.
This change does not redesign serialization of an in-flight custom segment or
claim exhaustive lifecycle coverage beyond the verified native entries.

## Follow-up optimization 1: replay index (v28)

The user authorized an iterative program: install one optimization, report,
wait for their testing, then choose the next cost-effective item. v28 replaces
the linear per-command scan with a frame-local 16384-bucket hash index over at
most 5000 tags. Fixed storage costs 105536 bytes, no heap allocation. Full
36-byte equality still determines matches; reverse insertion retains earliest
tag wins even for duplicate commands with different owners. The index rebuilds
each eligible frame, so stale entries cannot survive tag resets. Hash collisions
cannot cause incorrect matches. Worst-case collision work remains linear.

Production header `runtime/wide169/command_index.h` is shared with the offline
C++ test `tests/command_index_test.cpp`. MSVC x86 /O2 checks compared 72000 queries
against the old linear algorithm, for both normal hashing and a forced single
bucket. Covered zero/full counts, duplicates, misses, byte differences and
frame resets. All passed. Synthetic 5000-tag/12000-command load, 10 rounds:
linear 113.970 ms, indexed 3.190 ms including index rebuild, approximately 35.7x
faster in this matching operation. This is not a measured game FPS improvement.
Build/test artifacts and output: `build/render-index-v1/`.

Installed using `python modernization/tools/install_render_index.py install`.
Rollback: `python modernization/tools/install_render_index.py rollback` with
game closed restores v27. Exact module/launcher/source hashes are recorded in
`build/render-index-v1/manifest.json`; baseline and package integrity verified,
all other launcher resources/sections and protected game data preserved.
Gameplay remains untested by the agent. User should check test13 multi-unit
movement, turns, camera rotation, effects and occlusion for regressions. Stop
here and wait for feedback before optimization 2.

Ordered work completed in source: (1) redirect rendering correction; (2)
single-player shared search throttle removal; (3) review and conservative overhead
reductions. Installed together as v27. No game was launched. Intermittent
occlusion was not reproduced here; gameplay acceptance remains with the user.

## Delivery and verification

- Parent launcher: `c23ec895ca1cb5dae31556a9e76713e4963e5125ca4501ed63a344f5ffbe2301`.
- v27 launcher: `685b7452096bd22ba1bbcb37a3dc78d6199fa147561b4cc1621890369742e16c`.
- New resource 101: `1f7f52edffb2681db7a8ef0f6effe6c344e2765278cad1877a9044ddbb610b7a`.
- Unchanged engine: `43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`.
- Unchanged QoL resource 102: `af65b4ba36191bdb11840ff914cee314d7efc2b751c1028aab6ceee516b1b873`.
- Unchanged terrain DLL: `0a18ddae17025d16b44197b4eddca09685a63c1a8dbac130d9c3e1e5d7068391`.

Build/install tool: `modernization/tools/install_path_review.py`, actions `build`,
`install`, `rollback`. Rollback with the game closed restores the exact v26 entry
and manifests. Backup: `modernization/backups/wide169/path-review-1790706523647113700`.
Source snapshots and manifest: `modernization/build/path-review-v1/`.
MSVC x86 build passed. Only resource 101 changed; all other resources and all
non-resource launcher sections were compared byte-for-byte. Saves, CFG,
configuration, engine and terrain DLL hashes remained unchanged. Installation
baseline verification passed. No movement-speed or 30 Hz setting change.

## 1. Redirect sorting and prediction

Native sorting covers origin A and destination D; a redirect actually starts at
physical P on the previous segment. P can be outside A–D on flat ground.
`on_draw` now extends native foreground sorting bounds to include the physical
cell and height for an active custom segment, using the native rotation policy.
Collision and sprite screen position are unchanged. Replay prediction now uses
P–D velocity and remaining custom progress rather than native animation A–D.
This addresses two concrete mismatches, but does not prove every intermittent
occlusion case fixed. Test13 user acceptance must check foreground walls too.

Evidence: community original SHA
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`,
preferred image base `0x400000`; read-only Ghidra exports under
`D:/Tools/magic-mayhem-re/projects/path-review-export/`. Rendering function
`0x4f8960`, rotation selection `0x4fa01a`, sort conversion `0x4fa0bf` (grid*32+16,
height*16), existing hook `0x4fa261` (EDI unit, ESI scene; original stack locals
+0x18 X, +0x14 Y, +0x20 height), draw enqueue `0x4ffd30`.
Active source: `runtime/wide169/repath_multiunit_trial.cpp`, not the obsolete
unit-0 source. The pre-change rebuild reproduced embedded .text, .data,
.fptable and .reloc exactly; .rdata includes differing build metadata.

## 2. Search scheduling

Native thiscall request `0x5128a0` has per-request limits 70/210, shared budget
`0x6df188`, remaining request budget `0x6df18c`. `0x513162` takes the minimum;
`0x5131cd..0x5131d3` debit both. At `0x5131d8`, exhausted shared budget with
remaining request work sets continuation `0x6df184` and returns 2. Unit callers
such as `0x519ae0` yield. Even native fast-route success reaches this check.

New entry detour grants 601 shared units per single-player request. Original
70/210 bounds remain, so a request cannot exhaust that shared allowance. Entry
signature `81 ec ac 02 00 00` verified against the installed engine and again at
DLL attach; detour replays `sub esp,0x2ac`, resumes `0x5128a6`. Multiplayer retains
native budgets. Custom redirect search keeps its independent existing limit up
to 600 and no longer debits either native scheduler global. This removes the
identified shared-budget delay, not reservation waits or all AI scheduling.

`verify_path_request_hook.py` runs the compiled detour offline in Unicorn:
8 single-/multiplayer cases, zero/negative budgets included, verify registers,
stack adjustment, continuation and budget. All passed; report at
`build/path-review-v1/hook-verification.json`. Runtime latency remains untested.

## 3. Review results

Implemented:

- Full-map ownership diagnostic scans now require `MM_PROBE_REPATH_TRACE=1`.
- The same switch gates verbose sprite/draw logs and quadratic diagnostic
  terrain-frame matching. Essential replay actor tagging remains unconditional.
- 33 swept-path samples validate consecutive identical cells only once.
  Endpoints, every distinct sampled cell, support/headroom/occupancy checks,
  native segment startup and rollback remain intact.

Further opportunities, deliberately not bundled into this patch:

1. Native 70/210 request limits, redirect limit 600 and 16-waypoint buffers are
   different constraints. More search work may help complex routes; first audit
   planner storage and partial-route semantics and profile long/blocked routes.
2. Shared destinations and reservations still queue units. Formation destinations
   or shared paths require footprint-aware dynamic collision handling.
3. Replay command ownership performs up to 12000×5000 comparisons per frame.
   A hash index preserving first-match behavior is a promising separate change.
4. Redirect state identity uses pointer and unit ID. Save reload/reused slots
   merit a future verified world-generation reset; cursor/finish guards alone
   do not establish reuse safety.
5. Terrain exceptions and instant redirects cover eligible width-one walkers.
   Larger units and other movement modes fall back to native behavior. Terrain
   exception logging opens (bounded to 4000 accepts) are a smaller remaining
   cost; its accepted DLL was preserved in this patch.
6. Sweep checks, native edge validation and reservation rollback enforce
   correctness. CPU surplus is not grounds to remove them.

Test13 remains the user acceptance fixture for repeated flat/slope turns,
multiple units and camera rotations. Confirm legs no longer disappear and
units do not draw through foreground walls. Distinguish faster search dispatch
from legitimate collision waits. Save formats and multiplayer stay unchanged.

## Save17 long-distance route (2026-10-02)

### Save20 boundary-topology correction (2026-10-02)

Installed `wrap-route-v1` resource101, continuing command-response-v2 with all
command/marker fixes intact. User reports protagonist moving away when collecting
an apple in save20. Authorized isolated read-only observation:100×100×28 map,
unit0 `(88,59,5)`, goal `(0,56,5)`; saved route heads west87/86/... and after15s
reaches `(76,60,5)`. Save20 SHA
`4f151ef2a568e4dcdab4b310b0dff0ed5402a6a2f0b15f7fc8003fdd7d2b44a9`.
This is the rectangular-topology omission in the save17 full-map search, not
evidence of wrong apple pickup task/command-response interference.

Native514360 accepts99→0 and native513370 emits its correct seven-word route
record (direction2). The game has wrapped X/Y map topology. Updated long_route.inc
to wrap neighbor X/Y and use toroidal octile distances (min(delta,size-delta))
in A*. Z stays bounded. Every edge, including seam crossings, still passes native
occupancy/transition and direct-record validation. Search caps, cache lifecycle,
save format, ordinary local/corridor planners and multiplayer behavior remain.
Existing mid-segment redirect refuses a raw distant seam jump, leaving native
movement to cross the edge rather than interpolating across the map width.

Compiled save20 route14 points now heads east89..99, crosses to0, then reaches
`(0,56,5)`.24 seam/bounds/scope/cache-continuation checks +37 path regressions +43
command-response/marker checks pass (104 total). Those command tests retain their
documented doubles; real apple pickup and movement acceptance pending user test.
The pre-fix isolated observation only was launched, no post-install gameplay.
Evidence logs `remastered-ui/save20-route-before/`; new check tool
`tools/verify_11_wrap_route.py`. Latest build/source chain
`build/remastered-1.1-wrap-route-v1/`. Install/rollback
`tools/install_11_wrap_route.py`, backups `backups/remastered-1.1-wrap-route-v1/`.
Hash checks preserve modules102/103, wrapper/settings/assets and player saves.

Installed `remastered-1.1-long-route-v2` into the formal release, frozen package
and continuing candidate at the user's request. Fixture `Save/17.sav` SHA256
`03aefae5b9f3f11e133da82fcf64633fac4830da5a9b79a6a1d45fa304d273c2`:
unit0 starts `(51,71,6)`, destination `(71,71,8)`. The old planner follows the
southern local route and stops at `(70,78,6)` with an empty route. Increasing
its search budget to2400 did not correct this. Native terrain validation finds
a legal full-map detour around the divider via northern y10; proximity in
screen coordinates does not establish a short traversable path.

`runtime/hd11/long_route.inc` adds bounded full-map A* for eligible ordinary
single-player width-one walkers. Existing local/corridor planners remain first.
It retains native occupancy/transition checks and generates native seven-word
waypoints, sends at most16 at a time, preserves the original destination and
caches the remaining route. Cached edges are revalidated before emission;
unit replacement/deserialization forgets cached paths. Limits:16384 nodes,
8192 expansions,512 cached points,32 unit cache slots. Failure falls back to
existing behavior. No save-format or multiplayer changes.

Existing37 regression checks passed. Isolated save17 observation showed the
candidate turning north onto the long route; full arrival remains unverified.
The long observation paused mid-route and later the protagonist died; the user
confirmed this area includes story and dangerous combat, requested installation
and will perform the remaining acceptance. This is not proof that every
long-distance route or segment continuation succeeds. Repeated unreachable
requests may have a higher CPU cost; profiling/cooldown remains a follow-up
if observed, not an implemented optimization.

Evidence: `logs/remastered-ui/save17-route-before/`,
`save17-route-budget2400/`, `save17-route-long-v2/` and
`save17-route-long-v2-complete/`. Installation verifies current entry/manifests,
engine identity, compiled resource101 and unchanged resources102/103 before
replacement; saves, settings, wrapper and assets remain untouched.
Rollback: `C:/Python314/python.exe modernization/tools/install_11_long_route.py rollback`.
Backup: `modernization/backups/remastered-1.1-long-route-v2/rollback.json`.

## Movement start/cadence review — 2026-10-02

User reports intermittent jerky motion, slower ascent than descent and possible
startup acceleration; requested investigation/optimization assessment. No runtime
change or gameplay launch in this review. Current all3 launcher/resource hashes
match port-bindings-hd102 + roof-ghost-v2 101 + retained103. Engine SHA256:
42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.

Confirmed by actual installed engine bytes executed offline:

-505920 adjusts desired ordinary walking rate: dz+1 ->2/3, dz-1 ->3/2;
 movement kind4 bypasses these slope modifiers. It also derives a bounded
 next speed from previous speed and creature-type acceleration at+10 using
 square-root distance math (native4eaca0/4eac10 and CRT59bee0 executed).
 CFG/creature.cfg PLAYER_WIZARD has Acceleration=10. Synthetic divisor4,
 nominal240, acceleration10 flat sequence151,240,240 demonstrates startup
 acceleration, not measured protagonist speed or time. Slope targets160/360
 under those same synthetic inputs. The helper is called at segment setup;
 it is not a per-frame continuous acceleration integrator.
-511411..511471 preserves speed/remainder for ordinary ongoing motion5fc=2.
 For a different action it resets b63/b6b when carry flagb73 is clear,
 movement kind610 differs, or native direction difference exceeds1.
 Five actual branch/write fixtures execute; direction helper4ead10 is doubled.
 Therefore normal straight cell-to-cell movement does not restart from rest
 each cell. Retarget/replan paths call50db60(15) before510e80, so their
 existing carry/direction conditions can restart acceleration; occurrence
 frequency and relation to user's intermittent symptom are unmeasured.
-5104d1 adds current speedb63 to remainderb6b, divides by step thresholdb67.
 Zero quotient returns before moving. Each animation/root step later subtracts
 one threshold; position derives from integer offsets/6. Native per-frame
 motion can be nonuniform even at constant average speed; unit reservations/
 wait states and whole-frame stalls remain separate possible causes.

Current source evidence identifies a high-priority rendering consistency risk:
logic_time_trial.cpp effective_speed at30Hz applies31/50 (launcher sets
MM_PROBE_ORIGINAL_WALLTIME=1), while render_replay_trial.cpp before_draw
uses raw b63/threshold as Actor.speed. Continuous projected_shift uses
phase+speed*elapsed/span without that factor. Eligible30Hz motion therefore
has a nominal prediction-rate ratio50/31 ~=1.613 relative to actual accumulator
contribution, excluding integer remainder and max_phase clamping. This is a
verified source mismatch, not live proof of visible correction/jitter. Continuous
replay is already enabled; simply enabling60Hz or turning it on is not a fix.

Recommended next single iteration: share a pure timing-contribution policy
between logic and replay, account for compensated rate without mutating phase
while rendering, preserve native gameplay speed/acceleration/collision. Validate
slow/fast movement, all directions/slopes, segment ends, retargets, root-motion
frames,40/20 logic settings and multiplayer exclusion. Then user gameplay
feedback before any separate acceleration tweak. Secondary investigation:
preserve verified uninterrupted retarget momentum where native safety permits;
do not globally bypass restart/occupancy waits or alter movement endpoints.
Removing acceleration/increasing it is a balance/feel change and may alter
travel times; it is not necessary for visual smoothing. Player and AI units
must share any later movement policy.

Evidence/tool: tools/analyze_movement_cadence_11.py and
logs/movement-cadence-11/native-analysis.json. Ghidra read-only/noanalysis
exports outside repository at D:/Tools/magic-mayhem-re/projects/
move-start-20261002/functions/. Initial request for interior5104d0 failed
and export stopped after505920; corrected entry5104b0 exported successfully.
Installed engine execution/disassembly confirms the important arithmetic,
independent of provisional Ghidra prototypes. No live stutter reproduction,
CPU profile, average30/60-frame acceptance or measured startup duration claimed.

### User-approved movement smoothing handoff — 2026-10-02

User requested recording this plan for another session to execute. This session
does not implement or install it. Execute two separate iterations, with user
gameplay feedback between them:

1. First unify compensated movement contribution and render prediction through
   a shared pure timing policy. Verify the current installed launcher/module
   sources before editing; the source paths named above describe the analysis
   snapshot, not permission to replace newer changes. Rendering must not advance
   the logic accumulator or its fractional compensation state. Preserve actual
   movement speed, native acceleration, slope rules, collision/reservations,
   settings and multiplayer fallback. Account for integer rounding/remainder,
   selected logic rate and replay interval; do not blindly multiply every
   prediction by31/50. Compile and verify targeted checks, then hash-gated
   backup/install/rollback and stop for user acceptance. The source mismatch
   is confirmed; live jitter causality and improvement remain unverified.
2. After feedback, investigate and refine segment momentum continuity. Intended
   behavior: retain speed during uninterrupted walking/replanning, reduce speed
   appropriately for sharp turns, and retain native startup after an actual
   stop. Do not globally disable acceleration or bypass safety waits/action
   state handling. Observe actual reset branches before selecting a turn-speed
   policy; no exact angle, reduction factor or stop threshold is approved yet.
   Preserve terrain modifiers and movement endpoints, and use the same policy
   for player and AI. Measure travel-time/turn/occupancy effects rather than
   claiming this second change preserves all travel times by construction.

Clarification: replan alone does not imply restart. Native511411..511471 first
preserves speed/remainder when5fc=2; otherwise reset follows clearb73, changed
610 movement kind, or4ead10 direction difference>1. The latter is a discrete
direction comparison, not an established angular threshold. Replanning calls
can enter these conditions, but their runtime frequency is not yet measured.
Actual stop/turn/replan tests require explicit gameplay-debug authorization;
ordinary implementation ends at installation for user testing under AGENTS.md.

### Movement smoothing iteration1 — 2026-10-02

Implementation: `build/remastered-1.1-movement-timing/`, builder/installer/
rollback `tools/build_11_movement_timing.py`. Source101 is the installed
roof-ghost-v2; launcher sources and unchanged102/103 come from the latest
roof-click-floor. Installation refuses changed launcher/manifest snapshots.
No segment-reset, acceleration, slope, collision, reservation or AI code changed.

Shared pure policy `runtime/hd11/movement_timing.h` retains the installed logic
arithmetic exactly: eligible30Hz single-player positive speed31/50 with per-unit
integer carry (diagnostic alternative2/3);20/40Hz and multiplayer retain native
contributions. The render reader snapshots the NEXT integer contribution with
the matching unit's carry, without consuming it or initializing/replacing its
table entry. Pointer reuse reads zero carry until logic initializes the entry.
Continuous prediction converts elapsed seconds using the selected logic rate,
rather than the measured interval between captured/presented frames. Existing
0.75-tick cap, segment/height clamps, redirection geometry and30Hz-only replay
eligibility remain.20/40Hz are not newly enabled for continuous replay; their
existing native fallback remains. Observed-delta replay still uses measured span.

Verification: shared C++ conservation across10000 changing-speed contributions
per combination,20/30/40Hz/player/id boundaries and replay interval conversion;
5185 compiled x86 cases comparing old/new logic results and carries, ABI,
repeatable read-only prediction, native accumulator, pointer reuse and renderer
projection across four rotations/slopes/endpoints/redirect geometry. Existing
58 roof/raster,24 wrap-route,43 command-response and37 dynamic-wait regressions
pass. Report `build/remastered-1.1-movement-timing/verification.json`.
Module101 SHA256 `0f618f11afe86cba77b33a64938b07c25da2dad1afc365e414ae63ad43535dd2`.

Compatibility note: module102 is byte-for-byte preserved. Its optional
MM_PROBE_OPTIONS_LOGIC diagnostic used an already-stale hardcoded module101
RVA7c80 (prior installed tick hook98d0, now99f0); normal options/gameplay do not
enable it. This pre-existing diagnostic limitation is not addressed here.

Runtime jitter causality/improvement remains unproven. No game was launched.
Installed into the formal1.1 entry, continuing playtest and release staging;
post-install launcher/manifest/resource hashes pass. Protected runtime files,
settings, saves and AI files remain unchanged; evidence is
`build/remastered-1.1-movement-timing/installed-verification.json`. Backups and
hash-guarded rollback are in `backups/remastered-1.1-movement-timing/`.
After hash-gated installation and backup, stop for user feedback before any
iteration2 implementation or turn-speed parameter selection. Rollback (only
when game closed and no newer build installed):
`C:/Python314/python.exe modernization/tools/build_11_movement_timing.py rollback`.

### Movement smoothing iteration2 — 2026-10-02

User accepted the intervening save24 projection correction and authorized
resuming iteration2. Latest baseline is pick-projection:101 movement-timing,
102 accepted projection/AI/options/binding chain,103 unchanged diagnostics.
Build `remastered-1.1-movement-momentum` changes only101, preserving latest
launcher sources and unchanged102/103. Canonical implementation is
`runtime/hd11/movement_momentum.cpp`; installer/builder/rollback is
`tools/build_11_movement_momentum.py`.

Native evidence: engine SHA42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da,
preferred base400000. Existing Ghidra move-start-20261002 export510e80 checked
against instructions5112cb..511589. Before the reset gate,514360 validates the
edge,522f50 handles occupancy, and5093e0/509230 releases/reserves the segment;
early failure returns via5112b9 wait5 or511bdd wait7 and never reaches51143e.
Ordinary action2 same-edge fast path51134e..511410 already preserves momentum.
Other edges reach reset gate51143e after an initial505920 speed calculation;
505920 runs again below it at511584. Native4ead10 takes old/new directions in
ECX/EDX and normalizes signed differences to eight directions. Native50db60
stores speed at170/flag16c when leaving walking2; these native fields are not
repurposed as a broad grace period because they can survive waiting15.

Three signature-checked hooks:510e80 entry6 bytes saves entry speed, threshold,
fraction/direction/kind/action/wait;51143e gate8 bytes optionally replaces only
the speed reset;51158b finish6 bytes caps sharp-turn speed after native505920.
Common root offsets, action scheduling, animation setup and reservations remain
native. Unsupported cases execute the overwritten JE/CMP then original branches.
The gate preserves all registers/flags and resume stack. Entry snapshot is by
unit id+pointer and refreshed on every native start, including rejected starts.

Continuity scope: alive ordinary single-player width-one ground walkers,
movement kind0 unchanged, native established segment618=1, no wait66c, special
104/10c/71c/723 state absent, valid positive speed/threshold/bounded carry.
Allows native uninterrupted action2 or the existing validated on_order_impl
mid-segment redirect transaction. This transaction captures eligibility BEFORE
it clears618 and calls action15; the flag ends immediately after native start,
and the existing unit/cell rollback still restores failed starts. It does not
infer continuity merely from replan/15/b73 or wall time. Other native replan,
waiting or action paths retain original behavior unless this continuity is
proven. Player/AI ownership/selection has no privilege or filtering.

Restore ENTRY speed at gate, avoiding double acceleration from the first native
505920 call; subsequent native calculation applies terrain/desired speed and
acceleration. Preserve carry as floor(oldCarry*newThreshold/oldThreshold), always
below the new threshold; do not generate an extra root step or change positions.
0/1 discrete direction changes (straight/45 degrees) retain native acceleration;
2/3/4 (nominal90/135/180 degrees) cap to6/8,5/8,4/8 of new native terrain desired
speed. Cap never raises native calculated speed. Using desired speed rather than
the previous turn's reduced speed prevents repeated corners from multiplying
down toward zero. After the corner, native acceleration governs recovery. A real
stop uses original startup; type changes and multiplayer keep original resets.

Verification:1034 compiled policy/native-gate/x86-installer cases include
owners0/1/3/7,20/30/40 logic rates, all eight directions, explicit redirects,
stop/wait/special-state/terrain-type/multiplayer rejection, proportional carry,
native fallback, four slope-speed curves and detour signature rejection. Actual
505920 startup remains151,240 at nominal240/acceleration10, slope targets remain
up160/down360. First-iteration5185 timing-reader/logic equivalence cases pass;
162 existing roof/raster/wrapped-route/command/rollback/dynamic-wait cases pass.
Tests use synthetic inputs and explicit native-start doubles for prior redirect
transaction regression; no full native animation/occupancy gameplay acceptance
is claimed. Native safety/reservation code is unchanged, not globally bypassed.

Controlled cadence illustration uses four12-root-step segments and native
accumulator with31/50 at30Hz: straight72 ticks both; straight explicit replans
100 old versus72 new; successive90-degree corners72 old versus87 new;
successive180-degree reversals72 old versus118 new. These are synthetic timings,
not measured real saves/travel durations. The change intentionally alters some
travel times/turn feel; it is not merely presentation smoothing. Parameters
remain pending user gameplay feedback, and live jitter improvement is unproven.

Reports `build/remastered-1.1-movement-momentum/{verification,timing-preservation}.json`.
Backups `backups/remastered-1.1-movement-momentum/`; install verifies snapshots,
native hash, module resources and unchanged protected settings/saves/AI files.
Rollback with closed game and no newer installation:
`C:/Python314/python.exe modernization/tools/build_11_movement_momentum.py rollback`.
This restores preceding pick-projection, including iteration1 timing fix.
Status update 2026-10-02: user reports first-round stutter appears gone and explicitly defers iteration2 as a TODO. This candidate has NOT been installed; no iteration2 backup/rollback snapshot exists yet. Retain installed movement-timing101 and pick-projection102. Do not install this prepared candidate until the user resumes iteration2. No live game launched.
