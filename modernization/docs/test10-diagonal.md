# test10: apparently empty diagonal cells — 2026-09-30

## Reproduction and identity

The user reports two repeatable detours while the wizard automatically walks
toward the portal after loading test10. No selection or movement order is needed.
Two owned background replays reproduced the same ten-waypoint saved route,
reaching `(51,71,6)` approximately 8.2 seconds after the load click.

- Entry: `game/Chaos-Wide169-Trial.exe`, SHA-256
  `f9c90c345fe295802794b75822b53440d5b84abe11d491115e7e4a2d511f2eaf`.
- Engine: `game-wide169/Chaos-Wide169-engine.exe`, SHA-256
  `43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`.
- Fixture: `game-wide169/Save/test10.sav`, SHA-256
  `a8079e9e3d6ec05e991f28bd92c8ad4b7c4db6bef270f650e9f9641601ee6a18`.
- Installed package: v22 timer progress, checked against the installed manifest
  and `current-baseline.json.latest_development`.

Reports: `../logs/wide169/1790700017901499400/result.json` and
`../logs/wide169/1790700149365547600/result.json`. Both report no protected-file
changes. The second run includes complete tile-type data and
`diagonal-analysis.json`, plus map/unit snapshots and native-surface captures.
There were no gameplay orders or memory writes by the probe. Screenshots are
native 1280×720 diagnostic surfaces, not an HD visual acceptance result.

## Finding

The target cells are clear, but the native diagonal rule also checks the two
orthogonal side cells. Each reported location has one blocked side cell.
This is a local corner-clearance restriction, not a switch to four-direction
movement for the whole unit or map.

| Location | Direct diagonal candidate (x,y,z) | Rejected side cell | Evidence |
| --- | --- | --- | --- |
| Start | `(58,78,4)` → `(57,77,4)` | `(57,78,4)` | Tile 704, tile collision kind 16, flags `0x0001`; native clearance rejects its base tile. No occupying unit (`0xffff`). |
| Near portal | `(54,74,5)` → `(53,73,5)` | `(54,73,5)` | Tile ID zero, but flags `0x4000` mark solid volume. The terrain surface at the same XY is one layer higher, z=6 (tile 540, kind 1). No occupying unit. |

Both destination columns pass the reconstructed space/headroom check. The
other side cell passes at both locations. Consequently an empty-looking
destination can still be unreachable by a single diagonal step. At the first
location the saved route instead goes through `(58,77,3)`; near the portal it
goes through `(53,74,5)`. The exact visual identity of tile 704 has not been
mapped to an asset name; do not label it a specific tree or invisible prop yet.

## Native evidence and limits

User disposition (2026-09-30): the starting detour is correct because that
terrain really is impassable. Preserve it as a negative regression fixture.
The portal-side height detour is undesirable. The user requested a modification
plan benefiting all units; the proposed implementation is below, not installed.

Preferred image base is `0x400000`. The original community engine
(`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`)
was inspected through its existing Ghidra database in read-only/no-analysis mode.
Exports are outside Git at
`D:/Tools/magic-mayhem-re/projects/test10-diagonal-export/`.

- `0x514360`: unit transition validator; original call-site ABI is thiscall,
  six XYZ dwords, movement-kind output and a flag (`ret 0x20`). Calls terrain
  transition `0x4f3990` and unit-occupancy checks via `0x4f5a40`.
- `0x4f3990`: for a width-one unit and squared displacement greater than one,
  checks the side columns with `0x4f46b0` → `0x4f3440`.
- `0x4f3440`: rejects cell flags `0x4000`; rejects a nonzero base tile with
  kind 16 unless flag `0x80` applies; also checks headroom and terrain flags.
  The wizard type has width one, height four. Tile kind is the dword at
  `tile_table + tile_id*0x164 + 0x94`.
- Cells are 12 bytes, indexed `x + y*width + z*width*height`; tile ID at `+0`,
  unit ID at `+4`, flags at `+10`. This map is 80×80×25.
