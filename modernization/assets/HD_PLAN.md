# HD asset plan

**This is the asset pipeline reference.** The current implementation order is
the broad-to-detail HD repair plan in [../PLAN.md](../PLAN.md). Use this file
when that plan identifies an asset or pipeline defect. Then read
[HD_BUILD_LOG.md](HD_BUILD_LOG.md) for what has actually been built and
[HD_ASSET_LIST.md](HD_ASSET_LIST.md) for the per-asset table. Historical queue
counts and command examples below do not authorize mass regeneration ahead of
the early in-game value audit in `modernization/PLAN.md`.

## In-game Qwen value gate — current priority

**2026-09-29 battle-art reprioritization:** The user prefers testing a
real-time presentation filter before investing in mass battle sprite
replacement. Keep the terrain/animation Qwen batch paused. The isolated v4
light sharpen remains opt-in after same-scene game capture and performance
checks. Community sharp-bilinear, FSR and xBR candidates and offline
nearest/bilinear/bicubic/Lanczos/Scale2x comparisons are recorded in
[HD_BUILD_LOG.md](HD_BUILD_LOG.md). None is approved for default use; a GPU
filter would require a separate 1280×720 battle texture while preserving
native 1920×1440 UI pages, screenshot fidelity and input mapping.

Evaluate generated art early, while it can still change the remaining queue.
For representative finished UI, portraits, icons and realm art, and a small
pilot from pending terrain/animation classes, preserve three variants at the
same target pixel dimensions: source-derived plain enlargement, local Qwen
output and the currently accepted runtime asset. Install only into an isolated
candidate, capture the same game page/action at full output resolution, and
compare against the hash-verified baseline. Check important text and icon
identity, visual clarity at play size, geometry, colour keys, borders, flat
fills and frame-to-frame consistency. Include a battle regression for any
shared UI/battle sprite.

Record `accept`, `refine and rerun`, `plain enlargement wins`, or `defer`, with
source/output hashes and the paired capture. Edge-energy gain is supporting
data, not a value verdict. When a category repeatedly shows little useful
gain, stop its pending Qwen work. When failures share a cause, change that
category's canvas, detail strength, mask or frame packing, then run a small
pilot and repeat the in-game A/B check before restarting its batch. A complete
rerun requires evidence of a common pipeline defect, not merely a completed
queue or a higher edge-energy score. Keep local Qwen Image 2.1 as the only
generation/editing model.

The 2026-09-29 in-game value audit accepts the sampled main-menu and Grimoire
backgrounds but chooses ordinary enlargement for three small Portmanteau
`Buttons.spr` frames. A 49-frame terrain pilot and 144-frame wizard animation
pilot show only limited offline benefit and are **deferred for batch work**.
Before further terrain/animation generation, the battle renderer must prove
that 2× source art can be drawn at the old logical world size, then compare
Qwen and ordinary enlargement in the same battle scene. See
[HD_BUILD_LOG.md](HD_BUILD_LOG.md) for exact hashes, captures and limits.

## 0. Start here

**2026-09-28 requirement clarification.** The final game must render UI at a
native 1920×1440 resolution and load the corresponding generated assets at
their prepared pixel dimensions. Wrapper enlargement of a 960×720 or 1280×720
game surface is not an HD UI implementation. The earlier wide169 Qwen-art
preview is useful only to check art and resource wiring while native rendering
is built. Do not reduce final UI assets to 960×720 to fit that preview. Preserve
the existing wide169 and QoL features in the eventual combined candidate.

**Goal.** Raise the game art to a native 4:3 high-definition UI plus doubled in-game
art, using **only** the locally installed Qwen-Image 2.1. Nothing is installed into the
game by this workstream: the deliverable is a prepared tree mirroring the game layout,
plus the engine-side evidence installation will need.

**Current state.** The four-asset UI smoke test passed on 2026-09-27. The remaining
378 UI assets are generating in the original workspace; use its `status` and ignored
`assets/hd/ui-run.out.log` for current progress. An isolated playable copy now exists
on branch `codex/hd-ui-lab`. Generated menu and settings art loaded in that copy via
temporary, backed-up JPG replacements; full 1920x1440 art cropped on the old 800x600
surface, while 800x600 compatibility conversions aligned. See
[`../docs/hd-integration.md`](../docs/hd-integration.md). Nothing was installed in
the original game. The plan, build log and per-asset list are tracked in git;
`modernization/assets/hd/` is ignored.

**Historical asset order.** UI was queued first; terrain and animation were
deferred. Current repair priority is governed by `modernization/PLAN.md`.

