# Native 1920×1440 UI integration

## 1.1 startup DLL initialization correction — 2026-09-30

User startup screenshot reports native engine error 0xc0000142. Root cause found
in production `png_assets.dll`: DllMain uses exact disk-engine SHA-256 allowlist
and refused merged P1 engine `42f2aac7...`, while old original/HD60/v38/v4 hashes
were accepted. Build-time hook-span/resource checks had not checked this imported
DLL's engine acceptance. Full Readable map pixels do not cause this initialization
failure.

Installed candidate-specific corrected PNG loader includes exactly the pinned
merged engine in its allowlist; previous supported hashes and unknown-host refusal
remain. Loader SHA-256 `48916f6c...`. Launcher was rebuilt only to synchronize
its PNG DLL integrity pin; resources101/102 stay byte-identical, native engine,
wrapper, Full Readable map and player data stay exact. Full candidate integrity
check passed (5,830 manifest files); installed v38/1.0 identities unchanged.

Offline verification: actual compiled SHA-256 matches P1 disk engine; old/new
production allowlist expressions compiled and confirm old rejection/new acceptance,
previous-version retention and mutated/unknown-hash rejection; corrected production
DLL LoadLibrary refuses an unknown test host; native BMP hook seven-byte signature
and image base verified; launcher embedded modules equal before/after. No game
was launched, so user startup/gameplay acceptance remains pending. Evidence in
`build/remastered-1.1-loader-fix/verification.json`.

Backup `backups/remastered-1.1-loader-fix/` retains loader, launcher and manifest.
`tools/install_11_loader_fix.py rollback` with game closed restores these exact
prior components while preserving later unrelated metadata/player state; it also
restores the known startup defect. Updated `tools/build_remastered_11.py` and
`runtime/hd11/png_assets.cpp` carry corrected dependency/pin recipe for future
candidate builds rather than relying only on the one-time binary installation.


## Full Readable Celtic map installed in 1.1 — 2026-09-30

User reviewed the Full Readable result, accepted its art direction and explicitly
requested trial installation. This supersedes the earlier conservative decision
against runtime adoption for this single selected variant; it does not establish
map overlay/interaction acceptance or accept every generated structural change.

`02-full-readable-target.png` (1920x1440, source SHA `e3ffa2c9...`) is now staged
at `playtests/remastered-1.1-p1/runtime/Interface/RealmViewer/800x600/Celtic_Map.PNG`.
Lossless PNG construction places exact source RGB pixels at (320,0) in a
2560x1440 canvas, with two black 320px sidebars; no sharpening, residual mix or
additional resize is applied to this normalized candidate. Installed hash
`1dd9b4d7...`; previous map `f2d1906a...`.

Only this runtime file changed; existing realm overlays, flags, masks and input
code retain their current behavior. Greek/Medieval maps have no Full Readable
trial yet and remain current assets. All 5,830 candidate runtime files passed
integrity verification; launcher/engine/modules and protected v38/1.0 identities
remain exact. No game was launched. Art/overlay/hit alignment acceptance pending
user testing of the Celtic realm.

Backup: `backups/remastered-1.1-fullreadable-celtic/` contains prior PNG, manifest
and installation evidence. After closing the game, restore only the old map with
`python modernization/tools/install_fullreadable_map_11.py rollback`.
The helper hash-gates both source and old target, verifies exact native content
pixels/sidebars and sole-file delta, and updates only the candidate asset manifest.
Player saves/configuration are preserved. User is to run the same isolated 1.1
entry; installation does not promote the candidate as the installed baseline.


## Remastered 1.1 P1 construction checkpoint — 2026-09-30

User authorized implementation, local Qwen experiments and subagents after review.
P1 is installed at `playtests/remastered-1.1-p1/`; no game was launched. Authoritative
entry `MagicMayhem-Remastered-1.1.exe`, separate `runtime/Save` and configuration.
All 5,830 runtime hashes and launcher identity match; protected installed v38/1.0
identities are unchanged. Backup `backups/remastered-1.1-p1/` records protected
identities and baseline/install manifests; immutable v38/v4 sources remain intact.
Rollback parks the complete candidate runtime including player data; original
1.0/development entries are available without restoring or overwriting their saves.

Implementation uses v38's hash-verified source recipes and preserves the optimized
command index, lifecycle reset, 600 search budget, group slots, cleared waits,
corrected occluded-body reveal and tutorial anchoring. HD adapters are compiled
with a common `runtime/hd11/layout_context.h` used by fonts, tooltip mode, replay
eligibility, presentation and inverse input. Latest pre-tooltip QoL badge layering,
empty-slot binding, refresh and double-key self cast were kept. Old v4's presentation
badge hook was intentionally excluded. Progress hook now verifies v38's existing
disk shim before replacing it; old raw-entry assumptions would have rejected v38.
The port icon variant selector uses page mode/frame identity and UI bounds rather
than a fixed triplet of coordinates. Other native-page constructors still use
verified legacy geometry; this is the common-mode foundation, not a completed
migration of all pages to declarative anchors.

Battle source caches retain 1280x720 pixels with the actual HD primary pitch, so
native UI output size does not force full 2560x1440 cached battle images or expand
the scene/HUD. Shared control classification uses the known battle controls and
rejects independent-page rectangles; fonts/tooltip cached surfaces switch together.
Four major independent-page background files have 2560x1440 canvases containing
1920x1440 artwork at (320,0), with verified black sidebars. This is an offline
asset/layout contract; actual fonts/clicks/page transitions require user acceptance.

Engine merge used pinned pre-FMV-centering wide169 ancestor `1d2df613...`, latest
v38 `43e12256...` and v4 `3eda4a37...`: zero conflicts, 665 old-HD changed bytes and
all 50 latest-only byte changes retained. Result engine SHA-256 `42f2aac7...`.
Interface/font/sprite derivatives were ported; old AI, encrypted gameplay configs,
FMVs and enhancement DLLs were excluded. Current v20 right-tab locations and v21
clasp correction supersede v4's old right-tab/clasp inputs: right coordinates are
scaled 2x, corrected 32x139 clasp frames become 64x278, other frame payloads stay
exact. PNG loader compatibility and BMP-free active runtime remain in force.

Validation ran the actual built modules offline: 284 behavior/ABI cases for
occlusion/lifecycle/budget/group/wait/tutorial, 14 shared mode/input cases, six
engine hook spans, exact launcher resource/DLL equality, and preserved terrain,
FMV, creature, speech, wizard, text and OGG asset identities. Evidence under
`build/remastered-1.1-p1/`: `offline-regressions.json`, `integration-verification.json`,
`asset-compatibility-verification.json`, `engine-merge.json`, `build-provenance.json`.
`tools/build_remastered_11.py` supplies build/install/verify/rollback;
`tools/verify_remastered_11.py` executes bounded offline regressions. Offline map
fixtures are recovered by pinned object hashes from the existing backup into the
build only. No automated/manual gameplay or visual acceptance was performed.

P1 user focus: menu, options, load/save, battle/Esc and return, Chinese/Latin font
sizes/wrapping, ordinary cursor and clicks; also confirm 1.0 movement/reveal behavior.
Grimoire, realm, inventory and other staged HD pages remain broader acceptance
work. Mixed FMV/loading and tutorials need user verification. Filter remains disabled.

Asset quality: static map review compares original, plain Lanczos and previous
Qwen at actual 1920x1440 size/crops under `assets/hd/quality-review-1.1/`. Celtic
and Greek outputs add granular/noisy texture without enough road, building or
landform clarity; they need refinement. Prior successful generation/hashes do
not constitute artwork acceptance. Authorized local-Qwen trials are separate
from runtime adoption, and preserve coastline/road/river topology and overlay
registration. The agent's trial outputs are under the `model-trials/` subdirectory.

Three actual local Qwen Image 2.1 jobs completed: two full-reference jobs
(1024x768 and 2400x1792 raw outputs), plus one contextual crop follow-up. Candidate02 resolves roofs/rock faces/conifer groups
better but changes building arrangement and road/river shapes, so full-map
replacement is rejected pending a structurally safe method. Candidate01 drifts
more strongly. Protected residual blending preserves excluded pixels exactly
but offers too little detail gain. The bounded contextual crop follow-up also completed: raw forest/rock detail
is clearer but structures drift; protected mixing preserves excluded pixels
exactly, changes only about 0.91% of full-map pixels and gives limited benefit.
All three new model outputs remain art studies, with none adopted; original
outputs and runtime are unchanged. Full call/settings and
1:1 crops are in `assets/hd/quality-review-1.1/model-trials/REPORT.md`.


## Remastered 1.1 review and proposed integration — 2026-09-30

Historical review status: subsequently approved and implemented as P1 above.
The review itself did not launch a game or modify a runtime.
This section supersedes historical baseline/queue counts for planning only.

### Verified current state

- Authoritative installed package: `build/wide169/package-v38-png-assets`.
  Installed-state manifest SHA-256 matches; all 5,823 package file hashes match.
  Installed nonmutable files match the package using the installer exclusions
  for saves, encrypted configuration, learning data, preferences, wrapper INI
  and QoL settings. Launcher SHA-256 is `3458afcd...`; engine is `43e12256...`.
- `playtests/mixed-ui-v4/manifest.json`: all 262 listed files match. This is
  a selective candidate manifest, not a complete inventory of its runtime.
  Its engine is `3eda4a37...`, and embedded modules remain derived from v11.
  The September 30 PNG migration is present; it does not imply integration of
  the later gameplay, tutorial, FMV and other v38 changes.
- Generated queue: 820 records; 519 done, 157 pending, 136 blocked on sequence
  decoding, 7 blocked on format, 1 partial. Done assets comprise 507 rasters
  (332 tiered UI, 50 untiered UI, 88 portraits, 37 bitmaps) and 12 SPR
  containers. All 507 output hashes and declared dimensions match; all 930
  frame-file hashes in the 12 done sprite manifests match. This proves stored
  output integrity, not appearance, integration, alpha correctness or motion.
  Notable assets: 190 Grimoire half-pages at 960x1440, 102 tiered and 41
  untiered full pages at 1920x1440, eight progress images at 1440x86.
- Current-baseline JSON names two development DLLs whose on-disk hashes no
  longer match that JSON (`runtime/wide169/wide169.dll`, `qol_bindings.dll`).
  Installed launcher resources 101/102 instead match the v38 manifest module
  hashes `9c7a0a25...` / `af65b4ba...`. Treat these loose build artifacts as
  untrusted rebuild inputs until provenance is reconciled; installed package
  integrity passed. Do not silently promote these artifacts or old engines.
- Historical README, known_open and paired-verification metadata lag later
  tooltip, icons, font spacing, realm flags and cursor/progress repairs.
  Use the detailed dated evidence in this document for what was actually fixed;
  repeat acceptance on the future v38-derived candidate. Past v11 pairs do not
  establish current-baseline compatibility.

### 1.0 optimization preservation cross-check — 2026-09-30

Read-only comparison of the actual `D:/Games/Magic&Mayham_Remastered_1.0`
release, immutable v38 package and installed development entry confirms identical
embedded enhancement resources: 101 = `9c7a0a25...`, 102 = `af65b4ba...`.
Their native engine (`43e12256...`), terrain module (`3791b8ea...`), wrapper
(`85e0f7d5...`) and PNG loader (`206c645e...`) are also byte-identical.
Launcher file hashes differ because release layout/icon/launch plumbing differ;
the functional payloads do not differ.

The release was derived from v37, whose manifest names v36 final occlusion as
its parent; v38 names v37 as its parent. Consequently v38 retains the delivered
v28-v33 replay/path optimizations, v36 corrected 50% occluded-body reveal and
v37 tutorial anchoring. No reverse merge from 1.0 is needed for these features.
The old mixed-ui-v4 candidate remains the version missing these later modules.
Use the verified functional payload identities as explicit 1.1 preservation
checks rather than relying on equal native-engine hashes alone. This confirms
inclusion, not new gameplay acceptance; no game was launched.

### Findings and recommended architecture

Start 1.1 from immutable v38 and port identified HD changes, assets and evidence
from v4 in bounded increments. Reuse the existing compositor, corrected ordinary
mouse-message transforms, font variants, tooltip surface reconstruction and
page-specific sprite variants. Do not wholesale install v4 or rewrite the engine.

Keep output at 2560x1440. Proposed independent-page content viewport is native
1920x1440 at output origin (320,0), rendered 1:1 with 320px side margins. A
2560x1440 primary/composition surface may remain for engine compatibility; it
must not substitute low-resolution content enlarged by the wrapper. Battle
scene and HUD stay at their current 1280x720 native size with exact 2x output.
This centering policy is a proposal requiring user confirmation.

The old candidate combines doubled wide169 geometry with full 1920x1440 artwork
and a 2560x1440 primary. It is not sufficient to assume every page's content,
clicks and clipping already implement the desired 1920x1440 contract. Audit each
page against the proposed viewport. A single global multiply cannot handle all
legacy 800x600, modified 1280x720 and generated-asset coordinate systems.

Introduce a small shared rendering/layout context using existing engine page
identification: page kind, native content bounds, design space, output transform,
asset/font profile and layout generation. The current `mixed_ui_fonts.cpp` and
`wrapper-probe/mm_mixed.h` independently inspect live controls; consolidate their
mode contract so input, composition, fonts and caches cannot disagree. Add family
adapters at construction/layout boundaries using the existing `ui_layout.h`
helper where appropriate. The adapter remains limited to the two requested modes;
full responsive layout, arbitrary native resolutions and a new UI engine are
outside this proposed release.

For each migrated page, derive drawing, hover/hit rectangles, text bounds and
clip regions from the same geometry. Switch glyph metrics, advance, line spacing,
wrap, tooltip bounds and cached surfaces together. Preserve battle fonts before
2x presentation. Give shared UI/HUD sprites distinct page variants; the past
SplIcons trial fixed Portmanteau but enlarged and cropped a battle spell icon.
Replace coordinate-specific recognition with explicit page/resource selection
where proven engine context permits it, rather than expanding coordinate lists.

### Proposed implementation sequence and acceptance

1. Create isolated 1.1 from v38 with separate saves/configuration, immutable
   source hashes, latest launcher modules and working rollback. Reconcile loose
   build artifact provenance and migrate PNG-compatible asset staging tools.
2. Implement shared context and mode/coordinate transitions; deliver menu,
   options and load/save as the first visible UI candidate. Check ordinary mouse
   paths and cached surfaces, not only private diagnostic input.
3. Integrate Grimoire/realm/region entry/character pages using verified full-size
   art; fix folds/tabs, lists, scrolling, overlays and font reflow per family.
4. Integrate Portmanteau and its resource variants, tooltips, drag/drop, equipment
   and all QoL binding/transfer/Delete behavior. Finish battle/page transitions,
   dialogs, tutorial anchoring, transient loading and victory/defeat pages.
5. Complete user acceptance and package 1.1. Optional battle filter is secondary
   and disabled by default; retain exact 2x as reference. Existing v4 CPU sharpen
   added about 3.5 engine CPU seconds per 10 wall seconds in historical runs,
   and stronger sharpen amplified grass noise. Evaluate a supported GPU
   presentation filter only after compatibility/performance evidence; no speed
   claim or new filter implementation was verified in this review.

Build/install each agreed checkpoint with hashes, backup and rollback, then stop
for the user's testing. Preserve current `MaxFramesPerSec=30`, save formats,
Chinese/Latin text, OGG/FMV, existing fixes and original multiplayer policy.
Runtime acceptance remains pending user testing. Paired full-resolution captures
from a freshly hash-verified v38 baseline are the visual evidence standard;
automated or manual gameplay capture requires explicit user authorization under
the September 30 project rule. Inspect user-provided captures and feedback by
page; offline geometry/asset checks cannot stand in for visual acceptance.

Scope proposed for confirmation: complete independent UI coverage with existing
approved generated assets; retain selected plain enlargement where documented
comparison found it clearer (e.g. three small Buttons frames). Re-generation,
if needed, must use the user's local Qwen Image 2.1. Creature/terrain animation
HD, real 60 distinct render frames and gameplay-time compensation are separate
unfinished projects, rather than implied 1.1 deliverables.


## Portmanteau tooltip layout repair, 2026-09-29

The first v4 hover pair showed a real geometry defect: the independent-page
tooltip kept the 300×53 battle layout while its doubled text wrapped to 248px
high and was clamped to the old 600px lower boundary. Read-only fields on the
hash-identified engine's global tooltip object (`0x657fe8`) confirmed this was
layout state, not Qwen art or a talisman hit-box problem.

The isolated v4 runtime now selects tooltip width, line height, padding and
edge bounds together with the mixed font mode. It also rebuilds the tooltip's
offscreen surface when switching modes, preventing a stale 300px canvas from
clipping the right half. Fresh baseline-first pair
`assets/hd/baseline-comparisons/1790669405986762600/` shows the middle and left
talismans at exact 2× geometry; threshold-48 markers contain no tooltip region.
The final captured geometry is 600×106 at `(366,1212)–(966,1318)` for the
middle hover, matching the baseline's 300×53 `(183,606)–(483,659)` after 2×.

The core tooltip pair `1790669585816674700/` confirms battle tooltip fields and
pixels remain at the original 300×53 and 1280×720 coordinates, including the
battle-return transition. Its remaining threshold-48 regions are existing
wide-screen top-right icon differences. Candidate launcher and all 250 files
were hash-checked and restored after each capture; the launcher backup is in
`playtests/mixed-ui-v4/before-tooltip-layout-20260929/`.

## Portmanteau top icon investigation, 2026-09-29

The first icon value audit targeted the wrong resource. Read-only live control
inspection shows the controls at `(1292,52)`, `(1456,52)` and `(1618,52)` use
`SplIcons.spr` frames 2, 1 and 0 for the red, green and blue circles. The
portrait, book and green creature at `(1794,52)`, `(1932,52)` and `(2072,52)`
use a different vtable (`0x5c7780`). A second file-name inference to
`mitems.spr` was also wrong: the live sprite pointer `0x6f3148` resolves to
`Sprites/Buttons.spr` with `BUTTONS` frame headers 0, 3 and 9. Neither earlier
audit measured these icons. The proposed source hook mapping change was
reverted before any rebuild; the v4 binary and 251-file manifest were left
intact. The final value audit targets `Buttons.spr` and changes pixels only
inside the three top icons.

The verified `Buttons.spr` A/B is
`assets/hd/qwen-value-audits/1790676679178214200/`: baseline, Qwen v4 and
source-derived Lanczos v4 use the same `test5.sav`. The Qwen/plain difference
box is `(1818,52)–(2163,148)` and does not touch battle or page geometry.
At actual 2560×1440 play size Qwen gives no useful improvement for these
three small icons; plain enlargement is preferred for this sampled frame set.
The candidate was restored to its original Qwen file after the trial.

