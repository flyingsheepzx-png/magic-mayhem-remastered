# HD build log

## 2026-09-28: asset verification and mixed UI v2

The local Qwen Image 2.1 Manager queue currently has 382 completed UI,
37 bitmap, 88 portrait and 5 sprite-container records. The output verifier
checked all 512 completed records, including 311 generated sprite frames,
against their recorded hashes with zero failures. The five SPR containers are
PNG frame outputs only; encoding and game integration remain open. There are
165 pending sprite containers, 7 blocked-format records and 136 blocked
sequence decodes. Bitmap and portrait results also remain uninstalled.
`modernization/playtests/mixed-ui-v2/` provides an isolated runtime for visual
correction, with native independent pages and a 2× battle. Its extended
Save Game/movement verification is documented in `docs/native-ui-1920.md`.

## 2026-09-28: native-resolution UI requirement and probe

The user requires the game itself to render UI at 1920×1440, matching the
prepared full-screen Qwen output. The earlier wide169 art preview reduced it
to 960×720 and is not the target. The existing Qwen queue dimensions are
already correct, so no all-asset regeneration is needed for this requirement.
The resumed UI generation run finished **62/62** items with zero recorded
failures. `hd_verify.py --category ui-800x600 --category ui-untiered` verified
all **382/382** completed UI rasters, hashes, dimensions and key/alpha checks
with zero failures. This validates prepared files, not in-game integration.

`tools/native_ui_2k_probe.py` made a separate copy of the latest hash-verified
wide169 v7 package and produced an actual 2560×1440 game surface with the
1920×1440 Qwen main-menu and load-game images centered at 1:1. Private
background captures, scaled menu hit rectangles and a Load Game transition
passed. The wrapper client measured 2048×1152 on this desktop; do not call the
output gate complete. Text still uses old font pixels. The direct-engine probe
does not include the replay/QoL modules or adapt other screens. Full evidence,
screen files, build hashes and next steps are in `docs/native-ui-1920.md`.

## 2026-09-28: wide169 Qwen art preview and live comparison

- Resumed the remaining 62 pending UI records from the hash-verified
  `source-original` tree in one background `hd_pipeline.py run` process. Output:
  `assets/hd/ui-resume-20260928.out.log`. Manager job
  `22c65f9389e54b3eb0031902a6694ae7` was queued behind other users' GPU
  work for about 17 minutes, then dispatched and completed the first resumed
  item, `Greek_Region_04.JPG`. Its 1920×1440 PNG, source/output hashes and
  Manager ID matched queue and manifest. The next job dispatched immediately;
  do not start another queue writer. The 320 previously completed UI records
  passed `hd_verify.py` with zero failures; 321 are now done and 61 remain.
- The current installed wide169 directory fails its package checker because 11
  non-mutable `CFG/*.cfg` files listed in the immutable v7 package are absent.
  The latest launcher, engine and runtime DLL hashes still match
  `current-baseline.json`. The preview therefore uses a fresh copy of the
  hash-verified v7 package under ignored
  `assets/hd/preview-wide169-v7-qwen/`. It does not change the installed game.
- Replaced two assets in that preview: `Load Game 800-600.JPG` and Grimoire
  `Backdrop.JPG`. Their original package hashes and Qwen PNG manifests were
  verified before conversion. Qwen 1920×1440 PNG content is resized to the
  current 960×720 content region, placed inside the 1280×720 letterboxed image,
  and saved as a diagnostic JPEG at the engine's original path. The preview's
  exact replacement hashes are in `assets/hd/wide169-art-trial.json`. Run
  `python modernization/tools/hd_wide169_art_trial.py --restore` to restore
  those two preview images from the v7 package. The v7 package itself is intact.
- Private background captures verified that both images load in the game,
  menu/Grimoire interaction still works, side bars stay black, 11 runtime hooks
  remain active, the native surface is 1280×720 and the 30 setting is retained.
  The `test2` save loaded with the expected unit position and widened battle
  image. The wrapper client in this diagnostic session was 2048×1152; this does
  not close the exact 2560×1440 output gate.
- Comparison against the same untouched v7 package: Load Game mean absolute
  RGB change 5.61/255 with 69.19% of content pixels changing by more than 6;
  Grimoire 2.523/255 and 37.05%. Measured edge-image means rose 17.445→32.105
  and 12.352→19.174 respectively. The latter indicates more detail, but the
  side-by-side image `assets/hd/wide169-before-after.png` shows only a modest
  overall visual change at the current 960×720 presentation size. A first
  Grimoire capture was taken during a transition and showed no difference;
  explicit waits fixed the capture gate. Do not infer that zero difference
  means an asset is unused until the screen has settled.
- A CPU-only post-downscale sharpening check at 50% and 100% unsharp strength
  (`assets/hd/sharpen-review.png`) made the parchment grain slightly crisper
  but did not materially change readability or the overall result. Keep the
  current candidate; do not add a blanket sharpen pass to all 382 UI images.