```powershell
# 1. rebuild the queue, the mirrored output skeleton and the list  (~4 s)
python modernization/tools/hd_pipeline.py plan

# 2. completed pilot: full screen, illustrated page, narrow bar, keyed flat area
python modernization/tools/hd_pipeline.py run --route composite --source 'Interface/MainScreen/800x600/Main Menu 800-600.JPG' --source 'Interface/Grimoire/800x600/Backdrop.JPG' --source 'Interface/Grimoire/Generic/statbar.bmp' --source 'Interface/RealmViewer/Generic/Celtic_Silhouette_00.PCX'
python modernization/tools/hd_pipeline.py review --category ui-800x600 --category ui-untiered

# 3. running after successful asset smoke checks (~5.2 h total)
python modernization/tools/hd_pipeline.py run --route composite --category ui-800x600 --category ui-untiered

# 4. later, when the user asks for them
python modernization/tools/hd_pipeline.py run --route composite --category portrait --category bitmap
python modernization/tools/hd_pipeline.py run --route atlas      # 17 realm terrain atlases
python modernization/tools/hd_pipeline.py run --route sheet      # 153 animation containers

# check progress at any time; safe to repeat any run command
python modernization/tools/hd_pipeline.py status
python modernization/tools/hd_verify.py --category ui-800x600 --category ui-untiered
python modernization/tools/hd_pipeline.py review --category ui-800x600
```

`run` skips records marked done and retries anything failed. The pilot does not touch
installed game files. The queue is atomically saved after every asset. Before running,
the runner verifies selected source hashes and checks output and manifest hashes for
completed conventional images. Container output integrity still needs its own check.

## 1. Objective and constraints

- UI art targets a native **1920x1440** 4:3 surface, a uniform **2.40x** of the 800x600
  tier. In-game art is doubled in both dimensions.
- World scale, gameplay and save formats must not change. Sprites are doubled in pixels
  but must keep their logical world size, which is a renderer concern.
- Only Qwen-Image 2.1 may generate or edit raster art. It is reached through the local
  Manager workbench; never talk to the raw ComfyUI port.
- Nothing may be installed into the game until the engine-side requirements in section 8
  are met and verified.

## 2. Confirmed decisions

| # | Decision | Reason / evidence |
| --- | --- | --- |
| 1 | UI target **1920x1440**, a uniform **2.40x** of the 800x600 tier, 4:3 | Chosen by the user over 2048x1536 and 2560x1920 |
| 2 | In-game art **2x** width and height | User requirement |
| 3 | **Only Qwen-Image 2.1**, no second model | The two-model experiment was dropped as too complex |
| 4 | Canvas tier is **per record**: **2048** for UI art, **1024** for animation frames, terrain and other small art | Native 800x600 UI measured **+288%** edge energy at 2048 against **+87%** at 1024 |
| 5 | Composite strength **1.0** at or above 400 px on the longer side, **0.6** below | Small sources force a large canvas scale, so the model invents more |
| 6 | **12 steps**, fixed seed, official prompt enhancement **off** | 39.57 at 12 steps against 38.41 at 40: more steps buy nothing, and 12 is three times faster |
| 7 | **Every output is PNG.** JPEG is banned | A colour key must stay exact. Worst deviation inside the keyed region: 2 in the originals, **7 to 8** after a quality 95 JPEG re-encode, 2 to 3 at quality 100, **0** in PNG |
| 8 | **Colour-key masks are restored byte for byte** after the model runs | 28 of 60 sampled assets are keyed, covering 9% to 99% of the image. Without it the key drifts and the field gets mottled |
| 9 | Terrain uses the **atlas** route, not sequence alignment | Tiles are independent. Aligning put a 64x48 tile in a 126x83 box: 9 frames per canvas and **1.06 to 1.12** gain, against **1.22** with tight cells |
| 10 | The legacy **640x480 tier is not built** | It duplicates the same artwork and would give one portrait two output sizes |
| 11 | **Cursors are deferred** | A 32x32 cursor is forced to about a 24x canvas scale; measured 79.93 to 80.54 edge energy |
| 12 | **`.ani` files are not image assets** | They hold a sprite name and a table of frame indices, no pixels. Frame count and order are preserved, so they stay valid unchanged |

## 3. Method, per asset

1. **Base.** The original is resampled with Lanczos to its target size. Layout and
   lettering derive from the original; their final pixels still need verification.
2. **Key detection.** A colour-key background is detected from border pixels with a
   tolerance, because palette art uses pure magenta or blue while JPEG sources carry
   shifted keys (251,0,253 and 0,0,254). Detection is skipped when the asset has real
   alpha.
3. **Canvas.** The asset is placed on a flat canvas whose proportions match a Qwen
   preset exactly, so the content region is never stretched or cropped. Assets flatter
   than 4:1 are edge-replicated first, because the engine bands the subject above about
   8:1 and smears it above about 22:1.
