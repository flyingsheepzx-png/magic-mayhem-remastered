# 16:9 experimental candidate

## test14 spell tutorial anchor — 2026-09-30

Current package v37 `package-v37-speech-layout` anchors the fixed teaching scroll
to the sole enabled live spell control. Test14 load, initial dialogue click,
arrow placement and actual spell selection passed; 24 offline hook cases passed.
Existing native battle surface remains 1280x720. Shared UI adapter assessment,
evidence and rollback: `ui-layout-adapter.md`.

## Translucent occluded units — 2026-09-30

Previous package v36 `package-v36-occluded-units-final`: corrected recognition
of actual body passes (mode 31) after v34 failed the user's test13 case.
Stationary test13 stone occlusion verified in game; 30 offline checks passed.
See `unit-occlusion.md` for evidence and remaining visual acceptance scope.

Original v34 design: eligible native-submitted
opaque unit bodies receive a 50% reveal over scene occlusion on native and
replay frames. Original visible pixels and floor clipping are preserved.
Build, 26 offline checks and backed-up installation passed; user visual
acceptance pending. See `unit-occlusion.md` for scope, limits and rollback.

## Cleared occupancy wait — 2026-09-30

Previous package v33 `package-v33-clear-wait`: ordinary width-one walking
units may finish a recorded occupancy wait early when their original next
edge becomes walkable. Native retry, yielding priorities and other waits remain
intact. Build, 28 offline checks and backed-up installation passed; gameplay
acceptance pending. See `path-review-test13.md`.

## Additional ground group slots — 2026-09-30

Previous package v32 `package-v32-group-slots`: ordinary ground-click group
allocation for width-one walkers can try 32 additional positions after the
native 17 are exhausted, within the existing four-cell radius. Original slots,
native validation and excluded command modes are preserved. Build and 165
offline checks passed; gameplay acceptance pending. See `path-review-test13.md`.

## Opt-in terrain trace — 2026-09-30

Previous package v31 `package-v31-terrain-trace`: terrain diagnostic file I/O
is disabled by default; enable only with `MM_TERRAIN_DIAGONAL_TRACE=1`.
v30 embedded modules and all gameplay predicates remain unchanged. Launcher
diff is solely the pinned external terrain DLL hash. 80 offline terrain
comparisons and 4 switch cases passed; user gameplay acceptance pending.
See `path-review-test13.md` for details and rollback.

## Ordinary search allowance — 2026-09-30

Previous package v30 `package-v30-search-budget`: single-player ordinary
searches now receive 600 expansions, matching existing direct/redirect searches.
Native early exit, 16-waypoint output cap and multiplayer budgets are unchanged.
Build, 29 offline checks and installation integrity passed; user acceptance
pending. See `path-review-test13.md` for analysis and rollback.

## Unit lifecycle cache invalidation — 2026-09-30

Previous package v29 `package-v29-unit-lifecycle`: native unit reset and
deserialization invalidate that unit's redirect/replay caches, retaining the
user-accepted v28 index optimization. Build, eight offline compiled-hook cases
and installation integrity passed. User gameplay acceptance pending.
See `path-review-test13.md` for evidence and rollback.

## Replay ownership index — 2026-09-30

Previous package v28 `package-v28-render-index`: only replay command ownership
lookup was optimized; v27 movement and v26 QoL retained. Offline equivalence and
synthetic performance checks passed; user accepted on 2026-09-30.
See `path-review-test13.md` for details and rollback.

## Pathfinding review — 2026-09-30

Previous package v27 `package-v27-path-review` preserved v26 QoL and accepted
terrain changes. Redirect sorting/prediction corrected; shared search throttling
removed for single-player; expensive redirect tracing is opt-in. Build, offline
x86 detour verification and installation integrity passed. Gameplay acceptance
is pending user test13. See `path-review-test13.md` for evidence and rollback.

## Double-key self-cast — 2026-09-30

The preceding v26 `package-v26-qol-double-key` introduced two fresh presses of the
same spell key within 400 ms validate self using native portrait target rules,
then call the existing portrait submitter. Single-press targeting and prior
hotkey refresh/empty-slot changes are retained. See `qol-input.md` for evidence,
behavior and rollback. Build/integrity passed; gameplay acceptance is pending
user testing. Entry SHA-256:
`c23ec895ca1cb5dae31556a9e76713e4963e5125ca4501ed63a344f5ffbe2301`.

