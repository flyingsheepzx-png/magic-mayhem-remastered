# UI layout adaptation and test14 speech repair — 2026-09-30

## Implemented: v37 spell tutorial anchor

The user reported the fixed mouse tutorial scroll pointing at empty ground in
test14. Reproduction requires loading test14 and clicking once through the
raven's centered dialogue. User explicitly authorized this gameplay debugging.
The wide asset builder had translated every speechbox.cfg BoxPos by (+240,+60),
including fixed tutorial box 4. Its origin (460,300) did not follow the battle
spell controls, which use their own right/bottom placement policy.

Installed v37 moves fixed box 4 only when exactly one live spell control is
enabled, using that control's real rectangle. No spell ID or translated text is
matched. Arrow-tip metadata (200,312) belongs to the existing 420x320 asset;
position it 8 native pixels above target top, horizontally centered, and clamp
the box to the native surface. In test14 the target is (984,670)-(1024,714),
giving box origin (804,350) and arrow tip (1004,662). Header, body, portrait,
embedded example icon and arrow are already composed into the same surface.
Changing its final origin moves them together without moving the real button.

`runtime/wide169/ui_layout.h` introduces a small native-coordinate anchor helper.
`render_replay_trial.cpp` hooks `0x57336d` after native origin assignment in
`0x572f30`, replaying `8b 0d d5 e6 6d 00`, then resuming at `0x573373`.
EBP is speech surface (controller+0xc), ESI is descriptor. Descriptor+0xc is
one-based box number, +0x30 fixed/dynamic flag. Surface+0x20/+0x24 are placement.
Native resource selection, internal text layout and click handling are unchanged.
Multiplayer, 640-mode, other box styles, dynamic/world speech and absent or
ambiguous target controls retain previous behavior. This is a focused fix,
not a claim that all speech types or all resolutions now adapt automatically.

Evidence engine SHA-256:
`43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`, preferred base
0x400000. Original/current instruction spans verified before build; runtime
signature checked before patch. Read-only Ghidra exports `00572870.c`,
`00572f30.c`, `00573990.c`, `00578db0.c` live under
`D:/Tools/magic-mayhem-re/projects/path-review-export/`.

Validation:
- 24 compiled hook cases in `tools/verify_speech_layout.py`: 800x600,
  1280x720, 1920x1080, 2560x1440 synthetic surfaces; anchor math, exclusions,
  registers, flags and stack. These validate the helper, not engine support
  for those native resolutions.
- Before: `logs/wide169/1790711319628589900/tutorial.png`.
- Installed final: `logs/wide169/1790712120923286500/` includes initial centered
  dialogue, corrected tutorial and `spell-clicked.png`. Clicking (1004,692)
  dismisses tutorial and yields targeting mode 2 / selected icon 1.
  `changed_protected: []`; original prefs/PlayFMV and save bytes restored.

Package `build/wide169/package-v37-speech-layout`.
Launcher `d97e73e8e4908d67c57602d67bc0c9d9b4f402b01c26b48368feeba00159c61c`.
Resource101 `9c7a0a2511b7b5af63a1ece60ff4c0ecddff3c8c57ae7b940ddc7299ed3a4cbf`.
Backup `backups/wide169/path-review-1790712004139991800`.
Rollback with game closed: `python modernization/tools/install_speech_layout.py rollback`.
Engine, terrain, QoL resource, saves and configuration remain intact.

## Assessment: a shared adapter is feasible, a global scale hook is insufficient

Existing evidence shows different coordinate spaces and rendering paths:

| UI family | Existing issue/evidence | Recommended policy |
|---|---|---|
| Battle countdown | v22 corrected five stale right/bottom call-site constants | Shared edge anchor applied through timer position setter; distinguish scripted top timers |
| Save/load progress | v22 shared constructor corrected signed offset and bottom cropping | Center against content viewport; size measured from the actual asset |
| Ordinary dialogue | Fixed art and text compose into one surface | Center/group translation; preserve text metrics |
| Teaching scroll | test14 background centered while target moved | Attach arrow to target control rectangle; one origin for all local contents |
| World dialogue | Native projection and fixed 800x600 bounds in 573990/572f30 | World projection first, then viewport fitting/arrow selection; separate from UI anchors |
| Grimoire pages | v7 repaired left-page inset; keyed 480x720 pages inside 640x720 halves | Explicit page canvas and fold anchors; same transform for tabs, text and hits |
| Portmanteau/tooltips | Native UI v4 required font, wrapping, surface allocation and clipping changes together | Page-specific scale profile and a layout generation; rebuild cached surfaces on transitions |

A late blit hook cannot know whether coordinates represent a world sprite,
page-relative text, edge-aligned HUD or a tutorial target. It also cannot fix
control hit rectangles, cached surfaces, wrapping, font metrics or color-keyed
page padding merely by moving pixels. Existing patches already transform some
paths: blindly applying a new scale would double-transform those paths.

Recommended architecture, proposed rather than fully implemented:

1. `LayoutContext`: actual native surface, content viewport, page kind, design
   canvas, asset/font scale, and generation counter. Keep wrapper output size
   and native drawing size distinct. Respect the existing policy: battle stays
   1280x720 with 2x output; independent HD pages target native 1920x1440.
2. Declarative anchors: left/right/top/bottom, center, page fold, or target
   control. Express margins in design units. Add explicit coordinate types
   to prevent page/surface/output coordinates from being mixed.
3. Family adapters at layout/construction entry points, before drawing/hit
   testing. Compute one rectangle used by background, text, hover and click.
   Convert input back through the inverse transform only where required;
   preserve accurate current native input until that family migrates.
4. Invalidate surfaces and text layout when context generation changes. Fonts,
   wrap width, clip bounds and asset variants must change together.
5. Migrate one family per acceptance iteration. Remove its old constant patches
   only after equivalent same-resolution behavior and inverse hit mapping pass.

Cost/risk/benefit assessment (relative engineering effort, not a fixed schedule):

| Increment | Cost | Risk | Benefit |
|---|---|---|---|
| Common geometry/context + simple timer/progress/modal adapters | Low–medium | Low–medium; stale per-caller assumptions | Eliminates repeated offset fixes for frequent small widgets; best next step |
| Tooltip/page adapter with font/cache transitions | Medium–high | Medium–high; wrapping, clipping, stale surfaces | Consistent independent-page scaling and reliable hits |
| Grimoire/Portmanteau full migration | High | High; asset keys, half-page geometry, drag/drop | Reusable responsive pages with fewer per-resolution assets/patches |
| Arbitrary native battle resolutions and live resize | Very high | Very high; scene culling, picking, fixed replay buffers and renderer allocations | Wider native scene support, but conflicts with current fixed battle policy unless separately requested |

Start with the first increment and reuse the existing mixed-UI context where
possible, instead of introducing another competing screen-mode detector.
Output-resolution flexibility can be delivered sooner by keeping supported
native canvases and adapting presentation. Arbitrary native resolution needs
separate renderer work and cannot honestly be promised by a UI wrapper alone.
No broader migration was installed in this task; only the test14 fix/helper.

Acceptance matrix for future adapters: baseline/candidate at current mode;
multiple aspect ratios/surface sizes for math; actual page open/close, hover,
click and drag at edges; long Chinese/Latin text; battle/page transition; timer
and save progress; all required rollback/hash gates. Each new family needs its
own runtime fixture rather than relying solely on synthetic geometry tests.