- The opt-in preview launcher is
  `assets/hd/preview-wide169-v7-qwen/game/Chaos-Wide169-Trial.exe`. The
  comparison/rollback tool is `tools/hd_wide169_art_trial.py`. Further UI
  replacements should prioritize assets that retain visible detail at native
  presentation size, or wait for a genuine higher-resolution UI surface.

## 2026-09-28: resumed Qwen UI work

The original 820-record queue pointed at the project root after workspace
reorganization, while source assets now live under `game/` and some UI files
have already been fitted. Reconstructed `modernization/assets/hd/source-original`
from 560 unchanged game files, 258 checked UI backups and two immutable baseline
files. Each staged byte stream matched the queue's recorded SHA-256; the queue
now points at that source tree. No game runtime asset was changed for staging.

The first resumed item, `Medieval_Silhouette_13.pcx`, completed through Manager
Qwen job `56d7cebc5f4e47d9bf3d22fe04e8af4e`. It spent most of 1505 seconds
queued because Manager had paused GPU dispatch for two older recovery-required
jobs. The Manager's `/api/admin/reconcile` checked backends and resolved those
jobs, then dispatched this exact queued job without replay. Queue done count is
305. A five-item continuation has started, with the first Manager job
`a8fe27bfd4f747b4b2f5601f6b8e232c`. Verify each output and inspect an
integration sample before enlarging the batch. The pipeline now prints job IDs
and 30-second status, and reconciles/cancels its own job on timeout.

Use [HD_PLAN.md](HD_PLAN.md) for the method and execution commands, and
[HD_ASSET_LIST.md](HD_ASSET_LIST.md) for the generated asset table. This file records
actual build progress and checks across sessions.

## 2026-09-27: review and preflight

- Regenerated `modernization/assets/hd/hd-queue.json` and the empty pack skeleton.
  Queue: 820 records; 382 UI, 125 other bitmaps/portraits and 170 SPR containers are
  pending; 143 containers are blocked. There are no generated files in `pack/`.
- The Manager health endpoint reports `qwen21.ok=true` and `assets_ready=true`.
  Python 3.14 and Pillow 12.3 are available; D: had about 437 GB free.
- Corrected the main plan's stale 2560×1440 claim. The selected UI target is
  1920×1440, 4:3. This does not provide the project's separate 16:9 viewport goal.
- The staging tree cannot be copied over the game as an installable pack: raster
  extensions change to PNG, and SPRs become frame directories. Engine loading,
  coordinate transforms, backups and rollback must be proven before installation.
- The first GPU step is the four-asset UI pilot in `HD_PLAN.md`. It has **not** run.
  Check output dimensions, SHA-256 manifests, keyed pixels, text, layout and visual
  quality before the remaining UI batch. Terrain and animation remain deferred.
- The runner now atomically saves status after each asset, verifies selected source
  hashes and completed conventional-image output and manifest hashes before skipping,
  and exits nonzero if any asset fails. A synthetic missing-output test returned exit 1.
  Completed SPR frame sets still need an integrity check before their later phases.

At that preflight checkpoint no generated image had been loaded by the game.

## 2026-09-27: 2K UI smoke test and UI batch

- Generated the four pilot assets from `HD_PLAN.md` through the local Manager's
  Qwen-Image 2.1 engine. All four jobs completed with no error: Grimoire backdrop,
  main-menu background, Grimoire stat bar and Celtic realm silhouette.
- Verified PNG format, target dimensions, source/output SHA-256 against queue and
  manifest, and Manager job IDs for all four. Both keyed images have maximum pixel
  difference **0** in the nearest-neighbour restored key and two-pixel rim.
- The review sheet reports edge-energy gain 7.30× for the two 800×600-tier images
  and 2.15× for the two untiered images. These measure detail, not fidelity.
  A direct inspection of the main menu and review sheets found no obvious changed
  Chinese title, layout shift or key contamination. This is an asset smoke pass,
  not an in-game rendering pass.
- Added `tools/hd_verify.py` for repeatable batch checks of source/output hashes,
  dimensions, PNG format, alpha coverage and keyed pixels. It passed the first six
  completed UI images with zero failures while the batch continued.
- Started the remaining 378 UI jobs in a hidden background process, PID 43932,
  writing `hd/ui-run.out.log` and `hd/ui-run.err.log`. The queue is saved after
  every asset; use `python modernization/tools/hd_pipeline.py status` to inspect
  progress. Do not start a second batch against the same queue while it runs.
- Hash-gated static inspection of `Chaos.exe` found hardcoded `.JPG`, `.BMP` and
  `.PCX` resource path templates, including main-menu and Grimoire assets.
  `CFG/prefs.cfg`/interface CFGs expose only 640×480 and 800×600 layouts. The
  generated PNGs are therefore still staging assets; game integration requires a
  verified loader path and native UI/input coordinate work.