4. **Route** decides how frames share a canvas:
   - **composite**: one conventional image per job.
   - **sheet**: an animation container; frames are aligned to the container box so motion
     inside each frame survives, then split again.
   - **atlas**: a tile atlas with no ordering; each frame gets a tight cell of its own
     size, which packs 49 frames per canvas instead of 9.
5. **Restore.** Qwen-Image 2.1 restores the canvas in one job. The API has no denoise,
   strength or CFG knob, and `ref_image_size` has no measurable effect on content, so
   steps and the prompt are the only levers.
6. **Composite.** Only the model high-frequency band, above a 1.6 px blur radius, is
   added to the base, and only where two gates allow it:
   - a **structure gate** limits changes to text strokes, icons and borders; pixel
     identity and hit targets have not been proven across all assets;
   - a **texture gate** keeps deliberate flat fills flat. Without it a realm silhouette
     blue went from a standard deviation of 0.00 to 10.49 with invented contour lines.
7. **Key restore.** The keyed region plus a two pixel rim is copied back from a
   nearest-neighbour resample of the original, so no value is interpolated.
8. **Alpha.** Coverage is never generated; it is rebuilt from the original footprint.

## 4. Measured evidence

Gain is edge energy against a plain Lanczos enlargement of the same source:

| Category | Route | Gain |
| --- | --- | ---: |
| Grimoire illustration pages | composite | **4.0x** |
| UI full screens, parchment, maps | composite | **3.3x** |
| Realm terrain tiles and scenery | atlas | **1.2x** |
| Portraits and small bitmaps | composite | **1.1x** |
| Creature animation frames | sheet | **1.04x** |

Gain tracks how much smooth surface an image has. Hard-edged 8-bit pixel art puts nearly
all of its signal at edges, exactly where the structure gate is designed to do nothing,
so those categories move only slightly. Animation is the weakest category and carries the
largest time cost.

Other numbers: a 1024-class canvas job takes about **8.7 s** and a 2048-class job about
**50 s** on the installed RTX 5090. Sprite sheets do not flicker (frame to frame
difference rises 0.14% with alpha applied), and model artefacts on sheets land in the
transparent gutters that the alpha discards. Key protection was verified byte for byte
over 3.4 million pixels: maximum difference **0**.

## 5. Scope and cost

| Group | Assets | Route | Tier | Frames | Est. GPU |
| --- | ---: | --- | --- | ---: | ---: |
| ui-800x600 | 332 | composite | 2048 | - | 4.5 h |
| ui-untiered | 50 | composite | 2048 | - | 41 min |
| portrait | 88 | composite | 1024 | - | 13 min |
| bitmap | 37 | composite | 1024 | - | 5 min |
| sprite-container, terrain | 17 | atlas | 1024 | 29,090 | 87 min |
| sprite-container, animation | 153 | sheet | 1024 | 27,856 | 5.3 h |
| **total runnable** | **677** | | | **56,946** | **12.2 h** |
| blocked, legacy SPR v2 | 7 | - | - | - | - |
| blocked, `.ani` | 136 | - | - | - | - |
| not queued, 640x480 tier | 424 | - | - | - | - |
| not queued, cursors | 20 | - | - | - | - |

The UI phase alone is 382 records and about **5.2 hours**.

## 6. Build procedure

See section 0 for the exact commands. Two properties matter when picking this up:

- **Resumable with checks.** `run` selects records whose status is not done. It saves the
  queue after every asset and checks completed conventional-image output hashes before
  skipping them. A failure returns a nonzero process status. Container output integrity
  is not yet verified on resume.
- **Re-plan limits.** `plan` preserves status when source hash, target size, preset,
  strength and route match. It does not compare prompt, seed, steps, detail blur, padding
  policy or code revision. Changes to those inputs require an explicit rebuild decision.
- A trial limited with `--max-sheets` writes real but partial output and is recorded as
  `partial`, not `done`, so the rest of the container is not silently skipped.

## 7. Output layout and installation

`plan` creates the whole tree, so the pack mirrors the installed game layout:

```
modernization/assets/hd/pack/
  Interface/CharacterScreen/800x600/CharacterScreen.png       <- 1920x1440
  Portraits/800x600/Aeetes 800x600.png                        <- 160x200
  Creatures/Brownie.spr/0000.png ... plus sprite.json         <- aligned frames
  Realms/Celtic/Plains/Terrain.spr/0000.png ... sprite.json   <- per-frame size
```

Every asset has a JSON manifest beside it with the source and output SHA-256 and the
Manager job id. Sprite containers keep frame index, name, source box, offset and flags in
`sprite.json`, which is what a future SPR re-encode needs. `pack/_work/` holds the
canvas and raw model output per job; it is review material and can be deleted.

