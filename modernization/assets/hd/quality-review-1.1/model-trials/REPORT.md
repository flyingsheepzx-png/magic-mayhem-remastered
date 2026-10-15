# Celtic map bounded local Qwen trial — 2026-09-30

## Final user-reviewed conclusion — 2026-09-30

**Closed. None of the three actual completed Qwen Image2.1 trials (01,02,03-context-crop-v2) produced a directly installable solution combining structural fidelity and improved readability.** The user reviewed02's village comparison and03-v2's forest/rock comparisons and evaluation, confirmed raw structural displacement and protected compositing's very small gain, and requested no further generation.

Candidate02 remains an art study with clearer local detail, not an installation recommendation. Prompt-driven full-map or contextual-crop redraw cannot guarantee original roads, lake/coast boundaries, building arrangement or forest geometry. Source-protected residual blending preserves excluded pixels but has not delivered sufficient readable detail. No result is promoted to the asset queue, candidate package or runtime.

Any later separately scoped work should use **actual structural constraints and a regional material workflow**, with source-derived geometry, explicit protected roads/lake banks/buildings, bounded material edits inside existing forest/rock regions, and paired same-scale fidelity/readability review. Repeating prompt-only whole-image redraw is not the recommended next step. This records direction only; no additional trial or implementation is started here, and no claim is made that the current service supports a suitable hard constraint API.

Service terminal states were read directly at2026-09-30 17:52:28 +0800:

| Candidate | Manager job ID | Service terminal state | Output retained |
|---|---|---|---|
| 01-full-conservative | `2621f84e18bf407ea63fe803c8fe5e60` | `completed` | Yes |
| 02-full-readable | `dc10409816b34765877142a68ec87dff` | `completed` | Yes |
| 03-context-crop (canceled before generation) | `1257fa7d914948dd824be749b6797d80` | `interrupted` | No image was generated |
| 03-context-crop-v2 | `0a293cd33fe6481085ef2b768cf1e700` | `completed` | Yes |

All existing results, prompts/settings, source hashes, call logs, masks, comparisons and scripts remain retained. `closeout.json` preserves live service terminal-state evidence and final integrity checks; each call log also records its service closeout status. `artifact-index.json` inventories retained files and hashes. Source, old output and queue bytes remain unchanged. No game launch, installation, runtime acceptance test or external cleanup was performed.

## Initial offline comparison decision (superseded by final conclusion above)

Two genuine local **Qwen-Image 2.1** image-reference jobs completed through LocalModelManager. No other model was used. Candidate **02-full-readable** is the strongest offline art study: its existing roofs, mountain faces and conifer groups are more readable than the old noisy Qwen image. It is **not suitable for direct replacement**: it reinterprets building arrangement, road width, river geometry and forest structure. Candidate01 is smoother but shifts overall features and changes recognizable landmarks more strongly. Neither satisfies exact structural preservation, nor has either passed installation or runtime acceptance.

The source-anchored protected residual derivative demonstrates a safe geometric boundary, but adds too little useful detail to recommend it as a quality upgrade. Preserve it as evidence of the fidelity/detail tradeoff. This study does not promote an asset or queue status.

## Inputs and integrity

- Source: `modernization/assets/hd/source-original/Interface/RealmViewer/800x600/Celtic_Map.bmp`, 800×600 RGB.
- Source SHA-256: `adffa4c6a0c4c98de1d1af61566df00bba584f22ca2367717921e17b7f14d904`, verified against the existing queue record.
- Existing 1920×1440 Qwen: `modernization/assets/hd/pack/Interface/RealmViewer/800x600/Celtic_Map.png`.
- Existing SHA-256: `5a0ba1f7e5039c9253f51da7087dba57a168f410da9befa25e7cc69126269ab1`.
- Input provenance and final checks: `input-provenance.json`, `postflight-integrity.json`. Source, existing image and queue bytes unchanged during this trial. No game was started; no runtime, candidate package, main build helper or queue writes were performed. All trial scripts, outputs and reports reside in this directory.

## Actual local jobs

| Trial | Model raw size | Seed | Manager job ID | Result |
|---|---:|---:|---|---|
| 01-full-conservative | 1024×768 | 26093011 | `2621f84e18bf407ea63fe803c8fe5e60` | Completed, about 16 s polling wall time |
| 02-full-readable | 2400×1792 | 26093012 | `dc10409816b34765877142a68ec87dff` | Completed, about 157 s polling wall time |
| 03-context-crop | planned 1024×768 from source crop (250,110)-(650,410) | 26093013 | `1257fa7d914948dd824be749b6797d80` | Canceled while waiting GPU to respect narrowed scope; Manager terminal status `interrupted`; no generated candidate |