## Empty talisman slots follow-up — 2026-09-30

Current package: v25 `package-v25-qol-empty-slots`. User reported v24 did not
resolve immediate binding after adding a talisman. Removed remaining empty-slot
rejection from binding and badge display; preserves v24 refresh/layer ordering.
Entry SHA-256 `a7928183cd379f8c0885413c3d6007a4409b99ba9884c1e994994e0ee3e05f60`.
Build and integrity passed, user gameplay acceptance pending. Details and
rollback are in `qol-input.md`.

## Hotkey live-slot and refresh fix — 2026-09-30

Current installed package is v24 `package-v24-qol-refresh`, retaining v23's
terrain-diagonal fix (user reported test10 normal). Fixes test11 live talisman
binding, invalidates old badges on transfer/Delete, and draws badges before tips.
See `qol-input.md` for native evidence and rollback. Build/hash checks passed;
gameplay acceptance belongs to the user per their new standing instruction.

Entry SHA-256: `69018495fde8109d18f4aea69aefc2e1b9eb762b4c50045d7a39fda34e5bdac5`.
Only embedded QoL resource 102 changed; engine, terrain DLL, other embedded
modules, saves and config remain intact.

## Battle countdown and transient save progress — 2026-09-30

Installed v22 (`package-v22-timer-progress`) fixes the two reported positions.
The exact v21 engine input is
`dbce6a86bfd9becefc3e680078b9f674c944cdb94352374484079c81fe4899dc`.
Five standard battle calls to timer position setter `0x4DE5A0` retained the old
800×600 anchor (640,464), overriding its initialization position. Their X/Y
immediates now add the 480/120 canvas delta, yielding (1120,584). Special
top-screen scripted timer placements are unchanged. Read-only test8 evidence
at global timer `0x6905A8` (+0x28/+0x2C and +0x46/+0x4A) confirms the same
old/new coordinates, with the icon now above the lower-right HUD.

The old progress callers contain `83 C0 CA`: signed imm8 -54, not the intended
positive centering remainder. The high-resolution result is X=53 after divide
by two. Their Y=578+120=698 also cropped the 43-pixel bar at the bottom. A
hash-checked detour at shared constructor `0x4DC4A0` to zero-verified cave
`0x5C4400` sets arguments to (281,655), then replays the original prologue.
Its 718×43 frame is centered on 1280×720 and ends at Y=698. This shared path
covers load/save; no save format, timing, asset or gameplay logic changed.

Independent baseline/candidate captures, test8 fixture hash and byte spans are
under `modernization/playtests/wide169-timer-progress/`. Test8 input SHA-256:
`52b8ee9978f9dab9d78624d9daf051856590653b2c7f3521891cbe5f0504d698`.
`before/baseline/test8-timer-native.png` and
`after/baseline/test8-timer-native.png` show the position change.
`save-frames/frame-144.png` captures the actual saving screen with a partly
filled bar; difference against frame 092 has exact bounds (281,655,999,698).
The independent save completed and returned to battle; all capture sessions
report mutable restoration. Diagnostic saves remain solely in that playtest.
Installed test8 and prefs.cfg hashes were unchanged by installation.

Reproduction tool: `modernization/tools/wide169_timer_progress.py`, using
`modernization/config/wide169-timer-progress-patch.json`; rejects unknown
engine/launcher identities and mismatched old bytes. New engine SHA-256:
`43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`;
launcher SHA-256:
`f9c90c345fe295802794b75822b53440d5b84abe11d491115e7e4a2d511f2eaf`.
All 5070 immutable package files verified. Close the game before rollback:
restore launcher to `game/`, engine to `game-wide169/`, and the two JSON state
files to `modernization/` from
`modernization/backups/wide169/timer-progress-v22/`. This returns to v21.

## Corrected clasp diagnosis and acceptance — 2026-09-29

