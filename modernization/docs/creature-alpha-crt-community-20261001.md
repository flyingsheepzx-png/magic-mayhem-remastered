# Creature transparency and CRT community research — 2026-10-01

## User feedback after offline comparisons

On 2026-10-01 the user liked the CRT 4x diagnostic result and explicitly asked the main implementation chat to try this shader. Creature asset replacement is deferred for now. This authorizes exploration of an opt-in CRT display route, not promotion of the CPU preview to verified GPU/runtime support or a change to the accepted battle rendering policy. All-treatment comparison: `modernization/assets/creature-seedvr-sheet-expanded-20261001/Phoenix/all-renderings-crt/index.html`; kernel/profile: `full_crt_lottes.py` and `Phoenix/full-crt-lottes/parameters.json` in the expanded review directory.

Scope: read-only community/source research prompted by Phoenix halo tests. No model downloads, inference, shader installation, runtime changes or game launch. This is a research recommendation, not a change to the accepted art plan. Source snapshots and hashes are under `modernization/assets/creature-crt-community-research-20261001/sources.json`. Mutable upstream files were inspected as of this date; hashes identify inspected text, not a pinned upstream release.

## Main conclusion

A light PC-CRT-inspired final-frame filter is worth comparing against unchanged source art. It can restore some perceptual pixel integration and make coarse shading less harsh; it cannot reconstruct missing anatomy/detail, remove contaminated sprite RGB accurately, or prove the game was designed for a particular CRT/connection. The graphics are from a Windows PC game, so VGA/RGB monitor behaviour is a better initial hypothesis than 240p composite TV simulation. Original target monitor, authoring display and signal path have not been established.

There are two independent approaches: improve the RGBA asset pipeline before super-resolution, or retain original assets and change presentation. They should be evaluated separately first. Combining AI detail, aggressive sharpening, scanlines and bloom makes it hard to identify the actual benefit.

## Community transparency alternatives

1. **Pre-inference RGB colour bleed in alpha-zero regions.** Keep source alpha unchanged, but fill hidden transparent RGB close to the subject with nearest valid subject colours before an RGB-only upscaler sees it. This is fundamentally different from inference over grey/black followed by cleanup. Godot documents `Image.fix_alpha_edges()` as blending low-alpha pixels with neighbours. Our SeedVR implementation separates RGB/alpha and feeds RGB to the model, so hidden RGB matters. Use bounded per-frame bleed and isolated padded cells, retaining raw sources. This prevents a neutral background colour being mixed into the immediate edge, but can affect the model's imagined background or thin structures. It requires an actual new A/B test; not tested here.

2. **Premultiplied-alpha filtering/compositing.** Standard resize/filtering should operate on colour multiplied by alpha, then divide safely when returning to straight alpha; final renderer blending must match the stored convention. ImageWorsener explains the halo from independently averaging colour and alpha. Godot exposes `premultiply_alpha()`. This helps deterministic resize/mipmap/composite operations, but feeding premultiplied RGB into an RGB generative model and expecting it to ignore alpha-zero black is not a solution. It is not a replacement for a correct inference input.

3. **Alternative RGB/alpha pipelines.** Real-ESRGAN's official implementation accepts RGBA, processes RGB and alpha separately and offers `alpha_upsampler='realesrgan'` or the `bicubic`-named option; inspected code actually uses `cv2.INTER_LINEAR` in the latter branch. This is not joint RGBA generation and does not automatically remove contaminated RGB. xBRZ's command-line community implementation reports testing on 32-bit RGBA PNG, with deterministic integer 2–5x scaling. It is worth an RGBA baseline for sprite outlines but may round shapes or merge narrow feathers; frame-to-frame branch changes can still cause edge jitter. No new models/algorithms were installed or tested for this research.

4. **True alpha-aware learned SR / matting.** Architecturally attractive, but the checked Real-ESRGAN and current SeedVR2 implementations do not establish joint RGBA inference. Generic background-removal models are a poor automatic substitute for preserving tiny appendages and internal sprite holes. No verified ready-to-run locally registered joint-RGBA model was found in this research; do not label a method alpha-aware merely because it accepts a PNG with alpha.

## What CRT filtering can and cannot do

CRT shaders simulate combinations of horizontal signal/beam response, scanlines, phosphor masks, gamma, glow/halation and geometry. Local pixel blending can soften stair steps and integrate colour patterns, with no anatomy hallucination. More blending also removes high-frequency detail. Apparent sharpness can improve from contrast and mask structure without increasing recovered image information.