- The user approved three resolution tiers: 640×480, 800×600 and 1920×1440.
  `tools/hd_layout_tier.py` generated 23 staged CFG files with 367 `Rect3`
  rectangles and 38 `1920x1440_*` coordinates. Source and output hashes passed.
  This is data preparation only: the Boolean `IsHighRes` setting and existing
  executable do not yet read a third tier.
- Another active chat is changing pathfinding/frame timing in this shared checkout.
  HD work is confined to `modernization/assets/hd/`, HD-specific documents and
  tools. The other chat was notified. This work does not touch installed game
  files, preferences, wrapper, executable, saves or runtime patches.

## 2026-09-27: isolated game integration trial

- Created a full playable game copy in the managed `codex/hd-ui-lab` worktree.
  `docs/hd-integration.md` contains the baseline hashes, test evidence and
  rollback procedure. The original installation remains the other chat's
  pathfinding/frame-timing workspace.
- A generated 1920×1440 main-menu image loaded through a temporary JPG at the
  original path but cropped to the top-left of the 800×600 surface. Native 2K
  UI therefore **failed** its first game-load test.
- Exact PNG bytes at the original `.JPG` path produced a Chinese file-read
  error dialog naming that file; the original JPG was restored. The engine
  needs an explicit PNG loading path.
- The same generated image downsampled to 800×600 aligned with the Chinese
  menu. The generated settings background also displayed correctly in the
  options page. Both were restored to their original verified hashes afterward.
- A diagnostic wrapper presented a 1920×1440 client while the captured game
  surface remained 800×600. This is a working compatibility presentation tier,
  not native 2K rendering.
- Added a Python private-input trial that clicks only the owned lab window in
  the background, captures the primary surface and restores the DLL/INI. A
  client click at `(400,480)` reached settings; captured frames differed by
  mean absolute RGB 14.955. It stops before input if startup leaves the game
  foreground. No computer-use interaction is needed for this trial.
- `tools/hd_resolution.py` now selects 640, 800 or 2K presentation modes in
  the lab with checked rollback. The old in-game settings UI still exposes two
  radio buttons; third-tier engine support remains open.
- `tools/hd_compat_pack.py` staged only unkeyed JPG conversions for content
  checks. The first 78 completed UI outputs yielded 9 compatible JPGs; 65
  keyed JPGs, 4 BMPs and 1 PCX were skipped to preserve colour-key semantics.
- Left a reversible compatibility demonstration installed in the isolated lab:
  converted generated main-menu/settings JPGs plus 1920×1440 wrapper output.
  The final bounded background test reached settings with the 2K client, then
  restored its diagnostic wrapper. `docs/hd-integration.md` lists exact rollback
  commands. The original game files were hash-checked afterward and unchanged.

## 2026-09-27: expanded battle HUD implementation in isolated lab

- After the user accepted the 1120×840 test2 view, traced the original
  640×480→800×600 fixed battle HUD offset `(160,120)` in the verified community
  EXE. The isolated HD sibling applies the same lower-right anchoring rule with
  another `(320,240)` for the wizard portrait, spell toolbar and control-limit
  counter. The builder checks exact x86 instructions and does not overwrite
  `Chaos.exe`.
- The final isolated sibling is `Chaos-hd-hud-lab-v2.exe`, SHA-256
  `71e58150ecc98b3b6ef9b2fe7e29bce6c15dc22161e6dc19841cd27bd71325dd`.
  A 1920×1440 wrapper client displayed a 1120×840 native battle surface.
  `hd_hud_verify.py` found 100% matching gold pixels in all three relocated
  controls after translation and zero gold pixels in their old positions.
  Private click on the relocated portrait selected the player; a click in the
  new map band moved unit 0 from `(66,48,6)` to `(76,46,3)` without activating
  the game window or changing saves.
- `hd_resolution.py` and `hd_launch.py` now offer an opt-in three-tier isolated
  launch: 640, 800, and 2K presentation with a 1120×840 battle viewport. The
  original game's runtime files and the active pathfinding session remain
  untouched. Legacy menus/settings are still 800×600 within the expanded
  surface; native 2K UI assets and all-screen testing remain later work.

## 2026-09-27: isolated HD follow-up v4

- Built `Chaos-hd-hud-lab-v4.exe` from hash-verified community EXE; SHA-256
  `baf839075c7df3c95af7071d3266d84499a4bdeb224c31cbdf6017218b1de922`.
  Added roof anchor, exact scroll edges, cursor backing/restore bounds, window
  input geometry and main-menu backing surface. The earlier map-object claim
  about the house icon was incorrect; it is the roof visibility button.
- Trial `background-trials/1790467844974042900`: roof state `1→2→1`, all four
  outer scroll edges changed camera position with expected direction cursors,
  stable cursor restore rectangles in added bands, 1920×1440 client and
  1120×840 captures, selected player moved into the right added terrain band.
  Diagnostic files restored and no saves changed.