The user rejected the v20 screenshot: spacing tabs did not fix the doubled
clasp itself. The prior claim that the reported visual defect was fixed was
incorrect. Backdrop.JPG was scaled 1.2x, while icons.spr close-control frames
0 and 1 remained 27×116. Their unchanged origin (1088,286) placed a smaller
clasp over the larger painted clasp, creating the doubled bottom contour.

Installed `package-v21-grimoire-clasp-scale` resizes only these two RGB565
frames to 32×139 with Lanczos; all other 32 frame payloads remain byte-identical.
This is a deterministic scale correction of existing art. The v20 tab spacing
is retained. Engine, launcher, FMVs and preferences are unchanged.
The isolated candidate and evidence are in
`modernization/playtests/grimoire-clasp-v21/verification/baseline/`.
`clasp-comparison.png` compares the rejected v20 crop, corrected crop and hover;
the corrected crop has one continuous clasp contour. `closed-native.png`
confirms clicking it returns to Region Entry. The capture reports restoration.
No installed preference was changed for this candidate test.

Installed sprite SHA-256:
`6b2f3daa5c047aa1855e36db97a8d9adf71dc833b88b2d0811c4a54cf8ea99d4`.
The 5070-file package manifest SHA-256 is
`bc7ffb80c73f711e1d85b1d80974755e34cb9eb32d305523a91ca3a9f98d3c7c`.
Rollback with the game closed: restore `icons.spr` from
`modernization/backups/wide169/grimoire-clasp-v21/` to
`game-wide169/Interface/Grimoire/800x600/icons.spr`, then restore the backed-up
`wide169-installed.json` to `modernization/`. This returns to v20, including
its known clasp defect. Earlier trial packages below are historical.

## Grimoire right tabs and book clasp — 2026-09-29

The user reported overlap between the right chapter tabs and the book clasp.
The clasp is painted into `Interface/Grimoire/800x600/Backdrop.JPG`; its active
close control is placed at `(1088,286)` by `Grimoire.cfg`. Moving that control
alone duplicated the painted clasp (package-v15 trial). Moving the right tabs
inward to X=996 hid most of them behind the book page (package-v16 trial).
Those captures are in `modernization/logs/wide169/1790689950333391700/`
and `1790690127899620200/` respectively and must not be treated as accepted
visual results.

Moving all right tabs to X=1120 kept the click areas clear, but visually
detached the tabs from the book (v17). Moving only the two middle tabs did not
produce a regular layout (v18). The final installed
`package-v20-grimoire-tab-clearance` keeps X=1026 and arranges tabs 1–4 above
the clasp and tabs 5–8 below it. The Y origins are
`10,80,152,219,410,477,544,611`; the close control remains
`[1088,286,1116,403]`. Read-only control inspection found zero overlap
between any adjacent tabs and zero overlap with the close control. The settled
page, lower-tab selection and close/return were captured in
`modernization/logs/wide169/1790691181612847900/`; the run completed with
no protected-file changes. `PlayFMV` was temporarily disabled for the owned
diagnostic run and restored afterwards.

The immutable installed package is
`modernization/build/wide169/package-v20-grimoire-tab-clearance/` (5070 files;
manifest SHA-256
`03678f1fcdd6e32e6fcf71f5505f5b892ac5454389bc9df325352943d4dc0a72`).
The original Grimoire config and install state are backed up in
`modernization/backups/wide169/grimoire-tabs-v19/`; the immediately preceding
v19 state is in `modernization/backups/wide169/grimoire-tabs-v20/`.
`modernization/wide169-installed.json` identifies the installed v20 package.

## Current FMV checkpoint — 2026-09-29

The installed Wide169 entry now plays the startup film centered on its 1280×720
native canvas. The five compatibility AVIs use MSVC with the source PCM streams;
the engine uses `(320,180)` for both startup and in-game FMV paths. Installed
`package-v13-fmv-center` contains 5070 manifest-checked files. Launcher SHA-256:
`84d201637ce3ccebf49b8c9f930c1e5d41083ecc40015d342e19e6ef9b232448`;
engine SHA-256:
`dbce6a86bfd9becefc3e680078b9f674c944cdb94352374484079c81fe4899dc`.
The installed startup capture is
`modernization/logs/wide169-fmv-center-installed-topmost.png`; original AVIs
and the prior installed binaries are backed up at the paths in
`docs/fmv-compat.md`. Other film triggers remain to be played through. The
historical FMV status and hashes below describe earlier packages.