- Engine disk spans `0x4f3320..0x4f5bdf` and `0x514360..0x51462f` are identical
  to community bytes. Span SHA-256 values are in the analysis JSON.

This is a read-only replay plus an offline reconstruction of the relevant
native clearance predicates, not a live invocation of the validator. It does
not claim every function or every movement mode recovered. The saved route
and the specific blocked-side predicates agree. An original-executable replay
and geometric sprite/collision-footprint audit were not performed.

No collision patch was installed. Simply removing the side checks would also
change wall-corner and height-edge traversal. If smoother local navigation is
implemented, preserve terrain support, swept footprint, headroom and unit
occupancy; retain these two cases as regression fixtures alongside genuinely
blocked wall corners and slopes. Visual accuracy of the collision footprint
remains a separate question from explaining the current route.

## Reusable probes

Run `python modernization/tools/probe_test10_route.py`, then
`python modernization/tools/analyze_test10_route.py <run-directory>`.
The replay backs up mutable files, observes the saved route without new orders,
and restores the wrapper/configuration. It temporarily disables `PlayFMV`
with a disk backup and restores the exact original prefs bytes and timestamps.
The user confirmed physical Esc skips the intro; this harness's posted Esc did
not skip it, so a fixed four-second launch wait must not be treated as a menu
gate when FMV is enabled. The two initial failed intro runs collected zero
unit samples and are not reproduction evidence.

The loose development `runtime/wide169/wide169.dll` differs from its historical
baseline entry. This diagnostic used the hash-verified installed launcher with
its embedded runtime, not that loose build output, and did not update baseline
identities.

## Proposed modification: height-aware diagonal clearance

### Scope and behavior

Implement one shared terrain-transition policy for single-player navigation,
independent of unit index, faction, selection, or whether an order came from
the player or AI. Ordinary walking units of different sizes use their actual
footprint, height and native movement capabilities. Large units must be covered
before declaring all-unit support complete; equal rules do not imply that a
large unit fits every passage that a small unit can use. Flying/swimming and
other movement modes retain their existing capability rules; benefit where the
same terrain restriction actually applies, without removing mode restrictions.
Multiplayer remains native until separately validated.

The intended change is to distinguish the solid material under an adjacent
walkable slope from an actual wall/prop. A destination that is otherwise legal
may become diagonally reachable beside such a slope. Preserve tile 704's block
at the start. No coordinate whitelist, test10-only map edit, global clearing of
`0x4000`, or blanket conversion of AND side checks into OR side checks.

### Proposed admission rule

1. Retain all native source/destination support, movement-mode, headroom,
   occupancy and map-bound checks. Keep an already accepted native edge unchanged.
2. Consider an alternative only when a local diagonal is rejected specifically
   by a side-column terrain check. Classify the rejection explicitly; a generic
   validator failure is insufficient to enter this alternative.
3. Inspect the adjacent terrain's actual support surface and shape. The first
   candidate scope is a unique connected surface at most one layer higher, as
   in test10. A `0x4000` bit alone never establishes a slope: verify terrain
   type/shape and native walking connections to both ends, without recursively
   using the new diagonal exception. Reject a wall/prop, overhang, closed door,
   unsupported ledge, ambiguous bridge/floor, or excessive climb.
4. Validate the entire movement corridor against the unit's physical footprint
   and height, using terrain surface/edge geometry and the engine's collision
   conventions. A center line or a few isolated samples is insufficient. For
   multi-cell units evaluate the full swept footprint. Retain dynamic occupancy
   and any required reservations; a raised neighboring surface must not conceal
   a blocking unit. Define exact boundary-contact semantics deterministically.
5. Accept a normal diagonal only if this corridor is supported and clear and
   native interpolation can execute it correctly. If height following is
   necessary, verify the engine supports that trajectory before admission.
   Never authorize a geometrically colliding straight segment just because the
   higher side cell is individually walkable. Unknown geometry uses native
   behavior and is logged as an unresolved case, not counted as a fixed test10.

