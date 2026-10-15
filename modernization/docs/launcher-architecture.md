# Launcher architecture review — 2026-09-30

## Latest roof input/body iteration — 2026-10-02

Save21 v2 supersedes the v1 resource101 path below: latest source is now
`build/remastered-1.1-roof-ghost-v2/`, handling roof-family policy1 as well as
height-limit policy0. Resource102/103 preserved.162 offline checks and bounded
save21 background proof pass; user observed effect and takes broader testing.
See `docs/roof-visibility.md` for evidence and the corrected mixed-output crop.

Latest resource101 source: `build/remastered-1.1-roof-ghost/`, preserving
wrap-route-v1 search/command-response-v2 and adding `hd11/roof_ghost.inc` private
upper-layer body rendering. Latest resource102 source:
`build/remastered-1.1-roof-tab/`, preserving options-render-v1, AI budget/danger
limits and main-portrait-cancel, adding Tab native roof-control dispatch.
Resource103 and installed runtime files remain unchanged. Formal launcher SHA:
d47dbfad39d68dec2e68e6777e4995c209df0e601543011160f1705637cba412.
All three installed launchers/resources/manifests verified after backups.
95 roof/input and156 ghost/path checks passed offline; user bridge-save visual
acceptance remains pending. See `docs/roof-visibility.md` and `docs/qol-input.md`.

## Installed 1.1 FMV extension, 2026-10-01

The current isolated1.1 launcher source is
`build/remastered-1.1-fmv-h264/launcher.cpp`, not the earlier P1/portrait launcher.
It carries current resources101/102 byte-for-byte and adds the delivery worker's
tested early movie hook. The engine is created suspended; a temporary entry loop
allows DLL initialization before startup film calls, then the original entry
bytes/protection are restored and execution resumes. fmv_h264.dll is hash-pinned.
Engine disk bytes and the existing feature-module load sequence are unchanged.
Future launcher builds must retain this startup hook and installed DLL hash.
Integration recipe: `tools/build_11_fmv_h264.py`; details: `docs/fmv-compat.md`.

PE resource readers must close `pefile.PE` mappings explicitly before replacing
an executable on Windows. `install_11_minimap_v2.resources` now uses finally/close:
retained mappings had made the installer itself lock its target, producing
WinError5/32 despite no running game. This does not indicate an engine hang.

The launcher/engine split was an agent implementation choice, not a user
requirement. The user asked to review its rationale after release delivery and
development cleanup. No architecture conversion was requested or performed.

The preserved documents show how the strategy evolved, but do not contain an
explicit comparison that selected it against all alternatives. The reasons
below are engineering inferences from the recorded workflow and implementation.
Do not present them as the user's decision or a recovered verbatim rationale.

## Evidence and evolution

- `runtime/releases/full60_v1/README.md`: freezes accepted enhancement DLL and
  trial launcher; main entry embeds that exact DLL and keeps the engine separate.
  This supports immutable functional binaries, isolated trial entries and rollback.
- `docs/full60-2k-merge.md`: installation made Chaos.exe a launcher and retained
  original engine separately; merging HD required engine byte audits and hook
  conflict checks. Permission to install does not establish that the user chose
  the architecture.
- `runtime/releases/hd60_v1/README.md`: disk engine combines known native/HD
  edits; runtime DLL adds hooks. Launcher packages the DLL as resource 101 and
  launches only a pinned engine. Original and previously accepted binaries stay.
- `docs/qol-input.md` (historical QoL trial): embeds unchanged accepted module
  plus independent QoL resource; experiments can update one module while keeping
  the others fixed. v37 retains resources 101 and 102 plus external terrain DLL.
- `releases/remastered-1.0/launcher.cpp`: self-location, hash validation,
  environment flags, native child process, temp resource extraction, remote
  LoadLibraryW via CreateRemoteThread, and exit-time cleanup. Load order is
  main enhancement, QoL, terrain. WaitForInputIdle precedes first injection.
- `runtime/wide169/build.cmd`: MM_ALL_IN_ONE combines several enhancements into
  one DLL; it does not combine that DLL into the native game EXE.

## Why it made sense during development