Both completed jobs used `engine=qwen21`, `quality=quality`, 40 steps, one output, `transparent=false`, and `official_prompt_enhance=false`. The reference was losslessly converted from the verified BMP to PNG in memory. Exact prompts and negative prompt are in `trial-settings.json` and each `*-call.json`. Call logs contain owned IDs, requested settings, health model description, phases, output hashes and result gateway URLs, without credentials or embedded reference data.

No denoise strength or ControlNet capability was assumed. The supported workbench request provided a reference image and text constraints, not a hard spatial control map. Candidate02's available preset is close to 4:3 rather than exact: 2400/1792 = 1.3393 versus 1.3333. Its raw image is retained; the comparison normalizes it with Lanczos to 1920×1440, introducing about 0.45% aspect adjustment. Candidate01 is exact 4:3 but its 1024×768 raw result requires further enlargement, limiting achievable final detail.

## Review evidence

`comparison-overview.png` compares original pixels, Lanczos, old Qwen, candidate01 and candidate02 at the same displayed footprint. The overview is for composition, not high-frequency judgement. `comparison-village-lake-1to1.png`, `comparison-forest-1to1.png`, `comparison-mountain-1to1.png` and `comparison-roads-1to1.png` contain **unscaled 360×360 crops from the 1920×1440 surfaces**, with labels above them.

- **Original / Lanczos:** reliable source topology and landmark identity; soft and pixel limited. The nearest original enlargement exposes source information without claiming new detail.
- **Old Qwen:** broad shapes closely match the source, but the village and canopy have dense grain/fragmented microtexture. More high-frequency energy does not resolve building structure.
- **01:** reduced speckle and rounded canopy groups; changes the conifer character, village roofs and southwestern circular landmark. Roads become much stronger and feature positions shift. The nearest-correlating windows in six selected regions shift approximately 5–7 source pixels horizontally and 3–4 vertically (roughly 12–17 and 7–10 output pixels). This approximate correlation is diagnostic, not precise geometric registration.
- **02:** clearest roof planes and conifer shapes among the trials; closer broad alignment than01. Region correlation finds approximately -1 to 0 source pixels horizontally and 0 to 1 vertically, yet the 1:1 crops reveal changed roof count/arrangement, forest pattern and road/river shape. Small correlation displacement does **not** prove topology or building preservation. The southeast forest retains considerable intricate texture; noise improvement is not consistent across regions.

Offline metrics (0–255 RGB units):

| Image | Mean absolute RGB difference vs Lanczos | Mean low-pass RGB difference (radius12) | High-pass luma RMS (radius1.2) |
|---|---:|---:|---:|
| Lanczos | 0.0000 | 0.0000 | 2.9290 |
| Old Qwen | 5.0621 | 0.1512 | 9.0913 |
| 01 | 21.2525 | 14.4992 | 4.5498 |
| 02 | 15.4022 | 11.1444 | 10.0042 |
| Protected residual | 0.0484 | 0.0047 | 2.9331 |

The new full renders modify low-frequency color/shading substantially as well as detail. High-pass RMS measures texture energy, **not** useful detail or noise in isolation. Full diagnostics, fixed source-coordinate boxes, zero-shift correlations and search results are in `offline-metrics.json`. Visual checks are offline asset inspection only.

## Protected-region experiment

`04-protected-texture-1920x1440.png` uses the source Lanczos enlargement as its base. Only three small interior forest/grass ellipses can receive candidate02 high-frequency residuals. Source broad shading stays intact. The generated-minus-source high-frequency delta is clipped to ±12 RGB, blended at 0.45, and feathered inward. The saved mask is `protected-texture-mask.png`; exact settings/results are in `protected-blend.json`.

Outside the saved mask, max RGB difference from Lanczos is **0**; global maximum difference is **5**, and only **1.47%** of pixels change. Coast, roads, river, lake, settlement and selected mountain/landmark windows stay source-derived. This is CPU compositing of an actual Qwen result, not a third model generation or model-enforced structural control. It does not improve protected buildings or roads; texture benefit is very weak. Interior generated detail can still be invented. `comparison-protected-forest-1to1.png` documents that limitation.

If a subsequent separately authorized experiment is desired, a contextual crop with explicit structural masks and original roof/road/river preservation is more defensible than full-map substitution. This trial does not start that work or assert the service supports hard structure control.

## Reproduction

From `D:/Games/Magic&Mayham`, with existing Python, Pillow and NumPy and the managed local service running:

```powershell
python modernization/assets/hd/quality-review-1.1/model-trials/run_trials.py prepare
python modernization/assets/hd/quality-review-1.1/model-trials/run_trials.py generate --candidate 01-full-conservative
python modernization/assets/hd/quality-review-1.1/model-trials/run_trials.py generate --candidate 02-full-readable
python modernization/assets/hd/quality-review-1.1/model-trials/evaluate_trials.py
```