The mirrored tree is a staging layout, **not an installable replacement pack**. JPEG/BMP/PCX
sources become PNG files with different names, and each SPR becomes a directory of PNG
frames plus `sprite.json`, not a loadable SPR. Installation requires a verified engine
loader or a proven re-encoder, a backup of every touched game file, and a tested rollback.
**Nothing has been installed and the engine has never loaded a generated image.**

## 8. Engine-side requirements before anything can be installed

| # | Requirement |
| --- | --- |
| 1 | The engine must render a **1920x1440** UI natively. The prepared art is not a proven game mode. |
| 2 | The engine must resolve the new **PNG paths** for JPEG/BMP/PCX sources; copying a PNG next to the original does not replace it. |
| 3 | Doubled in-game art must be drawn at **2x scale** with unchanged world size; blindly doubling sprites would enlarge every unit. |
| 4 | SPR frame directories need a verified loader or a lossless re-encode path that preserves frame indices, offsets, flags and palette/key semantics. |
| 5 | Scale and validate the coordinate tables in `Interface/MainScreen/screen (MainMenu).cfg` and `Grimoire.cfg`, then trace any hardcoded layout and input transforms; scaling two CFG files alone may not cover all hit targets. |
| 6 | Colour-key assets must still key correctly after the rebuild. The keyed region is byte-identical to the original, so this should hold, but it needs an in-game check. |

The approved resolution policy is three selectable tiers: existing 640x480 and
800x600, plus 1920x1440. `tools/hd_layout_tier.py` stages `Rect3` and
`1920x1440_*` coordinate candidates under ignored `assets/hd/config-1920x1440/`.
The current `IsHighRes` setting is Boolean and the executable has no verified
third-tier reader; staged CFG files are not installed or sufficient by themselves.

## 9. Known limits and risks

- Gain is strongly category dependent, and the weakest category carries the largest time
  cost: animation is 5.3 hours for about 1.04x.
- PNG is lossless but much larger than JPEG; the full pack plus working files is expected
  to be several GB. About 437 GB was free at the 2026-09-27 preflight.
- The 2048-tier UI jobs are 50 s each, so the UI phase alone is 5.2 hours.
- Nothing is proven in game. Every engine-side item above is unverified.
- The project also targets a later expanded 16:9 viewport. This 1920x1440 4:3 UI pack
  does not establish that widescreen mode or its layout policy.
- Edge-energy gain measures added detail, not visual fidelity. Review representative
  Chinese text, glyphs, buttons, maps, transparency and flat fills before a long batch.
- The Qwen Research License is for non-commercial research/evaluation; distribution of
  generated assets also depends on the game's asset rights.
- 7 legacy SPR version 2 containers remain undecoded and are low value.

## 10. Repository layout

| Path | What it is | Tracked |
| --- | --- | --- |
| `modernization/tools/hd_pipeline.py` | planner, builder and reviewer: `plan`, `run`, `status`, `review` | yes |
| `modernization/tools/hd_verify.py` | completed raster hash, size, alpha and colour-key checks | yes |
| `modernization/tools/hd_layout_tier.py` | stages third-tier CFG coordinate candidates without changing installed files | yes |
| `modernization/tools/qwen_canvas.py` | canvas composition, restoration, key protection, gates | yes |
| `modernization/tools/spr_assets.py` | SPR v4 reader, including the multi-palette terrain header | yes |
| `modernization/tools/spr_sequence.py` | per-frame versus per-sheet experiment and flicker measurement | yes |
| `modernization/docs/local-model-workbench.md` | workbench API surface and measured limits | yes |
| `modernization/assets/HD_ASSET_LIST.md` and `.csv` | the per-asset table | yes |
| `modernization/assets/hd/` | build workspace: queue, pack, logs, review sheets | **no**, regenerated by `plan` |
| `modernization/assets/experimental/` | artifacts from an earlier session, superseded | **no**, safe to delete |

The generated art derives from commercial game assets and a research-licensed model, so
it is deliberately kept out of the source repository.

## 11. Handover notes

- Read this file, then [HD_BUILD_LOG.md](HD_BUILD_LOG.md), then
  [HD_ASSET_LIST.md](HD_ASSET_LIST.md).
- The executable state is `modernization/assets/hd/hd-queue.json`, regenerated by
  `plan`; it records per-record status, hashes and Manager job ids.
- Do not change the method without re-reading section 2. Every decision there is backed
  by a measurement, and several were expensive to find: the single-flag structure gate
  mottled flat fills, sequence alignment on terrain halved the gain, and a JPEG re-encode
  broke colour keys.
- Report honestly. Nothing here is a delivered game feature; it is prepared art plus the
  evidence installation will need.