## Latest checkpoint and next-session handoff — 2026-09-27

The user requested ending this long session after a focused finish. The latest
development entry is now `game/Chaos-Wide169-Trial.exe`, incorporating the latest
HD60 QoL source and engine. Future development must start from the latest version
unless the user explicitly chooses another baseline. `AGENTS.md` records this
rule; `current-baseline.json.latest_development` records current binary hashes.
The older top-level fields in that JSON retain the HD fallback/migration inventory.

Completed in this revision:

- Launcher embeds both the widescreen combined runtime and latest QoL runtime.
  QoL only changes its surface guards from 1120×840 to 1280×720. Existing cast,
  cancellation, drag and selection logic is retained.
- Esc background origin changes from hard-coded (100,100) to (280,120), centering
  its 720×480 resource at (640,360). The existing centered button rectangles are
  retained; the test2 Cancel rectangle is (460,456)–(820,504).
- Independent bindings are in `game-wide169/modernization/config/qol-hotkeys.json`.
  Package-v4-qol includes them and reinstall preserves user binding changes.
- `1790521509513913000/result.json`: centered Esc screenshot, verified draw origin,
  Cancel hit and removal of menu controls; 11 combined hooks plus 6 QoL hooks,
  1280×720 native surface, 2560×1440 client, 30 setting; protected hashes unchanged.
- `1790521476479211400/result.json`: test7 Q/W/E/R select native icons 0/2/3/1;
  right-click cancels each and preserves one selected unit. All 17 hooks and
  geometry gates pass; protected hashes unchanged.
- Package check passes with 5070 files. Actual rollback and reinstall both pass,
  preserving the independent QoL configuration and all fallback file hashes.
  Lifecycle evidence is in `modernization/logs/wide169/qol-merge-lifecycle.json`.

Next session should read this checkpoint, `AGENTS.md`, `qol-input.md`, and the
installed manifests before modifying anything. Remaining widescreen QoL gates:
test6 hover bind/transfer/Delete and badge placement, actual left-release spell
effect and box-drag cancellation. Those behaviors passed in the HD QoL parent;
the merged widescreen candidate has only the focused checks above. Also retain
the previously open FMV playback, exact world-map destination, long combat and
multiplayer checks. Do not repeat the full earlier widescreen geometry suite
unless a new change creates a concrete regression risk.

Reproduce the focused checks with:

```powershell
python modernization/tools/wide169_trial.py esc
python modernization/tools/wide169_trial.py qol
python modernization/tools/wide169_install.py check
```

Pre-merge binaries are parked under `modernization/backups/wide169/pre-qol-merge/`.
Package-v3 remains historical. The first Esc probe `1790521412385537300` clicked
Quit rather than Cancel and is superseded by the corrected probe above; do not
use its Cancel claim as evidence.

## Accepted requirements (2026-09-27)

Build a separate opt-in launcher from the hash-verified community engine using
the latest HD60 QoL implementation as the functional starting point. Native battle
canvas is 1280x720, presented at exactly 2x as 2560x1440. Unit/map pixel scale is
unchanged: relative to 1120x840 this adds 160 horizontal pixels and removes 120
vertical pixels. Retain MaxFramesPerSec=30. Presentation is not native 2560x1440
rendering and is not proof of 60 distinct game frames.

Outside battle, retain 4:3 content at 960x720 centered in the canvas, with 160
native-pixel bars / 320 output-pixel bars. Derive art and layouts from original
resources and reversible backups; no generated art. Cover menus, world map,
Portmanteau, Grimoire and character/talismans, including matching input regions.

Keep accepted HD60 and Chaos.exe as fallbacks. Use an independent runtime copy,
package manifest and reversible launcher install; never modify the fallback
runtime to test this candidate. Keep saves independent and compare fixture hashes.

## Required gates

- test2: actual 1280x720 map geometry, four scroll edges, selection and target
  orders, edge-aligned HUD rendering/input and 2560x1440 output client.
