# Creature sequence model review — 2026-09-30 / 2026-10-01

Completed eight actual Manager FIFO jobs on six Bat.spr frames AALF0001–0006, retaining original index order (1,5,9,13,17,21). This is an isolated review, with no runtime installation, game launch, UI changes, asset deletion or art-plan change. No callable subagent facility was exposed; the work was performed in this chat.

## Findings

PixelPerfectV4 is the strongest conservative image-sheet candidate in this small sample. VideoBit RepNet Base is the strongest conservative temporal candidate by motion-relative residual; RepNet GAN is close. These are candidates for broader testing, not approved production replacements.

SeedVR2 invents smoother wing membranes and changes body details. Its sheet result performs better than its temporal result on this small source. Qwen changes dark blue/white/red rendering toward brown and substantially reinterprets internal forms, despite the restoration prompt. Direct Qwen restoration is unsuitable here. No generated detail blend was used to hide model drift.

Contact-sheet inspection shows the original six wing poses remain readable with PixelPerfect and RepNet. CDA variants darken/smooth wing detail. SeedVR2 changes local wing/body rendering from frame to frame. Qwen has the largest colour and structure drift. Exact source-alpha locking prevents added silhouette pixels but cannot prevent misplaced internal anatomy; full anatomical stability is not established by this bounded sample.

| Actual arm | Motion-relative residual delta MAE | Low-frequency structure drift MAE | Wall seconds |
|---|---:|---:|---:|
| PixelPerfectV4 sheet | 20.499 | 7.412 | 3.05 |
| VideoBit RepNet Base temporal | 15.707 | 8.577 | 15.05 |
| VideoBit RepNet GAN temporal | 16.565 | 8.438 | 6.06 |
| VideoBit CDA HiFreq temporal | 25.291 | 11.506 | 12.11 |
| VideoBit CDA Smooth temporal | 24.037 | 11.511 | 9.04 |
| SeedVR2 7B Sharp sheet | 45.238 | 10.798 | 18.09 |
| SeedVR2 7B Sharp temporal | 57.438 | 13.473 | 18.12 |
| Qwen-Image 2.1 sheet, 12 steps | 79.614 | 36.920 | 15.13 |

Metrics use 0–255 RGB values, compare against a 2× Lanczos baseline, and evaluate residual changes between adjacent aligned frames on shared opaque pixels. Lower measures greater fidelity, not necessarily better art. The temporal proxy includes legitimate texture motion and does not implement optical flow. Lanczos scores zero by definition. Still-sheet models receive all frames at once, but have no true temporal mechanism. Video outputs include Manager encoding effects. Timings include dispatch/model startup and are not benchmark-quality comparisons.

## Preservation and scope

Sources are copied unchanged into `sources/`; live source SPR and ANI hashes were rechecked. Original frame width, height, offsets, flags, names and indices are recorded in `manifest.json`. Each arm supplies both native-size RGBA frames with byte-exact original alpha and 2× RGBA frames with exact nearest-neighbour 2× alpha. Dimensions are never inferred from generated subject bounds. Alignment uses original offsets on fixed 128×128 input / 256×256 output canvases. No SPR/ANI replacement is written.

ANI semantics, native action labels, direction mapping and timing have not been decoded. AALF is a consistent source name-prefix grouping, not a verified gameplay state. Previews use six frames at 125 ms each for diagnostic comparison only. Other creatures, attack/death states, direction transitions, long loops and gameplay remain untested.

All installed suitable entries exposed by Manager's upscale catalog were tried: SeedVR2 plus four VideoBit presets. PixelPerfect was additionally confirmed in managed ComfyUI's UpscaleModelLoader registry. Qwen21 was confirmed healthy by Manager keyframe status and tested. The `/api/models` catalog exposes an LLM, which is unsuitable for raster upscaling; H3 is motion generation rather than faithful source-frame SR and was not used. Unregistered models, additional checkpoints, segmentation and model downloads were outside this scope. Qwen status advertises a research/non-commercial license; no shipping approval is implied.

## Reproduce / resume

From the project root:

```powershell
python modernization/assets/creature-sequence-review-20260930/run_review.py
python modernization/assets/creature-sequence-review-20260930/evaluate.py
```

The runner reads the assigned Codex credential privately, calls only Manager ports 8790/8791 for inference and persists input hashes, stable idempotency keys and owned job IDs before polling. Completed jobs are reused; rerunning does not resubmit them. Each task has a 1200-second polling bound, preserving its existing ID on timeout. Do not remove the manifest to resume. Model files remain under E:/AI; managed inference media remain under D:/AI/LocalModelManager/media; durable review copies remain in this directory. CPU processing uses Pillow, numpy and E:/AI/LosslessCut/resources/ffmpeg.exe.

`manifest.json` holds registry snapshots, IDs, input/output hashes and timings. `evaluation.json` holds metrics and limitations. Per-arm `frame-validation.json` records native dimensions/alpha and metadata. `comparison.png` is the full contact sheet; `comparison-animation.png` is a lossless APNG grid, with `comparison-animation.gif` as a compatible preview. Each arm includes raw model output, extracted frames, native/2× derivatives and individual animation previews. Qwen's request and PixelPerfect's workflow are saved beside their outputs.