The selected plain frames 0, 3 and 9 are now staged in isolated v4 with the
other 18 `Buttons.spr` frame payloads preserved. The new asset SHA-256 is
`dd94d69c...`; rollback is
`playtests/mixed-ui-v4/before-plain-port-buttons-20260929/`. Baseline-first
Portmanteau and core retests are `1790677064806244500/` and
`1790677264772377000/`. The travel box, two talisman hovers, battle and
battle return passed; the latter two are pixel-identical to the prior v4
core reference. Both sessions restored mutable files and v4 matches all
251 manifest entries.

The remaining threshold-48 regions at the top of the Portmanteau page are not
the `Sprites/Buttons.spr` trial. A follow-up inventory corrected the initial
resource attribution: `magico80.spr` has only 61 frames and cannot provide
frame 73. The live `SPELL I` controls instead share `Sprites/SplIcons.spr`,
a 234-frame SPR v4 container. V4 had enlarged only frames 0–2 for the colour
buttons; top portrait frames 43, 54 and 73 and overlay frames 99, 100 and 107
were still their baseline sizes. Their live control rectangles are doubled,
so these six frames are the focused next replacement candidates. Verify the
shared battle path after staging them.

A reversible six-frame trial used the verified local Qwen frames and preserved
the other 228 payloads byte for byte. Baseline-first Portmanteau pair
`1790670596119094200/` restored all three top icons at 2×. The threshold-48
diff then had one small talisman-adjacent region and no top-icon regions.
However, baseline-first core pair `1790670682844244900/` found that a battle
spell icon using the same shared frame became enlarged and cropped at output
box `(1872,1354)–(1962,1438)`. This trial was rolled back from
`playtests/mixed-ui-v4/before-port-icons/`; the original v4 `SplIcons.spr`
hash `ea65414c...` and manifest are active again. The next implementation
must select original and enlarged frames by page, with battle using the
original source. The failed trial's exact frame set and evidence are retained
in `playtests/mixed-ui-v4/port-icons-stage.json`.

The page-specific implementation now keeps the shared `SplIcons.spr` byte for
byte and loads the six enlarged local-Qwen frames from isolated
`Sprites/port-icons.spr`. The v4-only draw hook selects that sprite only for
the three hash-verified Portmanteau top controls (the exact rectangles and
frame indices observed live), then restores the control's original pointer
immediately after drawing. Baseline-first Portmanteau pair
`1790671252132993800/` shows all three icons at 2×; its threshold-48 marker
has only one small talisman-adjacent region. Baseline-first core pair
`1790671339451602900/` reached menu, options, load, battle, portrait tooltip,
Esc, save and battle return. Every v4 output image there is pixel-identical
to the pre-icon v4 pair `1790669585816674700/hd/`, including the spell HUD.
Both runs restored mutable files; the 251-file manifest matches. The prior
launcher and manifest are in `playtests/mixed-ui-v4/before-page-specific-port-icons/`.

## Portmanteau tooltip geometry regression evidence, 2026-09-29

Fresh installed-v11-first pair `assets/hd/baseline-comparisons/1790667951624799500/`
opened the same test5 Portmanteau, dismissed its tutorial, then hovered the
left and middle equipped talismans using their live native control rectangles.
Both runtimes reached the page and restored mutable files. At threshold 48,
the plain Portmanteau has only the cursor mark; both hovered talismans expose
a new geometry defect. The middle tooltip's light box is approximately
`(368,1214)–(963,1315)` in 2× baseline output but
`(517,473)–(814,718)` in native v4 output. The marked pair is in
`diff-middle-hover-t48/`. Its HD box has roughly half the baseline-output
width and appears above the talismans instead of beside them.

A reversible launch with the pre-font-spacing v4 binary reused the verified
baseline capture in `1790668056235475900/`; the same tooltip defect remained.
That binary and manifest were restored byte for byte, so the 2026-09-29
Chinese spacing repair did not introduce this issue. The page's Qwen art is
not the tooltip source. Follow the runtime tooltip placement and sizing path
with exact-engine identity; do not shift every mouse coordinate or alter the
working Portmanteau control hit boxes. Options before/after paired run
`1790667857236118400/` still changed controls correctly and has no
threshold-48 structural mark beyond the cursor.

## Grimoire Chinese wrap spacing repair, 2026-09-29

The runtime translation shim at engine `0x4a58e0` depends on calling state;
wrapping it in a C++ diagnostic hook corrupted Grimoire lower text. That
probe was fully rolled back, and `1790666330468005500/` reproduced five
pre-probe HD pages pixel for pixel. A fixed-width DLL edit at RVA `0x1276`,
`0x127d`, and `0x1284` likewise had no effect and was rolled back. These
constants are not the active advance path for the Grimoire page.

Read-only captures in `1790666439144741400/` instead showed the SFT font
object's horizontal spacing at `+0x230` was 2 in both runtimes, even though
the HD font height and glyph metrics were doubled. The isolated v4 mixed-font
selector now sets that spacing to 4 on native independent UI pages and back
to 2 on the 1280×720 battle/Esc mode. Baseline-first pair
`1790666541519573000/` shows the next Grimoire page's lines and paragraph
wrap matching the baseline at full output resolution. Relative to the old v4,
only text regions changed in menu, introduction and next page.

The core baseline-first pair `1790666715861725600/` reached menu, options,
load, battle, Esc, save, and battle return with the same verified legacy test2
fixture. Its battle, Esc and battle-return HD captures are pixel-identical to
the pre-spacing v4 pair `1790663832020465400/`; independent pages show text
spacing changes. Both runs restored mutable files, and the temporary test2
copies were removed. The v4 manifest still has 250 matching files. This
accepts the specific Grimoire reflow repair, not all font sizes, other
chapters, tooltips or transitions.

## Stable Grimoire text reflow check, 2026-09-29

Fresh installed-v11-first and v4 captures are in
`assets/hd/baseline-comparisons/1790664104009548600/`. After turning the
Grimoire page, each runtime was captured immediately, three seconds later,
and eight seconds later. Each runtime's three full 2560×1440 output images
are pixel-identical. Thus the different Chinese line endings and wraps on
the paired `grimoire-next` image are stable layout differences, not an
unsynchronized typewriter effect. A threshold-48 text-region marker is in
`diff-grimoire-text-stable/`; the target region was `(480,80,900,400)`.

An isolated four-pixel width-padding experiment changed the scaled Chinese
glyph frame returned by `native_ui_font_scale.c` and was tested with another
baseline-first pair, `1790664474888306200/`. Its Grimoire and menu outputs
were pixel-identical to the pre-experiment v4 captures, so the glyph frame
width is not the advance or wrap control for these pages. The experiment was
fully rolled back from `playtests/mixed-ui-v4/before-chinese-spacing-20260929-144748/`;
all 250 v4 manifest files again match. Next inspect the Chinese text measure
and line-layout path in the hash-identified engine/translation DLL, then test
any spacing adjustment on an isolated copy across Grimoire, lists and menus.
Do not assume every intended high-resolution glyph difference is a defect.

The existing Ghidra export for v4 engine SHA-256
`3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d`
shows line layout at preferred VA `0x4a6630` accumulating the return value of
width routine `0x4a58e0` for each character and comparing that sum with the
text rectangle's right edge. This explains why changing only the returned
glyph bitmap did not move wraps. The export is static pseudocode and does not
include translation-module runtime hooks; check the actual `0x4a58e0` entry
and measured returns under the hash-verified process before patching advance.

A further baseline-first owned pair, `1790664775811631600/`, read the first
12 bytes at `0x4a58e0` on menu, introduction and next page. Both runtimes
retain a `push <address>; ret` translation shim there; their target addresses
differ only because `chaos95.dll` loaded at different module bases. The
on-disk bytes at translation DLL RVA `0x17e2` match in the original and v4
DLLs. Both captures restored their mutable files. The next investigation
must account for the translation shim and SFT object spacing; unpatched engine
`0x4a58e0` pseudocode alone cannot explain the wrap. The later spacing repair
is documented above.

## Grimoire introduction left-tab repair, 2026-09-29

The v4-only QoL DLL now hooks the verified page load at `0x4c5520` and
the generic tab draw at `0x4cb5a0`, checking exact original bytes before
installing either hook. Read-only trace `baseline-comparisons/1790663609788037400/`
recorded introduction page draw `(chapter 0, section 0, page 1)`, then
`(0,0,2)`, and the forest tab draw while owner state was `(0,0,1)`. After
turning, the owner state changed to `(1,1,1)`. The hook now skips only the
forest tab control at native 2560×1440 coordinate `(344,216)` when owner
state is `(0,0,1)`; it leaves input rectangles and all other draws unchanged.
The user-correct right clasp remains untouched.

Baseline-first Grimoire pair `baseline-comparisons/1790663736971210100/`
passed open, next page and return with both runtimes restored. Relative to
the prior v4 screenshot, only `(355,216)–(474,358)` changed on introduction;
the next page and return captures were pixel-identical. Threshold-48 diff
regions on introduction dropped from 13 to 12, and the prior largest left
tab region `(352,224)–(464,352)` disappeared. Core baseline-first pair
`1790663832020465400/` passed menu, options, same-fixture load, battle, Esc,
save and battle-return. Temporary test2 copies were removed after capture.
All 250 manifest files still match. Current v4 launcher SHA-256 is
`574abc5fbc5ad7506faa2e555a9b51d7bfc3de7144f42bfbb2b78be2113ee41c`;
prechange source, DLL, launcher and manifest are in
`playtests/mixed-ui-v4/before-grimoire-tab-20260929-143139/`.

The diagnostic hook still writes page/tab records only when
`MM_GRIMOIRE_TRACE=1`; normal play does not create that log. Remaining
Grimoire glyph/reflow and other chapter interactions need broader review.


## Grimoire left-tab compositing trace, 2026-09-29

The fresh v11 pair `v11-merge-grimoire-1790649353903472600` still shows
the introduction's forest tab in v4 and not in baseline; the next page shows
it in both. A read-only owned run at
`assets/hd/grimoire-tab-state/1790662453181337300/tab-state.json` read
0x200 bytes from all eight left tab controls on intro and next page, in
both baseline and v4. Every control's bytes are identical across page turn,
including visibility byte `+0x79`, state `+0x39/+0x3d` and frame indices.
This rules out a page-turn control-state change as the cause.

The exact v4 engine is `3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d`.
At `0x4cb5a0`, the `0x5c6bd0` control's draw method checks `+0x79`,
selects its SPR frame and draws through `0x6903dc` or `0x6c4e3c`.
`0x4c5520` loads the page bitmap and composites it separately; its callers
pass chapter/section/page from `this+0x42/+0x46/+0x4a`. Static pseudocode
is under `D:/Tools/magic-mayhem-re/projects/mixed-ui-font-20260928-export/`.
The intro `C0S00P1` BMP has opaque paper at the forest-tab region; the
following `C0S01P1` uses blue transparency there. At threshold 48, baseline
intro pixels within `(352,224)–(464,352)` match its opaque page source
(mean RGB difference 1.7), while v4 differs by 60.6 due to the visible tab.
Outside the tab region, v4 intro page pixels match its source within about
3 RGB levels.

A reversible, manifest-gated paint probe changed only
`C0S00P1_PrefaceContents.BMP`, captured v4, then restored both the file and
manifest byte-for-byte. A red patch at `(480,270)–(520,310)` appeared exactly
there, proving the page is loaded. A patch under the forest-tab region did
not appear, proving later tab drawing covers it. Probe artifacts:
`grimoire-tab-state/visible-paint-1790662816389855500/` and
`paint-flow-1790662585549468400/`. All 250 v4 manifest hashes match again.

Required fix: make the opaque intro page cover the forest tab while retaining
normal tab drawing on later transparent-keyed pages, or conditionally skip
only that tab's draw on the intro page after confirming the page-state
pointer at runtime. Keep input/control hit rectangles unchanged and keep the
user's correct right-edge clasp reference. Do not edit the shared icon frame.
The page-state pointer and draw order across the final compositor remain to
be traced; this visual defect is still open.


## Save cleanup defect and partial recovery, 2026-09-29

`CaptureSession.__enter__` delegates to the base session, which calls
`__exit__` even when startup fails. `CaptureSession` initialized
`before_saves` to an empty set and unconditionally deleted every Save file
not in it. An identity failure before snapshot creation therefore deletes
existing saves. The failed `hd-match-fixture` run from the prior merge work
selected the installed baseline (only exact label `hd` chose HD), failed on
its loose DLL hash, and ran this cleanup before establishing its snapshot.
This explains the observed installed Save loss; v4 initially had no saved
fixtures and its tests intentionally staged/removed temporary copies.

The comparison harness now rejects any label other than `baseline`/`hd`,
sets a snapshot-ready guard only after copying original mutable files to
`<capture-run>/mutable-backup/`, and never deletes unrecognized new saves.
It preserves new saves in the runtime and copies them to `new-saves/`.
Four no-game regression tests in `tests/test_capture_save_safety.py` pass:
pre-snapshot identity failure, invalid label, new save preservation, and
restoration of existing saves after runtime failure.

Seven legacy saves were checked against historical manifests and recovered
from `backups/wide169/rollback-1790562698030243900/runtime/Save` into both
installed and v4 Save directories, without overwriting any files. The old
test2/test7 were named `test2-legacy.sav` and `test7-legacy.sav`, so they
cannot silently stand in for the newer v11 fixtures. Recovery copies,
SHA-256 identities and destinations are recorded in
`backups/save-recovery/1790661735830701800/recovery.json`. All 250 v4
package hashes still match. Original game Save and v3 Save were not changed.

The newer two-zombie test2 (`cdf39217...`) and injured test7 (`0eb63c2c...`)
have not been found in project/backups or searched user download/desktop/
document/temp folders. Prior runtime verification evidence remains, but
the actual latest fixtures cannot presently be rerun. The user has been
asked for a copy or source path; do not label recovery complete until those
files are recovered or the user decides how to proceed.


## Grimoire detail review in progress, 2026-09-29

The user supplied `assets/hd/grimoire-feedback-baseline-bug-user-reference.png`
(SHA-256 `1055f04a39f610c58d641835a7aeba3477b670fa2546ef4c49dc6039497b63ac`)
and clarified that its **left half is the faulty baseline and its right half
is the correct reference**. Do not treat the right half as another error. The
baseline has extra black strips above/below the right-edge clasp and an
incorrect exposed tab arrangement. The current v4 crop from
`1790621195557872200/hd/grimoire-2560x1440.png` matches the correct right
half's continuous book-edge strip and clasp arrangement. Keep the known
baseline defect excluded from pixel matching and preserve v4's right-edge
artwork. The left introduction tab difference is a separate issue.

Isolated v4 replayed the previously hash-verified baseline Grimoire flow
`1790608437815907700` in `1790621195557872200` and again with read-only
control records in `1790621558215586900`; the comparison JSON records the
reused baseline provenance while another session edits its QoL module.
Open, next page and return all passed, with mutable files restored.
The right feedback-tab exclusion `[2080,208,2176,368]` remains a known
baseline defect and is not a v4 repair target.

Threshold-48 review found a separate, larger left tab mismatch on the
introduction page, `[352,224,464,352]`: baseline intro leaves the forest
tab artwork hidden, then displays it on the next page; v4 displays it on
both. The older original-size in-game capture
`assets/hd/grimoire-game-before-1280x720.png` also hides it on intro, so the
v4 intro state is probably wrong. The page has the same left-side control
rectangles in both captures, and v4's first two left tab control objects
have identical first 160 bytes before and after page turn. Therefore the
visual difference is not explained by a control frame/state change; page
compositing or clip order needs tracing before an isolated fix. Do not blank
the shared icon frame, which is needed on the next page. The other marked
areas on the next page are Chinese glyph strokes/reflow; inspect them against
readability requirements rather than matching pixels blindly.

## Options page detail audit, 2026-09-29

With another session changing the installed baseline's QoL DLL, isolated v4
replayed the exact `options` flow against previously hash-verified baseline
capture `1790607767165119100`; the new comparison
`1790620846631673800/comparison.json` records that source explicitly.
Both clicked the medium speed option and changed music volume, with visible
control-region changes of 0.310% baseline and 0.369% v4, then restored config.
At threshold 48, the before/after pages have the same five small boxes.
One is the left-bottom cursor and is explicitly excluded in
`options-reviewed-t48/`; the remaining four fall only on strokes of Chinese
labels (title, game speed, minimap and dialog animation), reflecting the
intended higher-resolution SFT glyphs. No box falls on slider rails, knobs,
radio controls or button geometry. Baseline and v4 control rectangles for both
buttons, both slider rails and all twelve radio rows match exact 2× scaling.
The two slider knob centers differ by 2 output pixels at their maximum edge;
their 36×36 dimensions and interaction pass. No setting-page patch is warranted
by this evidence; do not regress to low-resolution glyphs to erase pixel diffs.

## Realm overlays restored in isolated v4, 2026-09-29

Read-only owned-v4 probe `assets/hd/realm-draw-probes/1790619652772309800/`
validated the realm instance at `0x659408` with vtable `0x5c6a60`, nine flags
and an 89-frame loaded sprite. The visible target entry has source map
coordinates `(501,203)`. Flag draw `0x5506a0` and wizard/marker draw
`0x550970` still set software sprite clipping to 640/800 by 480/600 through
`0x57dc60`, while their positions were projected onto 2560×1440. This clipped
the overlays away. `tools/stage_mixed_ui_v4_realm_overlay_clip.py` replaces
only the two clip-setup blocks at `0x5506d4` and `0x5509a5` with a 2560×1440
rectangle. Exact v4 engine SHA is now
`3eda4a37079e6c4fb09dfc1b01760afa0bf6979d82dd479a56631f5ea96f056d`;
launcher SHA is `01146685cab0721adb1f18f0ee96d92634b2b8a535f35561c869273cbd40d9bb`.
Backup engine, launcher, launcher source and manifest are preserved in
`playtests/mixed-ui-v4/before-realm-overlay-clip/`.

Retest `1790620189137797200/` restored the wizard and banner but exposed their
original small art. The already validated local Qwen 89-frame flags derivative
was then restaged with `stage_mixed_ui_v4_flags_after_clip.py` (SPR SHA
`615dab4f...`). Retest `1790620335120339300/` restored size but exposed original
ANI placement offsets. Static loader `0x4644d0` reads ANI v5's 44-byte header,
sequence index table and 44-byte records. The source `flags.ani` SHA
`4d159b39...` has 102 sequences and 440 records; record signed x/y offsets at
`+8/+12` match the live animation `(frame 5, -2, -47)`. The isolated derivative
made by `stage_mixed_ui_v4_flag_offsets.py` doubles only these x/y fields;
header, sequence table, frame numbers, timing and every other byte remain
unchanged. New ANI SHA is
`9ccf7025b443df4c7109a3358fa4a690a4bad66ae28a809afe6df7d9cbc4f250`.
Resource/manifest backups are in `before-realm-flags-after-clip/` and
`before-realm-flag-offsets/`.

