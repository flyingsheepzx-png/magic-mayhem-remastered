# Community SR review — 2026-09-30

User authorizes researching alternate local HD methods and installing models
compatible with LocalModelManager. Qwen-only project rule remains the default
outside this explicitly authorized SR pilot. No commercial/API image service used.

## Sources and relevance

- https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler : supports direct single
  image,7BSharp, tiledVAE and recommendedLAB correction. Existing managed model,
  no new redundant weight download. README snapshot seedvr.txt.
- https://github.com/chaiNNer-org/chaiNNer : community restoration workflows,
  Spandrel loader and OpenModelDB/interactive comparison references.
- https://openmodeldb.info/models/4x-PixelPerfectV4 : sprite-targeted ESRGAN4x,
  WTFPL. Deployed/passed inference; size/hash match catalog. pixel-installed.json.
- https://openmodeldb.info/models/4x-GameAI-2-0 : explicitly says unsuitable for
  very low resolution item icons; rejected for this icon task despite its name.
- https://openmodeldb.info/models/4x-Nomos8kSC : photograph/blur/JPEG model,
  not first choice for tiny rendered sprite icons; not installed.
- https://openmodeldb.info/models/4x-FSDedither-Riven : addresses ordered dithering
  in old game images; future terrain/background candidate, GPL3 metadata retained.
- https://openmodeldb.info/models/4x-Fatal-Pixels : sprite/pixel-art model,
  CC-BY-NC-SA4; not needed for this first trial, not installed.
- https://github.com/xinntao/Real-ESRGAN : restored primaryREADME after transient
  network failure. Mature non-prompted restoration/tile/alpha workflow; not a
  guarantee that its photographic/anime weights suit these sprites.

## Actual managed trials

Source-atlas256x192 uses six original book/chest frames3..8 at original size,
constant dark background, padded cells. No pre-enlarged reference and no prompt
sheet reconstruction. SeedVR2 generates1024x768 via jobdd6c24ccd5a643a9bc4137a4389d8b62.
PixelPerfectV4 generates same dimensions via Manager queued Comfy graph
jobe688201abe7d40b1a766ce720830ec07. Existing SeedVR2 independently processes the
800x600 original map into1920x1440 via job424bb0de1f914527833fd0770a546bdd.
All three succeeded. Runtime mediaD:/AI/LocalModelManager/media; copied reviewed
outputs retained here. GPU execution/lifecycle only via Manager.

Six-state comparison.png (actual filename six-state-comparison.png) columns:
Lanczos/currentHD/priorQwenSheet/SeedVR2/PixelPerfectV4. SeedVR2 gives clearer
page/metal detail; invented tiny page glyphs and residual edge grid need care.
PixelPerfectV4 smooths noise and coherent shapes but makes green emblem/metal
look too rounded/plastic and removes much texture. Neither result is declared
universally best. Prior Qwen sheet changes width/pose/state family more markedly.

Trial SPRs substitute all six states, keeping other15 payloads exact. Decode
checks cover all21frames: exact existing dimensions/name/offset/flags/alpha,
RGB565error<=9. Both preserve brighter pressed states; report
six-state-verification.json. Exact alpha/metadata do not establish artwork edge
coverage or gameplay acceptance. No SPR trial installed into runtime.

Map three-way preview shows originalLanczos, installedFullReadable, SeedVR2.
SeedVR2 better defines some rocks/trees but largely sharpens the original scene,
with darker/stronger contrast. No decisive improvement over the user-liked
FullReadable; keep installedmap SHA
1dd9b4d7b9da16b5d24010792029ef6ab8138910c866b39a0828b94386a392d8.

## Recommended production direction

Use non-prompted SR as first step for small sprites and all their states; CPU
resize to actual2x target, validate native masks/offsets and frame families.
SeedVR2 detail-first and PixelPerfect clean-form outputs remain alternatives
for user comparison. Generated HD does not apply to low-res battleHUD without
separate policy; independent page assets only remain the implementation target.
For readable re-art use one motif/master at a time, same outline/pose in each
state and explicit region-limited edits. Proposed Qwen prompt revision:
"Restore this one vintage fantasy toolbar object at exactly its current pose,
outline and center. Preserve hinges, cover angles, page boundary and green
emblem. Improve broad leather/paper/metal planes inside the existing outline.
No new lettering, symbols, objects, frames or background texture. Keep the
normal, highlighted and pressed versions geometrically aligned; only lighting
and the existing pressed highlight may change."
This prompt is proposed, not run/passed. Single-object references and common
state geometry are the principal workflow change; prompt wording cannot assure
pixel alignment. Keep procedural/native text outside generated imagery.