Without a source-level game rebuild in this repository, known engine edits can
remain audited binary patches while substantial C++ additions compile into DLLs.
Loading those DLLs into the existing process lets them attach to recovered native
addresses without rewriting all engine code as disk patches. Multiple trial
entries can select behavior without replacing the accepted native executable.
Embedding accepted DLL bytes binds an entry to a known module version and avoids
mixing mutable build outputs with an accepted engine. Current packaging caught
exactly this issue: loose development DLL hashes differ from current resources.

These benefits justify modular enhancement code and immutable snapshots. They
justify an external injecting launcher as a convenient implementation, but do
not prove that an external launcher is technically required for a final release.

## What remains useful; what is incidental

Useful release responsibilities are deterministic module versions and order,
engine identity checks before address-based hooks, consistent working directory,
failure handling, and clean behavior when another game instance is running.
Those can move into a native bootstrap or DLL loader; they are not inherently
launcher-only features. Portability similarly depends on relative paths, not on
having two EXEs. The existing engine is already modified on disk for layout, so
"we must never modify the engine" is not a valid explanation.

There is no demonstrated steady-state frame-rate benefit from this launcher.
It waits after loading. Rendering/pathfinding improvements execute in the game
process, not in the parent launcher. Hash checking/temporary extraction is
startup work; exact startup cost was not benchmarked.

Costs in current code: two visible EXEs with a bypassable native engine entry,
extra process, temporary DLL files, remote loading, initialization timing after
window readiness, and cleanup failures that can leave temp files after abnormal
termination. These are implementation costs, not observed new gameplay failures.
The terrain failure branch also terminates the child and returns before the
normal temp-file/handle cleanup path; reviewing that is separate from this task.

## Alternatives and judgement

1. Keep current loader and put engine/support files in a runtime directory.
   A single player-facing entry; small packaging/path change, same architecture.
   Lowest immediate behavioral risk, but does not remove injection/child process.
2. Let the native engine load the enhancements itself through an audited entry
   bootstrap/import change. One player-facing game process and no external remote
   loading. DLLs may remain separate. Need to preserve module initialization
   timing, flags, failure behavior and known hook order; importing today's DLLs
   before native startup is not automatically equivalent to post-window injection.
3. Integrate enhancement code into extra PE sections or a native bootstrap.
   True single executable for game code, higher engineering and regression cost:
   relocation, imports, CRT/global initialization, address hooks, lifecycle and
   compatibility must be audited. Renaming or appending DLL bytes is insufficient.
4. Embed the engine in a launcher and extract it on startup. Cosmetic single-EXE
   distribution, still two processes and temp engine/DLLs. Does not solve the
   underlying architecture issue and is not the preferred consolidation.

The current release preserved the accepted v37 behavior to avoid mixing
packaging with a loader rewrite. It should be described as a development strategy
carried into the release, not as the only sensible permanent release design.
For actual simplification, the strongest next investigation is a native loader
bootstrap (option 2), with a separate hash-gated candidate and user gameplay
acceptance. No conversion is part of this review; current delivered release
remains as validated. Option 1 is sufficient if the immediate concern is only
which EXE the player should launch.

2026-09-30 follow-up: user explicitly retained the launcher approach and requested
one root executable with a game icon, engine/support content in runtime/. This
packaging change is implemented; it is not a native bootstrap conversion.
# Latest1.1 module delta: save3 local routing — 2026-10-01

Latest resource101 is `build/remastered-1.1-local-route/repath.dll`, SHA256
`149be78cef0d65884e1d65b8095f2e73d4dcf189e2f45195acafff36d56d55a5`.
Resource102 remains the latest character-icons module, unchanged byte-for-byte.
The exact existing FMV diagnostic/formal launcher sources remain from that
build; portable compositor SHA8c46de4d and all external runtime assets retained.
Never rebuild from older corridor/FMV embedded modules without carrying these
latest deltas. Engine hash42f2aac7 remains unchanged.

`runtime/hd11/local_route.inc` adds bounded A* after the existing straight-corridor
adapter: ordinary single-player one-cell walking, target distance<=16, no wrap,
256nodes within radius16, only complete paths<=16steps. Every candidate edge
passes native522f50 occupancy and514360 transition(kind0); every committed
record is produced and checked with native513370. Failure leaves output unchanged
and follows existing navigation. Flight/combat/multiplayer/ambiguous special
movement remain native. This is a local route improvement, not unrestricted
global optimality or a general performance claim.