- The generated main-menu JPG and seven `Rect2` rectangles now fit 1120×840
  in the isolated 2K tier. Menu-to-test2 click passed; screenshot outer bands
  contain menu art. Verified 800→2K→640→2K tier transitions and dry-run launch.
  Settings/other menus and normal foreground pointer mapping remain open.

## 2026-09-27: all-screen fit, Qwen samples and source-derived key templates

- Generalized the reversible fit from the main menu to 270 UI files: 23 CFGs,
  57 full-screen JPEGs and 190 Grimoire page JPEGs. A completed 800→2K cycle
  verified every current and backup hash.
- Synchronized and verified 304 completed Qwen UI records from the interrupted
  producer batch without restarting it. Enabled the main menu, battle options
  and load-game backgrounds as reversible samples; the seven-screen menu flow
  passed on a 1120×840 surface.
- Replaced output-based blue cleanup with a fixed source-derived Grimoire colour
  key template. The original 400×600 page alone determines art, blue and magenta
  positions; nearest-neighbour template scaling and exact colour painting happen
  after Qwen generation and resizing. Six deliberately different-content checks
  produced identical key pixels, and all 190 completed pages now have template,
  source, Qwen and derivative hashes.
- Built `Chaos-hd-ui-lab-v13.exe` from community SHA-256 `b1eccc46...`; output
  SHA-256 `d0e3f37b...`. It contains 148 hash-gated changes and selects lossless
  BMP Grimoire pages before JPEG fallback. The final Grimoire, menu-flow and
  test2 regression reports are named `grimoire-v13-qwen-template.out.json`,
  `menu-flow-qwen-v13.out.json` and `battle-regression-v13.out.json`.
- Do not install v13 over the accepted 30/60 entry. The next owner must compose
  a separate candidate and make replay surfaces/pitch/clipping dimension-aware.

## 2026-09-27: combined HD60 UI defect follow-up

- Updated the user-selected combined entry in the playable lab. Final SHA-256:
  launcher `9ab567e1f720a440a6d1d52bdddbed85cfe5363917ff35ccf3a7791849c28a66`,
  engine `b7414bb05f67bc80857f31cfce5ce07ccd755594f774f1878cfa93938c070744`,
  runtime DLL `1ec698a03854a1bb95f88a764b8dc411dd83f363d136dff1e9abc4d580acb181`.
- Added hash-gated engine edits for the two right-aligned enemy-warning columns,
  1120×840 tooltip bounds, full-surface speech/cutscene continuation input, four
  loading-bar anchors, and the loading renderer's 837×50 geometry.
- Enlarged the ESC bitmap to 840×560 and all eight progress images to 840×50.
  BMP scanning also brought three realm-view maps and the spellbox portmanteau
  into the reversible 1120×840 fit; `ui-fit.json` now has 283 records.
- Private-background `test2` passed roof, cursor, four-edge scroll and added-band
  movement checks. Private-background `test3` passed exact enemy rectangles,
  right-bottom tooltip pixels and centred ESC-menu pixels. Both save hashes were
  unchanged. The test now explicitly selects `test3` row 1 or `test2` row 2.
- Startup verification passed all 11 hooks, a 1120×840 live surface, the loading
  and cutscene patch immediates, all progress/ESC resource sizes, and the retained
  `MaxFramesPerSec=30` preference.
- Loading cannot be screenshot through the private wrapper while its main thread
  is blocked, so its current gate is static byte and resource-dimension evidence.
  Cutscene input is also byte-verified pending a stable story fixture.
- Previous combined binaries and a checked rollback manifest are under
  `modernization/backups/hd60-pre-ui-fix/`; run
  `python modernization/tools/rollback_hd60_ui_fix.py` with the game closed.

## 2026-09-27: victory, realm map and portmanteau follow-up

- Reproduced the three 800×600 clipping defects with the new `test4` save. Its
  SHA-256 is `9cbd2bd5fdf2ceba6015e21d98db48241570962a6c5baf40bb7ff25af232b09a`.
- Enlarged the victory/defeat and portmanteau backing surfaces and interaction
  bounds, plus the realm map initial and refreshed backing surfaces. The 12
  patch sites are instruction-checked in `hd_hud_build.py`. Resource lookup
  dimensions remain 800×600 because the existing fitted assets live there.
  The realm click mask also remains 800×600; its source coordinates and stride
  must not be enlarged without rebuilding the mask.
- The current playable launcher is SHA-256 `4ed7bb070dad1c135cdf26b53f5f179fdddd87b11115d0a5150a7b94b939d2a7`;
  its engine is `b05d382387ef1727c8df33c77b03fbd6b934c9d09e5c889cff99b5d4afd6545e`.
  The rebuilt runtime DLL is `ba24cab91e716495f88780625d0eed4344009de2baca81d9497da3ac05130f0f`.
- Python private-background `test4` reached victory, clicked its relocated OK
  control, opened the full-size realm map and then the full-size portmanteau.
  Captures were 1120×840, wrapper client 1920×1440, and the save was unchanged.
  `test2` battle movement/edge scroll and `test3` UI flow also passed unchanged
  saves. Runtime startup passed 11/11 hooks, 1120×840 surface and retained
  `MaxFramesPerSec=30`.
