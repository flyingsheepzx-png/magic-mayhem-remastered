# Phoenix soft-edge alpha trial

CPU-only eight-frame PBLD experiment reuses the saved SeedVR2 sheet RGB. No new inference or runtime changes.

Three arms: strict binary source alpha; Lanczos antialiased source alpha using unchanged raw RGB; identical antialiased alpha with newly exposed fringe RGB copied from the nearest originally covered pixel. Output dimensions are exactly 2x the source. New alpha support is restricted to two output pixels around original coverage. Padding prevents crop-edge resampling artefacts; no frame dimensions/offsets are changed.

Partial alpha smooths diagonal outlines at display size, but does not create more anatomical detail or establish higher accuracy. Raw RGB on the newly exposed fringe includes the grey inference-sheet background and can cause grey halos on white/black. Fringe repair mitigates this contamination heuristically; thin feathers and changing edge colours still require review. Antialiased alpha also changes some formerly opaque edge pixels to partial coverage.

Use comparison.png (first frame, grey/black/white backgrounds) and lossless animation-grey/black/white.png for eight frames. GIF is palette-quantized and should not be used to judge alpha. validation.json records new coverage and partial alpha counts. Saved numbered RGBA PNGs preserve actual alpha.

This demonstrates image-domain antialiasing only. Native SPR uses transparent skips/opaque runs; preserving these partial alpha values in-game requires separately verifying or changing renderer/asset support. No claim of runtime compatibility is made.