The loaded-route adapter now replaces continuation even when the first node
equals the existing active edge. It copies that exact old edge metadata and
retains motion/animation/reservation, resets route cursor for the new route and
clears macro continuation. Existing redirect machinery remains for changed edges.

User-authorized save3 fixtureSHA2993d4c804fef221bf816f4e936f6315940ce7fa6c20ba2da7a10fdb160e7703
captures are under `logs/remastered-ui/save3-route-before` and `save3-route-after`.
Start(29,45,5),goal(18,36,6). Before18steps detoured east to31; after16steps
never exceeds29, moving north along the left wall then northwest. Arrival in
these captures12.77 vs10.92seconds; measurement includes the initial stored
segment and is scoped to this scene. Eight compiled/native emulator checks cover
actual captured terrain, blocked target, scope exclusions and prior test18 ramps.
Emulator now verifies returnPC to detect exhausted instruction budgets instead
of treating partial EAX values as a completed function result.

`tools/build_11_local_route.py` installs formal/frozen/candidate launchers and
manifests, with backup `backups/remastered-1.1-local-route`; rollback subcommand
requires stopped game and verifies before/after hashes. Static5105-file formal
verification passed. No gameplay after installation; user acceptance pending.
User's earlier slight occlusion-opacity reduction remains pending separately.
# Latest1.1 module delta: occlusion opacity — 2026-10-01

## Subsequent external terrain half-stair fix — 2026-10-01

Save13 fixtureSHA256
`f6e1ad4a88fee6e11252ba6d091597d2a1be3503c6cebff7f792cf88dfb4c6b9`
reproduced an exterior16-edge detour from(67,35,6) to(70,35,7).
The direct edge(69,35,6)->(70,35,7) has half-height terrain tile1381(height8)
below an empty upper cell supported by floor779(height16). Both endpoints
pass native support/headroom. Native514360 delegates to4f3990, whose extra
side-column check calls4f46b0 for(69,35,7);4f3440 rejects the roof atlayer10.
The raised side column is not the actual half-step endpoint. This is a
terrain-transition rejection, not an A* search-budget or minimap issue.

`runtime/terrain_diagonal/terrain_diagonal.cpp` adds `try_half_stair` at the
existing hash-verified4f3fff hook after native endpoint/movement checks.
Only single-player ordinary width-one walking, cardinal adjacent cells,
one grid layer difference and exact8-unit physical rise qualify. Low surface
must be an unflagged terrain half-step; high endpoint must be empty and have
a full terrain floor immediately below. Both native space/support checks
are repeated. Original514360 occupancy checks still execute after the hook.
Other heights, diagonals, cliffs, flight, wide units and unsupported movement
remain on the existing native/diagonal path. No tile/save edits or collision
flag removal. It benefits eligible walkers rather than one character/save.

Build/installer: `tools/build_11_half_stair.py`, production provenance and
hashes in `build/remastered-1.1-half-stair/verification.json`. Formal/frozen/
candidate launchers are rebuilt from the exact latest minimap-release sources
with only the external terrain DLL hash changed. Embedded resources101/102/103
remain byte-identical, as do the battle HUD wrapper/pack and engine42f2aac7.
Future launcher builds must retain the new external terrain SHA from current
manifests instead of hardcoding its predecessor3791b8ea.

Verification:15 terrain checks,100 earlier test18 slope/profile comparisons
and324 nearby edge comparisons. Six newly accepted edges are exclusively
eligible half-stair connections; prior accepted edges remain accepted. Cases
cover blocked headroom, occupied destination, missing support, other heights,
multiplayer and movement profile exclusions. Native call returnPC is checked.
`tools/probe_save13_route.py` uses isolated copies, private background input
and read-only memory. Before/after evidence is under
`logs/remastered-ui/save13-route-{before,after}/`: after path is exactly
(67,35,6),(68,35,6),(69,35,6),(70,35,7); observed arrival11.66s->3.56s,
including initial stored segment timing. Owned engines stopped and fixture
state restored. Formal5106-file verification passed after installation.
Installed wider gameplay acceptance remains pending user feedback.