The numerical collision footprint and tile 540's precise surface shape remain
unrecovered. Resolving them is the first implementation gate. The preferred
outcome is the portal-side diagonal without the sideways grid step. If native
movement cannot represent the required safe trajectory, implement a bounded
local terrain-following segment with coherent occupancy/interpolation as a
separate step; do not silently replace the fix with a visual-only smoothing.

### Integration

- Recover and trace the planner's neighbor evaluation, execution-time step
  validation, and redirect validation. `0x4f3990`/`0x4f46b0` and `0x514360` are
  investigation anchors, not yet approved patch sites. Verify callers and exact
  signatures on the then-current latest baseline; planner coverage is not proven
  merely by the existing movement-validator disassembly.
- Put the new policy in a shared module used by every relevant walking path.
  Do not extend only `on_order` in `repath_multiunit_trial.cpp`: that mechanism
  handles mid-segment new orders and would miss automatic/saved/AI paths.
- The planner and executor must agree on legal edges and movement kinds.
  Recheck transient occupancy before committing a step; use native wait/replan
  when obstructed. Preserve native terrain costs and segment-time calculation;
  a shorter route may arrive sooner, but movement speed and game time must not
  be changed. Keep shared route budgets and per-unit state isolation.
- Loaded saves can contain the old route. On enabling the candidate or loading
  a level, queue one bounded refresh for active compatible movement orders at
  the next native safe segment boundary, preserving their destination and order
  semantics. Spread work across the existing budget. No active route-buffer
  overwrite during interpolation, forced teleport, or clearing an AI action.
  New orders naturally use the shared policy. Save format stays unchanged.
- Terrain changes invalidate terrain-only cached results; occupancy is live.
  Include movement profile/size and map identity/revision in any cache key;
  discard caches and pending refresh state on load or unit-slot reuse.

### Implementation sequence and gates

| Step | Deliverable | Exit gate |
| --- | --- | --- |
| 1. Recover geometry and call coverage | Hash-identified terrain/footprint evidence; planner and executor call map; failure reasons for test10 | Explain both blocked-side cases geometrically and identify a safe portal-side corridor, including large-unit fit |
| 2. Offline policy | Deterministic shared predicate and synthetic terrain tests, plus read-only fixture comparison | Start remains blocked; portal case accepted only with demonstrated clearance; rotations/reverse direction, stairs, cliffs, walls, bridges and headroom agree with independent expected outcomes |
| 3. Isolated integration | Opt-in candidate from latest baseline with shared checks and boundary-safe route refresh | No-input test10 removes the portal-side detour while retaining the starting detour; fresh orders and loaded orders both use the new policy |
| 4. All-unit and compatibility validation | Friendly, summoned, neutral and hostile actors; small/large/tall profiles; simultaneous crossing and obstacles | No actor-specific bypass, no clipping/duplicate sprites/stray occupancy, no route oscillation or budget starvation; special movement and multiplayer preserved |
| 5. Playtest and delivery | Separate runtime/saves/config, manifest and rollback, paired surface captures and telemetry | User can reproduce the improvement; latest QoL, save/load, timing and rendering behavior retained; outstanding cases clearly listed before promotion |

The test10 acceptance compares the original automatically resumed route against
the candidate without issuing a replacement user movement order. It also checks
reverse/rotated equivalents and an independently requested route so the saved
route refresh cannot masquerade as a general planner fix. The actor must reach
the same portal normally. Full unit/occupancy checks accompany screenshots.

All-unit testing must include actual native AI travel/chase and summoned-unit
orders, not just repeated manual orders on unit 0. Large/tall units keep genuine
size restrictions. Dynamic tests add another unit or close a door before entry;
failed revalidation must wait/replan without overlap. Bounded stress runs retain
the existing search budget and measure added work and worst update gaps against
baseline. Existing mid-segment redirection and selection/casting behavior also
need regression checks.

### Execution authorization and scope correction — 2026-09-30