Final same-save `realm-select` retest `1790620563358734700/` restores the
wizard/banner size and placement; ROI `[1400,360,1620,540]` has **zero structural
regions at threshold 48**, and region selection and mutable-file restoration
passed. Its baseline was the earlier hash-verified baseline-first capture
`1790618768115004900`, explicitly recorded in `baseline_capture_source`,
because the user is concurrently fixing baseline bugs in another session.
This is a fixed-baseline comparison, not a fresh capture of those ongoing fixes.

Core retest `1790620636999547300/` passed options/load/test2/battle/Esc/save/
return and restoration. Relative to previous v4 `1790614655695137400`, menu,
options, Esc and battle-return are pixel-identical; first-battle difference is
limited to central animation `[1240,602,1364,728]`, leaving the HUD unchanged.
Load and Save rows differ because v4's Save directory was empty and the harness
temporarily staged only the hash-verified requested fixture. All manifest
hashes match. Installed runtime and user v3 were not modified. V4 still requires
the other page/interactions release gates; this resolves the tested map overlay.

## Realm banner paired review, 2026-09-29

Fresh baseline-first `realm-select` pair
`assets/hd/baseline-comparisons/1790618768115004900/` used the same verified
`test5.sav` SHA-256 `2b00d842...` and restored both mutable runtimes. At the
default threshold 48, ROI `[1400,360,1620,540]` yields one structural box
`[1448,408,1560,488]`. Enlarged native-source crops show the baseline has a
wizard and banner above the village, while v4 has neither. This remains a
missing dynamic overlay; neither map bitmap contains it.

Static disassembly of exact v4 engine SHA-256 `404b7f2d...` establishes that
the live realm object's vtable is `0x5c6a60` (constructor assignment at
`0x54fc91`). Its page update entry is vtable slot `+0x10` at `0x5517a0`,
which passes the same object in `ecx` to refresh `0x5512c0` at `0x551d79`.
Refresh invokes flag draw `0x5506a0` and unit/marker draw `0x550970` at
`0x55141a` / `0x551426`. The flag draw reads `[object+0x823]` as count and
`[object+0x9f]` as its sprite. Loader `0x54f790` builds
`Interface\\RealmViewer\\Generic\\FLAGS.SPR` and `FLAGS.ANI`, then stores the
sprite in that same object. Both baseline and v4 on-disk `flags.spr` currently
have identical hashes, so the missing wizard as well as banner points toward
object state or draw positioning rather than a failed Qwen asset replacement.
The exact cause still requires live read-only confirmation.

`tools/probe_realm_draw_state.py` is a bounded, hash-gated, owned-process
read-only probe that scans for the verified vtable and records candidate realm
objects after loading test5 in baseline then v4. Its first run refused to
start because shared `modernization/runtime/wide169/wide169.dll` no longer
matched `current-baseline.json`; the observed hash changed again during the
check, indicating a concurrent rebuild. No process was launched and no
identity check was bypassed. Resume only after the shared runtime and
baseline manifest agree; do not alter the accepted manifest to accommodate a
transient build.

## Realm banner source audit, 2026-09-29

The banner difference in `test5` is not in either map bitmap: direct crops of
the installed 1280×720 `Celtic_Map.bmp` and the v4 2560×1440 Qwen derivative
both show only the village at this location. Source crops are saved as
`assets/hd/flag-bitmap-baseline-probe.png` and `flag-bitmap-hd-probe.png`.
The binary has `%s%sFLAGS.SPR` and `%s%sFLAGS.ANI` loader strings. At the exact
v4 engine SHA `404b7f2d...`, `0x54f884` calls the SPR loader using the
`[realm+0x9f]` object; realm refresh `0x5512c0` calls separate draw functions
at `0x5506a0` and `0x550970`. The 89-frame `flags.spr` trial still produced
an identical capture and was rolled back, so the banner's actual active
draw path or object state is not established. A prior read-only snapshot at
`0x6cbb78+0x823` yielded zero in both builds, but that address was an
unverified object assumption; it is **not evidence** that the sprite was
absent or the flag count was zero. The telemetry field has been removed from
the comparison harness. Next establish the live realm object pointer and
frame index using a verified callsite or controlled read-only trace, then
adjust its native position/size and compare at threshold 48. Do not bake the
baseline banner into the map or install more sprite guesses.

## v4 talisman labels and realm flag audit, 2026-09-29

The higher-threshold difference review isolated three undersized QoL binding
letters beneath the Portmanteau talismans. In
`build/mixed-ui-v4-runtime/qol_bindings.cpp`, `labels()` now draws each source
pixel as a 2×2 block only for independent Portmanteau pages; the battle path
retains its original 14×18 pixels. The rebuilt launcher is SHA-256
`3109aabdbd942dd4a3c430dbbe3a723c4108940896e402165ba4d03fc43eb200`;
its previous binary and manifest are in `playtests/mixed-ui-v4/before-port-labels/`.
Baseline-first pair `1790614363760689000/` changed v4 pixels only within the
three label boxes and left no structural diff region in ROI
`[300,1180,1150,1440]` at threshold 48. Core pair `1790614655695137400/`
passed navigation and restoration. Relative to the prior v4 core run, menu,
options, load, Esc, save and battle-return captures were identical; the first
battle difference was confined to the central animated object.

The realm flag at approximately `[1440,404,1552,484]` remains wrong. Its
visible baseline art matches a banner among `Interface/RealmViewer/Generic/flags.spr`
frames; the local Qwen queue completed all 89 frames (517 assets done total).
However, after encoding and staging the container only in v4, the same realm
capture was pixel-identical to the pre-stage v4 capture and retained the exact
same high-threshold diff box. This is a failed path hypothesis, not a visual
repair. `playtests/mixed-ui-v4/realm-flags-stage.json` records the result and
the original container was restored from `before-realm-flags/`. Next inspect
the actual flag draw/animation path and coordinate transform before further
asset replacement.

## Full-resolution difference review, 2026-09-29

`tools/mark_hd_differences.py` consumes an existing baseline-first
`comparison.json` and a page name. It retains the 2560×1440 source images,
produces a 5120×1440 annotated pair, a 2560×1440 structural heatmap and
ranked rectangles in `differences.json`. The default difference threshold is
48 RGB levels after a 3-pixel blur, raised at the user's request to suppress
minor Qwen texture variation. `--roi X Y WIDTH HEIGHT` focuses a page region;
`--ignore X Y WIDTH HEIGHT` excludes a documented defect in the baseline and
draws its box in blue. The tool never aligns or rescales captures, so geometry
mistakes remain visible. Two synthetic tests cover box localization and the
baseline-defect exclusion. Review remains necessary because an annotated
difference is evidence, not an automatic correctness verdict.

The first review of pair `1790610681858834300/` isolated the three undersized
Portmanteau colour buttons. Read-only inspection of the live controls showed
they actually reference `Sprites/SplIcons.spr` frames 0–2, each 40×40; the
earlier frames 222–233 trial was unrelated and remained rolled back. The new
v4-only derivative doubles frames 0–2 while preserving all other 231 frame
payloads byte for byte; original bytes are in `before-colour-buttons/`.
Pair `1790611290383532900/` changed pixels only in the three button regions,
and the focused difference review went from three marked regions to zero.
Core pair `1790611482962454300/` still passed; relative to the prior v4
run, its menu, options, load, Esc, save and battle-return captures were exact,
and the battle HUD below y=1100 was unchanged.

At threshold 48, the remaining Portmanteau marks are the three small labels
under the talismans. The realm map retains a flag/marker difference near
`[1440,416,1552,496]`. Options marks remain around text and slider rails;
the latter require a separate source/rendering check before calling them
defects. Grimoire review remains at `1790608437815907700/diff-grimoire-t48/`.
The user identified a **baseline bug at the book's right feedback button**.
The baseline capture lacks that tab's icon while v4 shows it. The original
installed `game/Interface/Grimoire/800x600/icons.spr` visibly contains the
tab art; decoded source evidence is `assets/hd/grimoire-original-icons.png`.
Do not remove the v4 icon to mimic this baseline defect. The reviewed diff
`1790608437815907700/diff-grimoire-reviewed/` excludes only
`[2080,208,2176,368]` and records the exclusion explicitly; other Grimoire
differences remain under review. A user-provided original screenshot may
further refine the intended feedback state, but the present source evidence
supports keeping the icon visible.

## v4 realm toolbar correction and rejected colour-ring trial

Baseline-first pair `1790609325532850700/` verifies the realm toolbar repair
in `tools/stage_mixed_ui_v4_toolbar.py`. `Buttons.spr` had already been
enlarged, but the hardcoded toolbar rectangles remained 48×48 with a 52-pixel
step. The v4 repair uses 96×96, a 104-pixel step and y=8; all four live
rectangles now equal the baseline's rectangles multiplied by two. The travel
button changed from `[2188,4,2236,52]` to `[2136,8,2232,104]` and still opens
Portmanteau. The same region selection passed in `1790609458273361900/`.
Core navigation and restoration passed in `1790610329861702000/` after the
repair. The new exact engine hash is
`404b7f2dca4c7ddde93cead1d627e657351d3fd277dcb9340aad76bc78adf5ac`;
the launcher was rebuilt with this hash. Engine, launcher, manifest and source
rollback bytes are in `playtests/mixed-ui-v4/before-realm-toolbar/`.

Local Qwen generated `Sprites/SplIcons.spr` (queue now 516 done). A controlled
trial enlarged only frames 222–233 and preserved the first 222 native frame
payloads byte for byte. Pair `1790610054341597900/` showed the Portmanteau
capture was pixel-identical to the preceding pair, so these ring frames are
not the source of the small colour buttons in the tested page. This trial
was rolled back; the original shared container is active in v4. Its failure
record and backup remain in `colour-buttons-stage.json` and
`before-colour-buttons/`. Do not repeat this trial or install the full shared
container without a verified page-specific contract. Remaining: trace the
actual colour-button draw resource, enlarge realm flags/markers with their
projection, tutorial/tooltips and item drag/drop. V4 remains a development
candidate; v3 remains the user's current isolated playtest.

## v4 realm and Portmanteau paired follow-up, 2026-09-28

`mixed-ui-v4` is an isolated development candidate copied from the playable
v3 package. It preserves v3, the installed runtime and their separate saves.
Its engine SHA-256 after the native realm patch is
`324594eed030aa62fd1ac2e7355213f72c811b81726538d3456cb5330a1490bd`.
The exact patch and rollback bytes are in `playtests/mixed-ui-v4/native-realm-stage.json`
and `before-native-realm/`. The three Qwen realm maps occupy native 1920×1440
at x=320 on a 2560×1440 surface. The original 800×600 region mask is projected
from those visual coordinates; the Portmanteau button is in its actual realm
toolbar, rather than the persistent battle HUD.

Baseline-first paired evidence `assets/hd/baseline-comparisons/1790605333951386800/`
reached Portmanteau from `test5` in both builds. Evidence
`1790605554910690200/` selected the same realm region in both builds;
the selection changed the expected page pixels in each. The earlier v3 pair
`1790604810007569300/` did not reach Portmanteau and retained a small realm
image, so the v4 change addresses an observed defect.

The Portmanteau pair `1790605796855496600/` then exposed undersized magic
items and talismans against the baseline. `tools/stage_mixed_ui_v4_portmanteau_sprites.py`
encoded the already completed local Qwen `mitems.spr` (23 frames) and
`Talisman.spr` (95 frames) as RGB565 v4 in v4 only. Source hashes matched the
Qwen manifests; each decoded frame retained its exact nearest 2× alpha
coverage, name and doubled offset; RGB565 error was at most 9 levels. The
original files are in `playtests/mixed-ui-v4/before-portmanteau-sprites/`.
The native rerun `1790606737298875000/` reached Portmanteau in both builds,
dismissed the tutorial, kept the page open, restored mutable files, and shows
full-size items and three talismans in the 5120×1440 pair. The direct game
capture is `hd/portmanteau-after-tutorial-2560x1440.png` in that directory.

V4 core flow `1790607058974190300/` and Grimoire flow
`1790607130206611900/` passed paired navigation and restoration after the
sprite replacement. The Grimoire page turn changed 6.16%/6.63% of sampled
baseline/HD pixels. These gates confirm the tested routes, not all visual
details. V4 still has undersized Portmanteau top buttons, realm toolbar and
options sliders/radio controls. Those controls use assets shared with battle;
their full-size replacement needs a page-specific reference or loader path so
the battle HUD remains at its established 1280×720 size. Item drag/drop,
tooltips, QoL bindings and long-run gameplay remain unverified. Keep v3 as the
user's current playtest while these v4 issues are repaired.

The subsequent options repair encoded four Qwen radio frames and seven Qwen
slider frames, after completing `Sprites/slider.spr` through the local Qwen
Manager. Originals are in `playtests/mixed-ui-v4/before-options-sprites/`.
Pair `1790607516503358100/` shows their restored size; the paired interaction
flow `1790607767165119100/` selected medium game speed and changed music
volume, producing visible changes in both builds (0.310%/0.369% in the
sampled control region). Both runs restored configuration. Relative to the
pre-replacement v4 run, menu, load, Esc, save and battle-return captures were
identical; battle HUD below y=1100 was identical, with the first battle's
difference limited to a central animated object.

`Sprites/Buttons.spr` then received a reversible 21-frame Qwen trial,
with originals in `before-buttons-trial/`. Pair `1790607864415156300/`
shows the three Portmanteau head/book/exit icons at restored size. Core pair
`1790608152206566600/` retained identical menu, options, load, Esc, save and
battle-return pixels relative to the preceding v4 run; first-battle differences
were confined to `[1240,602,1364,728]`, rather than HUD controls. The subsequent
Grimoire pair `1790608437815907700/` still opened, turned and returned.
All recorded restoration gates passed. Retain this limited trial in v4;
this does not verify all shared-button uses or battle interactions. The three
Portmanteau colour buttons remain small, and the realm toolbar positioning,
tutorial/tooltip sizing, equipment drag/drop and full QoL regressions remain
open. Qwen queue count is now 515 done; generated assets are not automatically
accepted or installed.

## v3 paired fixes, 2026-09-28

Isolated `playtests/mixed-ui-v3/Run-Mixed-UI.cmd` now enables mixed rendering
and screen-aware fonts. It retains separate Save/CFG/AI data. The installed
baseline and v2 were not replaced. Candidate engine SHA-256 is
`7327c93dc75a0cf61b377b37a244fc9318cf702da1b06a0ff3484d83578ab20a`;
all staged resources and launcher/wrapper/DLL identities are in its manifest.

Baseline-first evidence `assets/hd/baseline-comparisons/1790604321122661300/`
reproduces New Game → Region Entry → Grimoire → next page → Region Entry.
The region's 1920×1440 Qwen content is installed 1:1 at x=320 on the
2560×1440 primary. Grimoire uses 960×1440 content per page on 1280×1440
half canvases, preserving source-derived blue/magenta keys. All 190 keyed
pages and 36 region backgrounds were staged with producer/derivative hashes.
The prior black Grimoire and undersized Region Entry are corrected in this
path. Native page controls, page visibility and return navigation passed;
next-page changes measured 6.16% baseline and 6.63% HD pixels above 16 RGB
levels. Body text and the resized icons no longer overlap after adapting the
native caption offsets, row height gates and software text clip dimensions.

Evidence `1790604367178761200/` repeats menu/options/Load Game/test2/battle/
Esc/Save Game/return. The Esc text region `[920,460,1640,1010]` and the
battle counter `[2384,1120,2492,1172]` both match the baseline's exact 2×
output at 100% within 8 RGB levels. Font SFT heights were 32/22/15 during
Esc and 64/44/30 in independent pages. Idle battle telemetry can show large
fonts when no text redraw occurs; the counter is cached during Load Game
and needs an explicit original-font selection at draw return `0x4DE797`.
This bounded evidence does not establish full QoL, all fonts, FMV, long-run
timing or 60 distinct frames per second. All diagnostic Save/CFG/AI and
temporary baseline-wrapper restoration checks passed.

Three Qwen Grimoire sprite containers (34 + 155 + 4 frames) are now encoded
as RGB565 SPR v4. Original coverage is exact nearest 2×; RGB565 error is
bounded to 9 levels; frame order, names and scaled placement are preserved.
The first encoder revision passed the Python reader but failed native loading;
its failure evidence and rollback were preserved. Ghidra on the exact
`531ca844...` database confirmed loader `0x57D310`: frame +28 is a palette
selector/pointer, -1 for RGB, and +32/+36 are optional mask offsets. Function
`0x57D560` converts the contiguous pixel block for RGB555, so interleaving
each row's runs with pixels is invalid for the native renderer. Revision 2
uses all run bytes followed by all pixel bytes, -1 RGB selectors, and zero
optional mask offsets. These derivatives are limited to the three UI files;
they are not a validated creature/terrain encoder. The native open/turn/close
flow then passed. Static exports are outside Git under
`D:/Tools/magic-mayhem-re/projects/mixed-ui-font-20260928-export/grimoire-sprite/`.

Final assertion-enhanced rerun `1790604617165582300/` also required the
Grimoire close control, nonblack native surface, page-turn pixel change and
Region Entry return control in both runs. Its baseline/HD turn change was
6.16%/6.63%, and both cleanup checks passed.

Remaining: test5 realm map native geometry/mask/input, complete Portmanteau
interaction, Region Entry toolbar/radio sprites, options widgets, Chinese
wrap/advance details, other chapters/illustrations/turn animation, full QoL
regression and all existing release gates. Do not mark all independent UI
accepted based on this subset. The Qwen queue remains 382 UI, 37 bitmaps,
88 portraits and 5 containers done; 165 containers pending and 143 blocked.

## Baseline-first visual acceptance, 2026-09-28

The user required an explicit installed-baseline comparison because isolated
geometry and hash gates missed visible defects. `tools/compare_hd_baseline.py`
now verifies `current-baseline.json`, the installed v7 package manifest and
both engine hashes, captures the installed `Chaos-Wide169-Trial.exe` first,
then repeats the same save and actions in isolated `mixed-ui-v2`. Each run
keeps native game-surface captures and full 5120×1440 paired images; the
1280×720 baseline is reconstructed with exact 2× nearest pixels. Both runtimes
restore saves/configuration, and the baseline diagnostic wrapper is restored.

Evidence: `assets/hd/baseline-comparisons/1790602592632569600/` covers menu,
options, load, battle, Esc, Save Game and return; `1790602282220066600/`
covers test5 realm and Portmanteau attempt; `1790602663180061200/` covers
New Game realm and Grimoire attempt. All reported restoration checks passed.
The capture harness must assert page arrival, since visual comparison found
that the HD Grimoire attempt remained black and the HD Portmanteau attempt
remained on the realm view. These are real failures, not accepted pages.

Open visual defects from those pairs, highest priority first:

1. Independent realm views (New Game and test5) render at 1280×720 in the
   upper-left of the 2560×1440 surface, leaving most of the window black.
   Their top buttons use old locations and do not reliably open Grimoire or
   Portmanteau in the HD candidate. Correct page geometry and input together.