- test5/menu: 4:3 proportions, black bars, menu transitions, Portmanteau and all
  three complete aligned talismans; Grimoire and world-map input alignment.
- Eleven runtime hooks, 30 setting, replay allocation/stride/clip bounds.
- Save/load, OGG/FMVs and window switching. Hash every trial's protected files and
  saves; verify one rollback/reinstall cycle.

## Installed candidate and reproducible package

The opt-in entry is `game/Chaos-Wide169-Trial.exe`. It starts
`game-wide169/Chaos-Wide169-engine.exe` with the latter directory as its working
directory. The accepted `Chaos-HD60-Trial.exe`, its paired engine, and original
`Chaos.exe` retain their baseline hashes. The installed engine SHA-256 is
`57b6327d178d798285c5ca64391c1fff5453c12b2af1c35438f117c298985626`;
launcher SHA-256 is
`4cb48052ffad0d1982229725a635c742c544bb0074be3c303a8f3da12890937d`.
`modernization/build/wide169/engine.json` lists each hash-checked address
change. The independent package has 5070 runtime files including its QoL key
configuration; its manifest is `modernization/build/wide169/package-v4-qol/manifest.json`.

Build source: `modernization/tools/wide169_build.py` and
`modernization/runtime/wide169/`. The builder accepts only the known community
engine and checks the HD60 fallback pair and all files in
`hd-qol-trial-installed.json`. It applies only the audited widescreen edit spans
to the latest QoL engine, preserving the remaining engine bytes. Interface derivatives
come from verified original UI backups; Grimoire page BMPs preserve the original
blue and magenta key positions. No new artwork is generated. The native 1280×720
surface is presented by cnc-ddraw at 2560×1440. The independent `ddraw.ini`
sets `savesettings=0` so a previous window size cannot override the package's
2× output on restart.

Install/check/rollback commands, from the project root, with game processes
closed:

```powershell
python modernization/tools/wide169_install.py check
python modernization/tools/wide169_install.py rollback
python modernization/tools/wide169_install.py install
```

Rollback parks the complete independent runtime, including its saves, under
`modernization/backups/wide169/rollback-*`. Reinstall copies the hash-checked
package and restores independent saves, AI state and QoL bindings from the parked runtime.
The package is immutable; a later revision must use a new package directory.
The `package-v3` rollback/reinstall cycle passed, including a fresh launch at
2560×1440 and unchanged fallback hashes. `modernization/wide169-installed.json`
records the installed package and last parked runtime.

## Validation evidence (2026-09-27)

The reports below are under `modernization/logs/wide169/`, each containing
protected-file and save hash checks after the owned process exits.

| Gate | Evidence | Result |
| --- | --- | --- |
| Native geometry, output, hooks and 30 setting | `1790516932156696300/result.json` | 1280×720 native scene; 2560×1440 client; 11/11 hooks; `MaxFramesPerSec=30` |
| test2 interaction | same report | 125-unit fixture; eight selection-corner pixels; hero grid `(66,48,6)` to `(74,47,5)` after target click; roof 1→2→1; four scroll directions pass |
| Replay bounds and composition | `game-wide169/modernization/logs/render-replay.csv`, `render_replay_trial.cpp` | `pitch=2560`, clip `(0,0,1280,720)`, `ui_preserved=1`; buffers sized for 1280×840 and guarded by stride, width, height and clip checks |
| test5 UI | `1790515786539468200/result.json` | world map, Portmanteau, character page and black bars; three talismans complete (743/696/720 colored pixels, 38/37/39 rows); each +/− hit; minimize/restore passes |
| Grimoire | `1790515839112408000/result.json` | centered keyed pages, navigation and zero nonblack bar pixels |
| World map marker | `1790518872540071400/result.json` | centered marker click changes the map selection image; mask conversion retains 800×600 storage and 800-byte stride |
| Save/load | `1790515866398227800/result.json` | new save written and reopened; save bytes and protected files restored after trial |
| OGG/audio | `1790516841394730200/result.json` | game-owned Windows audio session reached peak 0.154; files are present with package hashes |
| Rollback/reinstall | `1790519546539792600/result.json`, `modernization/wide169-installed.json` | package-v3 installed after actual rollback; post-install client 2560×1440; fallback hashes unchanged |