Rollback command:
`C:/Python314/python.exe modernization/tools/build_11_half_stair.py rollback`.
Requires stopped game and checks installed/backup hashes. Backup is
`backups/remastered-1.1-half-stair/rollback.json`; player saves are untouched.

Resource101 now comes from `build/remastered-1.1-occlusion-opacity/repath.dll`,
SHA256 `a680f98e3b51f8f8e315fe52af5055b6fdc3d1586d19a4ae3d9b598d201264b8`.
It retains the complete save3 local-route implementation and all prior features;
resource102 remains the character-icons module unchanged. Engine/wrapper/FMV/
art/settings/saves are retained. Future builds must preserve this newest module.

The user requested characters slightly more transparent when obscured. Only the
reveal pass changes: covered pixels blend3/8body +5/8scene instead of1/2each.
RGB565 channels are calculated separately with nearest rounding to avoid channel
carries or dark truncation. Already-visible pixels compare equal and remain
untouched. Body tagging, terrain-floor clipping, viewport bounds, movement/replay
offsets and multiplayer exclusions remain unchanged. This applies to the existing
character-body reveal family, preserving its scope rather than only the hero.

`tools/build_11_occlusion_opacity.py` builds from exact latest local-route source,
then runs the established compiled/native rasterizer regression suite with the
updated expected blend. `emulate_11_render.py` replaces dependence on obsolete
terrain captures with a current-engine hash-gated rasterizer fixture.30checks
pass: blend, visible pixels, transparency, clipping, padding, restored context,
overlapping bodies, four rotations and exclusions. No gameplay test was run.

Installed formal/frozen/candidate launchers and manifests with backup
`backups/remastered-1.1-occlusion-opacity`; rollback subcommand requires stopped
game and validates hashes. Formal5105static-file verification passed. User
runtime appearance acceptance remains pending.

## AI telemetry and subsequent Portmanteau correction — 2026-10-01

Subsequent latest launcher/module build is `build/remastered-1.1-minimap-release/`.
It retains the same101/103 and AI launcher behavior, restoring authoritative
scanner click-width hook555f1d in resource102; SHA
367ab2a1f22546aff64d38d19afc42c21ae5373ecefbdb9266412f3f5b4c5244.
Use tools/build_11_minimap_release.py rollback; backup under the matching name.
Formal launcher intentionally clears private input flags; controlled save10
test used paired candidate launcher with formal assets and identical modules.

Prior Portmanteau launcher source is in `build/remastered-1.1-port-preview/`, copied from
`build/remastered-1.1-ai-diagnostics/` and retaining default-off `--ai-trace`
handling plus resource103. Resource101 stays
`a680f98e3b51f8f8e315fe52af5055b6fdc3d1586d19a4ae3d9b598d201264b8`;
resource103 stays `4e63e0d8452f2bfbcfef52e1838e17575d2bf7cddf37c4a1213dbe6f2ac95c17`.
Port preview resource102 is
`ee2ce1d9018439f3bf1d2ad305df0fb7918e3051badf12b69e722acb2ec888fc`.
Use `tools/build_11_port_preview.py rollback` for this UI delta; backup is
`backups/remastered-1.1-port-preview`. Engine/wrapper/assets/player data unchanged.

## Save14 dynamic-obstacle waiting — 2026-10-01

Latest resource101 is `build/remastered-1.1-dynamic-wait-v2/repath.dll`, SHA256
`26342aeb43cf11151be42ef930df6243330548e5c1643279f0c426a96cc484e5`.
Launcher sources come from latest minimap-units build and preserve resource102
`e554abe3ccfcca97cb5c44b165cf5efeb387b36b0eead99e1dd0063b4adb4c6e`
and103 `4e63e0d8452f2bfbcfef52e1838e17575d2bf7cddf37c4a1213dbe6f2ac95c17`.
External half-stair terrain, HD HUD/UI/art/video, engine and saves are retained.