2. Esc overlay draws its Chinese text with doubled fonts inside a battle that
   is already enlarged 2× at output. Switch battle/overlay text to original
   metrics and glyph sizes while retaining enlarged independent-page fonts.
3. Options page background is full-size, but sliders and radio controls remain
   roughly half the baseline-output size. Scale their sprites and hit boxes
   together, then compare selected/unselected states.
4. Load/Save list entries and menu lettering look smaller than baseline in the
   paired output despite font object heights 64/44/30; audit the Chinese glyph
   hook and row pitch against actual screenshots, rather than using SFT height
   telemetry alone as acceptance.
5. QoL badge at the top of the battle portrait differs from the baseline
   screenshot. Verify binding/config state before calling it a rendering bug.

The mixed-font candidate in `modernization/build/mixed-ui-v3-runtime/` is now
integrated in isolated v3 and checked in the paired Region Entry, Esc, Save
Game and Grimoire paths above; broader classifier and transition checks remain.

## Requirement and current boundary

The user's final clarification on 2026-09-28 requires **mixed rendering**:
independent UI pages use native 1920×1440 art and enlarged fonts, centered
within a 2560×1440 output canvas; battle keeps the established native
1280×720 scene and HUD, enlarged 2× to 2560×1440 output. Native 2560×1440
battle exploration below is historical diagnostic evidence and is superseded
by this requirement. Do not enlarge the battle viewport or double its font
size again. Implement and verify the transition rather than shrinking UI art.

On 2026-09-28 the user clarified that **the game must render UI at 1920×1440
native pixels**, and its UI source assets must be prepared at that resolution.
Enlarging a lower-resolution game image in cnc-ddraw does not satisfy this
requirement. The earlier 1280×720 wide169 Qwen preview tested asset loading but
reduced 1920×1440 content to 960×720. It is not the target implementation.

The existing UI asset queue is consistent with the requested resolution: a
source 800×600 full-screen image becomes 1920×1440; a 400×600 Grimoire page
becomes 960×1440. Other shapes retain a 2.4× factor. The 2048-pixel Qwen
canvas is an inference work area, not the final raster size. Do not regenerate
assets merely to change their output size; the existing targets are correct.

## Isolated native-canvas probe, 2026-09-28

`tools/native_ui_2k_probe.py` starts from the hash-verified latest wide169 v7
package. It copies that package under ignored
`assets/hd/native-ui-2k-probe/runtime/`, then changes only verified fields in
the copied engine, full-size main-menu, load-game and options resources, and their CFG
rectangles. The original `game/`, `game-wide169/` and immutable package remain
untouched. `assets/hd/native-ui-2k-probe/build.json` records every modified
address and hash. `assets/hd/native-ui-2k-probe/before-load/` preserves the
first menu-only probe state before the load-screen addition;
`before-options/` preserves the menu plus load state.

The probe selects a 2560×1440 native game surface and centers each full
1920×1440 Qwen UI image at x=320. The resource at the engine's existing JPEG
path is a diagnostic 2560×1440 frame around the unchanged-size generated
content. The PNG pack remains the prepared source of truth. Both 320-pixel
side bars in the native captures are black. Main-menu, load-game and options `Rect2`
coordinates are doubled from the working 1280×720 wide169 layout, so the
content-region inputs line up with the 2× native geometry.

Verified in an owned background game process:

- The actual primary game surface is **2560×1440** in read-only engine memory
  and the wrapper's own PNG capture, independently of wrapper presentation.
- The complete 1920×1440 Qwen main menu appears centered without clipping.
  Its first button has native hit rectangle `[680,744,1880,840]`.
- Comparing native captures against the exact diagnostic 2560×1440 resource,
  **98.81%** of menu pixels and **99.19%** of Load Game pixels in the central
  1920×1440 region differ by at most 8 RGB levels. Text, cursor and widget
  overlays explain the larger differences; this is direct game-surface evidence
  that the full-size asset is rendered without geometric downscaling.
- Clicking the scaled Load Game button at `(1280,912)` transitions to the Load
  Game screen. After its backing-surface and asset adaptation, that screen also
  fills the centered 1920×1440 region without clipping.
- Clicking the scaled Battle Options button at `(1280,1152)` reaches a third
  native-size screen with 27 scaled `Rect2` entries. Its central native capture
  agrees with the 1920×1440 diagnostic resource within 8 RGB levels at **98.67%**
  of pixels. The old font sizes remain conspicuously small there.
- `MaxFramesPerSec=30` remains set. Owned runs exited cleanly, and the diagnostic
  wrapper plus all protected runtime files were restored after captures.
- The output client measured 2048×1152 on this desktop despite the 2560×1440
  request. Native canvas evidence is valid, but exact 2560×1440 presentation is
  still a separate gate.

Evidence: `assets/hd/native-ui-2k-probe/menu-native-2560x1440.png`,
`assets/hd/native-ui-2k-probe/load-native-2560x1440.png`,
`assets/hd/native-ui-2k-probe/options-native-2560x1440.png`, `probe.json`,
`follow-menu.json`, `follow-options.json`, and the corresponding owned `modernization/logs/wide169/`
run reports.

## Reversible 2× font probe, 2026-09-28

The user also requires larger readable fonts at the native UI scale. The game
uses two distinct font paths. `Sprites/*.sft` v3 supplies Latin glyphs and line
metrics. The Chinese translation module `chaos95.dll` resolves GB character
codes through `Egfonts.enc`, produces a cached run-length glyph, and hooks the
engine's text routines. Enlarging only the SFT files made English wider but left
Chinese tiny; it also exposed that SFT glyph bytes are coverage values 0–63,
not RGB palette indexes. The first palette-based variant was backed up and
superseded; it must not be reused.

`tools/hd_font_probe.py` now decodes the original SFTs, scales coverage glyphs
and per-row spacing by 2, then writes all six verified fonts into the ignored
isolated runtime. Original files are retained in
`assets/hd/native-ui-2k-probe/before-fonts/Sprites/`; the discarded first
variant is under `before-font-coverage/`. `font-build.json` records every hash.

`runtime/native_ui_font_scale.c` provides a position-independent x86 function
that doubles a decoded Chinese glyph's coverage, dimensions and offsets while
preserving the original code lookup. `tools/hd_chinese_font_probe.py` takes its
no-import COFF code, adds an executable and writable section to a hash-verified
copy of `chaos95.dll`, and routes only the glyph lookup result through it. A
matching engine patch clears 64 rather than 32 per-line spacing entries in nine
verified text paths. The original DLL and engine are under `before-chinese-fonts/`.
Source DLL SHA-256 is
`b627c7483b65ed84aacfc2120f629ce9bd367ab175b2c5a2203060d1df3eeca4`;
probe DLL and engine hashes plus exact edits are in `build.json`. No installed
runtime or immutable package was changed.

In a bounded owned background run, read-only memory reported `LARGE` line
height 64 (48+16), `SMALL` 44 (34+10), and `TINY` 30 (24+6), all exactly twice
their 800-mode counterparts. The native surface stayed 2560×1440, the UI art
remained 1920×1440 at 1:1, and `MaxFramesPerSec` stayed 30. Main Menu,
Battle Options and Load Game displayed larger Chinese and Latin text without
visible clipping. Options Cancel returned to the menu; Load Game selected
`test2`, entered battle, and read its expected unit and fixture state
`[66,48,6]`, 125. The diagnostic run restored temporary files and reported no
changed protected files. Evidence is `assets/hd/native-ui-2k-probe/font-flow.json`
and `modernization/logs/wide169/1790574352008936200/result.json`.

Full-resolution review files (no 720p downsample):

- `assets/hd/native-ui-2k-probe/options-font-before-after-3840x1440.png`:
  two unscaled 1920×1440 content crops, old on the left, enlarged font on right.
- `assets/hd/native-ui-2k-probe/menu-native-font-2560x1440.png` and
  `font-options-font-2560x1440.png`: native menu and options captures.
- `assets/hd/native-ui-2k-probe/font-load-font-2560x1440.png` and
  `font-test2-font-2560x1440.png`: load and battle captures.

This remains an isolated direct-engine probe. The battle viewport and HUD still
use older pixel layouts; no battle font placement acceptance is claimed. The
translation DLL helper uses one writable scratch buffer and currently assumes
the game's synchronous text drawing path. Full dynamic text, wrapping, tooltip,
Grimoire and longer-session checks remain before a release candidate.

## Quick Battle → single-player setup → map selection, 2026-09-28

The isolated probe now extends the same 1:1 full-size path through three more
screens. `tools/native_ui_2k_probe.py advance-quick` adds Quick Battle;
`tools/native_ui_2k_stage_screen.py` adds Single Player Battle Setup and Map
Selection. Each stage validates the latest source package and Qwen output hash,
backs up the prior engine/resource/CFG into a named `before-*` folder, changes
only the verified DDSD width/height immediates, and scales every `Rect2` by 2.
The backgrounds are 2560×1440 diagnostic JPEG frames containing unchanged
1920×1440 Qwen art at x=320.

Owned background input followed the complete path from the main menu into Quick
Battle, single-player setup, map selection, selected the second map, and returned
to the setup screen. The native surface remained 2560×1440 with
`MaxFramesPerSec=30`; the enlarged Chinese/Latin fonts remained active. Scaled
controls appeared at the expected locations (Quick Battle create-single
`[800,840,1760,960]`, setup Cancel/Start `[1280,1176,1700,1260]` /
`[1760,1176,2180,1260]`, map list `[716,428,1844,1030]`). No protected
runtime files changed in the runs.

Comparing native captures to their exact 2560×1440 diagnostic resources, the
fraction of central pixels with all RGB differences ≤8 was 98.75% for Quick
Battle, 92.49% for setup, and 96.72% for map selection. Dynamic text and
controls account for much of the setup difference. Native evidence files are
`assets/hd/native-ui-2k-probe/quick-battle-native-2560x1440.png`,
`single-player-setup-native-2560x1440.png`, and
`map-selection-native-2560x1440.png`; run reports are `follow-quick.json`,
`follow-single-setup.json` and `follow-map-selection.json`.

The first map-list screenshot showed the last visible enlarged line touching
the ornamental bottom border. `tools/native_ui_2k_map_list_fix.py` reduced the
list rectangle bottom from 1076 to 1030 in the isolated CFG, preserving the
original in `before-map-list-fix/`. The follow-up native capture kept all text
inside the frame, and selecting a map followed by OK returned to setup with
the selected map name updated. Full-list scrolling and keyboard navigation
still need separate checks. Setup's many dynamic labels and sliders also need
focused text-collision and actual gameplay start checks.

## Portmanteau shell and battle boundary, 2026-09-28

Starting the single-player setup reached the prebattle Portmanteau. At first,
its old 1280×720 BMP and 53 hit-box rectangles occupied only the upper-left
part of the 2560×1440 canvas. `tools/native_ui_2k_portmanteau.py` now stages the
verified 1920×1440 Qwen background as a 2560×1440 BMP with 320-pixel side bars,
expands the four checked backing/interaction dimensions, and doubles the 53
existing Portmanteau rectangles. The previous engine and bitmap are preserved
under `before-portmanteau/`; exact hashes and edits are in `build.json`.

The game displayed the complete centered panel at native resolution. Against
its exact diagnostic bitmap, 96.56% of content pixels differed by at most 8
RGB levels. The prebattle Ready control proceeded into battle, and an owned run
restored all mutable files with no changed protected files. A click on one
item cell did not produce an observable inventory difference, so item binding,
equipment interaction, source sprite sizes and QoL badges are **not verified**.
Evidence: `portmanteau-native-2560x1440.png` and `follow-portmanteau.json`.

The earlier statement that the battle viewport occupied only part of the native
canvas was based on small objects and fog in a screenshot. A later read-only
test2 run measured `scene_rect=[0,0,2560,1440]` and captured newly rendered map
pixels across the full native canvas. The battle **viewport is expanded** in
this historical direct-engine probe. The user subsequently rejected this
battle geometry in favor of 1280×720 native gameplay scaled 2× to the output.
Unit art, HUD widgets and their anchors remain at older pixel sizes/locations.
Evidence: `test2-native-viewport-2560x1440.png`, `follow-test2.json` and the
owned run at `modernization/logs/wide169/1790581996272622500/result.json`.

## Work required before a playable candidate

This is an **eight-screen direct-engine diagnostic**, not a launcher/package or
accepted HD UI build. It does not inject the combined timing/replay and QoL
modules, so their features are not yet present in the probe. Their current
surface guards and replay storage assume at most 1280×840; retain their
1280×720 battle path and make UI transitions dimension-aware before integration.
Battle, Grimoire,
world map, Portmanteau, character screen, dialogs, loading, victory/defeat,
remaining settings behavior, multiplayer screens and save/load behavior beyond
the tested `test2` path need full-size resources, surface allocation,
coordinates and input/colour-key checks. The font probe above needs these
screens' dynamic text and wrapping gates before integration.

Keep the latest wide169 QoL executable/runtime as the input identity; compose a
new opt-in launcher only after the combined runtime and screen-specific
dimensions are adapted. Preserve the current installed and fallback entries.
The QA gate must show 1920×1440 UI art at 1:1, verify the battle's 1280×720
logical scene/HUD scaled exactly 2× to 2560×1440, transitions and input in both
modes, save/OGG/FMV compatibility, rollback, and actual output geometry.

## Mixed-rendering boundary inspection, 2026-09-28

`tools/native_ui_mixed_probe.py inspect` performed another owned, hash-checked
direct-engine run. Main Menu, `test2` battle and Esc all reported primary
surface 2560×1440 and scene rectangle `[0,0,2560,1440]`. The game uses the
static rectangle at `0x5e1720` (`0x6c482c` points there); the battle-world
pointer at `0x6a46bc` was zero in the menu and nonzero in battle **and Esc**.
Therefore merely shrinking this rectangle cannot implement mixed rendering,
and battle-pointer presence alone cannot classify every full-size overlay.
Latin font objects remained at doubled line heights 64/44/30 in battle, so a
screen-aware font choice is required before the 2× battle output pass. The run
kept `MaxFramesPerSec=30`, restored all temporary files and reported
`changed_protected=[]`. Exact observations are in
`assets/hd/native-ui-2k-probe/mixed-inspect.json` and owned run
`modernization/logs/wide169/1790583659936395000/result.json`.

`tools/compare_mixed_battle.py` creates a full-resolution 5120×1440 comparison
from actual `test2` captures: left is the earlier accepted 1280×720 battle
surface scaled 2× using nearest-neighbor; right is the rejected native
2560×1440 exploratory battle. File:
`assets/hd/native-ui-2k-probe/battle-size-compare-5120x1440.png`. This is a
size reference, not proof of a working in-game mode switch. Both diagnostic
runs measured a 2048×1152 output client on this desktop; exact 2560×1440
presentation remains open.

## Save Game screen from battle, 2026-09-28

The eighth full-size UI screen is now staged in the ignored diagnostic runtime.
`tools/native_ui_2k_stage_screen.py save_game` verifies the local Qwen output,
backs up the previous engine/resource/CFG under `before-save-game/`, enlarges
the verified DDSD allocations at `0x4ab034/0x4ab044`, and doubles seven CFG
`Rect2` controls. `build.json` records the new engine and resource hashes.

The owned `test2` → Esc → Save Game run captured the game's native
2560×1440 surface. The centered 1920×1440 content matched the prepared
full-size art within eight RGB levels at 98.60% of pixels; save/cancel controls
and the edit/list boxes aligned. Esc returned to battle. A separate owned
run typed `hdprobe` into the enlarged edit box, clicked Save, and observed a
340,696-byte save before cleanup removed the diagnostic save. Both runs
reported `changed_protected=[]`; no installed package or user save changed.
Review `assets/hd/native-ui-2k-probe/save-game-native-2560x1440.png` at its
native size; details are in `follow-save-game.json`, `write-save-game.json` and
owned runs `1790584084807234600` / `1790584140722970300`. A save reload
through the new UI and the actual mixed-rendering battle transition remain
unverified.

## Battle rectangle isolation and compositor groundwork

`tools/native_ui_mixed_rect_probe.py stage` temporarily changed only the
verified static scene rectangle at `0x5e1728/0x5e172c` from 2560×1440 back to
1280×720 in the ignored probe engine. The primary surface remained
2560×1440. The Main Menu content still matched its native-size Qwen resource
within eight RGB levels at 98.17%, and the battle's upper-left 1280×720 crop
matched the earlier accepted wide169 `test2` crop at **99.04%**. The rest of
the native battle surface stayed nearly black. Save Game opened from battle
and retained its 98.60% full-size content match with the smaller scene rect.
The owned diagnostic runs restored protected files. The rectangle patch was
rolled back with the tool's hash-checked rollback; the accepted isolated UI
probe remains at engine SHA
`9ee77fc85a0aa5ab1f5ded984ad8c07e540ca8f33e3f43e92580ab6b082b017d`.
Diagnostic full-resolution captures are `battle-rect1280-on2560.png` and
`battle-rect1280-scaled-preview-2560x1440.png`; the latter is an offline
nearest-neighbor size preview, not an in-game compositor result. Supporting
run: `modernization/logs/wide169/1790584493477479800/result.json`.

`wrapper-probe/mm_mixed.h` is early opt-in compositor groundwork; it is not
wired into a built DLL. The implementation still needs a safe source/output
buffer boundary, all relevant DirectDraw update paths, exact screen-mode
classification, screen-aware fonts and native input mapping. Do not put this
header into an installed runtime or claim mixed rendering is working on the
basis of the offline preview.

## Mixed D3D9 live probe, 2026-09-28

The isolated engine's 1280×720 scene rectangle was reactivated only after
verifying the latest installed wide169 engine, manifest, prior probe engine,
rollback backup and exact two patched DWORDs. The new opt-in wrapper takes the
2560×1440 primary without editing it, identifies battle/Esc by the world
pointer and the black area outside the 1280×720 source, and uploads a separate
2× RGB565 scratch to D3D9. Its private screenshot path uses the same scratch.
The diagnostic DLL SHA-256 is
`859f5ec34bcf891cfb0bdf1c8976100177bb564dd60268622a1834137039402f`;
it is selected only by the ignored probe harness and exact engine path.

`tools/verify_native_ui_mixed.py` ran menu → `test2` battle → Esc → Save Game
→ battle in an owned process. The three battle/Esc captures were exactly
2× pixel replicated at 2560×1440. D3D9 composition upload count increased
from 52 to 124, confirming live presentation rather than only offline scaling.
The full-size Save Game backdrop matched its 1920×1440 resource within RGB
error 8 at 98.60%. `MaxFramesPerSec` stayed 30, and cleanup reported
`changed_protected=[]`. Report and actual-game screenshots are
`assets/hd/native-ui-2k-probe/mixed-live-verification.json`,
`battle-mixed-live-2560x1440.png` and `save-mixed-live-2560x1440.png`.