Community discussions explicitly distinguish RGB/PVM and composite captures and show disagreement about how much real CRTs blend dithering: the analogue signal path matters, and CRT alone is not a guaranteed dithering blender. A strong composite/NTSC filter would be an artistic treatment for this PC game, not established restoration.

Apply CRT only after the battle scene, units and their backgrounds are composited. Per-sprite CRT processing makes the phosphor grid move with each unit and causes seams/glow problems; it does not reproduce a screen. Screen-anchored sampling is needed to avoid moving scanline/mask patterns. It can soften remaining halos into the scene, but cannot correctly recover foreground colour from them.

The established battle remains 1280x720 scaled 2x to 2560x1440. At only two output rows per source row, strong scanlines and dense masks have little sampling headroom and can reduce brightness, alias or shimmer. Independent native 1920x1440 UI pages should retain their present readability; the research does not authorize changing their fonts or render policy. CRT effects must be opt-in and reversible if ever integrated.

## Candidate filters and proposed first comparison

| Candidate | Verified basis | Suitable initial use | Main limitation |
|---|---|---|---|
| CRT-Easymode | Source describes a flat CRT shader for 1080p+; controls horizontal/vertical sharpness, mask strength, beam widths, scanline strength and gamma | First lightweight comparison, preferably weak scanlines/mask and flat geometry | Default scanline/cutoff behaviour may differ at 720p input; tuning and actual output capture required |
| CRT-Lottes | Public-domain source includes linear-gamma scaling, scanline/bloom weights and several shadow masks | Small shader implementation study / simple prototype | TV-like defaults should not be mistaken for calibrated PC-monitor emulation |
| CRT-Guest-Advanced | Inspected preset has 12 passes; source includes high-resolution scanline and no-scanline controls, beam, sharpness, glow, bloom and gamma | Flexible high-resolution PC-style experiment after a simple baseline | More passes/parameters, possible perf/brightness costs; inspected code GPL-2.0-or-later |
| CRT-Royale | Official docs discuss masks, resolution and performance; EDP shadow-mask examples can require near 4K for compelling detail | Later reference-quality comparison if output resolution and cost permit | Complex; 1440p may not support desired dense mask appearance |

Suggested isolated comparison uses the same existing battle screenshot (no new game launch needed): nearest/integer presentation, mild gamma-correct beam filtering without visible scanlines, weak CRT-Easymode-style treatment, then one original-vs-SeedVR asset scene comparison. Initial settings are hypotheses rather than measured prescriptions: no curvature, no deliberate chromatic misalignment, no simulated interlace, weak or disabled mask, low bloom, and screen-fixed patterns. Compare at full 2560x1440 and during movement before runtime acceptance. A CPU blur/scanline illustration must not be labelled an executed community shader.

## Sources

- [Godot Image API: fix_alpha_edges / premultiply_alpha](https://docs.godotengine.org/en/stable/classes/class_image.html)
- [ImageWorsener: resizing with transparency](https://entropymine.com/imageworsener/resizealpha/)
- [Real-ESRGAN actual alpha implementation](https://github.com/xinntao/Real-ESRGAN/blob/master/realesrgan/utils.py)
- [xBRZ RGBA command-line implementation](https://github.com/atheros/xbrzscale)
- [CRT-Easymode source](https://github.com/libretro/slang-shaders/blob/master/crt/shaders/crt-easymode.slang)
- [CRT-Lottes source](https://github.com/libretro/slang-shaders/blob/master/crt/shaders/crt-lottes.slang)
- [CRT-Guest-Advanced preset](https://github.com/libretro/slang-shaders/blob/master/crt/crt-guest-advanced.slangp)
- [CRT-Royale official documentation](https://docs.libretro.com/shader/crt_royale/)
- [Community: composite-vs-RGB comparisons are not interchangeable](https://forums.libretro.com/t/19193/30)
- [Community: dithering blending has blur tradeoffs](https://forums.libretro.com/t/30602/2)
- [Community: VGA PC monitor shader discussion](https://forums.libretro.com/t/19193/2533)

Limitations: posts are anecdotal, not measurements of this game. No CRT shader was executed and no gameplay/visual acceptance was performed. Browser surface was unavailable; public HTTP sources and forum search results were read directly. Forum excerpts were checked, not every full conversation. No conclusion about Magic & Mayhem's original display calibration or intentional dithering design is established.