FMV playback remains unverified. The five original AVI files are included and
`PlayFMV=TRUE`/`PlayFMVOut=TRUE` remain set, but this is not playback evidence.
A bounded new-game flow (`1790520184375620600/result.json`) reached Region
Entry; it did not exercise an AVI. The world-map marker probe
(`1790520074850158100/result.json`) confirmed a local visual response, while
the sampled `0x659f51` field stayed zero; this field does not establish the
selected destination. Its exact region ID and destination transition remain
unverified. Output
scaling is not native 2560×1440 rendering, and wrapper presentations do not
establish 60 distinct game frames.
# Input, portrait casting and realm projection follow-up — 2026-09-28

The latest opt-in development entry remains `game/Chaos-Wide169-Trial.exe`, now
installed from immutable `modernization/build/wide169/package-v5-input-map/`.
Launcher SHA-256 is `6a66563580091307ba3b0a27b693a488a64da627069166164457a19a46cc5808`;
the engine remains `57b6327d178d798285c5ca64391c1fff5453c12b2af1c35438f117c298985626`.
The parent package-v4 and complete prior runtime are preserved. The installer
parked the latter at `modernization/backups/wide169/rollback-1790526635871501600`.

- Unit picking retains the native sprite-mask hit and skips the original nearest
  unit fallback. In test9, a blank click at `(610,340)` selected none; clicking
  the wizard sprite `(640,320)` selected one.
- A second left click on the same sprite within 400 ms and eight pixels selects
  visible, active units of the same native type and owner. test9 selected unit
  indices 21–24, and no other units, after double clicking `(480,340)`.
- While a target spell is armed, releasing left on the player's portrait now
  dispatches the native battle cast event instead of the portrait selection
  event. In test9, input mode changed 2→1, pending spell 0→−1, selection stayed
  one, and the wizard's resource field at `unit+0xb0` changed 104→64.
- The realm hover outline and enemy wizard draw positions now use the same 6/5
  projection and +160 horizontal offset as the resized 960×720 map. test8
  captures show the dashed outline inside the mountain region and the enemy
  wizard icon on the map, with multiple hover positions exercised.

Evidence: `modernization/logs/wide169/input-map-verify-1790526825260028000.json`
and its referenced test9/test8 captures. The formal package rollback/reinstall
passed with fallback hashes unchanged. Post-install `wide169_trial.py qol` and
`wide169_trial.py test2` passed in reports `1790526863307251700/result.json` and
`1790526908546460100/result.json`; `wide169_install.py check` verified 5072
runtime files after testing. Saves and protected files were restored by the
bounded sessions. Further widescreen compatibility work listed below remains
open; these checks do not establish 60 unique rendered frames or unchanged
gameplay time.

Rollback: with game processes closed, run
`python modernization/tools/wide169_install.py rollback` from the project root.
The preserved package-v4 runtime above is available for restoration if needed.

## Realm texture alignment and relaxed picking — 2026-09-28

The current package is `package-v6-realm-targets`. Launcher SHA-256:
`73cfd65f9230972e86b881caa5b482714cf22f57eeb4416b63e34694687d370a`.
The engine is unchanged. The complete previous installation is preserved at
`modernization/backups/wide169/rollback-1790535452729393100`.

Two separate realm defects were measured. The live hover handler at `0x55199e`
reads mouse queue coordinates and performs its own mask lookup; it never calls
the previously patched `0x5505a0` helper. The handler now subtracts 160 from X
and uses 960/720 visual denominators while retaining the 800-byte mask stride.
Second, `0x58c8a0` normally uses `BltFast`, which ignores destination dimensions.
The cached border source is ECX/EDI; the destination is the first stack argument
and later EBX. A source-identity-gated hook uses keyed `Blt` with a destination
rectangle projected by 6/5 and +160. Moving only the origin or rectangle without
changing BltFast cannot align the highlighter's terrain texture.