This remains an isolated D3D9 prototype. The probe reported a 2048×1152
client through a DPI-unaware process. On this desktop, `GetSystemMetrics`
reports 2048×1152 before `SetProcessDPIAware` and 2560×1440 afterward, so
the earlier client number is a Windows logical-coordinate measurement, not
evidence that the monitor or game output is only 2048×1152 physical pixels.
Measure the game window with a DPI-aware observer before closing the physical
output gate. Screen-aware Latin/Chinese font selection, native physical
mouse mapping, other renderer paths, combined v7 QoL/replay runtime and broader
screen transitions still require validation. The current battle text is
rendered from doubled native-UI fonts before the 2× scene presentation.

## Isolated correction build

The newer isolated `mixed-ui-v2` is at
`modernization/playtests/mixed-ui-v2/Run-Mixed-UI.cmd`; v1 remains available.
It uses copied v7 QoL and replay modules adapted to the mixed 2560×1440
canvas. An extended owned test passed Save Game entry/cancel, native page art,
return to battle, confirmed wizard selection and movement. In a three-second
movement segment, 66 replay frames reported shifted commands, 216 adjacent
composition buffers differed, and 108/108 replay checks preserved the HUD
outside the scene rectangle. `extended-verification.json` holds the exact
hashes and screenshots. This does not establish long-run 60 distinct frames
per second or unchanged game time. One bordered-window startup reported a
2542×1393 physical client; v2 now uses a backed-up borderless configuration,
and two follow-up checks measured 2560×1440. The root cause and wider display
compatibility still need testing. English SFT and Chinese glyphs are still
doubled in battle before the final 2× enlargement; screen-aware font switching
is the next implementation gate.
The v2 font-state probe measured SFT line heights 64/44/30 in the menu,
battle and Save Game. `0x6a46bc` is zero on the menu but stays nonzero through
Save Game; `0x6e1f0c` and the scene rectangle also did not distinguish the
battle from Save Game. A font switch based only on the world pointer or scene
rectangle would shrink independent-page text. The next hook needs a verified
page classifier and must switch both SFT metrics and Chinese glyph output.

`modernization/playtests/mixed-ui-v1/Run-Mixed-UI.cmd` launches a copied
runtime with separate `Save`, `CFG` and screenshots. Its wrapper accepts only
the probe and playtest engine paths under `MM_PROBE_MIXED_RENDER=1`; the
hash-checked launcher embeds the latest v7 QoL/replay modules and expects
engine SHA `531ca844330ed03c4314e762a4f23f4b72db9ca30ec88608023103099ab80ac0`.
The package is ignored by Git and does not overwrite `game/` or
`game-wide169/`. `tools/verify_mixed_playtest.py` tested an owned launcher run
with all six QoL hooks active, physical window client 2560×1440, native
surface 2560×1440, `MaxFramesPerSec=30` and exact 2× `test2` battle capture.
A separate ordinary startup without the diagnostic background input flag
passed the same launcher/QoL/geometry gate. Manual mouse flow and broader
QoL play remain for user correction and subsequent automated verification.

## v4 merge of installed wide169 v11 fixes, 2026-09-29

The isolated v4 launcher now embeds the installed v11 behavior fixes while retaining
its native 1920×1440 UI hooks, enlarged independent-page fonts and 2× battle
presentation. The portrait left-release calls native `0x57ce70`; the path hook
keeps redirect state separately for each validated unit-table slot. Source changes
are in `build/mixed-ui-v4-runtime/qol_bindings.cpp` and `repath_trial.cpp`.
The rebuilt launcher SHA-256 is
`ba14206f875144ab70a8bf0dfd916af4197828f2210f30e6110210470c5e68bf`.
Pre-merge source and DLLs are in
`playtests/mixed-ui-v4/before-v11-merge-20260929-102224/`; the previous
launcher hash is recorded in the preceding v4 manifest history and original
launcher can be recovered from prior `before-*` stage backups. The current v4
manifest was updated for the rebuilt launcher.

An isolated core smoke run `baseline-comparisons/v11-merge-smoke-1790648804732223900/`
passed menu, options, load, battle, Esc, save and return at 2560×1440; mutable
files were restored. In injured `test7` (fixture SHA `0eb63c2c...`), one left
portrait cast raised actual life 122→200 and target mode stayed 2. Evidence:
`baseline-comparisons/v11-heal-1790648860847408400/`. In `test2` (fixture SHA
`cdf39217...`), unit 0 and summons 9 and 10 were each selected and each
produced at least three `order_mid_segment`/`redirect` pairs. Evidence:
`baseline-comparisons/v11-multiunit-1790648901448624100/`. All isolated
mutable files were restored.

A new baseline-first core capture reached all seven pages in both builds, but
the HD flow automatically used the older v3 `test2.sav` (`56108a09...`) while
the installed baseline used `cdf39217...`; this is not a valid same-fixture
visual comparison. The capture is retained under
`baseline-comparisons/v11-merge-core-1790648957253485300/` for diagnostics
only. The installed `game-wide169/Save/test2.sav` was no longer present when
trying to repeat the HD side; do not infer visual acceptance from this pair.
The separate `wide169.dll` and `qol_bindings.dll` hashes in
`current-baseline.json` are stale relative to disk, though the installed
launcher, engine and v11 package manifest matched. Reconcile those records
before using the stock `compare_hd_baseline.py` identity gate again.

Next: obtain a hash-verified copy of the same `test2` fixture in both isolated
runtimes, rerun the full-resolution pair and difference audit, then continue
with the previously open magic-book tab and other visual issues.

A valid latest-launcher paired core run then used the identical older v3 `test2`
fixture (`56108a09...`) temporarily in both runtimes. All seven paired
full-resolution captures completed and both runtimes restored mutable files;
temporary fixture copies were removed. Evidence:
`baseline-comparisons/v11-merge-paired-1790649129625902200/comparison.json`.
The threshold-48 structural diff tool found two dynamic map-view regions in
battle/escape/return near `(2240,32)–(2544,176)`; the battle HUD is otherwise
unchanged at this threshold. Menu/options/load/save have only small isolated
regions in this pass. The pair does not resolve the previously known Grimoire
and realm-page issues; those remain open.

A rollback launcher was reconstructed from the backed-up DLLs and unchanged
launcher source at `playtests/mixed-ui-v4/before-v11-merge-20260929-102224/`
(SHA `7ec95f5cce7ac07ea79e76ae17be4402e1ab482e9ec8fdf28ee5cd3f3ac27e16`).
It is not byte-identical to the pre-merge binary and has not been run; keep
the current v4 build or v3 playtest for user testing.

The stock comparison identity gate was adjusted to verify the installed
launcher, installed engine and package manifest, which are the files executed
by this workflow. Loose development DLLs are embedded in the launcher and
are not loaded from their source directory during comparison. This removes
the stale-hash false failure while preserving executable hash checking.

### Battle sharpening pilot, 2026-09-29

The isolated v4 wrapper now offers an opt-in RGB565 presentation sharpen pass
after 2× battle enlargement. It does not alter the 1280×720 scene/HUD source,
the 2560×1440 output geometry, independent UI pages, or the engine primary.
`MM_PROBE_BATTLE_SHARPEN=1` is the light setting; `=2` is stronger, and unset
or `=0` retains the prior output. The light setting gave a modest edge gain
in test2; the stronger setting exaggerated grass noise. Verified game-surface
captures, full-size crops, and hash restoration are recorded in
`assets/HD_BUILD_LOG.md` under the battle presentation sharpen trial. Launch
the opt-in light setting with
`playtests/mixed-ui-v4/Start-Battle-Sharpen-Light.ps1`. Full motion performance
and user visual acceptance remain unverified. A follow-up block-based
implementation reproduces the initial output pixels on static test captures,
but 10-second background runs still show roughly 3.5 additional engine CPU
seconds per 10 wall seconds at the light setting. Keep it opt-in. The current
isolated wrapper hash and both backup stages are logged in `assets/HD_BUILD_LOG.md`.
The isolated v4 screenshot hotkey now reads the mixed presentation surface,
so battle screenshots include the 2× output and optional sharpening. Menu
and battle-Esc captures matched the private presentation path in a background
hook test. The final wrapper identity and backup are logged in the same build
log; physical Print Screen key activation remains untested.

The 2026-09-29 isolated launch regression was caused by the direct preview
EXE not setting the mixed-render flag. The corrected v4-resource launcher
sets mixed-render and mixed-font flags for both ordinary and sharpened entry
paths. Same-save background runs without harness-provided mixed flags now
confirm full-width battle presentation, battle/Esc font heights 32/22/15,
and working Esc controls. The exact launcher hash, rollback and screenshots
are recorded in `assets/HD_BUILD_LOG.md` under the isolated launch regression.

Latest baseline-first Grimoire pair:
`baseline-comparisons/v11-merge-grimoire-1790649353903472600/`. Five pages
(menu, new-game realm, Grimoire, next page, return) passed navigation and
restoration. At threshold 48 the opening page has 13 structural diff regions;
the largest are the left top tab `(352,224)–(464,352)` and the matching right
tab `(2080,224)–(2176,352)`. The user's reference image supplied earlier
shows the right half as the correct tab stacking; the baseline's missing or
incorrect right-side feedback tab is an acknowledged baseline defect, so its
visual pixels are excluded as a target. Current v4 shows the tab in the
expected position. Further Grimoire type and control spacing review remains.

### Mixed battle cursor and loading bar, 2026-09-29

The user's ordinary playtest showed that the software cursor disappeared once
it left the upper-left 1280×720 area while clicks still worked. The wrapper's
ordinary `HandleMessage` path returned physical 2560×1440 coordinates in
`MSG.pt`, unlike `GetCursorPos` and the window procedure. The game drew the
cursor at those physical coordinates on its unscaled 1280×720 battle region;
the mixed compositor then discarded it. Both message-position paths now use
the battle coordinate transform. Ordinary-window probes at four output
positions, including `(2500,700)`, show the cursor in the proper location.
Background-input probes alone could not have exposed this fault because that
channel already applied the transform.

The load/save progress bar is a separate engine drawing path with no battle
controls, so the battle compositor must not scale it. The v4 font module now
hash-gates the 1280×720 engine immediates and places the progress object at
native output `(562,1310)` with a 1436×86 frame. Eight isolated progress JPGs
were enlarged from 720×43 to 1440×86. Continuous read-only surface captures
of loading `test2-legacy` and saving `hdpgtest` show the bar across the lower
center of the 2560×1440 page. The owned diagnostic save was removed after
hash verification; gameplay saves and configuration were restored.

The staged runnable candidate is `playtests/mixed-ui-v4/`, with its preceding
DLL, launcher, assets and manifest in
`playtests/mixed-ui-v4/before-cursor-progress-20260929-221855/`. The complete
package manifest verifies 259/259 files. Candidate run evidence:
`assets/hd/cursor-progress-verification/1790692182272423000/verification.json`
(battle, Esc, four cursor positions, Save Game, return; `test3` fixture hash
`cff9d3e8...`; fonts 32/22/15 in battle and 64/44/30 on Save Game).
Transient progress evidence:
`assets/hd/loading-frames/1790691536067492800/` and
`assets/hd/loading-frames/1790691646985940300/`.
The installed baseline was captured first in
`assets/hd/cursor-loading-probe/1790690863341074900/`; a later baseline
recapture was intercepted by its startup FMV and did not reach the menu, so
that run is not accepted as a paired comparison. Ordinary-playtest and progress
results are verified against the isolated candidate; user visual acceptance
and a new same-page baseline pair remain open.


### Remastered 1.1 map correction and resolution policy — 2026-09-30

The user explicitly authorized 1.0-based test cases and sequential paired 1.1
comparison/correction on this date. This permits bounded owned background runs
for those cases, superseding the default no-gameplay-run checkpoint for this
specific UI work. Do not treat this as authorization for unrelated optimization
or unrestricted playtesting. Use windows-game-background-debug private input,
read-only observations, isolated saves/settings and baseline-first evidence.

The first confirmed adaptation defect was in the latest QoL module: realm
point projection and keyed highlight blit accepted only a 1280x720 primary,
while the new primary is 2560x1440. The hover hook also removed a hardcoded160
pixel origin instead of320. Flags/background used HD engine paths already.
`runtime/hd11/realm_adapter.py` selectively adapts latest QoL; do not replace
it with old-v4 QoL. `ui_geometry.h` owns aspect-fit viewport, point projection,
sidebar rejection and inverse reference mapping. The native hover sampler
already scales local visual coordinates using its denominators; the adapter
removes only the viewport origin, avoiding a second inverse scaling.

Current engine and PNG loader identities remain unchanged. A module-only
launcher replacement has backup and rollback in
`tools/install_11_realm_fix.py` / `backups/remastered-1.1-realm-fix/`.
12,428 pure geometry checks cover1280x720,1920x1080,2560x1440,3840x2160
including edges/sidebar rejection and inverse round trips.89 compiled x86
cases execute the actual projection, hover, outline, enemy and keyed-blit hooks and verify
register/stack preservation;14 existing layout/transition checks pass.
These are offline evidence, not visual acceptance.

Future requirement: players may choose1K/2K/4K and fullscreen/windowed in
settings. Keep page logical coordinates, UI native raster resolution, battle
render resolution, output viewport and window mode separate. The UI reference
space is800x600; current native UI raster is1920x1440. Battle reference/render
is1280x720 regardless of display choice. A common layout profile must be
consumed by drawing, clipping, input, fonts and composition. Window mode must
not change logical hit coordinates. Mode changes must rebuild surfaces, reset
cached composition/replay/hover state and preserve the previous working mode
on failure. Never accept arbitrary engine dimensions merely because geometry
supports them. The currently installed engine/wrapper/font/control/assets
support only the current mixed2560x1440 output;1K/4K pure geometry tests do
not claim selectable runtime support. Migrate remaining hardcoded adapters,
engine constants and asset selection before exposing settings. Normalize UI
case positions to reference space, then project through the profile, retaining
full-resolution native/output screenshots plus control rectangles. Test all
page/battle/tooltip/loading transitions and inverse mapping per profile.


Paired runtime evidence (2026-09-30):
`logs/remastered-ui/map-fix-pair-retry-20260930/comparison.json` completes
new-game region-entry/difficulty page, hover, Grimoire and return. This is
not the campaign map itself. Actual campaign map evidence is
`logs/remastered-ui/campaign-map-pair-20260930/comparison.json`, completing
1.0 first then1.1 with identical hash-verified test5 save
2b00d8425eb01bb913b7b380f30f18f4e3d1948a0c05168c022819fca7205b7b.
Six paired surfaces cover menu/load/map/hover/Grimoire/return, source changes=[]
and both owned sessions restored.1.1 toolbar rectangles are exactly2x their
1.0 counterparts; fonts are64/44/30 vs32/22/15. In map, hover and return,
left sidebar x<320,y100..1319 and right x>=2240,y220..1319 contain zero
nonblack pixels (threshold8), confirming no characters/outlines left in the
old sidebar positions for this fixture. Full native2560x1440 surfaces and
paired5120x1440 images are retained. Visual/user acceptance is still pending.

Harness learns page readiness from controls and retries black transition
captures (preserving each failed capture). Closing Grimoire produced one
black transition frame in BOTH1.0 and1.1; the stable subsequent page passed.
One preliminary candidate run missed its toolbar after a fixed1s delay;
the gated retry passed. DPI-aware client measurement is needed: a preliminary
DPI-virtualized client measured2048x1152, while native captures remained full
2560x1440; current harness calls SetProcessDPIAware and records physical
client separately from render/capture dimensions. This is test tooling
readiness/DPI correction, not evidence of a toolbar patch in this iteration.


Settings/battle transition evidence:
`logs/remastered-ui/core-installed-pair-20260930/comparison.json`, baseline
first using identical test2-legacy fixture56108a097a01f0bf7a9035d031d96a630e60c43be77808b9c567c65c33cba66d.
Menu/options/load/save fonts64/44/30; battle/Esc/return32/22/15. Save entry and
cancel/return navigation passed. Source state changes=[]; owned candidate
exited; mutable state restored. This does not validate saving new gameplay,
loading-progress every frame, arbitrary resolution switches or all UI pages.

Important packaging/test limitation: current mixed wrapper enables compositor
and coordinate transformation only for exact allowlisted runtime paths. A new
cloned candidate path passes native independent UI checks but disables battle
2x and input transformation. Preliminary cloned core run accordingly failed
Save entry (not an installed candidate regression). Current harness supports
`--candidate-in-place` ONLY for the hash-verified isolated1.1 path, with full
mutable-state backup/restoration and owned process cleanup. Baseline remains
cloned. Do not use cloned battle screenshots as accepted evidence. Future
portable packaging must replace path identity with an engine hash/verified
launcher-owned rendering contract, while retaining unknown-host refusal.


Installed candidate map recheck:
`logs/remastered-ui/map-installed-pair-20260930/comparison.json` reuses the
hash-verified earlier1.0 test5 baseline and runs the installed isolated1.1
path (compositor path gate satisfied). All six captures pass; source changes=[];
mutable state restored; `map-pixel-checks.json` records zero nonblack sidebars
on map/hover/return at threshold8 and native2560x1440 sizes. This is the final
runtime evidence for the installed module-only map coordinate correction.
The earlier user-supplied screenshot before correction had visible characters
and an outline in the left black/sidebar area. Full Readable art acceptance is
user-positive; final corrected overlay visual/interaction acceptance remains
pending user gameplay feedback. Future player display-mode choices remain
planned, not enabled.


### UI elements iteration: Portmanteau slots and tooltips — 2026-09-30

User authorized continued UI HD implementation and local model-quality review.
This iteration fixes one page's incomplete sprite-state adapter and a shared
independent-UI tooltip boundary fault; other page work remains sequential.
Before evidence: `logs/remastered-ui/port-before-20260930/`,1.0 then installed
1.1 using identical pinned test5 fixture. Upper slots had HD-sized controls but
many dynamic spell/item frames remained40x40. Existing adapter selected only
frames43/54/73 and its page derivative enlarged only six frames. Original
Talisman/mitems and Buttons already had generated2x derivatives.

`tools/build_ui_spell_icons_11.py` now builds all234 page-only SplIcons frames
from hash-verified existing local-Qwen generated frame records. Names, doubled
original offsets/dimensions and exact nearest original alpha are preserved;
RGB565 error<=9. Derivative is `assets/hd/derivatives/hd11/port-icons.spr`
SHA a637e4363f6f09ff78736a367e62974e8135930f69f32a1102d508c16c32ca6c.
Shared `Sprites/SplIcons.spr` is untouched. The draw adapter requires independent
UI mode, a live Portmanteau slot control, a full-size slot rectangle, correct
234-frame source container and valid frame index before temporary substitution.
It restores the original pointer after each draw; Talisman/mitems source
containers and battle widgets are excluded. Variant is consumed only on page.
The source recipe now retains this asset/adapter through future1.1 builds.