Known engine42f2aac7 native522f50 tests cell flag0x10 at the destination and
one layer below for the width footprint. This is a dynamic-obstacle predicate,
not general unit occupancy. In captured save14, cell(18,47,6) has flag0x10;
hero waits at(18,46,6). Native51127c checks this predicate, and5112b9 stores
timer5 after action15 dispatch. Earlier clear-wait hooks only armed at511bdd
timer7, so adding logic solely there passed offline checks but had no effect
in the first isolated run. That rejected candidate was never installed.
New5112b9 hook gates exact bytes `c7866c06000005000000`, reproduces the store,
preserves registers/flags, records the same wait identity, and returns5112c3.
Existing50f823 tick hook still performs native timer load/decrement/dispatch.

`runtime/hd11/dynamic_wait.inc` adds a bounded detour while stationary, single
player, active living width-one ordinary walkers only. It first retains the
existing immediate wake when the original edge clears. If the destination still
passes native522f50 as blocked, a complete local route is sought through existing
256-node/radius16 A*, at most16 edges. Native occupancy, support, transition and
one-edge route metadata all validate the result. Only the route, macro-navigation
flag and wait timer are committed; motion, world position and map reservations
are untouched. Native action dispatch starts movement. No completed detour means
no route modification. Failed searches retry at most once after28 further waiting
updates; the cooldown survives repeated waits at the same origin/goal. Reset and
deserialize invalidate identity/cooldown. Multiplayer, flight, larger creatures,
ordinary unit congestion, distant goals and searches beyond the bound retain
native fallback. This improves local dynamic obstacles, not all macro routes.

Verification tools: `verify_11_dynamic_wait.py` (37 checks, actual native validators
and compiled hook ABI, fire detour, cleared fire, congestion, blocked goal,
cooldown, scope, reset/load, prior save3/test18 routes),
`probe_save14_dynamic_wait.py` (owned private-input/read-only capture), and
`accept_save14_dynamic_wait.py` (paired telemetry acceptance).
Current save14 fixtureSHA256
`3f9c035d4857e698a78c13a5d296d53f61671c82433bafe55da5116403817d43`
differs from the earlier minimap test fixture; the dynamic tests use the same
current bytes before/after. Evidence `logs/remastered-ui/save14-route-before-v1`
and `save14-route-after-v2`: path goes(18,46,6)->(17,47,6)->(18,48,6), avoids
burning(18,47,6), then reaches original goal(18,53,6). Observed arrival7.43s
before/6.97s after is one run, not a timing benchmark. Maximum sampled world
coordinate delta7; final native motion0/order1. Both owned runs restored cleanly.

Formal/frozen/candidate launchers and manifests installed with hash checks and
transactional backups. Formal5106static-file integrity passed. No gameplay after
installation; wider user acceptance pending. Build/install/rollback command:
`C:/Python314/python.exe modernization/tools/build_11_dynamic_wait.py rollback`
(use build/install subcommands for their respective actions). Rollback requires
stopped game, checks current and backup hashes, and restores preceding launcher
and manifests from `backups/remastered-1.1-dynamic-wait/rollback.json`.

## Save14 repeat-load access violation — 2026-10-01

Latest module/launcher source is `build/remastered-1.1-reload-surface/`.
Resource102 SHA256 is
`b31b980056711a99b8e271fdbe0ed9d67b0c705e65118a42318b09dcb3d5894e`.
Resource101 remains latest dynamic-wait26342aeb, resource103 remains4e63e0d8;
external half-stair terrain, HUD wrapper/art, approved maps, video and engine
remain unchanged. Formal launcher SHA256 is
`80a0fbd8179c7cbcaaefce73c0ea9e925e9dbed9a0ae6f0d81e028ef8702985c`.
Future builds must preserve these latest sources/resources rather than the
preceding minimap-only102 module.

User supplied a reproducible sequence: load14, operate/move/cast, load14 again.
Read-only32-bit dump of retained formal PID33636 confirms fatal0xc0000005
unwinding into OGGwinmm detach polling (one remaining thread). Original fault
cannot be inferred from that unwound stack. After the user closed it, an owned
reproduction with bounded first-chance exception observer captured the actual
fault before unwinding: engine42f2aac7 VA58b40b, EAX0, ESI6c4e69, read address0.
The object's+4 base interface is null, +8 queried interface1309ee50 is live,
and its single registry entry is index53 of54. The stack includes hooked
create_surface and native4d3840's creation call return4d38a4. The existing
create hook unregisters an earlier incarnation before recreation; native
Destroy checks+8 but unconditionally calls through+4 at58b406..58b40d.
This is a partial interface-lifecycle state, not a save-parser wait.
Exact source of the prior+4 clearing was not separately traced; the verified
fix supports this observed state without inventing its writer.

