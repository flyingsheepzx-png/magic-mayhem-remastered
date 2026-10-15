"""Finalize local provenance and a browser-friendly artifact index; CPU only."""
from pathlib import Path
import json,html
from run_expanded import OUT,MANIFEST,sha,write,verify_sources
plan=json.loads(MANIFEST.read_text());evaluation=json.loads((OUT/'evaluation.json').read_text());profile=json.loads((OUT/'effective-profile.json').read_text())
profile['provenance']={str(p):sha(p) for p in [Path('D:/GitHub/LocalModelManager/manager/upscale.py'),Path('E:/AI/ComfyUI_windows_portable/ComfyUI_windows_portable/ComfyUI/custom_nodes/ComfyUI-SeedVR2_VideoUpscaler/inference_cli.py')]}
write(OUT/'effective-profile.json',profile)
for job in plan['jobs']:
 job['request_fields']={'model':plan['model'],'width':job['target_size'][0],'height':job['target_size'][1],'scale':2,'data_url':'PNG base64 of saved input_sha256'}
 job['effective_profile_reference']='effective-profile.json'
 job['seed_policy']='Fixed installed CLI default seed 42; input/latent noise 0. Manager image endpoint does not forward seed/noise.'
plan['completed_coverage']={'creatures':7,'sheets':sum(j['status']=='complete' for j in plan['jobs']),'frames':sum(j['selected_frames'] for j in plan['jobs'] if j['status']=='complete')};verify_sources(plan);write(MANIFEST,plan)
assert plan['completed_coverage']['sheets']==14 and evaluation['complete_sheets']==14
table=['| Frame group | 2x residual delta | Native residual delta | Pre-alpha external / opaque | Border pixels >24 |','|---|---:|---:|---:|---:|']
for r in evaluation['results']:table.append('| %s | %.2f | %.2f | %.2f%% | %d |'%(r['name'],r['metrics_2x']['motion_relative_residual_delta_mae'],r['metrics_native']['motion_relative_residual_delta_mae'],100*r['diagnostics']['external_fraction_mean'],r['diagnostics']['border_pixels_total']))
text='''# SeedVR2 sheet expanded creature review — 2026-10-01

Completed **14 actual authenticated Manager FIFO image jobs, 7 creatures, 112 actual source frames**. Every selected group contains its eight available consecutive numeric suffix frames; none was duplicated to reach 12. Seven creatures were used because six creatures × two eight-frame groups would cover only 96 frames. Each creature has two different name prefixes. ANI action, direction and timing semantics are not inferred; consecutive suffixes are not necessarily a motion-only animation. The eight-frame previews use an arbitrary fixed 125 ms cadence.

Only SeedVR2 7B Sharp was submitted. No other models, downloads, Manager changes, runtime/UI changes, game launch, asset deletion or shared work-file changes. All outputs and scripts are confined to this directory. The independent packing-sensitivity experiment belongs to the main thread and was not duplicated or awaited here.

## Visual findings and usable recommendations

The 2x contact sheets were inspected for all seven creatures. Dog, Griffin and Phoenix are useful candidates for further user review: SeedVR2 smooths contours and clarifies coarse surfaces while generally retaining the pose read. Dog's black coat gains smooth outlined/curled structures, so the lower numerical drift does not mean unchanged anatomy. Griffin's feathers and face are reinterpreted. Phoenix's trailing narrow feathers and toes remain areas to inspect.

Bat reproduces the attractive thin wing-membrane look from the smaller trial, but wing membranes, face and torso detail vary across source frames. This expanded layout is not an exact replication of the previous six-frame sheet. Skeleton gains clear bone edges but changes skull/rib, shield ornament and sword detail, including notably changed shield centres in SBLA0004/0005. Dragon gains clean outlined scales/horns, but head, wing and joint details are redrawn. Wraith gains strong cloth folds, while hood interior, robe and staff/scythe edges are reinterpreted. These four need focused per-frame anatomy/edge review before any production recommendation.

Native-size exports were also compared separately. Their smoother shading remains visible, but much of the 2x fine detail is lost when resized back. There is **no established native-resolution quality gain or production acceptance**. Native residual scores falling relative to 2x primarily reflect smoothing/downsampling, not independent evidence of improvement. Battle still renders at 1280x720; the attractive 2x sheet does not authorize doubling native creature geometry or altering the rendering policy. The native-size PNGs are offline artwork candidates, not installable SPR replacements.

## Profile, provenance and controlled geometry

`effective-profile.json` records the installed effective defaults: **seed 42, input_noise_scale 0, latent_noise_scale 0**, image batch_size 1, Lab colour correction, CPU tensor offload, tiled VAE encode/decode. Manager does not expose/forward seed or noise in this image path, so no ignored seed field was submitted. Seed 42 is the installed CLI default, not a caller-controlled seed. This uses a single sheet as one image, **not true temporal context**; deterministic repeatability has not been tested. Model/VAE sizes and full SHA-256 are in `manifest.json:model_payloads`; Manager worker source and installed CLI SHA-256 are in the effective profile.

Each creature uses the same adaptive fixed cell dimensions and offset origin across both groups. Input cells have at least 32 native pixels of margin on every side and are rounded to multiples of 32, with four columns and two rows. No source image is resized before inference. Exact 2x targets range from 1024x768 to 1536x896 (Bat is 1280x512). Every raw output matched its target without squeezing, resizing or aspect correction. Crops use integer cell coordinates and cannot sample neighbouring cells. Large gaps mitigate cross-cell contamination, but do not prove model independence between cells.

## Palette, metadata and alpha validation

All 112 selected frames use one registered source palette and native selector **0**. The runner explicitly validates and uses the actual +28 selector before decode, rather than inheriting `spr_assets`' historical default palette0. Paletted selectors must be in range; RGB565 must use 0xffffffff. `manifest.json:field_semantics` and each frame row retain the actual selector and +32/+36 optional mask offsets; the legacy `flags` tuple is retained without relabelling it as gameplay state.

Original SPR and ANI copies, source dimensions, offsets, index, name, flags and decoded alpha hashes are preserved. Native derivatives have original dimensions and byte-exact original alpha. 2x derivatives have exactly doubled dimensions and exact nearest-neighbour doubled alpha, with corresponding 2x offsets recorded separately. Original and copied SPR/ANI SHA-256 were rechecked after inference and evaluation. No SPR writer was invoked; container mask payloads are preserved in original copies, not regenerated from PNG.

## Frame drift, pre-alpha silhouette contamination and halo

The three metric formulas match the earlier review: RGB drift MAE, Gaussian-blur-3 low-frequency drift MAE, and adjacent model-residual delta on intersecting opaque aligned pixels. `evaluation.json` provides all three at 2x and native sizes. Motion-relative residual is a proxy, not a pure flicker measurement: no optical-flow correspondence, verified ANI semantics or anatomy classifier is used. Frames may include changing viewpoints. Lower is more faithful to the baseline, not automatically better art.

Before applying source alpha, every raw cell was checked against the submitted flat RGB (48,48,56). Pixels with any channel difference >24 outside the exact source mask are counted; near-edge pixels use a four-pixel dilation ring, and far/background and 16-output-pixel cell borders are counted separately. This is a diagnostic threshold, not semantic segmentation: interpolation, background colour correction and global noise may count as contamination. All groups contain external non-background pixels. The mean external/opaque fraction is about 2.3–8.5%, highest for Bat. Thus a clean locked silhouette cannot be used as evidence that the model preserved the raw silhouette.

Nonzero border counts are small but prevent claiming complete absence of cell-border changes. The occupied input support has ≥64 output pixels of margin, and extraction is restricted to each cell. There was no visual evidence of a neighbouring creature pasted into another frame, but the diagnostics cannot conclusively prove no cross-cell model influence. `NN-prealpha.png` and magenta `NN-contamination.png` retain evidence that would otherwise be hidden by alpha locking.

Inside-edge RGB MAE and a thin-feature proxy (opaque pixels removed by a 9-pixel erosion) are saved per frame and group. Alpha equality guarantees covered thin limbs remain covered, not that they retain correct RGB contrast, joint placement or anatomy. Grey background can influence inside-edge colour before alpha is reattached; that survives compositing on black/white. Each creature includes `edge-background-check.png` showing first frames in Lanczos/SeedVR pairs on both backgrounds. This is a first-frame visual aid; numerical edge/halo checks cover all 112 frames. No claim of full halo-free or anatomical acceptance is made.

'''+ '\n'.join(table)+'''

## Artifacts and reproduction

`manifest.json` is the authoritative list of all 14 owned job IDs, original/input/output/model hashes, dimensions, frame metadata and request-field records. `evaluation.json` has the coverage and metrics. Each prefix folder contains original decoded frames, raw sheet, pre-alpha crops, contamination maps, exact-alpha 2x/native exports, `frame-validation.json` and separate original-native/Lanczos-2x/SeedVR-2x/SeedVR-native GIF and lossless APNG previews. Each creature directory has `comparison-2x.png`, `comparison-native.png`, `comparison-animation-1x.gif/.png`, `comparison-animation-2x.gif/.png`, and edge-background checks. `index.html` offers grouped links and animations.

Run from the project root:

```powershell
python modernization/assets/creature-seedvr-sheet-expanded-20261001/run_expanded.py
python modernization/assets/creature-seedvr-sheet-expanded-20261001/evaluate_expanded.py
python modernization/assets/creature-seedvr-sheet-expanded-20261001/write_report.py
```

The inference runner reads the assigned credential privately and only uses Manager ports 8790/8791. IDs and input hashes are saved before polling; stable idempotency keys prevent duplicate GPU submissions. Both per-invocation and per-job polling are bounded at 1200 seconds. A timeout retains the existing owned ID for resume without resubmission. Completed results are reused. A client-side first-result metadata read encountered an omitted `payload` field; it was fixed and the same successful owned ID resumed, with no repeated inference. Model files stay under E:/AI; transient Manager media stay under D:/AI/LocalModelManager/media. Nothing was cleaned or deleted.

Reproducibility is source/workflow/profile provenance, not proof of byte-deterministic inference. Per-frame metrics and previews can be regenerated CPU-only from the saved raw results. GIF is quantized; use PNG/APNG/native RGBA exports for colour/alpha judgments.
'''
(OUT/'REPORT.md').write_text(text,encoding='utf-8')
parts=['<!doctype html><meta charset="utf-8"><title>SeedVR2 expanded creature review</title><style>body{background:#222;color:#eee;font:16px sans-serif;margin:24px}a{color:#acf}img{max-width:100%;image-rendering:auto}section{margin:40px 0}</style><h1>SeedVR2 SHEET: 7 creatures / 14 sheets / 112 frames</h1><p>Offline review. Fixed preview cadence, ANI semantics unverified. <a href="REPORT.md">Report</a> · <a href="manifest.json">Owned IDs and hashes</a> · <a href="evaluation.json">Metrics</a></p>']
for source in plan['sources']:
 n=source['creature'];parts.append(f'<section><h2>{html.escape(n)}</h2><p><a href="{n}/comparison-native.png">Native contact sheet</a> · <a href="{n}/comparison-2x.png">2x contact sheet</a> · <a href="{n}/edge-background-check.png">Black/white edge check</a></p><h3>Native-size comparison</h3><img src="{n}/comparison-animation-1x.png"><h3>2x comparison: original / Lanczos / SeedVR</h3><img src="{n}/comparison-animation-2x.png"></section>')
(OUT/'index.html').write_text(''.join(parts),encoding='utf-8')
print(plan['completed_coverage'])