Before, left talisman tooltip rectangle was(147,1212)-(747,1318), intruding into
the x<320 sidebar. Native tooltip0x4db7e0 clamps against the full surface edge,
not the centered UI content viewport. Existing Ghidra export and current merged
engine disassembly were checked, engine SHA42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da:
VA0x4db932 bytes8b3de41e6e00 (`mov edi,[0x6e1ee4]`) precede final tooltip blit.
A signature-checked6-byte runtime module hook constrains destination origin
against the shared layout content bounds immediately before that blit, keeping
source rectangle/text/wrapping unchanged. Tooltip secondary RECT is+0x16a,
surface draw x/y are+0x144/+0x148. Hook preserves registers/stack/flags and
replays the overwritten instruction; UI-only guard keeps battle unchanged.
Result is(320,1212)-(920,1318). Interior tooltip stays(366,1212)-(966,1318).
Pure clamp/frame-policy functions are in `runtime/hd11/ui_geometry.h` and use
profile viewport/scale, avoiding another page-specific screen-width constant.

2,528 pure geometry/policy checks,88 actual compiled x86 tooltip/draw-adapter
cases and14 mode/transition checks pass. Actual frame roundtrip/alpha tests
pass for all234 frames. Build+transactional candidate install:
`build/remastered-1.1-ui-elements/`, `tools/install_11_ui_elements.py`, backup
`backups/remastered-1.1-ui-elements/`. Runtime engine, PNG loader, enhancement
resource101, Full Readable map and shared battle sprites remain byte-identical.
Only page icon derivative and resource102-bearing launcher changed.

After runtime evidence: `logs/remastered-ui/port-after-20260930/` compares with
baseline-first earlier case and retains slot-before-after.png. Full functional
case `logs/remastered-ui/port-full-after-20260930/` executes1.0 first then installed
1.1: menu/load/map/Portmanteau/three talisman hover states/three talisman clicks/
Grimoire/return,12 paired full-resolution surfaces. Active hover tooltips are
inside1920x1440 content; fonts64/44/30; book navigation and return pass.
Source changes=[]; owned processes exit; saves/config/timestamps restored.
User final visual acceptance remains pending.

Local Qwen generation review: one1024x1024 Qwen Image2.1 managed trial in
`assets/hd/quality-review-1.1/ui-icons-20260930/`, owned job/prompt/seed/output
recorded in qwen-call.json. Book/chest normal designs improve plane/hinge/page
readability; generated21-icon sheet is not adopted wholesale. A normal-only
candidate would visibly change style on hover/press; a deterministic three-state
family trial kept original masks/offsets/flash but produced doubled rim/page
edges (412 book and516 chest opaque pressed pixels lack normal-art coverage).
The six-state derivative is diagnostic only and NOT installed. Exact alpha
and metadata do not guarantee coherent artwork. Future trial should generate
one family master with consistent silhouette/pose, then build highlighted and
pressed states inside a common coordinate atlas, explicitly validating edge
coverage and state transition before installation. This is a concrete state-
geometry limitation, not rejection of readable reinterpretation.


Final UI-element transition regression:
`logs/remastered-ui/ui-elements-core-20260930/comparison.json` reuses the
hash-verified earlier1.0 test2-legacy baseline and runs newly installed1.1.
Settings/load/save independent fonts64/44/30, battle/Esc/return32/22/15,
Save entry/cancel passed; source changes=[], restored=true. Final build report
`build/remastered-1.1-ui-elements/verification.json` enumerates hashes/checks.
This confirms scoped navigation/render transitions, not all spells/hotkeys or
all menu pages. Current button-generation studies remain out of the runtime.


## 1.1 scanner/minimap repair — 2026-09-30

User reports missing minimap. Verified merged engine SHA-256
`42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`,
preferred base0x400000: scanner main vtable0x5c6a8c, secondary interface+0x21
vtable0x5c6a7c. 0x5548d0 initialization computes both draw origin and native
hit RECT using primary pitch/2 (+0xca on secondary object). A2560-wide primary
therefore creates RECT(2392,6)-(2552,86), outside the1280x720 battle crop.

Exact6-byte `8b86ca000000` loads at0x5548fb (draw origin) and0x554b06
(RECT) now use `mm_hd_profile(1).content_width`. Preserve actual pitch/2 for
pixel row addressing; the original native RECT setter0x4a4e20 updates the
click control. Expected normal scanner RECT(1112,6)-(1272,86), presented2x.
No engine disk patch, battle camera mapping rewrite or art substitution.

Source `runtime/hd11/mixed_ui_fonts.cpp`; build `build/remastered-1.1-minimap/`;
transactional install/rollback `tools/install_11_minimap.py`; backup
`backups/remastered-1.1-minimap/`. Actual compiled scanner adapters + native
arithmetic:27 fixtures varying logical width/pitch/map shape pass. Existing
88 UI adapters and89 Realm adapters pass on the new module. New module SHA
`4d4e7e184fc3db8fa8ccae278dc1483a28857c499e782b84831a25f00732d193`.
Protected1.0/v38 and all5830 candidate runtime files unchanged; only launcher
resource102/manifest changed. Paired settings-battle case now explicitly
checks minimap RECT and two camera jumps; runtime evidence recorded below.


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


2026-09-30 communitySR review completed after minimap repair. User explicitly
permits alternate-model trials/deployment within LocalModelManager for this
request. Existing SeedVR2 passes6-state original sprite4x and originalmap2.4x;
new PixelPerfectV4 sprite model installed underE:/AI, catalogsize/SHA verified,
real Manager Comfy inference succeeded. Manager audit/provenance recorded in
its docs andTASKS. Trial renders/exactalpha,offset,state/RGB565 checks and
community source snapshots: `assets/hd/quality-review-1.1/community-sr-20260930/REVIEW.md`.
Recommendation: direct non-prompted SR for tiny stateful UI elements; individual
motif+common-state-geometry workflow for readable re-art. SeedVR2 more detailed,
PixelPerfect smoother but plastic; candidates are diagnostic, none installed.
FullReadable kept: newmap does not yet show decisive improvement. Broader UI
inventory/acceptance remains open; future1K/2K/4K/window switching still planned.


## User-selected SeedVR2 UI production — 2026-09-30

User selects SeedVR2 as best reviewed result, requests deletion of previous
generated assets, and explicitly authorizes generation/install/background-test
overlap. This supersedes Qwen UI art selection and earlierFullReadable selection.
Originals, formal baselines and rollback are preserved. ProjectAGENTS updated.
Producer `tools/seedvr_ui_11.py`:283UI raster/spritefiles,289resumable managed
jobs, exact input/output hashes and owned job IDs in
`assets/hd/seedvr2-ui-1.1/plan.json`. PNG production masters; compatibility JPEG
for still-native JPEG caller paths (never disguise PNG asJPEG). JPEG loaders
must be migrated separately before changing their filenames. Loading bars use
padded square model input with recorded crop, avoiding unsupported aspect ratio.
4solidbars reproduce original pixels procedurally. Fonts/dynamic text unchanged.
Original book raster colour keys are removed from DiT input, then the existing
runtime key footprint restored exactly; image geometry unchanged. Sprite
containers preserve every current frame size/name/offset/alpha, including the
latestv38 clasp correction for2frames. Shared battleSplIcons untouched; dedicated
234-frame port-icons is regenerated. One unsupported legacyScrollbutt format
is reported and preserved (not silently rewritten asv4).

Every file installs transactionally after verification, manifest updates and
backup. No replacement while owned or usergame active; `test.lock` separates
installation from paired captures while model jobs continue. Before GPU job
submission, retain its idempotencykey/jobID; resume same job after host worker
interruption instead of duplicate/restarting backend. Manager ownsGPU processes.
Profile/modelhashes storedgeneration-profile.json. Initial sprite controls +
12screens/states with all-new234pageicons pass:
`logs/remastered-ui/seedvr-all-sprites-20260930/` baseline-first original1.0
capture reused; restoredtrue/source_changes=[]; talisman clicks/Grimoire return
verified. Further raster batches/wholeUI visual acceptance remain in progress.
Cleanup plan `assets/hd/seedvr2-ui-1.1/cleanup-plan.json` lists old workingpack,
reviewmedia and pageicon derivative, hash-gated after full production install.
Preserve retained provenance, source-original, formalruntime/release backups,
modelweights and test evidence. SeedVR2 currentproductionroot excluded.

Production checkpoint:16 regenerated SPR containers contain780frames. Saved-file
audit tools/audit_seedvr_ui_11.py verifies actual encoded codec, exact colour-key
coverage, geometry, sprite alpha, native UI margins and original/rollback/runtime
hashes, not only pre-encode pixels. First87installed files passed. Prioritize
frequent backgrounds/maps after resuming the same owned Manager job; no duplicate
inference created. Core background regression seedvr-background-core-20260930
passes7screens, native UI fonts64/44/30 and battle32/22/15, source_changes=[],
restoredtrue/cleanup_errors=[], minimap16349pixels exact match1.0.

New SeedVR2 backgrounds additionally pass12Portmanteau states/actions and6loaded
Realm states/actions in seedvr-background-port-20260930 and
seedvr-background-realm-20260930; source_changes=[], restoredtrue,
cleanup_errors=[]. Paired1.0 captures retain exact package/save/hash identities.
Visual quality remains user acceptance, beyond these structural/input gates.

New-game5-state background comparison also passes in
logs/remastered-ui/seedvr-background-newgame-20260930/. Together these cover30
paired screenshots/actions across4flows (7core,12Portmanteau,6Realm,5newgame).
These runs overlap generation with the install lock and restore mutable state.

User correction (later2026-09-30): prefer previous Qwen/FullReadable RealmViewer
maps over SeedVR2. Restored all3Celtic/Greek/Medieval PNGs exactly from pre-art
backup hashes. Approved retained copies:seedvr2-ui-1.1/approved-qwen-maps/.
Productionplan retains explicit artwork_exceptions/approved_source hashes;280UI
files follow SeedVR2/procedural policy and3maps retain previous artwork. Cleanup
protects approved copies. SeedVR2 alternatives retained only as rollback/review.
Restore tool:tools/restore_qwen_maps_11.py; snapshot backup
backups/remastered-1.1-qwen-map-restore/. This supersedes earlier all-map model
selection; future rebuild must preserve explicit map exceptions.

Preferred Qwen maps + SeedVR2 UI pass6-state Realm regression in
qwen-maps-seedvr-ui-final-20260930; allbook backgrounds +12Portmanteau states
passseedvr-final-book-port-20260930. Saved-file audit detected1additional
colour-key-threshold pixel after JPEG encoding in MultiplayerBattleLoad;
repair_seedvr_jpeg_11.py retains exact pre-repairbytes and fixes decoded mask.
Producer now verifies decoded JPEG keys before install, guarding only changed
threshold pixels (quality100,subsampling0); fail rather than install a mismatch.

Completed production/install/retirement checkpoint:
-289/289Manager jobs complete;283/283planned files installed;16SPR/780frames.
-3Realm maps restored byte-exact priorQwen/FullReadable by lateruser correction;
  4tinybars procedural;276remainingfiles regeneratedSeedVR2.
-Final saved-media audit283/283passes:codec,dimensions,alpha,keys,margins,hashes.
-Final core7states passseedvr-final-package-core-20260930; minimap16349pixels
  exact1.0match; camera clicks unchanged; source_changes=[], restoredtrue,
  cleanup_errors=[]. Final book12states and restoredmap6states also pass.
-Cleanup applied2961files/3691768631bytes (~3.44GiB); retained576provenance
  records plus originals/formalreleases/rollback/evidence/modelweights/approved
  Qwenmaps. Per-filehash deletion journal:seedvr2-ui-1.1/cleanup-plan.json.
-Candidate manifest0968e8c2e2447801dd9e5dcba7c6ed411d867fb874e4575b54625142982ab241;
  5830runtimefiles verified, protectedv38/1.0unchanged. Engine/modules unchanged
  by this art replacement. Startplaytests/remastered-1.1-p1/MagicMayhem-Remastered-1.1.exe.
-Rollback:tools/seedvr_ui_11.py rollback restores pre-artbytes from
  backups/remastered-1.1-seedvr-ui/. Unknownfilehashes refused.
-Visualacceptance still userpending; uncoveredpages/multiplayergameplay are not
  accepted merely by saved-fileaudit. Future1K/2K/4Kswitching remainsplanned.

2026-09-30 user reports normal mouse disappears beyond upper-left area on all UI
menus; battle normal. Located ten verified cursor backing/dirty/restore/clip
immediates retaining1120/600 plus native160/120 ->1280x720. Runtime module
expands only these to2400/1320 ->2560x1440 fullprimary; battle wrapper input
remains1280x720 scaled2. Built remastered-1.1-cursor-full and installed via
tools/install_11_cursor_full.py with previousmodule hash0ece558e..., identical
resource101, unchanged engine/assets,5830file integrity and protected1.0/v38
checks. Backupbackups/remastered-1.1-cursor-full; rollback same tool rollback.
Runtime acceptance pending user testing; no gameplay run per project checkpoint.
Outstanding ordered fixes: (2)Grimoire wrong page/cover layering shown in user
screenshot; prior structural tests did not establish visual correctness.
(3)Realm selected/highlight regions must derive from approvedQwen/FullReadable
map pixels using original regionmask and nativeoffsets, preserve edge treatment
and originalhighlight semantics. No independentlygenerated regional art; exact
texture alignment with approvedmap is required. User explicitly requests this
correction. Continue after cursor testing checkpoint.

2026-09-30 user confirmed cursor fixed. Next orderedGrimoirefix installed:
loader originally hookedonly4c532f(backdrop BMP), leaving4c5380(backdrop JPEG),
4c574c(page JPEG first),4c575c(page BMP fallback) to inconsistent oldresources.
Newscoped png_grimoire.cpp hooksall4exactcalltargets, prefersPNG siblings for
BMP/PNG/JPG requests and retains nativefallthrough. PNGBackdrop sibling added
from SeedVR2 losslessmaster, avoiding missingBMP path/oldJPEG page selection.
190pages rebuilt:content960x1440 oncanvas1280x1440, leftorigin320/rightorigin0;
prior generation wronglystretched400x600source into1280x1440canvas. Existing
colour-key footprint preserved byteexact; models not rerun.
Actualx86 WIC/GDIpaint190/190 RGBexact, BMP/PNG/JPG aliases and failure/fallback
cases passed without game launch;installed5831files hashverified,protected
v38/1.0 unchanged and cursorfix retained. tools/build_11_grimoire_loader.py and
tools/install_11_grimoire_loader.py; backupbackups/remastered-1.1-grimoire-load/
includes pre-fix assets,module,launcher,manifest,productionplan. rollback same
installer rollback. Grimoire visual/runtime acceptance pendinguser playtest.
Useralso authorizedparallel subagent to comparecreature animationsequences
acrossavailable localmodels viaManager; isolated reviewonly,no runtimeinstall.
Mapselected-state fix remainsnextorderedUI work afterGrimoirecheckpoint.

### test16 campaign UI audit — 2026-10-01, fix pending

User explicitly authorizes test16 background debugging. Reproduction evidence
is in `logs/remastered-ui/test16-ui-before-20261001/`; the scoped runner is
`tools/probe_test16_ui_11.py`. Character, victory/experience, campaign Esc menu
and tutorial panels retain baseline geometry despite UI fonts being 64/44/30.
Global toolbar tooltip placement is already scaled and must not be confused
with the separate tutorial panel.

Victory confirmation is configured, not an unidentified hardcoded button:
`Interface/BattleEnd/screen (Battle End - Victory).cfg` TEXTBUTTON_1 has
Rect2=550,654,730,708, matching the captured control exactly. The Defeat cfg
uses the same rectangle. Their text rectangles also remain baseline-sized.
Keep their complete configuration/background/backing-surface transforms
together. Character backing immediates at 4b4452/4b4465 still use 1120/600;
BattleEnd at 473de2/473df5 uses the same dimensions, with interaction bounds
at 473e38/473e51 using 1119/599. These observations are not installed fixes.

Realm and Character tutorial cfg files contain speechBoxNum selections and
dialogue text, not panel geometry; follow the selected shared speech renderer.
MiniMenu is shared with battle, so campaign scaling must be mode-scoped.
Stale battle controls remain in the global table after transition; scaling
every registered control indiscriminately would corrupt battle behavior.

### Campaign UI installed checkpoint — 2026-10-01

tools/build_11_campaign_ui.py stages/builds/installs/rolls back the isolated
candidate. hd11/campaign_ui.cpp checks20sites against42f2aac7... engine;
disk engine/resource101/cursor/Grimoire/minimap/QoL/pathfinding retained.
16configuration/art corrections+8UI-only variants:Character/BattleEnd backing,
fourpageRect2,character sprites/bars/portrait,backgrounds,campaignMiniMenu.
Full backgrounds resize model output to1920x1440 then paste at320 on2560x1440;
stretching to2560 and cropping margins cut off decorative borders.
Title bypasses cfg via table5da230(50,36,749,76), now(440,86,2118,182).

MiniMenu scales fresh owner records only, choosing separate hd-ui background.
Campaign speech boxes1..3 temporarily scale local table data and load7SeedVR2
UI-only assets, then restore the shared table. Battle/dynamic/world speech and
original speechbox.cfg unchanged. PNG export @mm_png_page@12 resolves lazily
because launcher injects png_pages afterQoL. Production recipe now records
derivative_override hashes/scale-aware audit; Grimoire honors page_origin.
Actual manifest casing isSpeechBox. Release PE mappings before launcher
replacement; installer collects abandoned mappings and keeps backups.

Evidence:logs/remastered-ui/test16-ui-baseline-pair-20261001/ and
test16-ui-campaign-final-20261001/. Same fixture SHA-256
10048ef90dd4bee66a5bd688aa0015883c84eacc5430b1e5a6aa96d0e6bd1399.
verify_campaign_ui_11.py passes1confirmation/5menu/12character rectangles2x,
fonts64/44/30,output2560x1440,margins excluding cursor. Plus changes7439pixels,
experiencefield1392;minus restoresfield exactly.4tutorialclicks/Esc return pass.
Mutable state restored,cleanup_errors=[];art audit283/283;runtime5839files;
v38/1.0protected unchanged. User acceptance/battle gameplay/otherpages pending.
Rollback:python modernization/tools/build_11_campaign_ui.py rollback.
Backup:backups/remastered-1.1-campaign-ui/. Entry unchanged.
Remaining:broadercampaign/region-entry audit,Qwenmaphighlights,Portmanteaudrag.

## Approved-map region states — 2026-10-01