`runtime/hd11/surface_lifecycle.cpp` now gates native58b406 bytes
`8b46044750` and redirects those five whole instructions to a naked guard.
Present base interfaces execute original load/inc/push and continue58b40b,
with carry/stack semantics preserved. Missing base interfaces continue58b41c
to release the still-live queried interface. Native palette cleanup, registry
removal and field clearing remain intact; the old alias-compaction/create
hooks remain. It neither suppresses exceptions nor skips all surface cleanup.
No OGG shutdown patch is bundled: independent OGG exit-polling defects and
other possible load failures are not certified fixed by this specific delta.

`tests/surface_lifecycle_native_test.cpp` executes exact native Destroy with
compiled hooks and mock COM boundaries: stale indices/duplicate aliases,
the captured null-base/live-query state, repeated destruction,128 recreation
cycles, palette release and empty registry. Registry suite also passes.
Rebuilt module retains54 marker-anchor +252 scanner-click +27 scanner-draw
+324 preview-recreation cases. Embedded101/103 verified byte-identical.

Evidence: `logs/remastered-ui/live-save14-reload-p33636/` retained player dump;
`save14-reload-before-v4/exception/` first/second-chance dumps and
`root-cause.json`; `save14-reload-after-v1/` and `save14-reload-after-active/`
each complete3 operation/reload cycles on identical fixture bytes. First
fixed run observes no AV but observer detach reports0; owned cleanup succeeded.
The second run has no debugger and independently verifies3 repeat loads after
hero selection/movement and spell selection/cancellation. Attempted spell
targets were not accepted, so these tests do not certify spell execution.
Both runs restore isolated mutable state and stop only owned processes.
No user gameplay/config/save modifications and no installed gameplay run.

Tools: `probe_save14_reload.py`, `analyze_save14_reload_av.py`,
`accept_save14_reload.py`, `build_11_reload_surface.py`.
Formal/frozen/candidate installed transactionally,5106static formal files pass;
player acceptance pending. Rollback (stopped game and hash checks required):
`C:/Python314/python.exe modernization/tools/build_11_reload_surface.py rollback`.
Backup: `backups/remastered-1.1-reload-surface/rollback.json`.

### New Game / Esc / save14 portrait-bank fault (2026-10-01)

Player foreground sequence: skip intro, New Game, immediately Esc, Load14.
Owned background reproduction passed before this fix, so it cannot establish
resolution of this foreground fault. Live observer captured first/second chance
AV at4d3d21 followed by natural exit C0000005. Full dump and verified evidence:
`logs/remastered-ui/first-av-p444-1790853217278614000/portrait-root-cause.json`.
ECX/EDX=0, all32 bank bytes at6593e0 zero, base surface6a4646 nonnull.
Return5074ca identifies unit-selection5073d0, called from portrait event handler
4d2d7b. This is not proof of a save-restoration callback. Cleanup5782bc and
4be530 can clear this bank; the exact active writer/timing remains unproven.
Native loader46a5fe identifies this bank as sprites/markers.spr.

`runtime/hd11/portrait_sprite_ready.cpp` gates original entry4d3c90 bytes
51a146466a00 and checks bank header6593e0/table6593e8/data6593ec before surface
locking. A missing component skips only selection-bracket drawing. Selection,
load state, bank ownership and surface cleanup stay native. Once ready,
original pushECX/movEAX[6a4646] continue4d3c96 with identical registers, flags
and stack. Ordinary repaint can draw brackets once the resource is loaded.
No exception suppression or synthesized artwork.