test8 coordinates `(570,270)`, `(450,190)`, `(760,224)` now resolve to regions
5, 6 and 3 respectively. `1790533598637578100/texture-alignment.json` records
landmark gradient matching against the unhighlighted backdrop: mountain shift
(0,0), forest (0,1), lake (1,1) native pixels. Palette differences and distinct
resampling filters limit correlation; use both region identity and terrain
alignment, never just the outline's approximate location. The native 1280x720
diagnostic captures were verified, but this session's wrapper output client
was 1280x720 rather than the requested 2560x1440; full output scaling remains a
separate gate. Queued highlighter rendering was not active in these samples.

Unit sprite-mask picking now permits an eight-native-pixel radius around the
mask. The unbounded nearest-unit fallback remains disabled. Final candidate
regression: `input-map-verify-1790534011120697800.json` (blank 0, hero 1,
double-click 4, portrait cast retained, summon dispatched). Five test2 ground
movement samples in `1790531578287430600/ground-targets.json` had matching hover,
command and reached grid. These checks do not alone prove every visual cell
center or summon placement; preserve that distinction. Post-install realm and
battle regressions: `1790535691435232500` and `1790535797443552000`. Protected
files and saves were restored after diagnostics.
## Dialog, Grimoire and double-click selection follow-up — 2026-09-28

The latest development entry is installed from immutable
`modernization/build/wide169/package-v7-dialog-grimoire-selection`.
Launcher SHA-256 is `db177f3b73c123f3d3bec14483b657c5e709f6697513856db3e3fed66e369ab8`;
engine SHA-256 is `1d2df6135238dec69f6ec74280440a06b43c66353c886f42633f4143d710b16f`.
The complete previous v6 installation is preserved at
`modernization/backups/wide169/rollback-1790562698030243900`.

- The native confirmation dialog now centers against the 1120×600 content
  bounds. Its background and Yes/No controls align inside the menu. The
  800×600 resource selector is unchanged.
- `GenericL01`–`GenericL03` Grimoire pages now use the same 160-pixel left-page
  inset as other left pages. The realm tab in test8 now places its six icons and
  Chinese text within the book, without the black vertical gap.
- Synthetic same-type double selection sets the native group-selection state
  used by the next ordinary click. In test9, four skeletons selected by double
  click became only skeleton index 22 after a click on that skeleton.

The bounded candidate run passed all three checks at
`modernization/logs/wide169/followup-1790562623239677100.json`, including
native-surface captures and save/config restoration. Its 1280×720 native
surface and 30 FPS preference passed; the wrapper client was 2048×1152 in
this session, so exact 2560×1440 output remains a separate display gate.
The installed package manifest verified 5072 runtime files and the fallback
entries remained unchanged. Rollback with all game processes closed:
`python modernization/tools/wide169_install.py rollback`.
## v23 terrain diagonal — 2026-09-30

User-authorized install after stationary test10 paired replay and visual
confirmation. Shared native terrain hook removes the portal-side low-height
diagonal detour while retaining actual solid obstacles. No automatic saved-route
refresh; fresh movement commands use the new rule. Preserves v22 engine and
embedded QoL/repath modules. Entry SHA-256
`8ef2806f8c383323f81cb2fb69fde2fdd30ebd208a32bdecbe363418caffa5c3`.
Details, scope limits, evidence and rollback are in `test10-diagonal.md`.
Broader playtesting was explicitly delegated to the user, not reported passed.

# Repeatable portrait self-casting — 2026-09-29

The first v8 portrait correction (`e0989070…`) was incomplete: it dispatched
one native cast but left target mode. The user clarified that the spell must
remain selected so two consecutive portrait clicks can both cast without
pressing Q again. That corrected behavior is installed in immutable
`package-v9-repeat-self-cast`, launcher SHA-256
`1c8c76b07422975a17c34f2fc71ba6caf3979e5caaef544dc99a24ff2099b05b`.
The engine and embedded pathfinding DLL remain at their v7 hashes.