User requested deriving all hover states from approved Qwen maps, original
region masks and edge treatment, explicitly authorizing test17 Forest of Pain.
Installed 41 deterministic PNG derivatives: Celtic10, Greek14, Medieval17.
Maps are byte-exact approved-qwen-maps copies; PCX borders and semantic hit
masks remain unchanged. Each 800x600 original border's blue-key complement is
projected to 1920x1440 at x320, with Lanczos coverage. Region RGB derives only
from the installed Qwen map: 1.10 gain plus [3,4,0], masked coverage blend,
and an inward yellow-green rim mixed with the same map pixels. Outside coverage
is byte-exact base RGB. No inference and no independently generated terrain.
The blended full-size PNG bakes antialiasing against the actual base, avoiding
blue key contamination and bright/dark seams. Original region contours retained.

Existing hash-gated highlight hook 0x551360 now also retains owner ESI. Native
owner+0x12 supplies Celtic/Greek/Medieval, EDI supplies 1-based region ID.
draw_projected_highlight delegates to qwen_highlight.cpp for the projected
native destination rectangle. A single cached 2560x1440 surface is loaded using
png_pages and replaced/released on region/world changes. Source rectangle equals
destination rectangle, with SRCCOPY, no secondary scaling. Original native path
remains fallback if a verified derivative cannot load. Engine/resource101 and
all prior cursor, mixed render, minimap, campaign, drag, cover and modal fixes
preserved. No battle behavior changed. Assets are UI-only hd-selected siblings.

test17-highlight-before/final paired captures at full output pass: Forest of
Pain hover at native1800,1100, center/edge samples and mouse departure. Forest
ROI [1550,960,1700,1080] matches derivative within RGB565 max7/MAE2.817, versus
previous MAE35.314. Unhover ROI matches prior original exactly. All41 asset
hash/mask/provenance checks pass; mutable state restored and no cleanup errors.
5882-file integrity passes, protected 1.0/v38 unchanged. Greek/Medieval visual
acceptance remains with user; no live claim for those realms.

Generator/installer/rollback: tools/build_11_qwen_highlight.py; verifier
tools/verify_11_qwen_highlight.py. Build recipe records base map/mask hashes in
build/remastered-1.1-qwen-highlight/verification.json and package manifest.
Keep these overrides during future art regeneration; never queue regional
selected-state textures for independent diffusion. Backup at
backups/remastered-1.1-qwen-highlight; rollback requires closed game and checks
installed hashes. Test output logs/remastered-ui/test17-highlight-final.


## Exit confirmation modal — 2026-10-01

Installed isolated 1.1 common-modal adapter; user explicitly authorized test17.
The same save SHA d105e98fc2995d34a5ac2072fcbf54787e126ebf64e2ffcacf7fdaaa9701613a
was used for cloned 1.0 baseline and current 1.1 background captures.
Native setup 0x4cf3b0 (checked entry 6aff68c21c5c00) still centered the
416x280 dialog in the old 1280x720 design and registered an 800x600 modal.
Scoped bitmap calls 0x4cf45e and 0x4cf491 now select an independent UI-only
832x560 PNG sibling. This bitmap has no SeedVR job in the approved pack;
the geometry derivative uses Lanczos on the original, not new AI artwork.
The shared original remains for battle. Layout computes modal origin from
layout_context content rectangle, producing (864,440) on 2560x1440 output.
Text bounds, margins, button padding and hit rectangles follow UI scale.
Existing registered controls receive direct packed RECT updates: the native
RECT setter also registers controls and would duplicate table entries here.

test17-exit-final-v3 passes No cancellation, reopening and Yes returning to
the menu, exactly two modal buttons, centered backing and full modal bounds.
Buttons [924,876,1088,940] and [1472,876,1636,940]; text area
[924,500,1636,816]. Captures are full output resolution. Mutable files restored,
cleanup_errors=[],timed_out=false. 5841-file final integrity and protected
1.0/v38 checks pass. No battle run; broader shared-modal acceptance remains.
Evidence: logs/remastered-ui/test17-exit-{before,baseline,final-v3}.
Build tools/build_11_confirm_dialog.py; rollback action restores the prior
book-opening/drag candidate using backups/remastered-1.1-confirm-dialog.
The game must be closed and installed hashes must match. The 11 missing static
CFG sources detected before this run were restored from byte-exact trusted
copies matching the current package manifest before launching diagnostics.

## Drag restoration and initial book cover — 2026-10-01


User screenshots show persistent Portmanteau drag trails and an undersized
initial closed book. Installed fixes in isolated remastered-1.1-p1 only;
runtime acceptance remains pending user testing. No gameplay launched this iteration.

Hash-gated engine remains 42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.
Native Portmanteau draw 0x576830 reads width table 0x5c774c and height
0x5c7754, indexed by owner+0x24c. Values [83,66,83,66] were still original
while the 23 mitems frames had already doubled. port_drag.cpp wraps the checked
six-byte entry (81ec00020000), scales these constants using layout_context only
during an independent UI draw, and restores them afterward. Battle keeps its
original geometry. The table is in read-only .rdata and receives explicit
VirtualProtect before scoped writes. Offline production-wrapper execution
passed 200 UI/battle calls, verifying bounds and exact restoration. This fixes
the native dirty rectangle rather than reloading the background each frame.

The opening path at 0x4c3d7e (JPEG), fallback 0x4c3dcc (BMP), bypassed the
four existing PNG page hooks. ClosedBook.JPG remained 1280x720. Added PNG-first
coverage for both calls and a ClosedBook.PNG derivative of the existing
hash-verified SeedVR model result: resize content to 1920x1440, place x320 on
2560x1440 black canvas. Existing page surfaces already use 1280x1440 halves.
The original JPEG is preserved for fallback; the explicit PNG is authoritative.
No new model job. Pixel-exact WIC/GDI paint and BMP/PNG/JPG aliases passed at
full 2560x1440, including error/fallback and fastcall checks. Embedded resources
101/102 are unchanged by the cover update, preserving the installed drag fix.
Candidate integrity passes 5840 runtime files; protected formal v38/1.0 intact.

Build/install evidence: modernization/build/remastered-1.1-port-drag and
modernization/build/remastered-1.1-book-open. Backups use the same names beneath
modernization/backups. Roll back book first with tools/build_11_book_open.py
rollback, then optionally drag with tools/build_11_ui_repaint.py rollback.
Both require a closed game and check installed hashes before restoring.
Future resolution adaptations must include transient/dirty drawing bounds and
page-opening assets, not just steady-state controls and backgrounds. The cover
PNG is a separate installed derivative recorded in the package manifest; art
regeneration must retain or reconstruct it using build_11_book_open.py geometry.
# 2026-10-01: Minimap click-center checkpoint

## Window close lifecycle checkpoint — 2026-10-01

User accepted test18 path fix and requested next queued Alt+F4 correction.
Static current-engine evidence (SHA256
42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da,
image base0x400000): WndProc0x4e9d60 dispatches WM_DESTROY to0x4e9dd6, cleaning
input0x534b60/0x4a37d0, audio0x58acf0/0x535970, graphics0x463d40 and other owners,
then posts WM_QUIT at0x4e9e9a. Alt+F4 disk shim0x5c4259 instead calls
PostQuitMessage at0x5c4273 and returns into key handling. Main message pump
0x557370 has disk shim0x5c4294 catching WM_NCLBUTTONDOWN/HTCLOSE and also posts
quit instead of dispatching the original message. Thus both shortcuts bypass
native window destruction. This is verified control-flow evidence, not runtime
proof of which cleanup component caused the reported hang.

New runtime/hd11/window_close.cpp patches only two hash/signature-gated shim
spans: 5c4271 length7 (`6a00e89834fdff`) and5c4294 length8
(`817c2414a1000000`). Alt handler enters with prior pushfd/pushad, loads HWND
fromESP+0x70, uses existing PostMessageA IAT0x5c5270 to queue WM_CLOSE, restores
registers/flags and returns through native epilogue0x4ea124. Queuing avoids
destroying a scene while its key callback is still running. Native WM_CLOSE
DefWindowProc/WM_DESTROY cleanup retained; no ExitProcess/TerminateProcess workaround.
Title shim rejoins original TranslateMessage/DispatchMessage at5c42b1.
Other system keys and ordinary exit handling unchanged.

Tools/build_11_window_close.py copies exact installed resource102 sources from
minimap-center, adds this module; resource101 is byte-identical installed corridor
DLL. Known engine/launcher/module identities checked before build/install.
12 offline Unicorn cases execute native WndProc and compiled adapter, stub Win32
API boundaries: old-vs-new quit/close events, two HWNDs, stack/nonvolatile
registers, F4-withoutAlt and other keys, original close/destroy branch, title and
ordinary message dispatch. Actual Windows cleanup, GPU/audio teardown and
reported hanging process were not reproduced; actual exit acceptance pending user.
Report: build/remastered-1.1-window-close/verification.json.
Installed resource102 SHA256:
c8d5b7fcb2452eabbcb25758e39bd466a7d99d9859f7065bf717ef163ef4280b.

5882 runtime hashes pass; no engine/assets/saves/config changes; formal1.0/v38
protected. No gameplay/visual acceptance launch in this iteration. Test Alt+F4
from battle and main menu, then verify both launcher/engine disappear and relaunch
works. Stop for user feedback. Backup:
modernization/backups/remastered-1.1-window-close.
Rollback after game closes from project root:
`C:/Python314/python.exe modernization/tools/build_11_window_close.py rollback`.

Roof display persistence in saves remains a separate recorded TODO; not implemented.

Installed isolated 1.1 correction, pending user gameplay acceptance. Engine
SHA256 remains 42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.
No formal v38/1.0 files changed; no game launched for this iteration.

Static evidence: native thiscall scanner handler 0x555ec0 reads main+0xeb at
0x555f1d (bytes 8b ab eb 00 00 00), then subtracts that value from logical click
x at 0x555f23. Main+0xeb aliases secondary+0xca, the physical storage width.
Drawing origin/registered RECT already use logical battle width through hooks
0x5548fb, 0x554b06, 0x555b90. Thus the old inverse used 2560 where drawing used
1280. The new six-byte checked detour loads scanner_layout_width into EBP,
returns to 0x555f23, and leaves the original native rotation/world mapping and
camera call intact. Logical width comes from layout_context's battle profile.

build/remastered-1.1-minimap-center copies the exact installed Qwen-highlight
resource102 source chain, including modal/drag/book support; resource101 is
byte-identical. Tools/build_11_minimap_center.py hash-gates engine, installed
resource102 and pre-install launcher/manifest. Transactional install preserves
runtime assets, saves and configuration. Backup:
modernization/backups/remastered-1.1-minimap-center.

Offline Unicorn execution of compiled adapter plus native click inverse: 252
cases across 4 rotations, 3 logical widths, 3 physical widths and 7 points match
the original logical-width reference including flags/registers/stack. Old code
differs in 196 cases. Physical width field remains untouched. Existing 27 scanner
layout and 88 tooltip/sprite tests also pass. Report:
build/remastered-1.1-minimap-center/center-verification.json.
These checks verify the inverse-coordinate correction, not live camera-center
visual acceptance. Installed integrity: 5882 runtime files; protected v38/1.0
unchanged. User should check multiple minimap points and map rotations.

Rollback from project root after closing game:
`C:/Python314/python.exe modernization/tools/build_11_minimap_center.py rollback`.
Queued separately: test18 portal-path detour, then Alt+F4 unresponsive exit.

## Wrapper close policy follow-up (2026-10-01)

User reports the first engine-only window-close patch still hangs. The wrapper
source routes WM_SYSKEYDOWN/VK_F4 through DefWindowProc, then handles SC_CLOSE
with ExitProcess when game_handles_close=false. That bypasses native window
destruction/resource cleanup covered by the first correction. Source inspection
is a lead; the active wrapper is established by package hashes and the following
owned runtime comparison, not an assumption that temporary source matches it.

probe_11_close_wait.py now enumerates threads with Toolhelp instead of a slow
PowerShell query vulnerable to process-exit races. Read-only Windows wait-chain
snapshots after SC_CLOSE show one remaining thread; no cycle is reported. They
do not identify a particular DLL/lock as the root cause. Old config remains alive
after8.10s (exit-system-before-v2); harness stops only its owned engine and restores
mutable files. With game_handles_close=true, SC_CLOSE exits engine and launcher
in0.96s (exit-system-game-close-v1); synthetic WM_SYSKEYDOWN/VK_F4, Alt context
bit set, exits in1.03s (exit-altf4-game-close-v1). All diagnostic mutable files
restore successfully. These are menu close diagnostics, not physical keyboard,
battle, repeated-load or general gameplay acceptance.

build_11_wrapper_close.py stages and transactionally installs only the global
ddraw.ini game_handles_close setting in the isolated1.1 candidate. It refuses an
engine-specific INI section, pins the installed launcher, checks engine/wrapper,
and preserves every other runtime byte. Installed:5882 integrity entries pass;
launcher/resource101/resource102 unchanged, formal1.0/v38 protected unchanged.
No binary rebuild is necessary for this configuration correction. Backup:
modernization/backups/remastered-1.1-wrapper-close; stage/evidence:
modernization/build/remastered-1.1-wrapper-close/build-state.json.

Rollback after closing the game:
`C:/Python314/python.exe modernization/tools/build_11_wrapper_close.py rollback`.
Stop for user battle/Alt+F4 feedback after installation, per project checkpoint.
Queued separately in user order: test18 left-click healing on second teammate
portrait, then intermittent save-load hangs (first fails, subsequent attempt works).


## Chapter portal hover vortex restored, 2026-10-01

The original selected PCX for Celtic09, Greek13/14 and Medieval17 contains
vortex pixels, not ordinary selected terrain. The Qwen region generator used
only non-blue coverage and discarded its RGB artwork, producing an empty tinted
ellipse. Flags and hover hit testing were already working. This is authored
static selection artwork; no new animation or regenerated portal is invented.

`realm_portal_art.py` now composites the original colour-keyed art onto the
approved Qwen map, resizing RGBA in premultiplied space to avoid keyed-blue
fringes. Content is 1920x1440, centered at x320 in the 2560x1440 canvas. Pixels
outside alpha coverage are exactly equal to the approved map. The ordinary
terrain selection generator has the same portal exception for future rebuilds.
Four portal PNGs and the manifest were transactionally installed; engine,
launcher, DLL resources, base maps and ordinary region derivatives are unchanged.
Sources match the immutable 1.0 PCX hashes. All 5882 runtime files verify and
protected 1.0/v38 remain unchanged.

Authorized background test19 comparison before installation:
`logs/remastered-ui/portal-test19-1790802280842061100/`.
Both runs read hover region 9, then region 0 after moving away. Of 18,515 changed
portal pixels, 86.17% match the intended composite within RGB565 max error7;
remaining pixels include overlapping animated flag, cursor and tooltip. Mean
RGB difference from intended art fell from79.08 to15.68. `portal-pair.png` shows
empty outline before versus restored vortex after. Temporary asset staging was
restored and hash checked before installation. Other three portals passed asset
checks but were not exercised in-game. Installed acceptance awaits the user;
no gameplay run after installation.

Build/install/rollback: `tools/build_11_portal_highlight.py`.
Backup: `backups/remastered-1.1-portal-highlight/`.
User paused test19-to-test18 load-hang investigation after non-reproduction;
this asset fix does not resolve or claim to resolve that separate issue.


## Retained test18 failure: fatal AV followed by OGG teardown polling, 2026-10-01

User explicitly requested analyzing a live stuck test18 process. No gameplay,
input, suspension call, remote memory write, injection or termination performed.
Engine disk hash matched42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da;
loaded OGG proxy disk hash matched installed manifest:
7f6e9ad1580c3fc85bace977882e0100e65173bb3b3aa0294f24cf9508d8cccb.

`logs/remastered-ui/live-test18-hang-20261001-p2004/` holds native64 and native32
minidumps, parsed x86 stack, repeated shutdown state and findings. The64-bit
DbgHelp dump captured WOW64 compatibility context; added x86 dump helper obtains
real x86 EIP/ESP. This distinction is essential for future32-bit engine failures.
The read-only helper is `tools/hang_dump_x86.cpp`; verify engine identity in the
caller, then pass PID/exact engine path/new dump filename. It never terminates.

Frame index stayed23, mode1, controls53, units37. Only one thread remained.
The x86 EBP chain passes through the OGG proxy detach path, ntdll loader shutdown
and CRT exception exit. Retained CRT exception-exit argument is0xc0000005
(stack1afefc, return59e715 from exit at59e710). RtlDllShutdownInProgress's live
boolean was1 in three samples. Thus the process had already suffered an access
violation and was shutting down; frozen load UI is the last presented frame.
Do not describe this as an ongoing save parser waiting for completion.

At proxyRVA4c70, the code invokes Sleep(1), then checks byteRVA5b09c and loops
while nonzero. The live byte remained1. Before this loop it signals SetEvent.
Current main thread EIP is in ntdll's delay syscall with OGG returnRVA4c7d.
The proxy is waiting for worker-side cleanup, but the process has only the
shutdown thread left. WCT reports no lock cycle because this is flag polling.
This provides concrete evidence for a secondary exit hang. It is also a candidate
mechanism for prior Alt+F4 reports, but those sessions were not captured here.

The original AV instruction and fault address have not been recovered. The
saved CRT EXCEPTION_POINTERS slot at1aeb1c was overwritten by teardown frames;
`original-exception.json` is explicitly marked invalid. Residual VirtualAlloc/
allocator return values in stack memory are stale candidates, not proof of the
original fault site. Do not patch the allocator based on those words.

Next capture first-chance AV before CRT unwinding on a future load, then fix its
specific cause. Independently correct shutdown polling while preserving normal
music stop and dynamic-unload semantics. No fix installed and no game closed
in this diagnostic session; all current runtime bytes retained.

Subsequent save14 reproduction on2026-10-01 captured the first fault at58b40b:
native surface Destroy dereferences a missing+4 base interface while+8 is live.
The exact-byte-gated partial-interface release guard is now installed, with six
owned operation/reload cycles passing and installed user acceptance pending.
See docs/launcher-architecture.md "Save14 repeat-load access violation" for
current module hashes, evidence, limitations and rollback. Independent OGG
teardown polling is still not marked fixed; earlier evidence above is historical.
# Portmanteau top preview owner recreation — 2026-10-01

## Later formal release scanner regression and HUD audit

User requested save10 debugging. Latest formal resource102 lacked the prior
scanner_click_width_hook, although draw/layout/refresh width fixes remained.
Authoritative runtime/hd11/mixed_ui_fonts.cpp also lacked this patch, so copying
that file into later builds silently removed it. Restore checked555f1d detour
to authoritative source; build_11_minimap_release.py starts from latest
port-preview module sources and AI diagnostic launcher/resource103.

Module102 SHA367ab2a1f22546aff64d38d19afc42c21ae5373ecefbdb9266412f3f5b4c5244.
252 native inverse checks,27 compiled scanner draw cases,324 preview recreation
cases pass. Verifier also requires signature check and patch installation in
production source, protecting against a detached-hook-only test.

