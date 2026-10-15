# HD UI integration lab

## Isolation and baseline

The HD integration work runs in the managed worktree at
`C:\Users\DEVELOPER\.codex\worktrees\hd-ui-lab\Magic&Mayham`, branch
`codex/hd-ui-lab`. The original `D:\Games\Magic&Mayham` checkout remains the
pathfinding/frame-timing workspace. The lab has a full playable game copy,
including media, Chinese assets, saves and the installed community wrapper.
`modernization/assets/hd/copy-manifest.json` records SHA-256 for 4,876 copied
game files; this manifest and commercial files are ignored by Git.

`Chaos.exe` in the lab hashes to the verified community SHA-256
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
The wrapper is from the immutable baseline. The lab's `CFG/prefs.cfg` was set to
the user's installed 30-update preference, with its original 20-update bytes
backed up under ignored `assets/hd/backups/`. The mutable live `AI/EXPERIEN.DAT`
was replaced in the lab with the immutable baseline copy after the live file
changed during duplication. No game file was modified in the original checkout.

## Game-load evidence, 2026-09-27

The Qwen-Image 2.1 output for the main menu is a 1920×1440 PNG. The unmodified
engine requests `Interface/MainScreen/800x600/Main Menu 800-600.JPG` by name.
`tools/hd_menu_trial.py` verified the source and output hashes, backed up that
JPG in the lab and wrote a temporary quality-100 diagnostic JPEG to the known
path. It always provides a checked rollback. This JPEG is only a loader probe;
the actual prepared HD pack remains lossless PNG.

- Loading the full 1920×1440 JPEG at the old JPG path succeeded, but the game
  drew it unscaled into the 800×600 surface. Only its upper-left region was
  visible, while the Chinese menu labels and clickable rectangles stayed at
  old coordinates. This is a concrete failure of native 2K UI integration.
- Placing the exact generated PNG bytes at that `.JPG` path failed. The game
  opened a Chinese **file read error** dialog naming
  `Interface\MainScreen\800x600\Main Menu 800-600.JPG` and saying it could not
  read the file, then requested exit. The lab script captured the dialog text
  through Python window APIs and restored the original JPG. File content alone
  does not make the existing loader accept PNG.
- Downsampling the generated image to 800×600 before the same JPG-path test
  produced a correctly aligned menu. The Chinese title was intact, menu labels
  aligned and the background filled the surface. This validates the generated
  content as a compatibility replacement, not 2K native detail.
- Repeating that compatibility replacement for the Battle Options background
  yielded a readable settings page with music, effects, animation and resolution
  controls. The old in-game resolution radio buttons still show only 800×600
  and 640×480.
- A separate wrapper presentation test requested a 1920×1440 client. The client
  measured exactly 1920×1440 while a primary-surface screenshot measured
  800×600. This is output scaling. It is not native 2K asset loading or an
  expanded map viewport.

The private diagnostic wrapper (`SHA-256
92da583af01c045d6e9fb9661c7ae017909b774c4a98aa8f4d0b5b7cc056069d`)
was installed only during bounded lab runs. `tools/hd_background_trial.py`
uses its acknowledged private mouse channel and primary-surface screenshot
request. A click at client `(400,480)` opened the settings page; the two saved
800×600 surfaces differed by mean absolute RGB value 14.955. The trial restores
the community DLL and INI byte for byte and terminates only its owned process.
It now refuses input if the game retains foreground focus after launch.
Captures and JSON results live under ignored `assets/hd/background-trials/`.
An interrupted or failed trial leaves a `recovery.json` with the exact wrapper
and INI backups; the Python `finally` path restored both on the PNG failure.

`tools/hd_compat_pack.py` stages same-path 800×600 JPEG derivatives from
completed, unkeyed UI JPG outputs for content review. At the first 78 completed
UI outputs, it staged 9 and skipped 65 keyed JPGs, 4 BMPs and 1 PCX. It never
installs them. Re-encoding keyed JPGs would corrupt transparency, so full UI
replacement requires a verified lossless PNG loader or another format-safe path.

## Three-tier policy