The portrait hook supplies the represented wizard as the native picked target
for one synchronous dispatch, restores the pick cache, then reactivates the
same native spell button after the cast clears its pending state. In test7,
Q followed by two left clicks on the portrait at native `(1215,650)` kept
target mode 2, icon 0, pending spell 0 and one selected wizard after **each**
click. The wizard resource field changed 104→88→64 across the two dispatches;
that field is corroborating telemetry, not the sole success criterion.
Candidate and installed reports:
`modernization/logs/wide169/1790620757572478700/result.json` and
`modernization/logs/wide169/1790620877259399700/result.json`.
The installed report completed with no protected-file changes. The prior v8
launcher is backed up under
`modernization/backups/wide169/repeat-self-cast-1790620831950405600`.
With the game closed, `python modernization/tools/install_wide169_self_cast.py rollback`
restores v8. The v7 launcher is preserved in the earlier v8 backup.
Other spells and target types remain separate compatibility checks.

## Portrait healing verified against injured test7 — 2026-09-29

The earlier v9 acceptance was incorrect. `unit+0xb0` changes with animation
and the armed UI state does not prove a heal. The user supplied a new injured
`test7.sav` (SHA-256 `0eb63c2cc3381d057a2617be3deed29b28d1166a95600baa8f7d1b5a15291e1e`).
On v9, two left portrait clicks left the wizard's actual life (`unit+0xe4`)
at 122 with no golden cross. A right portrait click and a left world-sprite
click each raised life from 122 to 200 after about 0.5 s.

The portrait control's native right-click branch calls `0x57ce70` with its
wizard pointer. The v10 left-release hook now calls that same native routine
while target mode is armed, preserving the native spell selection. This
replaces the unsuccessful synthetic world click. Installed launcher SHA-256:
`5aadf9f8f1c0ea1e2d6da26d4b32e3ef71d0532280e664b8711d6b35e5484a4f`;
engine and embedded pathfinding DLL retain their v7 identities. In both
candidate and installed runs, Q then two left portrait clicks produced a
golden cross each time; golden pixels near the wizard increased from 75
before casting to 290 and 319 in the two click captures. Life rose 122→200
after the first click, and mode 2/icon 0 remained after both clicks. The
second heal occurred at full life, so its independent cast evidence is the
second cross. Installed report:
`modernization/logs/wide169/1790624316787225200/result.json`; no protected
files changed. The v9 launcher is backed up at
`modernization/backups/wide169/portrait-heal-1790624305275259100`.
Run `python modernization/tools/install_wide169_self_cast.py rollback`
with the game closed to restore it.

## Per-unit path redirection — 2026-09-29

The v10 embedded path hook returned immediately unless the moving unit was
unit 0 (`u == global(0x6def58)`). This explained why the wizard benefited while
summoned zombies did not. The v11 hook in `runtime/wide169/repath_multiunit_trial.cpp`
uses a separate redirect state per validated unit-table slot and checks each
slot's unit identity before reusing its state. It does not filter on owner, so
friendly and hostile units enter the same safety and rerouting logic. The
existing single-cell ground movement and collision gates still apply; unsafe
edges use the native route.

The updated isolated `test2.sav` contains the wizard at index 0 and two
summoned zombies at indices 9 and 10. On v10, repeated orders gave the wizard
three `order_mid_segment` and three `redirect` events; both zombies moved but
had no optimization events. With v11, each of these three units generated
three or more mid-segment events and redirects, plus custom-segment finishes.
An enemy at grid `(19,23,7)` also entered `order_mid_segment` and took
`fallback_anchor_busy` because the anchor was occupied. This confirms the
owner-independent entry and safe fallback; a successful hostile redirect in
this scene was not observed. Installed-run evidence is
`modernization/logs/wide169/1790625076876812700/result.json` and its paired
`modernization/logs/wide169/1790625076876812700/repath-trial.csv`. The run completed with no
protected file changes, and `test2.sav` stayed at SHA-256
`cdf39217fb5933d541ad9e943bf77b1ae9774d42fa4c5985f1308c17ffe90087`.

The v11 launcher retains the v10 QoL resource byte-for-byte. The candidate
repeated Q and two left portrait clicks in injured test7: actual life rose
122→200 after the first click and target mode remained armed after both.
Installed launcher SHA-256 is
`01119a189bfd50d3fed7a07d436be66dd02d93266dd259206084b34102c35bc0`.
Rollback with the game closed:
`python modernization/tools/install_wide169_multiunit.py rollback`.
The v10 launcher is backed up under
`modernization/backups/wide169/multiunit-1790625070374747500`.