Formal launcher clears MM_PROBE_BACKGROUND_INPUT by design; initial bounded
probe failed handshake and restored all mutable lab files. Subsequent owned
probe used identical formal engine/assets plus paired candidate launcher;
all101/102/103 resources compared byte-identical before testing. Evidence:
logs/remastered-ui/save10-minimap-before-diagnostic-20261001/result.json and
save10-minimap-fixed-20261001/result.json. Save10 minimap rect is
(1072,6)-(1272,106), storage2560,rotation0. All four pre-fix clicks mismatched
the original native logical-width camera mapping, all four fixed clicks matched.
Center(1172,56): expected(39,98), old(99,38), fixed(39,98).
Reference emulates native inverse/world wrap using live map/camera data and
1280 logical width; game memory is sampled read-only. No player save changed.
Owned engines stopped and isolated mutable files restored.

Installed formal/frozen/candidate; rollback:
tools/build_11_minimap_release.py rollback, backup:
backups/remastered-1.1-minimap-release.5105 static files verified. Ordinary
Release acceptance remains pending user testing.

HUD audit: battle native loader4d5e74 loads Sprites/SplIcons.spr into
HUD+18a4. Active SplIcons SHAea65414ca05b282c5b7fba3c05be469183d0406797b34d9c2cfb64231ff12fa8:
only frames0–2 differ from immutable originals (80x80 versus40x40 colour circles);
frames3–233 have identical raw frame payloads. Approved SeedVR port-icons.spr
is selected only on independent Portmanteau pages. Native portrait loader4d30e0
selects Bitmaps/Cornelius Young/Middle/Old.bmp; PNG loader resolves siblings.
All three PNGs have identical RGB pixels and164x80 geometry to originals;
Ariadne/Lancelot/Lucan/Percival/Twigkindle/UndeadLucan faces are similarly original
97x48 pixels. PNG conversion and2x battle presentation do not constitute native
HD HUD assets. This audit does not authorize changing battle's1280x720 contract.

User screenshot shows small spell previews at the top of the HD page. Existing
paired capture `logs/remastered-ui/port-before-20260930/1.1/capture.json`
identifies these as regular Sprite controls (vtable5c77bc), rectangles
(1292,52)-(1386,156), (1456,52)-(1548,156), (1618,52)-(1712,156),
not the page's SpriteBar controls. They qualify for the existing80px gate.
Native draw5790e0 (entry83ec145355568bf157), on engine SHA
42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da,
reads owner Sprite pointer at+55 and base/state/overlay frames+59 through+6d.

Adapter defect: once original_icon_sprite is cached, subsequent draws accept
only that exact owner address. Returning to the page can recreate objects and
therefore skip HD substitution. Cache approved port-icons.spr pixels only;
validate current owner (SPR,234frames,unpaletted) on every qualifying draw and
refresh its metadata before temporary substitution, restoring its pointer
afterward. Positions, hit bounds and existing frame/state logic are unchanged.
Do not globally enlarge shared battle SplIcons. No new model generation.

`tools/build_11_port_preview.py` installs formal/frozen/candidate with backup and
hash-checked rollback.324 compiled x86 regression cases pass, including repeated
owner changes, all relevant preview families, source/page/battle exclusions,
pointer restoration and stack balance. Resource101 and AI resource103 retained
byte for byte; formal5105-file verification passes. No gameplay launched;
user visual acceptance remains pending, including reopening the page and
switching previewed items. Evidence is static/offline, not a new runtime capture.

# CharacterScreen talisman SpriteBar clipping — 2026-10-01

Formal save2 reproduction in `logs/remastered-ui/character-icons-before-v2`
confirms valid generated SPR frames0..5 (80x82..86) are missing from all three
character rows. Native SpriteBar draw4dd6c0 calls57dc60 at4dd718 to install
the legacy clip width/height1280x720, while character rows already start at
y876/996/1116. Engine identity remains42f2aac7 (full hash in current manifests).
`runtime/hd11/campaign_ui.cpp` now gates that exact call and delegates through
a UI-only clipping adapter using destination6a49e0's +10width/+14height.
Native battle retains its existing clip arguments. No sprite art/config changes.

New module build/source `build/remastered-1.1-character-icons`, based exactly on
the latest surface-lifecycle module with one campaign adapter delta. It preserves
portable wrapper, terrain, FMV, current exit fix and all prior UI/input behavior.
Isolated after capture restores2law/1neutral/1chaos visible talismans; three row
changed-pixel counts10264/5864/5560. Control rectangles remain identical. This
is actual save2 page evidence, not only a geometry smoke test. Source player
save/config remain unchanged; owned test processes stopped and mutable state
restored. Installed gameplay acceptance pending user feedback.

Installer `tools/build_11_character_icons.py` updates formal/frozen/candidate
launchers and manifests with transactional backup; rollback subcommand restores
all six files from `backups/remastered-1.1-character-icons`. Future launcher
rebuilds must preserve this latest embedded module instead of the older FMV or
surface-lifecycle module. User's next requested item is a slight reduction of
character opacity when occluded, scheduled after this fix's user checkpoint.

# Battle HUD artwork at output resolution — 2026-10-01

Installed first HUD artwork batch in formal Remastered1.1, frozen release and
continuing candidate. The battle scene and native HUD controls remain1280x720;
the existing wrapper scales them2x and then draws HD artwork at2560x1440.
This does not expand the battle viewport or change native click bounds/fonts.
Independent UI pages retain native1920x1440. Preserve this wrapper addition
when rebuilding later releases; embedded engine/modules were not changed.

Portrait atlases were generated through LocalModelManager with SeedVR2 7B
Sharp;19 PNG portrait sheets retained as masters. Spell art reuses the approved
SeedVR port-icons derivative. Original low-resolution sources and exact colour
key masks remain authoritative for identification and coverage. Production
`Sprites/battle-hud.bin` contains242 templates: main normal/dead portraits,
teammates, spell artwork and main portrait face cores. It is an output overlay
pack, not a replacement for the shared native SplIcons sprite sheet.

`runtime/hd11/hud_overlay_core.h` and `wrapper-probe/mm_battle_hud.h` match
original RGB565 pixels inside known HUD controls and paint only corresponding
opaque output pixels. Full icons require complete opaque-template equality;
source-equal guards preserve cooldowns, labels and occlusion. Main health faces
use separate alive/dead row strips, a core excluding the native outer ring,
and verified horizontal offsets0/-1/+1 because native halves differ by1pixel.
Half and three-quarter dimming are supported. Unsupported effects and obscured
frames retain native pixels. Negative matches retry within500ms unless the
spell/state/rect changes; cached matches are revalidated. New dynamic meters,
HUD frames and other remaining artwork are outside this first installed batch.

`tools/build_battle_hud_assets_11.py` owns model inputs, PNG masters and packing;
`tools/build_11_battle_hud.py` adds only an include and output compositor call
to the exact latest portable wrapper. `tools/verify_11_battle_hud.py` verifies
source provenance, all726 pack/dim combinations and117 alive/dead split/offset
cases, including unchanged source pixels and bounds. Saved-frame native
fixture identifies10 icons/portraits; cached compositing measured about0.084ms
per frame, initial fixture lookup about22ms. These are offline fixture timings,
not a gameplay performance guarantee.

User-authorized isolated save10 capture:
`logs/remastered-ui/save10-battle-hud-1790844989068836500/run/capture.json`.
HD subpixel detail confirmed in main portrait, teammate and spell regions;
paired crops retained alongside capture. All4 minimap clicks match native
world-coordinate reference; battle font heights remain32/22/15. Owned child
stopped, mutable fixture state restored, player saves untouched. Runtime
verification is in `build/remastered-1.1-battle-hud/runtime-verification.json`.
Formal5106-file integrity verification passed after installation. Wider
gameplay/visual acceptance remains pending user feedback.

Transactional backup: `backups/remastered-1.1-battle-hud/rollback.json`.
Rollback: `C:/Python314/python.exe modernization/tools/build_11_battle_hud.py rollback`
(game must be stopped). It restores wrappers/manifests and removes only the
new overlay pack, retaining PNG masters and immutable sources.

# CharacterScreen pending stat preview atlas extents — 2026-10-01

User-authorized save12 captures reproduce a gray mana preview which stops
growing after7pixels. STATBAR Rect2 is840x48, but approved generated PNGs
`Mana Bar`, `Health Bar`, `Control Limit Bar` in800x600 each had size1400x40:
two horizontal states, each700x40. Native StatBar4dd9b0 uses control width
for value/preview length and imageWidth/2 as the gray source offset. At base
mana165/200, colored extent693 leaves only7gray columns before the old image
edge. Native blit clips subsequent preview increments against that edge.
This is a state-atlas dimension mismatch; no engine clip or progression fix
is required. Health/control would show the same truncation at higher values.

`tools/build_11_stat_preview.py` derives state extents from each authoritative
STATBAR Rect2, independently resizes approved color and gray halves, and
preserves exact nearest colour-key masks. All three PNGs now1680x48, two
states840x48. No model rerun, asset style change, cfg edit, engine/module or
HUD wrapper change. Future resolution/asset regeneration must normalize each
paired state to actual StatBar rectangle width/height, not multiply the old
atlas dimensions by a generic UI factor. Do not filter across state seams.
Immutable original BMPs and approved generation sources remain preserved.

`logs/remastered-ui/save12-stat-preview-{before,after}` record actual isolated
captures and canceled sequential point previews. `tools/verify_11_stat_preview.py`
matches screenshot RGB565 against source state pixels: before mana widths7/7/7;
after mana/health/control each21/42/63 for three additions, with unchanged
colored value extent. No increment leaves a gap. Full output2560x1440 and
native UI fonts64/44/30 retained.342363 legal value/preview source rectangles
stay within the normalized paired atlas. Owned child processes stopped,
mutable fixture restored and all previews canceled without saving points.

Installed formal/frozen/candidate with5106static-file validation. Exact hashes,
asset dimensions and pixel evidence: `build/remastered-1.1-stat-preview/verification.json`.
Backup: `backups/remastered-1.1-stat-preview/rollback.json`; rollback command
`C:/Python314/python.exe modernization/tools/build_11_stat_preview.py rollback`
requires stopped game and verified installed/backup hashes. Installed user
acceptance remains pending; stop before the next optimization.

## Talisman pending-point preview regression — 2026-10-01

Follow-up user concern tested using save12 in an isolated runtime. Talisman
SpriteBar4dd6c0 uses individual SPR frames rather than StatBar's paired bitmap
source regions, so it does not have the700/840 atlas-width failure. Six active
frames are three color/preview pairs with equal dimensions80x86/80x82/80x84.
Native pitch is frameWidth+1=81, giving7slots within the full UI clip already
fixed by campaign_ui.cpp. Existing spritebar clip fix must be retained.

`tools/probe_save12_talisman_preview.py` lowers only copied CharacterScreen
STEPS_COSTS coefficients to initial1/linear0/exponent0, keeping increment1;
no process-memory writes and no encrypted save edits. All three rows start
with2 colored icons, show1..5 full gray previews through total7, and stop at7
on the next click. Pixel evidence confirms each added slot>1000changed pixels,
unchanged original colored slots and untouched future slots. Five sequential
subtractions match the earlier addition states exactly; cancel/reopen restores
original rows. Formal save12 and configuration hashes remain unchanged.

Successful evidence:
`logs/remastered-ui/save12-talisman-preview-1790846907710481300/verification.json`.
Initial owned launch attempt exited during startup; its failed capture is
retained separately and is not counted as acceptance. The second bounded run
completed, stopped its owned engine and restored mutable files. No production
fix or runtime replacement was necessary for this follow-up.

## Battle scanner unit-marker anchors — 2026-10-01

Save14 reproduces missing unit marks despite correctly positioned terrain and
click inverse. Main scanner object689b80 has physical stride+eb=2560 while
native marker routines552f20/5532f0 compute +f7 layout anchor from that stride.
Captured +f7=2472 places marks outside logical battle1280x720, which is the
only source region composited. Terrain/background already uses separate
native layout hooks. Do not replace +eb globally: marker row addressing must
retain the actual2560pixel stride or writes go to wrong rows.

`runtime/hd11/mixed_ui_fonts.cpp` now adds two signature-checked six-byte
hooks552f29 and5532f9 replacing only EAX layout-width reads with battle profile
content_width. Their native continuations set +f7=1192 for80x80 maps and
retain +fb=6. Marker color, unit filtering, occupancy/visibility, rotation and
pixel writes remain native. Existing scanner click/terrain/refresh hooks stay
present. Resource102 rebuilt with this delta; embedded101/103, latest
half-stair terrain module, battle HUD pack/wrapper, art/config/saves retained.

`tools/build_11_minimap_units.py` builds from latest minimap module source with
latest half-stair launcher sources and preserves all unrelated files.54 actual
compiled hook cases cover layout widths/row strides/map extents;252 inverse
click cases,27layout/draw cases and324preview-recreation cases still pass.
`tools/probe_save14_minimap_units.py` captures owned isolated before/after:
`logs/remastered-ui/save14-minimap-units-{before,after}`. Read-only scanner
anchor2472->1192, stride2560unchanged. Visible red/yellow marker pixels0/0
before and16/224after, with same player fixture. Owned engines stopped,
fixture restored and full screenshots retained. This is real runtime evidence,
not solely hook emulation. Wider installed user acceptance remains pending.

Installed formal/frozen/candidate;5106static files verified. Provenance/hashes
in `build/remastered-1.1-minimap-units/verification.json`; backup in
`backups/remastered-1.1-minimap-units/rollback.json`. Stopped-game rollback:
`C:/Python314/python.exe modernization/tools/build_11_minimap_units.py rollback`.
Next requested item is dynamic-obstacle waiting/rerouting in save14; follow the
one-fix-per-user-feedback checkpoint before beginning that separate change.

## FullReadable second and third chapters (2026-10-02)

User requested Medieval and then Greek redraws in the accepted Celtic FullReadable style. Historical Greek/Medieval maps were conservative Qwen detail composites, not the accepted Celtic full redraw. Both new jobs used the exact Celtic `02-full-readable` settings: Qwen Image 2.1 via authenticated LocalModelManager, 40 steps, seed26093012, quality=quality, one output, prompt enhancement disabled, original800x600 map as reference. Only the chapter name and job nickname were changed. Manager jobs: Medieval `ed4b82ae6be64d318d06aad1684c4a8f`; Greek `74ab7c6c013d490dbc17ac2dd320bdb9`.

Raw2400x1792 output is normalized with Lanczos to1920x1440 (same approximately0.45% aspect adjustment as accepted Celtic), then pasted pixel-for-pixel at(320,0) in a black2560x1440 canvas. No residual texture mixing or sharpening. Generated terrain has clearer broad grass, rocks and settlements; landmark/road details can still change because text reference constraints are not a hard geometric guarantee. Runtime visual acceptance remains pending user testing.

Greek14 and Medieval17 selected states derive deterministically from their SAME new base map and immutable original blue-keyed PCX masks. Coverage uses Lanczos, gentle tint and inward antialiased rim. Pixels outside coverage remain byte-exact base; both black sidebars remain unchanged. Greek13/14 and Medieval17 preserve authored portal vortex art via premultiplied alpha compositing. Native masks, hit logic and program modules remain unchanged; Celtic remains unchanged.

Assets, owned-job provenance, verification, full-map/1:1 comparisons and interactive region preview: `assets/hd/fullreadable-realms-20261002/`. Generated by `tools/qwen_fullreadable_realms_11.py`; preview by `tools/preview_11_fullreadable_realms.py`. Installed to formal1.1, continuing candidate and release staging with hash-gated original asset/manifest checks, backups, post-write checks and unchanged launcher/engine/Celtic hashes. Production map copies updated in `assets/hd/seedvr2-ui-1.1/approved-qwen-maps/`; old maps retained in rollback backup.

Backup: `backups/remastered-1.1-fullreadable-realms-20261002/`. With game closed and no later conflicting changes, rollback:
`C:/Python314/python.exe modernization/tools/install_11_fullreadable_realms.py rollback`.
No gameplay launched. User performs acceptance.

## Global UI coverage audit (2026-10-02)

User requested checking all remaining UI that might have only resizing/sharpening rather than SeedVR2. `tools/audit_11_ui_coverage.py` enumerates all1,036 installed raster/SPR assets in Interface, Portraits, SpeechBox, Bitmaps and Sprites and checks every installed file against the release manifest. All1,036 manifest hashes match. Current artwork evidence:293 matching SeedVR2 outputs/derivatives,20 battle HUD source sheets with verified generated runtime overlay,3 approved Qwen maps,41 deterministic selected states,4 procedural thin-bar derivatives. No generation claim is made from size alone.

Remaining142 UI candidates lack matching model-output provenance after excluding640-resolution legacy variants, PNG-resolved sibling files, unchanged world effects and semantic masks. File-level original-pixel equality and CFG references are recorded; lack of provenance is distinct from proof of sharpening. Main gaps: ordinary dialogue portraits (80x100), additional dialogue boxes, battle border/control-limit/scanner/timer/cursor graphics, battlebuttons/markers/selection UI sprites, and unsupported Scrollbutt.spr. Eight page backgrounds have verified generated artwork but remain1280x720: EndGameSummary, HighScores, QuickBattleEnd and five multiplayer setup/load/select pages. These are geometry/resolution debt, not missing inference.

Common dialogue/scroll/border PNGs and confirmation hd-ui variant ARE SeedVR2-derived (common-ui plan supersedes historical Lanczos-only dialog installer). ClosedBook/Backdrop PNGs also derive from generated page tasks, not missing jobs. Thin bars should retain exact procedural geometry. Fonts require their own rendering/size checks rather than SeedVR processing. Full audit/report: `assets/hd/ui-coverage-20261002/{audit.json,REPORT.md}`. No runtime UI files changed by this audit. Next authorized task: terrain sprite拆解/SeedVR trial in isolated save22; retain1280x720 battle rendering and2x output.


## UI gap generation checkpoint (2026-10-02)

The coverage audit identified 142 unresolved candidates; the requested global audit is complete, while runtime loading evidence for these candidates remains incomplete. Optional follow-up generated 124 raster candidates through managed SeedVR2 7B Sharp: 84 portraits, 30 speechboxes and 10 bitmaps. Initial PCX/TGA jobs failed and were retried as PNG; two small bitmaps were padded for inference and cropped to their exact doubled sizes. All 124 candidate dimensions pass; original source files remain untouched. Owned jobs, source/output hashes and retry records are in `assets/hd/ui-seedvr2-gap-20261002/batch-plan.json`; full model results retained locally, not solely in expiring Manager output.

`tools/postprocess_ui_gap.py` creates candidate-runtime PNGs with original blue-key mask restored at nearest coverage. Accidental saturated-blue holes outside the mask are repaired from source colour. This threshold does not prove all blue fringe artefacts are removed; further edge inspection is required. The existing campaign_ui speech path only enables tutorial indices 0..2 in UI mode, so staging hd-ui files alone would not make the new 30 dialogue boxes or 84 portraits load. No runtime asset/module installation was made for this batch; do not label these UI candidates implemented or visually accepted.