The user's selected tiers are 640×480, 800×600 and 1920×1440. In the lab,
`tools/hd_resolution.py` selects all three with a verified backup and restore:
the first two set the original `IsHighRes` Boolean, while the 2K tier keeps
the 800×600 game surface and asks cnc-ddraw to present at 1920×1440. This is a
temporary compatibility path. `tools/hd_layout_tier.py` separately generates
candidate `Rect3` and `1920x1440_*` CFG values. The executable has no proven
reader for them, and they are not installed.

## Current isolated deployment

The lab copy is left in its opt-in 2K **presentation** tier. Generated menu and
settings backgrounds are installed there as checked 800×600 JPEG conversions.
The last background run reached settings at client `(400,480)`, measured a
1920×1440 client, captured two distinct 800×600 game surfaces and restored the
temporary diagnostic DLL/INI. `Chaos.exe` in the lab can be launched directly
for this compatibility demonstration. No lab game process was left running.

Rollback in the lab directory:

```powershell
python modernization/tools/hd_menu_trial.py restore --asset menu
python modernization/tools/hd_menu_trial.py restore --asset options
python modernization/tools/hd_resolution.py restore
```

The original game at `D:\Games\Magic&Mayham` still has the known executable,
menu, settings JPG and community wrapper hashes. Nothing was copied back.

## Remaining native 2K work

1. Map and implement a hash-gated, opt-in third resolution selector in the
   engine. Preserve the original two modes and multiplayer behavior.
2. Create a native 1920×1440 UI surface and propagate its dimensions through
   asset loading, blits, fonts, hit testing and input transforms. The failed
   full-size JPG test is the first regression case.
3. Resolve staged PNG paths, or provide a verified lossless loader for prepared
   assets. Existing hardcoded JPG/BMP/PCX path templates do not read the pack.
4. Validate settings, menus, Grimoire, save/load, Chinese text, FMV and OGG in
   the lab. Merge only after the pathfinding/frame-timing branch is stable.

Do not treat 1920×1440 wrapper output as native UI or as 60 distinct game frames.

## Expanded battle viewport investigation, 2026-09-27

The user selected **about twice the visible map area**, with unchanged world and
unit scale. For an initial 4:3 camera rectangle, `1120×840` native game pixels
provide `1.96×` the area of `800×600`. A 1920×1440 output can scale that 4:3
image uniformly by `12/7`. This is now an opt-in sibling EXE experiment in the
isolated copy, not a setting in the original game. UI positioning and the eventual native 1920×1440 artwork remain separate
work; the old HUD can first scale with the game scene for viewport testing.

The lab's `tools/hd_background_trial.py --load-test2 --present-2k` now loads the
SHA-256-verified `test2.sav` with Python private background clicks, refreshing the
game window handle after scene transitions. It verifies the known `Chaos.exe`
hash, backs up/restores the diagnostic DirectDraw DLL and INI, and checks save
hashes. In the successful run `assets/hd/background-trials/1790460320093409100`,
the foreground window remained unchanged during the two private clicks, the
load reached a 125-record unit table with unit 0 at `(66,48,6)`, and three saved
primary-surface images were all `800×600` despite a `1920×1440` wrapper client.
The selected-unit probe at `assets/hd/background-trials/1790460959665627300`
also showed a changed outline around the player after a private click at
`(400,295)`; the player crop's mean RGB delta was 12.464 while an unchanged
terrain corner measured 0. The foreground remained stable. This provides a
repeatable battle fixture without controlling the user's desktop cursor.

A further read-only geometry sample in run
`assets/hd/background-trials/1790462193172190800` found the active battle
rectangle pointer at `0x6c482c` containing `(0,0,800,600)`. The camera-like
object at `0x689930` held the same rectangle and stored width/height `(800,600)`
at `+0x51/+0x55`. Static disassembly of the supported executable shows
`0x4f7970` copying that rectangle and deriving its width/height. This makes
these fields useful tracing sites, but their relation to world culling and the
camera origin still needs runtime proof. The same object held `(66,48,6)` at
`+0x39/+0x3d/+0x41`, matching the loaded player grid triple; this is a camera
tracking lead, not yet a demonstrated projection transform. Moving the private
mouse to the right edge for one second left these fields unchanged, so that
gesture did not provide a camera-motion calibration. `0x46b91a`–`0x46ba10` is the battle
presentation path; `0x4a45b0` and `0x4a4910` use the Boolean resolution flag to
form `640×480` or `800×600` rectangles in display/input code. A whole-section
scan found 372 raw references to the high-resolution flag and many uses of the
two sizes. Patching one rectangle would
leave surface allocation, clipping, input, HUD, and camera culling inconsistent.
Later diagnostic runs measured a 960×720 wrapper client despite a 1920×1440
request, indicating wrapper window size also varies between runs; the game
surface and geometry remained consistently 800×600. Measure the client each
time rather than treating the requested wrapper size as proof of actual output.