- Hash-gated rollback for the two changed root binaries is
  `python modernization/tools/rollback_hd60_end_screens.py`; the checked backup
  and manifest are under `modernization/backups/hd60-pre-end-screens/`.

## 2026-09-28 mixed-resolution clarification and Save Game integration

The UI target remains 1920×1440 native art. Battle retains 1280×720 native
geometry, presented 2× at 2560×1440; the older full-native-2560 battle probe
is historical and superseded. `native-ui-2k-probe/` now includes an eighth
full-size UI screen, Save Game, in the isolated direct-engine runtime. Its
native capture is `save-game-native-2560x1440.png`; the central Qwen art matched
98.60% within RGB difference 8. An owned run created a 340,696-byte diagnostic
save through the enlarged edit box and Save button, then restored all protected
files and removed the new save. `battle-size-compare-5120x1440.png` shows the
preferred battle size on the left and the superseded exploration on the right,
both at 2560×1440 per side. Mixed-mode switching remains unimplemented.
An additional reversible scene-rectangle experiment kept the primary surface
at 2560×1440, restored battle drawing to 1280×720, and matched the prior
playable test2 crop at 99.04% within RGB difference 8. The full-size Save Game
page still loaded; the patch was hash-rolled back after capture. See
`docs/native-ui-1920.md` for the diagnostic runs and remaining compositor work.

## 2026-09-29: first in-game Qwen value decisions

The installed `Chaos-Wide169-Trial.exe` was hash checked and captured first. The
isolated mixed UI v4 was then captured on the same page and actions with its
Qwen asset and a source-derived Lanczos enlargement at identical 1920×1440
content size. Every comparison is a full 2560×1440 game-surface capture, not a
desktop or 720p thumbnail. All six capture sessions restored their mutable
files and reported no unexpected saves; the v4 manifest still matches 251/251.

| Asset | Evidence | Decision | In-game observation |
| --- | --- | --- | --- |
| Main menu background | `hd/qwen-value-audits/1790672823538568100/` | **accept this asset** | Carved title, logo and page edges gain useful clarity; live Chinese button labels and positions are intact. Paper texture is visibly grainier, so this is not a blanket approval for UI backgrounds. |
| Grimoire backdrop | `hd/qwen-value-audits/1790673125968504000/` | **accept this asset** | Page and spine texture are clearer. The plain enlargement exhibits a large rectangular edge seam and a different upper right tab appearance. Live list text remains legible. The known baseline feedback control defect is excluded from fidelity scoring. |

The menu and Grimoire results are asset-specific. They justify keeping these
two Qwen outputs in v4 but do not justify restarting the 160 pending SPR
containers. Next value samples should cover a portrait or icon in a reachable
page and a small terrain/animation pilot in battle; assess identity, keying and
temporal consistency before choosing `accept`, `refine and rerun`, `plain
enlargement wins` or `defer` for those categories. Do not launch the full
pending batch on edge-energy gain alone.

The first two Portmanteau icon A/B runs are **invalidated**: they replaced
`port-icons.spr` and `mitems.spr`, neither of which draws the pictured head,
book and green creature. Read-only live control and frame-header inspection
identified `Sprites/Buttons.spr` frames 0, 3 and 9 as the actual source. A
proposed hook change based on the first mistaken attribution was reverted
before any binary rebuild; v4 was never modified by it.

The valid same-fixture `Buttons.spr` audit is
`hd/qwen-value-audits/1790676679178214200/`. Qwen versus source-derived
Lanczos differs only within the three icon footprints (output difference box
`1818,52–2163,148`). **Plain enlargement wins for these visible frames**:
at game size Qwen gives no useful identity or readability improvement, while
the face and book look slightly darker. All three game sessions restored
protected files, used the same `test5.sav` hash, and the v4 manifest remains
251/251. This is not a verdict on the other 18 `Buttons.spr` frames or on
terrain/animation containers. Do not spend a full Qwen batch on similar small
buttons without a better pilot that shows visible in-game benefit.

The accepted choice is staged in the isolated v4 only: `Sprites/Buttons.spr`
frames 0, 3 and 9 now use the reviewed plain enlargement; its other 18 frame
payloads are byte-identical to the previous Qwen container. The new file hash
is `dd94d69c...`; rollback bytes and manifest are in
`playtests/mixed-ui-v4/before-plain-port-buttons-20260929/`. Baseline-first
Portmanteau retest `1790677064806244500/` opened the same `test5` page and
hovered two talismans. Relative to the preceding Qwen run, all three page
captures differ only at `(1818,52)–(2163,148)`. Baseline-first core retest
`1790677264772377000/` reached menu, options, load, battle, Esc, save and
battle return with the same `test2` save in both runtimes; battle and battle
return are pixel-identical to the earlier v4 core reference. Both runs report
restoration and the current v4 manifest matches 251/251. The missing `test2`
diagnostic fixture was temporarily staged from a hash-verified backup and
removed after the run.