`tests/portrait_sprite_ready_test.py` verifies the player's captured bank and
caller chain, reproduces the native null read, and executes the compiled guard
in512 pointer-readiness/flags cases. Ready paths match native entry state;
missing paths preserve callers; writes are confined to stack. Previous exact
native surface-destruction/registry tests pass. Embedded101/103 unchanged.
Candidate `build/remastered-1.1-portrait-ready/`; transactional builder and
rollback `tools/build_11_portrait_ready.py`. Installed formal/frozen/candidate
after user closed game;5106 static release files verified. Formal launcher
SHA2560c0bf45011a13937071aa25becd6246e39a1f45b6059fbd7565c9de857c3097a;
module102 bde8af298e687960424e944d43ff880b3304b12c109537927211203506237146.
Backup `backups/remastered-1.1-portrait-ready/rollback.json`; stopped-game
rollback: `C:/Python314/python.exe modernization/tools/build_11_portrait_ready.py rollback`.
Foreground reproduction and restored portrait appearance pending user testing;
unrelated load/OGG faults remain open. Player saves/settings excluded from install.

### Transition presentation epoch (2026-10-01)

User accepted the portrait-bank crash fix, then reported one-frame scale defects
after New Game loading and while leaving save14. Screenshots show partially
overlaid native UI and scaled battle pixels. Prior wrapper classified live
controls on the D3D9 upload thread; page controls can change before a completed
primary copy. This is a source-level timing risk consistent with the report,
not a captured runtime proof of the precise screenshot-producing sequence.

`tools/build_11_transition_present.py` extends the hash-verified battle-HUD
wrapper only. `runtime/hd11/presentation_epoch.h` separates completed-redraw
mode from live input/control mode. Primary Blt samples controls on the game
thread, serializes pixel copy and mode publication with existing g_ddraw.cs,
and commits only nonempty source-backed full-primary copies. Presentation
retains its last complete output while live controls disagree with committed
mode. Complete redraw releases the hold and selects native UI or battle2x.
Cursor/input continues using current controls; no delays, input suppression or
game-time changes. Last-output cache costs about7MiB and one full-output copy
per presentation; production performance and transition coverage await feedback.
Other update APIs do not commit an epoch; if a future page changes mode without
a full source-backed primary Blt, investigate that path instead of adding a timer.

`tests/presentation_epoch_test.py` executes actual compositor code with only
live control/eligibility/HUD boundaries substituted,1152 compiled cases across
64 UI-to-battle-to-UI cycles: early controls, partial pixel writes, retained
last image, battle2x corner mapping, native UI output, coordinate input and
unchanged native pixels. No gameplay run. Installed formal/frozen/candidate,
5106 static files pass. Wrapper SHA256:
4ff43a636ab7ef95e465921a1920c2e45c93357c5b42c3dd4e71ab0cb5d4749b.
Concurrent AI-budget300 launcher and embedded modules preserved byte-for-byte.
Current formal launcher8ddeae211abac8b199e43a91f9f8fb76e4d758f513ebd3a3f731e3d59f13cc75;
module102 d67a1bf249447e49c40d1f2b74d287fea160d9864e7f8bd00b00ec2a9bf8fd7b.
Build `build/remastered-1.1-transition-present-v2/`; initial preparation folder
contains an unsuccessful source-pattern attempt, not an installed candidate.
Backup `backups/remastered-1.1-transition-present/rollback.json`; stopped-game
rollback `C:/Python314/python.exe modernization/tools/build_11_transition_present.py rollback`.
Original foreground transitions remain pending user visual acceptance.

#### User rejection and actual frame diagnosis

User rejected v2 for both transitions. Owned runtime diagnostics establish:
primary complete copies use BltFast, not Blt; v2 epoch stayed uninitialized.
Simply adding BltFast (uninstalled v3) still displays a narrow confirmation
panel remnant during save14 exit while the mode remains battle. Actual frames
`tr-diag-fast-before` frame210 show that defect. Native confirmation teardown
changes controls54 ->51 ->46 before the new UI page; mode alone cannot detect it.

Final installed v6 wraps both Blt and BltFast. A signature of control count,
identity,vtable,rectangle invalidates the presentation on control replacement
even within battle. New signatures need full redraws at distinct GetTickCount
values before publication. This is a redraw-confirmation condition, not a fixed
delay. Prototype v4 using641fbc never advanced during the transition and held
black output; it was rejected in isolated testing and never installed. V5
resolved exit but actual New Game frames68-70 still enlarged the loading art:
battle controls precede battle pixels. V6 additionally requires an actual
main-portrait source-template match before committing UI->battle. It reuses
the existing HD HUD pack/matching logic at main control6c4e40; missing pack falls
back to normal eligibility. This extra search runs only during transition.