The read-only geometry wrapper, built from pinned cnc-ddraw commit
`279a057ee7e1e4d584b56141c014ab01f3c6ee6d`, found the shared battle
offscreen surface call at `0x4e41ec`. The hash-gated
`tools/hd_surface_lab_build.py` changes four sizing immediates in a sibling
`Chaos-hd-surface-lab.exe`. Its `1120×840` primary surface still left the
right and bottom bands almost entirely black. Thus surface allocation alone
did not expand the view.

Adding only the active high-resolution battle rectangle constants at
`0x5e1728/0x5e172c` produced `Chaos-hd-viewport-rect-lab.exe` (SHA-256
`0ce5ae60b3d399ff10632e5755e601afe8fd02f5691d62147615df90a1ea4f52`).
The builder checks the source community EXE SHA-256
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`
and exact old bytes at every patch site. It never overwrites `Chaos.exe`.
The isolated `test2` run `assets/hd/background-trials/1790463094937868800`
loaded 125 units; the active rectangle, camera rectangle, camera width/height
and all three primary-surface screenshots were `1120×840`.

`tools/hd_viewport_verify.py` compared that frame with the original `800×600`
`test2` frame from run `1790462810204068600`. The old view appears at
offset `(160,120)` within the expanded surface. In a static terrain region,
95.73% of pixels match exactly at 1:1 scale. The new surface area is `1.96×`;
the four new outer bands contain map pixels, with only 3.48–7.59% near-black
pixels. The right and bottom bands in the surface-only build had 98.41% and
100% near-black pixels. This establishes real added map content without changing
the size of existing terrain and units.

Input run `1790463224007471000` used the private background channel to select
unit 0 at native `(560,415)`, then right-click native `(1000,420)` in the newly
visible right band, outside the centered original view. The destination marker
appeared at that location; after five seconds unit 0 moved from grid
`(66,48,6)` to `(73,47,5)`. The user's foreground window stayed unchanged for
the private input, the save hashes stayed unchanged, and the temporary wrapper
DLL/INI were restored. This verifies a right-band order in this battle fixture.
Other battle maps, edge clipping, UI screens, save/load, multiplayer, audio and
FMV remain untested with this sibling EXE. The separate three-tier selector's
`2k` setting still presents the original `800×600` game surface; it does not
select this viewport experiment or load the native 1920×1440 UI assets.

An additional run `1790463506156961200` measured a `1920×1440` wrapper client
and five `1120×840` primary-surface images. Its script explicitly confirmed all
eight yellow selection-corner pixels before sending the right-band order;
unit 0 moved to `(74,47,5)`. Button-down is held for 80 ms so the 30 Hz game
poller can observe it; a preceding 10 ms trial failed the selection gate and
correctly sent no movement order. The private channel takes **native surface
coordinates**, bypassing the presentation transform; ordinary desktop mouse
input in the expanded mode is not yet validated. Earlier wrappers briefly
activated the game at startup despite the wrapper flags. The background patch
now adds `WS_EX_NOACTIVATE` to top-level windows. Wrapper SHA-256
`217ada6704b3eaf7d0ca1efde41980a303d2c8ad72925fcd50e285f8072dfec8`
is checked before each run. Run `1790463743396455200`, with the lab preference
restored to the authorized `MaxFramesPerSec=30`, measured a `1920×1440` client,
confirmed all eight selection-corner pixels, and moved unit 0 to `(76,46,3)`.
The foreground stayed unchanged from startup through every private input.
The script now also backs up and restores `CFG/prefs.cfg`. Its display-tier
tool preserves the authorized 30 FPS default. HUD icons currently retain their old positions inside the
expanded map; this is an experiment, not a release build.

To reproduce the diagnostic DLL, use a disposable checkout at the pinned
cnc-ddraw commit, run `hd_wrapper_geometry_patch.py <checkout>`, then build its
solution with MSBuild `/p:Configuration=Release /p:Platform=x86`. Copy
`bin/Release/ddraw.dll` into the lab's ignored
`modernization/assets/hd/background-noactivate-ddraw.dll`. A fresh compiler
build may have a different binary hash; review the source and deliberately
update the diagnostic hash before running, rather than disabling verification.

Repeat the experiment in the isolated copy with:

```powershell
python modernization/tools/hd_surface_lab_build.py --battle-rect
python modernization/tools/hd_background_trial.py --load-test2 --viewport-rect-lab --band-move-test
python modernization/tools/hd_viewport_verify.py modernization/assets/hd/background-trials/1790462810204068600/screenshots/frame-02.png modernization/assets/hd/background-trials/1790463743396455200/screenshots/frame-02.png --movement-result modernization/assets/hd/background-trials/1790463743396455200/result.json
```

At this viewport-only checkpoint, the next gate was a selectable HUD build,
additional maps and UI transitions, and the native 2K UI asset loader. The
selectable HUD build is recorded below. Merge with the pathfinding branch only
after both isolated changes are ready for joint regression testing.

## Bottom-right battle HUD and opt-in launch, 2026-09-27

The user accepted the 1.96× map area and requested battle UI movement toward
the lower right before implementation. The original community game implements
the `640×480` to `800×600` battle HUD by adding `(160,120)` to fixed control
anchors while keeping their physical sizes. For example, the wizard portrait
rectangle moves from `(520,340,635,480)` to `(680,460,795,600)`, and the spell
toolbar follows the same offset. The 1120×840 experiment follows that rule with
another `(320,240)` from the 800×600 anchors.

`tools/hd_hud_build.py` builds `Chaos-hd-hud-lab-v2.exe` (SHA-256
`71e58150ecc98b3b6ef9b2fe7e29bce6c15dc22161e6dc19841cd27bd71325dd`)
from the verified community executable. It preserves the 1120×840 surface and
map rectangle patches, then adjusts the wizard portrait, spell toolbar,
control-limit icon/counter, and related cursor clipping constants. Each site
checks the exact original x86 instruction and constant before writing; the
original `Chaos.exe` is untouched. The prior incomplete HUD sibling is retained
in the ignored lab files for rollback, and neither is copied to the installed
game. The earlier identification of the circular house icon as a map object was wrong.
Disassembly at `0x47106D` shows the roof-visibility control; its callback is
`0x46FC50`. It is now anchored at the lower right.

In trial `assets/hd/background-trials/1790465777554004000`, the wrapper client
was `1920×1440`, all battle primary-surface captures were `1120×840`, and the
wizard portrait runtime rectangle was `(1000,700,1115,840)`. The Python
private channel clicked its new center `(1058,770)`, confirmed eight selection
corners around the player, then ordered a move at `(1000,420)` in the expanded
right map band. Unit 0 moved from grid `(66,48,6)` to `(76,46,3)`. The game never
took foreground; diagnostic DLL/INI/preferences and saves were restored.
`tools/hd_hud_verify.py` compared the 800-anchored and 1120-anchored test2
screenshots: all 729 control-limit, 6,946 portrait, and 1,684 spell-toolbar
gold pixels matched after `(320,240)` translation, with zero such pixels left
at the three old positions. `tools/hd_viewport_verify.py` still found 1.96×
scene area, 98.37% exact static-terrain overlap after `(160,120)` camera
translation, and only 3.65–7.59% near-black pixels in the added outer bands.

`tools/hd_resolution.py` retains the three requested tiers. The `2k` tier
configures the 1920×1440 wrapper; `tools/hd_launch.py` now selects the
hash-checked HUD sibling for that tier and the community EXE for 640/800. This
is the opt-in implementation **inside the isolated game copy**. Launch with:

```powershell
python modernization/tools/hd_resolution.py 2k
python modernization/tools/hd_launch.py --dry-run
python modernization/tools/hd_launch.py
```

Rollback: stop the lab game, run `python modernization/tools/hd_resolution.py
restore`, and launch the unmodified `Chaos.exe` there. The binary sibling can be
rebuilt from source; the three-tier selector and launcher never edit the
community EXE. The full-size menus and settings UI still draw at their legacy
800×600 coordinates inside the expanded surface, leaving black extra bands on
those screens. Native 1920×1440 UI loading, layout and normal foreground mouse
mapping have not yet been validated. The installed original remains reserved
for the active pathfinding/frame-timing session; merge/deployment waits for
joint regression after that work becomes stable.


## Follow-up: roof button, scroll edges and main menu, 2026-09-27

The user reported three defects after testing the v2 lab. The verified community
EXE shows that the official 640×480→800×600 expansion is spread across roof
control creation (`0x47107E/0x471091`), cursor backing and restore regions,
window/input dimensions, and the exact-pixel scrolling logic at `0x469C31`
through `0x469D6E`. The menu has a separate backing surface and asset filename
calculation: enlarging the backing surface at `0x4A7181/0x4A7192` is safe,
while changing the filename calculations at `0x4A722F` onward would request
missing `1120×840` resource directories. The same official-resolution audit identified many unrelated bounds, which
were left alone pending screen-specific evidence.

`tools/hd_hud_build.py` now produces the isolated `Chaos-hd-hud-lab-v4.exe`
(SHA-256 `baf839075c7df3c95af7071d3266d84499a4bdeb224c31cbdf6017218b1de922`).
The original executable is hash-gated and unchanged. The roof button rect is
`(950,748,990,788)` in the 1120×840 battle. Trial
`assets/hd/background-trials/1790467844974042900` clicked its center twice
and read roof state `1→2→1`. Private cursor positions `(900,420)`, `(560,650)`
and `(1100,680)` maintained stable in-bounds restore rectangles. All four
exact outer edges `(1119,420)`, `(0,420)`, `(560,839)`, `(560,0)` selected the
expected direction cursor `7,9,8,6` and changed camera coordinates. The
1920×1440 wrapper client, 1120×840 game captures and expanded-band movement
also passed. The game did not take foreground; temporary wrapper/config/menu
files were restored, and saves were unchanged. This private input path bypasses
normal desktop-pointer transformation, so a foreground mouse check remains a
user-facing release gate.

`tools/hd_menu_fit.py` fits the verified generated menu image to 1120×840 and
scales all seven main-menu `Rect2` hit/text rectangles by 1.4, retaining the
community 800×600 resource filename and `Rect1` coordinates. The same trial
loaded `test2` via the scaled menu button. The outer right/bottom menu screenshot
bands matched the fitted JPEG with mean per-channel pixel differences below 7.
The three-tier selector applies this only for the 2K sibling and restores the
prior compatibility menu/JPG and CFG for 640/800; a 800→2K→640→2K selector
cycle and dry-run hash check passed. `modernization/assets/hd/backups/menu-fit/`
and `menu-fit.json` record rollback in the isolated lab. Settings and other
menus still need screen-specific full-surface adaptation and transition tests.
The original game and active pathfinding session remain separate until joint
validation.

## HD UI handoff candidate v13, 2026-09-27

The current isolated handoff is `Chaos-hd-ui-lab-v13.exe`, built only from the
hash-verified community engine SHA-256
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
Its SHA-256 is
`d0e3f37b9e5513878de4b26856b2482daf45c5fd4780bb9c2e6429e63fe0034e`.
`assets/hd/hud-build.json` is the machine-readable list of all 148 address edits,
including expected original values, replacement values and semantic labels.
The builder refuses any other source executable.

The 2K presentation tier is a 1120×840 native game surface shown through the
wrapper at 1920×1440. It deliberately remains distinct from native 1920×1440
rendering. The selector retains all three requested modes: 640×480, 800×600 and
2K presentation. `tools/hd_ui_fit.py` applies 23 scaled CFG layouts and 247
raster resources (270 tracked files total), records original/applied hashes and
restores them for the lower tiers. Three completed Qwen backgrounds—main menu,
battle options and load game—are enabled as verified samples. The remaining
full-screen images use deterministic source enlargement pending individual
generated-art review.

Grimoire pages use two independent colour keys. Blue marks the outside of the
torn parchment and magenta marks the text window. `qwen_canvas.py` now derives a
fixed three-valued template (art/blue/magenta) only from the original page,
scales that template with nearest-neighbour sampling and paints exact key colours
over the generated image after all Qwen/resampling work. Generated pixels never
participate in key classification. `tools/hd_keyed_pages.py` records the original,
Qwen, template and derivative hashes for all 190 completed pages. The v13 engine
tries the lossless BMP path and decoder before the legacy JPEG fallback, and the
2K selector installs 190 reversible BMPs with provenance
`verified-qwen-source-template-bmp`. The final Grimoire screenshot has no blue
outline around the parchment.

Final private-background regressions:

- `assets/hd/grimoire-v13-qwen-template.out.json`: region entry and Grimoire,
  1120×840 captures, clean keyed page, files restored, saves unchanged.
- `assets/hd/menu-flow-qwen-v13.out.json`: main menu, options, load, region,
  quick battle and multiplayer destinations at 1120×840; saves unchanged.
- `assets/hd/battle-regression-v13.out.json`: test2 load, roof `1→2→1`, stable
  cursor rectangles, four scroll edges, portrait selection and right-band order;
  unit 0 moved `(66,48,6)→(76,46,3)`, files restored and saves unchanged.
- An 800→2K selector cycle restored/reapplied the UI and keyed BMP state, and
  `hd_launch.py --dry-run` reproduced the v13 hash.

This is ready for a separate combined 30/60+HD candidate, not direct replacement
of the installed main entry. The frozen replay DLL still assumes an 800×600,
1600-byte-pitch surface; its buffers, clipping and UI merge must be generalized
before enabling it on 1120×840. Preserve the accepted 800×600 candidate and the
original engine as fallbacks. Normal foreground pointer behavior was previously
accepted by the user for the v4 battle path, but save/load, FMV/audio, alt-tab and
less common UI screens remain combined-release gates.

## Combined HD60 UI follow-up, 2026-09-27

The user's merged executable is now the direct playable candidate. Final files:

- `Chaos-HD60-Trial.exe`: SHA-256
  `9ab567e1f720a440a6d1d52bdddbed85cfe5363917ff35ccf3a7791849c28a66`.
- `Chaos-HD60-engine.exe`: SHA-256
  `b7414bb05f67bc80857f31cfce5ce07ccd755594f774f1878cfa93938c070744`.
- `modernization/runtime/combined_hd60/combined_hd60.dll`: SHA-256
  `1ec698a03854a1bb95f88a764b8dc411dd83f363d136dff1e9abc4d580acb181`.

`tools/hd_hud_build.py` now follows the same fixed-offset rule used by the
official 640×480→800×600 mode for the remaining screen-specific geometry. The
two five-item enemy-warning columns occupy `x=1084..1120` and
`x=1048..1084`, directly below the right-side map. Battle tooltip bounds now
use 1120×840, the speech/cutscene continuation control covers the full
1120×840 surface, and all four loading call sites use the enlarged bottom-centred
anchor. Loading internals consistently use an 837×50 active region.

The reversible UI fit now tracks 283 files. It adds the 840×560 ESC mini-menu,
eight 840×50 loading bars, and four additional 1120×840 BMP resources discovered
when BMP fitting was enabled. No Qwen-derived transparency classification is
used; the source-derived colour-key template policy remains unchanged.

Automated private-background evidence:

- `test2`: 1120×840 scene/camera, roof `1→2→1`, stable cursor rectangles,
  correct four-edge scroll directions, and a selected-unit order in the added
  right band. Unit 0 moved `(66,48,6)→(74,47,5)`; saves were unchanged.
- `test3`: all ten enemy controls exactly matched their right-aligned rectangles;
  a portrait click plus dwell produced the tooltip in `(1000,715)-(1115,772)`;
  the centred ESC image occupied `(100,100)-(940,660)`. All visual gates passed
  and saves were unchanged.
- `tools/verify_hd60_runtime.py`: all 11 runtime hooks were `JMP`, the live
  surface was 1120×840, all loading and speech immediates matched their expected
  values, the eight loading resources were 840×50, the ESC bitmap was 840×560,
  and `MaxFramesPerSec=30` was preserved.

The loading screen blocks the game thread and does not service the diagnostic
wrapper's private screenshot request during loading. Therefore the loading gate
is static and dimensional, not a captured visual frame. The cutscene click area
is likewise byte-verified because the current test saves do not expose a stable
cutscene fixture. These two checks must not be described as manual visual tests.

Rollback is hash-gated and restores the preceding launcher, engine and thirteen
newly fitted raster records:

```powershell
python modernization/tools/rollback_hd60_ui_fix.py
```

The backup manifest is `modernization/backups/hd60-pre-ui-fix/rollback.json`.
The accepted community `Chaos.exe`, `Chaos-singleplayer-600.exe`, saves and
the original installation were not modified.

## Victory, realm map and portmanteau, 2026-09-27

The latest playable lab entry is `Chaos-HD60-Trial.exe` SHA-256
`4ed7bb070dad1c135cdf26b53f5f179fdddd87b11115d0a5150a7b94b939d2a7`
with `Chaos-HD60-engine.exe` SHA-256
`b05d382387ef1727c8df33c77b03fbd6b934c9d09e5c889cff99b5d4afd6545e`.
The combined runtime DLL is SHA-256
`ba24cab91e716495f88780625d0eed4344009de2baca81d9497da3ac05130f0f`.

The official 640→800 logic uses separate dimensions for a screen's DirectDraw
backing and its resource-directory name. The HD builder now adds `(320,240)`
to the backing size for BattleEnd, RealmViewer and Portmanteau; BattleEnd and
Portmanteau interactive bounds grow by the same offset. Resource strings still
request `800x600`, where reversible UI fit already provides 1120×840 art.
The realm-region click mask is allocated as 800×600 and indexed with an 800
stride; preserving its coordinate system prevents out-of-bounds reads. Realm
flags likewise use the original map coordinates, which remain aligned with the
landmarks in the fitted asset.

The Python private-background `test4` flow captured a complete 1120×840
victory screen, clicked its OK button at `(560,807)`, then captured the complete
realm map and portmanteau. The game did not take foreground input and the save
hash did not change. `test2` and `test3` regressions passed with unchanged saves.
`verify_hd60_runtime.py` passed 11 runtime hooks, 1120×840 surface, and the
retained `MaxFramesPerSec=30`. The preceding launcher and engine are saved under
`modernization/backups/hd60-pre-end-screens/`; the hash-gated rollback command is
`python modernization/tools/rollback_hd60_end_screens.py`.

## test5 layout correction, 2026-09-27

The user's three screenshots rejected the previous end-screen result. Background
expansion alone did not fix the realm toolbar, Portmanteau tables or talisman clip.
Playable launcher SHA-256: `1ebb20d0f53f5e73532c02edfd68d81f4b3f7cf06c99081e90b3d6548807c4bf`.
Engine SHA-256: `be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7`.
The combined DLL remains byte-identical to the preceding end-screen build.

- `0x54fdc0` anchors the realm toolbar to the right (+320). Map mask, flags and
  coordinates are unchanged.
- Portmanteau 800-mode rectangle tables: `0x5f09f0` (21 carried spells),
  `0x5f0c90` (25 available spells), `0x5f0fb0`/`0x5f0fd0`/`0x5f0ff0`/`0x5f1010`
  (navigation), `0x5f1030` (three categories). Scale those records by 7/5;
  following independent 640-mode records remain unchanged.
- Talisman draw `0x4dd6c0` sets a separate clip via `0x57dc60`. Expand
  `0x4dd6fe`/`0x4dd710` to 1120x840. Character spritebar Y gains 14 pixels
  after layout scaling to centre retained native sprites with scaled text rows.
  `hd_ui_fit.fit_cfg` reapplies the adjustment on future selector cycles.

`test5-final.json` captures realm, Portmanteau, tutorial dismissal and character
through relocated buttons. `verify_test5_ui.py` checks the three icons: colour
populations 743/696/720 pixels with at least 37 visible rows, all complete and
aligned. Save hashes are unchanged and wrapper/config files restored.
`test5-runtime.json` verifies all 11 hooks, 1120x840, new clip constants and
MaxFramesPerSec=30. `test5-battle-regression.json` passes roof toggle and four-edge
scrolling, with saves unchanged. Other HD compatibility gates remain open.

Backups: `modernization/backups/hd60-pre-test5-layout/manifest.json`.
Rollback: `python modernization/tools/rollback_hd60_test5.py` (`--check` passed).
The main installed entry is unchanged.