Generation keeps existing PNGs, resumes only its recorded owned job, and refuses recorded failed/canceled/interrupted jobs rather than silently resubmitting. Fresh generation requires a separate copy of this script and inputs/settings within the authorized trial directory with fresh output names; local model reproducibility is settings-level, not a promise of bit-identical GPU pixels. The evaluator makes PNG sheets and pixel metrics only. Do not run the third candidate automatically: its canceled request documents the bounded scope.

The reusable evidence and decisions requested for this task are recorded here rather than changing outside project documents. Art acceptance and runtime integration remain pending user review/testing. Service health reports a research/evaluation license; the service description is recorded without independently certifying deployment rights.

## 2026-09-30 follow-up: completed 03-context-crop-v2

The user rejected direct installation of02 after reviewing the village comparison and authorized one fresh contextual trial. This new request used a fresh candidate ID and job; the canceled03 job was not reused. **03-context-crop-v2 completed on local Qwen Image2.1**, job `0a293cd33fe6481085ef2b768cf1e700`, approximately16.1 seconds of polling wall time including dispatch. Raw output:1024×768, SHA-256 `eccc922396fc82f59d0b2edf193d1287d1424f535bcc3bbe2bb753f653b25c8f`.

The source crop is `(360,240)-(760,540)`,400×300: southeastern conifer forest and cliff interiors, with lake, roads, water/coast and small landmarks providing context. The minimal-edit prompt asks to retain tall narrow conifers, original shadows/palette and all existing silhouettes, and to clarify only canopy/rock shading. Exact prompt, negative prompt, seed26093031,40 steps and disabled official prompt enhancement are recorded in `03-context-crop-v2-settings.json` and `03-context-crop-v2-call.json`. No hard spatial constraint/denoise setting is claimed. The new script bounds continuous GPU wait to180 seconds and total polling to600; neither limit was reached. The service actually sampled and returned a PNG.

### Review outcome

**A conservative prompt plus contextual crop still does not lock structure.** The raw render has more recognizable conifer and rock texture than plain Lanczos, but repositions/reconstructs canopy, rock edges and surrounding geography. Selected correlation windows prefer source-coordinate displacements of approximately5px (lake edge),7.1px (forest),8.5px (rock) and10.8px (east coast). These are local correlation heuristics, not precise vertex/landmark measurements, but reinforce the visible drift. Mean absolute crop RGB difference from Lanczos is18.89/255; low-pass difference is7.35/255. No full raw crop should be pasted into the runtime.

`03-context-crop-v2-context-comparison.png` shows nearest source, source Lanczos, old Qwen, new raw target and protected composite at equal displayed scale. The `*-forest-1to1.png`, `*-rock-1to1.png` and `*-protected-lake-road-1to1.png` compare unscaled regions from the960×720 target crop (2.4× source scale). Raw model1024×768 was normalized by Lanczos to960×720; source comparison was cropped from the full1920×1440 Lanczos map to ensure resampling boundaries match the actual paste target.

### Can interior details alone be pasted back?

A reviewable protected result was produced: `03-context-crop-v2-protected-full-1920x1440.png`, plus `03-context-crop-v2-protected-target.png` and local/full mask PNGs. Only three small canopy ellipses and one small interior region near rock may receive generated high-frequency detail. The original Lanczos broad shading is retained. Residuals are clipped to±24 RGB and blended at0.65 through inward feathering; no new low-frequency geometry is transferred. Final pixel verification confirms:

- **Maximum RGB difference outside the saved mask:0.** Roads, lake shore, buildings and coastline remain source-Lanczos pixels where excluded.
- Maximum RGB change anywhere:16/255.
- Changed fraction of the full image:0.914%.
- Original source and old Qwen hashes verified; queue bytes before/after identical.

**Local substitution is mechanically feasible, but this candidate does not establish a useful quality upgrade.** In the forest1:1 comparison, protected patches add fine contrast over the original blur without recovering coherent tree shapes; some changes read as extra grain. The rock1:1 protected comparison remains almost identical to Lanczos, with no meaningful gain in rock-plane readability. Copying broader model shapes would transfer the observed structural drift. The tiny allowed masks avoid the visible road/lake/landmark edges; their placement is a manual bounded exclusion policy, not automatically recognized terrain semantics. Interior invented detail remains possible even with outside pixels protected.

Keep the protected output as an offline review artifact, **do not recommend installation**. This closes the requested third completed trial; there is no new batch or pending GPU job. All changes remain in `model-trials/`, no game launched and no runtime/candidate/build tool/queue mutation.

### Reproduction of this fresh trial

```powershell
python modernization/assets/hd/quality-review-1.1/model-trials/context_crop_v2.py generate
python modernization/assets/hd/quality-review-1.1/model-trials/context_crop_v2.py evaluate
```

Existing raw output is retained without a second submission. `context_crop_v2.py` imports only the helpers in this directory; its candidate/settings overrides are in memory. Exact structural diagnostics and blend coordinates are in `03-context-crop-v2-evaluation.json`. The evaluator asserts that all pixels outside the protection mask match the original full-map Lanczos base.