Owned new-game flow: menu New Game, region page Enter384,642, battle, Esc,
quit640,420, Yes503,454. Save14 follows same quit path after exact fixture load.
`logs/remastered-ui/tr-newgame-v6` captures7 early battle-control presentations
with UI epoch retained; frame71 enters actual battle pixels. Contact sheet
`transition-newgame-v6-proof.png` confirms normal loading art then battle.
`tr-save14-v6` verifies load and exit; `tr-stable-v5` paired sequence shows the
prior narrow residual replaced by complete retained confirmation pixels.
All owned engines cleaned up and mutable settings/saves restored. Trace pixels
are sampled4x for continuous bounded records; screenshots retain full output.
No claim that every transition/render backend is exhaustively accepted.

Diagnostic `tools/probe_transition_frames.py` uses current candidate launcher
whose101/102/103 resources equal formal launcher. Formal launcher intentionally
clears background flags; three early formal diagnostic launches failed private
handshake without AV and were cleaned up. Tracing wrapper is isolated only.
An attempted old diagnostic new-game pair produced empty logs and is not counted.

V6 production installed formal/frozen/candidate with1472 compositor checks
and5106 static release hashes passing. All launchers/AI-budget modules unchanged.
Latest wrapper source `build/remastered-1.1-transition-present-v6/wrapper`;
backup `backups/remastered-1.1-transition-present-v6/rollback.json`.
Stopped-game rollback: `C:/Python314/python.exe modernization/tools/build_11_transition_present.py rollback`.
User foreground acceptance remains pending. Do not rebuild from v2/v3-v5.
# Command response resource101 continuation (2026-10-02)

Current continuation is now `build/remastered-1.1-wrap-route-v1/`, retaining
command-response-v2 and repairing full-map X/Y wrapped topology for save20.
Build/install/check tools build_11_wrap_route.py/install_11_wrap_route.py/
verify_11_wrap_route.py;104 offline checks pass, user save20 acceptance pending.
Authoritative boundary evidence is in path-review-test13.md save20 section.

Follow-up: latest resource101 now command-response-v2, retaining v1 and restoring
native movement destination-effect cleanup in commit_redirect_task. Build tool
build_11_command_marker.py; install/rollback install_11_command_marker.py.
80 offline checks pass; visual acceptance pending user testing. See latest
destination-marker section in ai-strategy-review.md.

Latest formal/continuing resource101 is built from
`modernization/build/remastered-1.1-command-response-v1/`, based on long-route-v2.
New source `runtime/hd11/command_response.inc` and build tool
`tools/build_11_command_response.py` preserve prior route/clock/render hooks.
Player and AI use identical single-player ordinary-walker redirect eligibility;
the new signature-gated50aef2 hook replays native50aa30 then attempts melee-target
redirection. Ground pursuit-to-move commit now restores the correct task handler.
Modules102/103 and external wrapper remain exact previous options-render versions.
No save-format change. Test boundaries and rollback are authoritative in
`docs/ai-strategy-review.md`, installed symmetric responsiveness section.

2026-10-02 conditional click passthrough: module102 build remastered-1.1-canopy-pick over roof-tab source; adds terrain hit-stack capture and unreachable-only right-click movement fallback. Preserves exact roof-ghost-v2 module101 and current103; source/options/AI/lifecycle/roof/casting modules retained. Native engine SHA42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da and original hook-site bytes gated. Build/install helper with before-manifest hashes, per-entry backups and rollback; behavior/evidence in qol-input.md.

2026-10-02 save23 Portmanteau hotkey repair: latest102 source/build remastered-1.1-port-bindings-hd over canopy-pick. Only old hover surface-size guard replaced with shared viewport bounds; native UI mouse and slot rectangles retained.101/103, canopy conditional movement, roof/casting/options/AI modules preserved.196 checks plus isolated live binding persistence pass; guarded installation/rollback helper build_11_port_bindings_hd.py. Details qol-input.md.