## 2026-09-29: terrain and animation Qwen pilots

To decide whether the remaining SPR queue merits GPU time, a bounded local
Qwen Image 2.1 run processed the first sheet of
`Realms/Celtic/Forest/Terrain.spr` (49 of 1712 usable frames, `partial`, job
`abcdae771c414030a8d35454ba592aa0`) and the 144-frame
`Creatures/16Mb Anims/CelticWizard.spr` sheet pilot (six jobs, `done`). All
193 output PNG hashes match their manifests. Queue status after the pilots:
518 done, 158 pending, one partial, 136 blocked-sequence-decode and seven
blocked-format.

The corrected full-size offline comparison sheets are
`hd/pack/Realms/Celtic/Forest/Terrain.spr/pilot-plain-qwen-contact-924x1456.png`
and
`hd/pack/Creatures/16Mb Anims/CelticWizard.spr/pilot-plain-qwen-aligned-1240x1480.png`.
The animation sheet must be cropped using its recorded aligned frame offsets;
the initial unaligned contact sheet made the Qwen figures look too small and
is invalid evidence. With alignment corrected, Qwen preserves poses and
silhouettes but gives only modest added texture. Across the first 48 animation
frames, median edge-energy ratio is 1.095 and adjacent-frame luma change is
11.63 versus 11.75 for plain enlargement. Neither metric proves an in-game
benefit. Terrain contours are somewhat harder, but visual gain is inconsistent
across the sampled tiles.

**Decision: defer mass terrain and animation generation.** The current battle
policy retains a 1280×720 native scene/HUD and presents it at 2×. These 2×
sprite PNGs cannot simply replace the original battle SPRs without doubling
their world size. A controlled battle renderer path that draws 2× art in the
same logical footprint, plus same-scene Qwen/plain captures, is required
before choosing `accept` or `refine and rerun` for these categories. The
pilots remain prepared assets only; no battle runtime was modified.

Follow-up render-path mapping: isolated v4's `mm_mixed_present` reads the
1280×720 battle area of a 2560×1440 RGB565 primary and writes every source
pixel as a 2×2 block into a separate output buffer. The primary is untouched.
The existing `0x5002a0` scene queue uses 36-byte entries with frame pointer
and native screen coordinates; this is a plausible controlled source for a
post-scale 2× sprite overlay, but no live frame identity or draw-order mapping
has been proven for test2. The screenshot's wizard visually matches
`Wizard1`, not the earlier `CelticWizard` pilot, so `Wizard1.spr` was prepared
as a 120-frame local Qwen pilot (four jobs, all output hashes verified).
Evidence and the next dynamic gate are in
`hd/qwen-value-audits/battle-render-path-20260929/mapping.json`.
No runtime overlay or battle asset replacement was installed. The queue is
now 519 done, 157 pending, one partial, 136 blocked-sequence-decode and seven
blocked-format.

## 2026-09-29: reversible battle presentation sharpen trial

The user asked to test a filter before continuing the expensive battle sprite
replacement. A RGB565 five-tap unsharp pass was added to the v4 mixed wrapper's
**presentation buffer only**. The native battle still renders at 1280×720 and
is copied 2× to 2560×1440; independent UI pages remain native 1920×1440.
`MM_PROBE_BATTLE_SHARPEN=1` selects the light pass, `=2` the stronger pass,
and an unset value or `=0` selects the original nearest-neighbour output.
The source primary is untouched and the temporary filter buffer is reused.

A current hash-verified `Chaos-Wide169-Trial.exe` baseline-first core run and
same-save v4 run completed at
`hd/baseline-comparisons/1790680533605652400/comparison.json`; restoration
passed. A separate isolated 0/1/2 capture used the same verified `test2.sav`
at `hd/battle-sharpen-trial/1790680614857107200/trial.json`. The three
2560×1440 battle frames and full-size `wizard`, `terrain`, and `hud` comparison
PNGs are there. Menu frames are pixel-identical across all three levels.
Against level 0, level 1 changes 62.51% of battle output pixels but only
0.06% by over 24 RGB levels; level 2 changes 76.92% and 0.48%, respectively.
The light pass modestly defines wizard/HUD contours. Level 2 makes grass
grain and pixel boundaries too harsh and adds no sprite detail. This is a
presentation experiment, not native sprite resolution improvement or a
replacement for the open scene/HUD issues.

The light option is available through
`playtests/mixed-ui-v4/Start-Battle-Sharpen-Light.ps1`; ordinary playtest
launches use the unfiltered output. The wrapper hash is now
`2f1c5881ed9e59fa82772ac14a60f6e79b7f44e6c80c2c0d7f797bc95a90a241`;
the previous DLL and manifest are in
`playtests/mixed-ui-v4/before-battle-sharpen-20260929/`. Full package hash
validation passed 251/251. The temporary `test2` copies were removed.

