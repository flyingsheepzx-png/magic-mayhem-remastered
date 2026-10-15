# Optional image restoration trial

## Active HD workstream

**[HD_PLAN.md](HD_PLAN.md) is the entry point.** It is self-contained and assumes no prior
conversation. The per-asset table is [HD_ASSET_LIST.md](HD_ASSET_LIST.md) with a matching
CSV, the running record is [HD_BUILD_LOG.md](HD_BUILD_LOG.md), and the local model service
is documented in [../docs/local-model-workbench.md](../docs/local-model-workbench.md).

Confirmed: a **1920x1440** native 4:3 UI surface (a uniform 2.40x of the 800x600 tier),
**2x** in-game art, **Qwen-Image 2.1 only**, a canvas tier of **2048 for UI art and 1024
for animation frames, terrain and other small art**, and composite strength of 1.0 on
large art and 0.6 on small. **Every output is PNG** and colour-key masks are restored byte
for byte after the model runs.

Geometry is never generated: every asset is a Lanczos resample of the original with only a
gated high-frequency detail band from Qwen added on top, so letterforms and hit targets
keep their exact pixels and deliberate flat fills stay flat. The list covers **820
records**, of which **677 are runnable**: 507 conventional images, 17 terrain atlases and
153 animation containers. The plan builds **UI first**; terrain and animation are deferred.

**The four-asset 2K UI smoke test passed, and the remaining UI assets are generating.
No generated image is installed in the original game, and no native 2K UI mode is
proven.** An isolated game copy has tested generated main-menu and settings art; see
[../docs/hd-integration.md](../docs/hd-integration.md). The `hd/`
queue and output tree were regenerated on 2026-09-27. See [HD_BUILD_LOG.md](HD_BUILD_LOG.md)
for the pilot evidence and current batch logs. The earlier trial below is a narrow
prototype, not a game integration.
This directory contains an **experimental, uninstalled** grimoire background trial. The installed community game assets remain untouched. Outputs live under ignored `experimental/` because they derive from the commercial game image and the local Qwen Research License model; do not include them in the source repository or a community release without resolving both sets of rights.

## Inventory and source choice

Run `python modernization/tools/inspect_assets.py --output modernization/assets/inventory.json --summary modernization/assets/inventory-summary.json` to recheck the complete installed asset tree. The expanded inventory covers 4,857 files, including 752 JPEG, 124 PCX, 50 BMP and one TGA; 181 proprietary `.spr` and 136 `.ani` files remain undecoded. Most UI images have 640×480 and 800×600 variants; replacing one at a larger pixel size has not been shown to make the game render it at native resolution.

`Interface/Grimoire/800x600/Backdrop.JPG` was selected because its blank pages avoid generated text and sprite frame alignment. The original is 800×600 RGB JPEG. The generated candidates are:

| File in `experimental/` | Pixels | Observation |
| --- | ---: | --- |
| `grimoire_backdrop_qwen21_1024x768.png` | 1024×768 | Clearer page and leather texture; frame, tabs and clasp have been reinterpreted. |
| `grimoire_backdrop_qwen21_2400x1792.png` | 2400×1792 | Higher texture detail, but its aspect is the model's 2K preset (~1.339:1) rather than exact 4:3; it also reinterprets geometry. |
| `grimoire_backdrop_preserved_1600x1200.png` | 1600×1200 | CPU composite retains source geometry, color and spine, using only high-frequency Qwen detail inside the page surfaces. Subtle improvement; still requires in-game layout testing. |

`grimoire_backdrop_preserved_1600x1200_comparison.png` shows the source and composite side by side. Each generated candidate has a JSON manifest with source/output SHA-256 and the Manager job ID. In this run the 1024×768 job was `445afa4e760a46838870dd0fa39bdf06` and the 2400×1792 job was `6c9f3d71e04345c995681e82ee6017c4`.

## Reproduce

The installed local Qwen-Image 2.1 workbench at `http://127.0.0.1:8790/workbench/` runs through LocalModelManager's queued GPU scheduling. The script uses its loopback gateway; do not point it to raw ComfyUI port 8188. It checks the Qwen engine, submits one I2I reference job, polls the managed job, downloads the PNG and saves a manifest. It does not start/stop services or read/store credentials. The model profile is the installed INT8 ConvRot diffusion + Qwen3-VL encoder + Texture-Fix VAE. Official prompt enhancement is off so the exact restoration instruction reaches Qwen-Image 2.1. This run used 40 Euler/simple steps, CFG 1.0 and fixed seeds.

```powershell
python modernization/tools/qwen21_asset_trial.py --source 'Interface/Grimoire/800x600/Backdrop.JPG' --output 'modernization/assets/experimental/grimoire_backdrop_qwen21_1024x768.png' --size 1024x768 --steps 40 --seed 260926
python modernization/tools/qwen21_asset_trial.py --source 'Interface/Grimoire/800x600/Backdrop.JPG' --output 'modernization/assets/experimental/grimoire_backdrop_qwen21_2400x1792.png' --size 2400x1792 --steps 40 --seed 260927
python modernization/tools/compose_grimoire_trial.py --source 'Interface/Grimoire/800x600/Backdrop.JPG' --candidate 'modernization/assets/experimental/grimoire_backdrop_qwen21_2400x1792.png' --output 'modernization/assets/experimental/grimoire_backdrop_preserved_1600x1200.png'
```

`qwen21_asset_trial.py` supports `--job-id` to recover a completed owned trial if downloading was interrupted. It never overwrites an existing candidate. The composite requires Pillow; no other image model is used.

## Integration gate

The game has not loaded any generated image. First prove the engine accepts a different JPEG/BMP size at the same path and that labels, hit targets and book edges align. Compare the source and replacement in 800×600 and widescreen output, and keep a rollback of the original before any opt-in install. If the engine forces an 800×600 surface, use the composite only as source for a carefully reviewed same-size replacement or a new high-resolution renderer path; do not call wrapper enlargement native asset support.