The user approved implementation except item 4 (automatic refresh of saved
routes). This supersedes all saved-route refresh requirements above: do not
enqueue a replan on load or enabling the feature. Existing serialized routes
remain native and unchanged. Acceptance uses explicitly reissued movement
orders in test10; no-input replay is only the unchanged-route control.
Implement the remaining shared-policy, genuine-obstacle and all-unit gates.

### Candidate work and invalid runtime trial — 2026-09-30

An isolated experimental module and playtest have been built at
`modernization/playtests/terrain-diagonal-v1/`. They preserve v22's extracted
embedded modules and do not install over the baseline. Sixteen offline tests
execute the actual compiled hook and native x86 validator using Unicorn and
captured map data. They pass the portal predicate, both directions, heights
1–8, and retained obstacle/headroom/occupancy/door/cliff/multiplayer gates.
Large footprint behavior is retained, not certified as improved.
Rotation/reflection, special movement modes and several creature profile IDs
also pass. Profile-ID coverage is not a substitute for actual AI movement.

The user observed that the fresh-order runtime probe clicked too late: the
wizard approached from the lower right rather than from below and had missed
the relevant height cell. These movement trials are **invalid acceptance** of
the requested correction. Do not infer a fix from their screenshots or arrival.
The user offered a new stationary debugging save before the problematic edge.
Use that save for identical baseline/candidate orders and paired captures.
The candidate is unqualified until this reproduction and actual all-unit/AI
movement/geometry checks pass. No successful live fix is claimed.

### Stationary fixture passed; user-authorized installation

The user supplied a replacement stationary `test10.sav`, SHA-256
`4bfe8dab1cc508b6663adcbf3949177d3e5555ec7a46ed1494e3dd4d3472f3de`.
Both paired runs verified unit 0 stationary at `(55,75,5)` and selected before
right-clicking the same native portal coordinate `(640,216)`:

- Baseline `logs/terrain-diagonal/1790701440982318400/baseline/capture.json`:
  `(55,75,5) → (54,74,5) → (53,74,5) → (52,73,5) → (52,72,6) → (51,71,6)`.
- Candidate `logs/terrain-diagonal/1790701490775845900/baseline/capture.json`:
  `(55,75,5) → (54,74,5) → (53,73,5) → (52,72,6) → (51,71,6)`.

Both restored mutable files. The user visually confirmed the correction and
explicitly asked to install immediately, taking over further playtesting to
save tokens. This supersedes the pre-install broad acceptance gate; it does
not mark the remaining geometry/all-unit/AI/long-run checks passed.

Installed v23 retains the exact v22 engine and embedded QoL/repath modules.
Entry SHA-256 `8ef2806f8c383323f81cb2fb69fde2fdd30ebd208a32bdecbe363418caffa5c3`;
new `game-wide169/terrain_diagonal.dll` SHA-256
`0a18ddae17025d16b44197b4eddca09685a63c1a8dbac130d9c3e1e5d7068391`.
Latest-baseline and package manifests identify these files. Saves and prefs
hashes stayed unchanged during install. Backup:
`modernization/backups/wide169/terrain-diagonal-1790701658779842000/`.
With the game closed, rollback is:
`python modernization/tools/install_terrain_diagonal.py rollback`.

Implementation hook: native `0x4f3fff`, after native endpoint/support checks,
before single-cell diagonal side checks. It admits only same-layer diagonals
with one subsurface-only blocked side, a walkable surface one layer above,
at most 16 world-height units above both endpoints, bidirectional native
walking connectivity, headroom and no side occupants/reservations. Native
execution occupancy remains in place. No faction/selected-unit filter or
load-time route refresh. Multi-cell and special movement retain native rules;
the improvement currently targets the single-cell side-check restriction.
Actual multi-cell improvements and swept geometry are not certified.

Correction to earlier terminology: tile `+0x94` is also added to `z*16` for
standing height at `0x507172..0x507180`; values called “kind” above are terrain
height values, with 16 representing a full solid block in the native check.
The earlier rejection diagnosis remains valid, but these are not abstract
creature or collision-type enum IDs.