Follow-up: a repeated 10-second owned-process test measured D3D9 upload counts
and engine CPU time in the same `test2` battle. The initial level-1 pass
produced 29.7 and 29.4 uploads/s with 15.83 and 15.88 CPU s per 10 wall s;
level 0 produced 30.0 and 25.9 uploads/s with 12.02 and 10.38 CPU s. The
unfiltered second sample fluctuated, so those readings establish extra CPU
cost but not a robust frame-rate delta. Level 2 reached 27.0 uploads/s in its
single sample. Raw results: `hd/battle-sharpen-trial/1790681373689530900/performance.json`.

An optimized implementation computes the same five-tap output directly from
each 1280×720 source block while writing its four 2× presentation pixels.
It avoids the separate 2560×1440 copy and pass. Level 0/1/2 menu and Esc
captures, plus a static battle terrain region, were pixel-identical to the
initial implementation (all differences zero); evidence:
`hd/battle-sharpen-trial/1790681618003374200/trial.json`. Repeated optimized
10-second samples gave level 0 30.0/30.0 uploads/s at 12.14/12.11 CPU s,
level 1 29.7/29.6 at 15.66/15.66 CPU s, and level 2 29.6 at 15.94 CPU s:
`hd/battle-sharpen-trial/1790681707708946400/performance.json`. This is
still a material CPU cost for a modest visual improvement; keep the filter
opt-in. The isolated wrapper now hashes to
`015a369ee8b8654434b3e745e61befe63346db521f4bb6acc5b3aca1e9e7796d`.
The preceding wrapper and manifest are backed up under
`playtests/mixed-ui-v4/before-battle-sharpen-optimized-20260929/`; package
verification again passed 251/251 and temporary saves were removed. The
strong level remains diagnostic only.

A compact RGB565 channel lookup-table variant was also trialled, then
rejected. The available level-0/1 menu, Esc, and static battle-terrain captures
were pixel-identical to the shipped block implementation. A third launch
failed to produce an owned engine; cleanup restored the original wrapper and
temporary save, so no level-2 claim is made from that attempt. Two 10-second
light samples used 15.27/15.36 engine CPU seconds and 29.6/29.0 D3D9 uploads
per second, versus the shipped implementation's 15.66/15.66 CPU seconds and
29.7/29.6 uploads per second. The small CPU reduction did not yield a stable
presentation improvement. Evidence:
`hd/battle-sharpen-trial/1790682097412926700/performance.json`. The LUT
source was reverted; the isolated playtest DLL remains the verified
`015a369e...` build and its manifest still validates 251/251.
For one-click Windows access, `playtests/mixed-ui-v4/Start-Battle-Sharpen-Light.cmd`
invokes the hash-checking PowerShell launcher. A launch-call dry run verified
the isolated executable, working directory, inherited filter flags, and
restoration of the parent shell environment. A subsequent Windows shell
double-click-equivalent launch (`os.startfile`) successfully started the
expected isolated `game-wide169/Chaos-Wide169-engine.exe`; its full process
path was checked and it remained alive during the startup observation.
The owned test engine and preview launcher were closed afterwards. Package
verification remained 251/251 and no temporary test2 save remained. This
checks the runnable entry; the light-filter visual and performance evidence
comes from the earlier hash-verified background test2 captures. An initial
direct `cmd /c` diagnostic invocation failed to find an engine and is not the
validated launch method for this path containing an ampersand.

The ordinary wrapper screenshot hotkey previously called
`ss_take_screenshot(g_ddraw.primary)`, bypassing the 2× battle presentation
buffer. The isolated wrapper now uses `mm_mixed_present(g_ddraw.primary)`
under the same wrapper/surface locks as the private capture path. With a
temporary background-only trigger into the real keyboard hook, native-menu
and battle-Esc hotkey captures were pixel-identical to the private
presentation captures at 2560×1440. Evidence:
`hd/battle-sharpen-trial/1790683311961478000/`. A plain posted key-up did not
invoke the Windows keyboard hook, so physical Print Screen activation was not
verified by that test. The diagnostic trigger was removed before packaging.
The isolated wrapper is now
`93b45aa6d8d776a7c02f8c5489d3ff807320d4c690a3b302bc03602a4fbfb2ff`;
the prior DLL and manifest are in
`playtests/mixed-ui-v4/before-mixed-screenshot-20260929/`. Final package
verification passed 251/251; no game process or temporary test2 save remained.

## 2026-09-29: community filter review for battle output

The same verified test2 battle output was reconstructed as 1280×720 source
pixels and compared offline at exact 2× using nearest, bilinear, bicubic,
Lanczos, a simple Scale2x rule, and the live light sharpen capture. Full
resolution crops are
`hd/battle-sharpen-trial/1790680614857107200/{wizard,terrain,hud}-filter-options.png`.
Bilinear and bicubic smooth the wizard, but blur grass texture and the battle
HUD's letters. Lanczos keeps more contour contrast but still softens text.
The simple Scale2x rule retains hard edges and alters small HUD glyph shapes;
it does not consistently improve this textured game. These are still-image
comparisons, not runtime validation of a shader.

Community source inspected at `libretro/glsl-shaders` commit
`f8e23ff880668f0f0e837a05a316534d82a7f31b`:

- [`sharp-bilinear.glsl`](https://github.com/libretro/glsl-shaders/blob/f8e23ff880668f0f0e837a05a316534d82a7f31b/interpolation/shaders/sharp-bilinear.glsl)
  is public domain and primarily addresses non-integer scaling. At exact 2×,
  the current nearest copy already preserves the pixel grid.
- [`fsr-pass0.glsl` and `fsr-pass1.glsl`](https://github.com/libretro/glsl-shaders/tree/f8e23ff880668f0f0e837a05a316534d82a7f31b/fsr/shaders)
  describe MIT-licensed EASU/RCAS GPU passes. They have not been tested here;
  the current wrapper supplies an already enlarged 2560×1440 texture, so
  EASU cannot replace the CPU enlargement without render-path work.
- [`xbr-lv2.glsl`](https://github.com/libretro/glsl-shaders/blob/f8e23ff880668f0f0e837a05a316534d82a7f31b/xbr/shaders/xbr-lv2.glsl)
  includes an MIT-style permission notice. It is an edge-stylizing candidate,
  but its benefit for this game's textured terrain and animated sprites
  remains unproven. The related `xbrz-freescale.glsl` incorporates GPL-3.0
  material, so it should not be copied casually into the isolated package.

The pinned cnc-ddraw wrapper supports GLSL shaders with OpenGL and built-in
nearest/bilinear/bicubic/Lanczos with D3D9. The mixed compositor currently
copies the 1280×720 battle source into a 2560×1440 CPU buffer before D3D9
upload, while independent UI pages use native 1920×1440 rendering. Merely
changing `d3d9_filter` or `shader` cannot move this battle enlargement to the
GPU; that needs a separate 1280×720 battle texture and correct mode switching
for independent UI, screenshots, and input transforms. Given the offline
quality trade-offs and the existing CPU cost, retain light sharpen as an
opt-in comparison rather than promoting another filter now.

## 2026-09-29: isolated launch regression reported by user

The user reported that both suggested entries appeared frozen, then clarified
the tested save was mistaken and the concrete display fault was the battle
occupying only the upper-left 1280×720 while old page pixels remained outside
it. Read-only observation of the user-owned run showed a responsive HWND,
changing scene pixels and a running 2560×1440 engine. The direct EXE was
previously missing `MM_PROBE_MIXED_RENDER=1`; recommending it as the normal
unfiltered entry was incorrect.

A first attempted rebuild from `playtests/mixed-ui-v4/build-launcher.cmd`
used stale v2 resource DLLs and produced incorrect 64/44/30 battle font
heights. That binary was rolled back before delivery. The final rebuild used
the existing v4 `build/mixed-ui-v4-runtime/candidate.res` and exact current
engine hash, with the mixed-render and mixed-font flags set inside the
launcher. The direct EXE now hashes to
`0bb54b014be6c2852a346342b10d49778d94a2a9dbb4fdcf9a011dafc5a14ab1`;
the original EXE and manifest are in
`playtests/mixed-ui-v4/before-launcher-mixed-flags-20260929/`.

With *no mixed-render/font variables supplied by the test harness*, both
unfiltered and level-1 runs loaded the same verified test2 save. Full
2560×1440 battle screenshots had 98.0% and 94.6% lit pixels in a right-side
sample, respectively; menu fonts were 64/44/30 and battle/Esc fonts
32/22/15. Esc controls responded in both runs. Evidence:
`hd/launcher-mixed-fix/1790688125414896600/launcher-check.json` and its
game-surface PNGs. The package passed 251/251 hashes; diagnostic test2 was
removed and no owned game process remained. Both entrypoints now use the
same current v4 resources; light sharpening remains optional.
# 2026-09-29 mixed cursor and progress correction

- Corrected ordinary message-queue mouse coordinates in the isolated mixed
  wrapper. Native cursor screenshots at `(500,350)`, `(1700,350)`,
  `(1700,1050)` and `(2500,700)` show a visible cursor; all four automated
  crops contained 388 cyan cursor pixels. See
  `hd/cursor-progress-verification/1790692182272423000/verification.json`.
- Enlarged and relocated load/save progress drawing on the 2560×1440 native
  primary. Read-only consecutive frames are in `hd/loading-frames/`, including
  load `1790691536067492800` and save `1790691646985940300`.
- Staged only in `playtests/mixed-ui-v4`; rollback is
  `playtests/mixed-ui-v4/before-cursor-progress-20260929-221855/`.
  The package manifest verifies 259/259 files. The installed baseline was not
  modified. Full same-page baseline comparison remains pending because its
  startup FMV interrupted the later capture.
