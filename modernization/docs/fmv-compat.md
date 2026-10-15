# Original 1.10 FMV playback on current Windows

## Authorized 1440p H.264 delivery — 2026-10-01 (delivery complete)

The user now authorizes Medieval/Intro1/intro0 SeedVR2 delivery at2560×1440,
Celtic/Greek H3 reconstruction with mixed/spliced edits, reusing completed media
and compressing all five asH.264 for Remastered1.1. This supersedes the old
stopped-batch instruction for this explicitly requested scope. Actual in-game
movie playback checks are authorized. Work and reproducible evidence are isolated
under `modernization/assets/fmv-delivery-1440p-20261001/`; its `REPORT.md` and
`manifest.json` identify current verified outputs, while `intro0-manager.json`
owns the one new full4× Manager job. No shared runtime/UI changes or baseline
promotion occur during preparation. Existing Medieval/Intro1 use reused3×
SeedVR2 image areas plusLanczos delivery resize, not fresh4× neural inference.
All five H.264 2560×1440 deliveries passed full decode, timing/source hash and
archival PCM checks. intro0's single new Manager job completed; no rerun needed.
Celtic reuses H3/SeedVR2/H3; Greek reuses the latest H3 two-shot whiteout splice,
without SeedVR2 middle footage. The separate MFPlay bridge has actual game
natural-end evidence for Medieval/Intro1. The user confirmed intro0 playback
normal and stated its exit was deliberate (2026-10-01: “是我退出的，播放没问题”).
Celtic/Greek passed hidden player-component natural-end checks; realm campaign
triggers are not tested. Audio endpoint output was verified separately.
Shared1.1 integration remains pending, with concrete instructions in that
directory's `HANDOFF.md`; the opt-in isolated launcher and final film copy hashes
are verified. Direct parent notification was blocked by the app's native-ancestor
messaging restriction. See `REPORT.md` and `mixed-player-validation.json` for
acceptance scope, rather than interpreting older VfW checks asMP4 support.

## Renewed research checkpoint — 2026-10-01

Read-only research; no inference jobs submitted, stopped batches resumed, downloads, runtime video replacement or game launches. Re-read historical evidence below and probed 29 existing original/restoration/remake media files. Inventory and fetched community-source hashes: `modernization/assets/fmv-research-20261001/`. Historical visual verdicts are attributed to recorded review, not newly repeated viewing. `game/FMV` currently probes as original Indeo files, not proof that these are the launcher's active installed runtime; resolve the actual latest runtime before future integration.

### Actual source and completed work

All five source films are 640x360, 16:9 with stereo PCM s16le at 22050 Hz. Celtic is 15.7s/10fps; Greek 16.625s/16fps; Medieval 42s/16fps; Intro1 63.125s/16fps; intro0 112.25s/16fps. Stream time slots are not always decoded image counts. Prior verification reports Celtic157, Greek261, Medieval642, Intro1 997 decoded frames; the original time-slot counts are157/266/672/1010, respectively.

Prior SeedVR2 2x and VideoBit RepNet tests used intro0 40–45s. SeedVR2 better preserved burnt-in Chinese text; RepNet introduced jagged/noisy text. The later SeedVR2 3x batch finished Celtic/Greek/Medieval/Intro1 but was stopped by the user for limited visual benefit, with intro0 cancelled. The completed 1920x1440 previews remain under `D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/1920x1440/`; their image area is1920x1080 with180px top/bottom bars, not native4:3 source. Timestamp and PCM verification already exists; it must be reused rather than assumed or discarded.

H3 Ref2VA, text-led reconstruction, reference-frame regeneration and hybrid H3/SeedVR/H3 edits were separately tested for Celtic/Greek. They generated more modern-looking material but altered geometry, motion and event continuity; prompt `fully_preserved` cannot guarantee preservation. The later Greek direction explicitly favoured source-constrained detail-density restoration. The user accepted the existing Celtic three-part splice and stopped further H3 work on2026-09-29. Do not automatically regenerate or promote it. External preview availability does not establish runtime acceptance.

### Current local vs new community candidates

Authenticated Manager upscale catalog was rechecked: SeedVR2 7B Sharp FP8 and VideoBit RepNet Base, CDA HiFreq, CDA Smooth and RepNet GAN all report installed. Prior FMV evidence covers RepNet Base, not comparative FMV acceptance of all four presets. Creature video results do not establish film quality. A short FMV comparison of existing CDA variants is a useful next hypothesis before adding new models; smooth vs HiFreq suitability for this rendered footage is not verified.

Manager's current SeedVR video worker uses batch_size9, uniform batches, chunk_size180, temporal_overlap3, Lab colour correction, CPU tensor offload and tiled VAE. At10fps nine frames cover about0.9s; at16fps about0.56s. Inference chunk boundaries and genuine scene cuts therefore need dedicated review. Installed CLI defaults seed42 and zero input/latent noise; current image/sprite workflow used batch1 and provides no evidence about this video profile's long-term temporal stability. Manager normalizes previews to H.264 CRF18 yuv420p/AAC192k; this delivery can lose fine Chinese strokes and gradients and is not a lossless master.

Checked [SeedVR2 ComfyUI upstream README](https://github.com/numz/ComfyUI-SeedVR2_VideoUpscaler) discusses overlap/Hann blending, streaming chunks, Lab tile/reference alignment fixes and an FFmpeg10-bit backend. These are upstream features/release claims, not verification that the installed Manager exposes each option. Do not silently change the shared worker. Upstream10-bit support will not benefit a final Manager path that re-encodes to8-bit yuv420p without separately changing that delivery design.

[RealBasicVSR](https://github.com/ckkelvinchan/RealBasicVSR) and [BasicVSR++](https://github.com/ckkelvinchan/BasicVSR_PlusPlus) are source-accessible temporal restoration alternatives worth considering for conservative recovery/codec-noise removal. They are not registered Manager candidates in this check and were not downloaded or executed. Their legacy MMEditing/MMCV/PyTorch dependencies need a separate runtime compatibility review on the RTX5090; documented old installation commands must not be applied blindly to shared production. RealBasicVSR's pre-cleaning may help real degradations but may also smooth small rendered features. BasicVSR++ trained degradation profiles are not guaranteed to match Indeo footage. Attempts to fetch StableVSR/SeedVR primary READMEs returned404; no unverified feature claims are based on those failed sources.

### Recommended next bounded test, not executed here

Start by reusing one existing source-aligned5s intro0 subtitle segment and one3–5s Greek/Celtic clip containing dark detail, portal motion and a real cut. Compare Lanczos, existing saved SeedVR2 result, and Manager CDA Smooth/HiFreq candidates. Only add a new SeedVR job when an explicitly different profile/input/target question requires it; preserve IDs/hashes before polling. Assess moving text/edges, invented textures, gradient banding, light/portal flicker and scene/chunk boundaries using actual video loops and full-resolution paired crops, not only still sharpness. Avoid optical-flow scores across cuts. No blanket interpolation to24/60fps; retain source decoded PTS and original PCM in archival delivery.

Use immutable original Indeo as input rather than recompressed MSVC compatibility AVI. Separate output tiers: preserved high-quality master, convenient compressed preview, and actual game-playable delivery. Inference should initially target2x1280x720 vs existing3x1920x1080; choose perceptual gain, not resolution labels. Subtitle regions may be reconstructed independently with conventional scaling/source masks if AI damages letters; this requires a stable timed region/mask, not unverified generated text. Moderate restoration and source/detail blending are possible hypotheses but must be compared against plain Lanczos.

Original+light CRT and SeedVR+CRT are display experiments, not video restoration. Existing creature4x CRT approval does not establish FMV acceptance. 640x360 to1920x1080 has3x sampling headroom, but subtitle readability, playback placement and final1920x1440 bars must be checked at the actual output size. Do not bake a display mask into masters; display optional CRT after image/video compositing, keeping masters reusable.

Runtime integration remains independent: MSVC AVI works with VfW but is lossy RGB555; past1280x720 AVI visibly cropped in the800x600 window. A2K master cannot simply replace the same AVI filename. Modern playback hook vs compatible downscaled640x360 delivery must be evaluated against actual latest runtime dimensions/centering. Preserve existing save/audio/FMVs, backups and user-testing checkpoints.

On 2026-09-28, the user-provided installation at
`D:/BaiduNetdiskDownload/魔法师传奇中文版1.10` skipped its startup movies despite
`CFG/prefs.cfg` setting `PlayFMV=TRUE` and `PlayFMVOut=TRUE`. Its five AVI files
were present and the community `Chaos.exe` matched SHA-256
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
`intro0.avi`, `Intro1.avi`, and `Medieval.avi` use Indeo IV50; `Celtic.avi`
and `Greek.avi` use Indeo IV41. The bundled cnc-ddraw registers
`vidc.iv41=ir41_32.ax` and `vidc.iv50=ir50_32.dll`, but those codec files are
absent on this Windows system. Direct Windows VfW `AVIStreamGetFrameOpen`
failed for all five originals. The original game showed its main menu without
the startup film and advanced through the new-game menu.

All five files were converted to AVI with Microsoft Video 1 (`MSVC`), preserving
their original 640×360 dimensions, frame rate, duration, frame count, and
unmodified PCM audio stream. The first Cinepak trial was rejected because VfW
could not open a frame on this system. All five MSVC conversions passed VfW
frame-open and first-frame decode checks; FFmpeg decoded their full streams.
In the original installation, the startup video was observed playing with
Chinese subtitles at launch and after 45 seconds, and the main menu appeared
after the film finished. Clicking New Game then entered difficulty selection;
confirming Enter led to battle without an additional film in this observed flow.
Do not claim a separate New Game film was restored based on this test.

The original Indeo files are backed up byte-for-byte in
`D:/Games/MagicMayham-backups/original-fmv-indeo-20260928/FMV/`. The five
converted files are installed at the same names under the user-provided
installation's `FMV/`. Per-file original and installed SHA-256 hashes are in
`modernization/logs/original-fmv-compat-20260928.json`. To roll back, close
the game and copy the backed-up AVIs over that installation's `FMV/` files.
That original-installation test did not change the project runtime. The later
Wide169 integration and centering are recorded below.

## Wide169 playback and centering (2026-09-29)

The five original-sized 640×360 MSVC/PCM AVIs were installed into the
independent `game-wide169/FMV/` runtime from immutable
`modernization/build/wide169/package-v13-fmv-center/`. This preserves their
original timing, Chinese subtitles and PCM audio; the external HD restoration
experiments below were not installed. The installed entry is
`game/Chaos-Wide169-Trial.exe` (SHA-256
`84d201637ce3ccebf49b8c9f930c1e5d41083ecc40015d342e19e6ef9b232448`),
which launches `game-wide169/Chaos-Wide169-engine.exe` (SHA-256
`dbce6a86bfd9becefc3e680078b9f674c944cdb94352374484079c81fe4899dc`).

The preceding engine (SHA-256
`1d2df6135238dec69f6ec74280440a06b43c66353c886f42633f4143d710b16f`)
used `(80,120)` for both the startup and in-game FMV origin, appropriate to
800×600 but top-left on Wide169's 1280×720 canvas. The hash-gated patch in
`modernization/tools/wide169_fmv_center.py` verifies the old values at preferred
VAs `0x5C6FB8/0x5C6FBC` and `0x5C7588/0x5C758C`, then sets both paths to
`(320,180) = ((1280-640)/2,(720-360)/2)`. It also updates the launcher's
embedded engine hash. The installed launcher displayed the startup film with
Chinese subtitles at the centered position; evidence is
`modernization/logs/wide169-fmv-center-installed-topmost.png`. Pixel sampling
of that 2576×1479 desktop capture found the bright video body at approximately
x=655–1925, y=391–1110; dark edge pixels account for the small difference
from the expected 1280×720 output rectangle centered in the game client.
Other in-game film triggers were not individually played through in this check.

Package manifest hashes cover 5070 files. Before modifying the Wide169 runtime,
the original AVIs were saved under
`modernization/backups/wide169/fmv-compat-1790688387123814000/`; the preceding
launcher, engine and install state are under
`modernization/backups/wide169/fmv-center-1790688961355333800/`.
`modernization/wide169-installed.json` identifies the current installed package.

## Local video restoration evaluation (2026-09-28)

All evaluation outputs are under
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/`. The original
Indeo AVI is the source; the test segment is `intro0.avi` at 00:40–00:45,
transcoded to a high-quality H.264 intermediate for the Manager API. The local
RTX 5090 D has 32 GB VRAM. The Manager gateway reported no active jobs before
the tests, and all model runs used its queue.

- VideoBit RepNet base at 2× produced a 1280×720 MP4. It sharpened textures,
  but made the burnt-in Chinese subtitle jagged and noisy. This is a fidelity
  problem for full films, even though the video job completed successfully.
- SeedVR2 7B Sharp at 2× produced a 1280×720 MP4. It retained the subtitle
  strokes much better and kept the wood and camera motion closer to the source.
  A 5-second test completed in about 150 seconds through Manager. A complete
  15.7-second `Celtic.avi` test also completed in about 184 seconds, preserving
  its 10 FPS video cadence and AAC audio in the test MP4 with about 0.01-second
  duration difference. It is the preferred faithful restoration candidate;
  this initial 2× evaluation is superseded by the five-film 3× batch below.
- MiniMax H3 Ref2VA was tested locally with the same 5-second video plus its
  first frame as references. A 12-step 640×352, 24 FPS, silent render completed
  in about 72 seconds. The camera and wooden interior were reinterpreted;
  objects shifted and overlapped, and the subtitle became distorted pseudo-text.
  It is a creative remake option, not a frame-faithful restoration path.
- A 1280×720 SeedVR2 result encoded back to MSVC AVI was displayed by the
  original game, but the 800×600 game window cropped the 1280-wide film.
  Keep 2× masters external. A game-compatible delivery needs a separate
  640×360 encode (or explicit engine/display work). The installed original
  `FMV/` files were not changed in this evaluation.

Community research: [official MiniMax H3 model card](https://huggingface.co/MiniMaxAI/MiniMax-H3)
describes Ref2VA video references and the 4–15 second, 24 FPS output grid.
Its H3-Regenerate-2K route regenerates H3 output in context, but the 2K module
is not open-sourced and is not a direct upscaler for legacy AVI footage.
The [community H3 latent upscaler](https://huggingface.co/LBH-123-AI/Minimax_h3_latent_Upscaler)
works on H3's 24-channel latents during generation, so it cannot directly
upscale these AVI files; its node/weights are not installed locally. The
[community H3 Fun ControlNet Union 2.0](https://huggingface.co/alibaba-pai/MiniMax-H3-Fun-Controlnet-Union-2.0)
supports edge/depth/gray guided video remake with a 13.5 GB branch checkpoint.
The prior local v1 Fun ControlNet integration crashed during model loading
(`D:/GitHub/LocalModelManager/docs/architecture.md`), so v2 requires a separate
runtime compatibility trial before use. The community
[MiniMax H3 Video Studio](https://github.com/siyuan-liu31/minimax-h3-video-studio)
offers V2V/RV2V workflows, but these are re-generation workflows rather than
guaranteed frame-preserving super-resolution.

## 1920×1440 delivery policy (2026-09-28)

**Batch stopped by user after visual review:** overall improvement was judged
limited. Celtic, Greek, Medieval and Intro1 finished and passed complete
decode, source-timestamp, PCM identity and VfW first/middle/end checks.
The unfinished intro0 job was cancelled through Manager; the result collector
was stopped. Keep completed comparison media and original backups. Do not
resume this batch or install the HD files without a new user instruction.

The user selected SeedVR2 for full-film restoration and requested 1920×1440,
with this task scoped to video compatibility and super-resolution. Use local
`seedvr2_ema_7b_sharp_fp8_e4m3fn.safetensors` through LocalModelManager's queue.
The source image remains 16:9: upscale 640×360 to 1920×1080, then center it on
the 1920×1440 canvas with 180 black pixels above and below. Do not stretch
the source into 4:3 or interpolate additional motion frames.

All media and the collection/verification scripts are under
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/1920x1440/`.
Deliver three formats: H.264/AAC MP4 for convenient preview; H.264/original
PCM MKV in `masters/` for preservation; MSVC/original PCM AVI in `compat-avi/`
for the Windows VfW playback path. MSVC's RGB555 colour and additional lossy
encoding make its AVI a compatibility delivery rather than the best master.

Preserve decoded frame timestamps, not just average FPS and total duration.
The original AVI timing includes held-frame gaps: Greek decodes 261 frames
from 266 time slots; Medieval 642/672; Intro1 997/1010; intro0 1756/1796.
Celtic has 157/157 slots. SeedVR2's streaming MP4 normalizes these into a
constant average cadence. Reassign each restored frame its original decoded
timestamp during final encoding. The generated `setpts` expression restores
the held-frame gaps without creating or dropping image frames. Use a precise
encoder time base and `fps_mode=passthrough`; never trim to the shorter stream
with `-shortest`, which can remove a final frame or the last PCM audio packet.

Verification must compare every decoded video timestamp to the original,
count all frames, fully decode each deliverable, compare PCM stream SHA-256
for MKV/AVI, and open/decode first, middle and final stream positions through
Windows `AVIStreamGetFrameOpen`/`AVIStreamGetFrame`. The stream length can
include held-frame slots and therefore differ from decoded image count.
Per-file evidence is saved in `manifest.json` and `verification.json` beside
the media. A successful VfW check establishes codec compatibility; it does
not establish viewport fitting in any development runtime. This batch stays
external to the game installations.

## H3 Celtic remake follow-up (2026-09-28)

After stopping SeedVR2 for limited perceived improvement, the user requested
community research to optimize the H3 prompt/workflow and then a Celtic trial.
This is a new H3 evaluation; do not resume the cancelled SeedVR2 batch.

Primary sources checked:
- [MiniMax official full-reference prompt guide](https://github.com/MiniMax-AI/MiniMax-H3/blob/main/skills/h3-prompt-writing/references/ref-en.txt):
  six English sections (`subject_definitions`, `summary`, `retention_analysis`,
  `detailed_description`, `overall_soundscape`, `non_diegetic_music`), explicit
  `<Video N>` and `<Picture N>` roles, `fully_preserved` for source editing,
  chronological shot descriptions and concrete timed composition anchors.
- [Community H3 Video Studio guide](https://github.com/siyuan-liu31/minimax-h3-video-studio/blob/main/docs/h3-prompt-guide.md):
  separate Ref2VA from FL2VA, reference videos limited to 15 seconds total,
  and official Base sampling at 20 steps, `res_multistep`/`simple` with
  `BasicGuider` and no Turbo LoRA. The local frame helper rounds to its H3
  frame grid; its actual output must be checked instead of assuming the
  community UI's duration formula.
- [Comfy-Org Ref2VA template](https://github.com/Comfy-Org/workflow_templates/blob/main/templates/video_minimax_h3_r2v.json):
  independently confirms 20 steps, `res_multistep`, `simple`, `denoise=1`.
  This remains reference-conditioned generation, not low-denoise img2img or
  the unreleased H3-Regenerate-2K module.

The initial trial splits the 15.7-second Celtic into 0–8 and 8–15.7 second
source references; each run requests 8 seconds (192 frames at 24 FPS),
1024×576, 20 steps, seed 42, CFG 1, no LoRA, with three original frame
anchors and the original source video. Reference audio is encoded, but
generated audio is disabled; postprocessing restores the original PCM for
the MKV and AAC for MP4 preview. No game files are changed. H3 can still
rearrange geometry and timing; prompt retention markers are instructions,
not a guarantee. The output is an experimental remake, not a restoration
acceptance. Inputs, prompts, job IDs and output are under
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-celtic/`.

The two Manager-owned jobs (`2a8514c7229f4b3a8c64e301dcc5e4af`,
`a09f7697b1d84d9c8c79a8e67c6f9506`) completed. Their 192-frame, 1024×576
H3 outputs were joined to a 377-frame, 15.707-second MP4 preview and an MKV
carrying PCM copied byte-for-byte from the original (stream SHA-256
`bad5b51531006368e0e8621750d7757fef58317b91ae16a7dd113ea6f7dcb57a`).
The preview fully decoded. The outputs are in the same `h3-celtic/` directory.
After both jobs, no Manager workbench jobs remained active and GPU use dropped
from roughly 28.1 GB during sampling to 2.9 GB; no out-of-memory event was
reported. The first run took 373.2 seconds. This 20-step, 192-frame,
1024×576 setting was much heavier than the previous 12-step, approximately
5-second, 640×352 experiment, so a two-minute runtime expectation does not
apply to this profile.

Visual review of `segment-1-comparison.png` and `segment-2-comparison.png`
found that H3 retained the initial stone-gate composition and some final
column/landscape frames, but changed the perspective and electrical-web
structure around 4 seconds and prolonged the bright doorway around 10
seconds. It is still a creative remake, not a faithful source-preserving
restoration. Do not install it as a game FMV without further user review.

## Old-video reconstruction direction (2026-09-28)

The user clarified that the objective is to reconstruct an old video with
modern visual quality, rather than merely clean or upscale the legacy game's
original rendering. The preservation-heavy Celtic H3 prompt above was too
restrictive for this goal. A new 5.17-second, 124-frame, 768×448 / 12-step
Manager-owned A/B used the same Celtic opening:

- Ref2VA job `946d97c6bc184c00a1f219f4f68b933e` provided the old clip as a
  reference with a modern-cinema reconstruction prompt. It still copied much
  of the old visual style and held a wide shot instead of pushing in.
- Text-only FL2VA job `200524bdf9be4dbb82e901a65df4fc4d` described the
  visual story and camera move without input video. It produced materially
  new weathered standing stones, grass, atmosphere, cinematic light and portal
  effects, with a forward camera push. The broad motif is recognizable, while
  exact stone shape and effect timing changed. This is the useful baseline for
  **creative reconstruction**, not a frame-accurate remaster.

The generated files, request prompts and `three-way-comparison.png` are under
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-celtic/video-reconstruction/`.
The preferred preview `Celtic-H3-text-only-with-original-audio.mp4` adds the
original soundtrack for comparison; full video decode passed. Both jobs
completed through LocalModelManager, no workbench jobs remained, and GPU use
returned to approximately 2.9 GB. No game installation was modified. For any
longer reconstruction, use source video for shot analysis/storyboarding, then
  generate new scenes from a shot-by-shot prompt; include reference frames only
  when their composition/identity is more important than a fresh visual style.

### Complete Celtic creative reconstruction

On request, the accepted text-only opening was continued through two new
Manager-owned H3 FL2VA jobs, `d7adea716093437faf53a0c0cfe990bb` and
`987606f698954369a7b558a6dd82d6e4`. Each uses the preceding segment's
last generated frame as its first-frame anchor, an original-video storyboard
for the next event, and a new modern-fantasy prompt; the old video frames
were not fed back as appearance references. Segment 2 travels through the
blue-white portal; segment 3 emerges onto a sunset terrace with classical
columns and distant mountains. Both are 124 frames at 768×448, 24 FPS,
12 steps, and completed successfully through LocalModelManager. Three H3
segments plus a 5-frame final hold produce a 377-frame, approximately
15.707-second complete film. The MP4 preview includes AAC from the original;
the MKV retains the original PCM stream byte-for-byte (SHA-256
`bad5b51531006368e0e8621750d7757fef58317b91ae16a7dd113ea6f7dcb57a`).
Both final files fully decoded, and Manager had no active workbench jobs after
completion. Deliverables and a timed contact sheet are under
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-celtic/video-reconstruction/`:
`Celtic-H3-full-reconstruction.mp4`, `Celtic-H3-full-original-PCM.mkv`,
`Celtic-H3-full-contact.png`, and `Celtic-H3-full-manifest.json`.
Contact-sheet inspection found a coherent portal passage and a sunset reveal.
The ending created more columns than the original; this is a creative
reconstruction and is not frame-accurate or game-installed.

### Celtic map-descent correction

The user identified an omitted event in the first full creative reconstruction:
at approximately 6–8.5 seconds, the original camera exits the blue-white
energy into a high aerial view of an island map, then dives toward it before
the white doorway and column landscape. The user's enhanced map reference is
`modernization/playtests/mixed-ui-v4/game-wide169/Interface/RealmViewer/800x600/Greek_Map.bmp`
(2560×1440). This is a visual reference, not a runtime asset edit.

Manager-owned H3 Ref2VA job `4cd28cee2527403784e8dcd5c80ecd43` used
the preceding portal frame plus a crop of that map to generate a new aerial
approach and descent. Its final ~1 second jumped back to the stone gate, so
only its first 100 frames were kept. FL2VA job
`a0617969d8cc4ef4b15d70c67d79d089` continues from frame 99 into a
magical aperture, dark passage, white door and sunset columns. The accepted
first 124 frames, 100 map-descent frames and 153 new ending frames form a
377-frame, 15.707-second film at 768×448/24 FPS. Full decode passed;
the archival MKV's PCM stream hash equals the original
(`bad5b51531006368e0e8621750d7757fef58317b91ae16a7dd113ea6f7dcb57a`).
Timed contact-sheet review confirms the island appears around 6–10 seconds,
followed by the white doorway and sunset columns. The timing and geography
are creative interpretations of the source and do not claim exact frame
correspondence. The corrected MP4 `Celtic-H3-with-map-reconstruction.mp4`,
PCM MKV, manifest and contact sheet are in the `video-reconstruction/` media
directory. The prior complete version remains there for comparison. No game
files were changed.

### Celtic northwest landing correction

The user clarified the geography of the aerial descent: after crossing the
portal, the camera lands in the snowy mountains at the **upper left of the
main island**, inside the red box on the supplied enhanced map, rather than
at the island center. The map crop is retained as
`northwest-snow-mountains-reference.png`. Manager H3 jobs
`75a547e002aa43268b0fb1d5656200c4` and
`802b6764338645f4b6bfa19cae1ab5a0` generated the corrected descent and
continuation. The descent visibly tracks from the island overview into those
snowy cliffs. The first assembly cut off most of the sunset-column ending;
the final edit uses all 141 continuation frames at a faster playback rate and
holds the final panorama briefly. It preserves the 124-frame opening and
124-frame northwest descent, totaling 377 frames at 768×448/24 FPS and
15.708 seconds. The preview `Celtic-H3-northwest-final-preview.mp4` and
archival `Celtic-H3-northwest-final-original-PCM.mkv` live in the same
external `video-reconstruction/` media directory. The MP4 fully decodes and
the archival PCM stream matches the original SHA-256 above. The earlier
center-landing and first northwest assemblies remain available for comparison.
This remains a creative reconstruction and was not installed in the game.

The user's subsequent review found the map dive lacked the original's
blue-white energy web. The external `Celtic-H3-northwest-energy-preview.mp4`
adds an animated, semi-transparent extraction of that effect over the map
sequence (roughly 5.25–10.95 seconds). This retains the northwest snowy
landing and sunset-column ending. The companion
`Celtic-H3-northwest-energy-original-PCM.mkv` keeps source PCM with the same
SHA-256, and the 377-frame preview fully decodes. The edit recipe and visual
contact sheet are `restore_mid_energy.py` and `northwest-energy-contact.png`
in the external media directory. This is a review candidate, not a runtime
replacement.

## Greek creative splice (2026-09-29)

### Video-reference-only experiment

The user then requested exactly two H3 generations, with the splice hidden
inside the portal whiteout. New Manager job
`1a64209fef5c4119b51d7e41dd0242ce` generated one continuous dungeon,
transport dais and energy-cylinder shot ending in full white. It was joined
to the existing video-only H3 coast job
`152cf85146ff408e8e48c60741292d55`. The coastal image fades in from
white after the cut while the black letterbox bars remain stable. The
resulting external review candidate is
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-greek/video-reconstruction/Greek-H3-two-shot-white-splice-preview.mp4`.
The 1920×1440 preview has 399 frames at 24 FPS, lasts 16.624 seconds and
fully decodes. The archival MKV retains the original PCM stream with SHA-256
`97bda8742f55dfaf8561cdbe905ecbbffcd7f608c172e27007f0fe22b90b17c7`.
This edit uses two H3 video segments and no SeedVR2 footage in its image
track. It remains an external creative preview, pending visual review; game
files were not changed.

The user requested removing all reference pictures and trying a
high-definition-remake prompt with the video as the only reference.
`greek_video_only_remaster.py` sends one `ref_videos` item and no image
inputs for each segment. Jobs `76252329fad341329d59ed126bbc7519`,
`abfad20e5d0748a6b03a3f649859f858`, and
`152cf85146ff408e8e48c60741292d55` completed through Manager.
The new external candidate is
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-greek/video-reconstruction/Greek-H3-video-only-remaster-preview.mp4`.
The 1920×1440 canvas contains scaled 1024×576 H3 footage, not native H3 2K
generation. It has 399 frames, about 16.625 seconds and passed full decode.
The archival MKV preserves source PCM with SHA-256
`97bda8742f55dfaf8561cdbe905ecbbffcd7f608c172e27007f0fe22b90b17c7`.
The dungeon gains visible stone/platform detail, but the two independently
generated dungeon/portal segments differ at the first join: the cylinder
appears, then returns to an earlier activation stage. This candidate remains
for user comparison; do not call its event continuity complete. No runtime
assets were modified.

At the user's request to process the next film, Greek uses the same external
three-part review approach as Celtic: H3 reconstruction of the torch-lit
stone corridor, the original-derived SeedVR2 1920×1440 portal interval, and
H3 reconstruction of the moonlit sea. The source timeline is 16.625 seconds.
The H3 prompt keeps the first shot continuous and gives explicit timed beats
for the portal platform and the ending sea glide. Manager jobs
`18b00f2a49944faf89f362e289d65506` and
`d84a90a32ab5458dbb799cfc3bda2af4` completed. The join uses 0.3-second
fades around 4.5–4.8 and 8.3–8.6 seconds. The preview
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-greek/video-reconstruction/Greek-H3-SeedVR2-H3-preview.mp4`
is 1920×1440, 399 frames/24 FPS, 16.624 seconds and passed full decode.
Its companion `Greek-H3-SeedVR2-H3-original-PCM.mkv` preserves the original
PCM audio stream (SHA-256
`97bda8742f55dfaf8561cdbe905ecbbffcd7f608c172e27007f0fe22b90b17c7`).
The external media directory also contains the two source segments, prompt
script and contact sheet. This is a creative review candidate and was not
installed into the game.

The user judged that first Greek splice poor and requested that H3 generate
as much of the film as possible, with a high-definition-remake description
and detailed pre-portal dungeon materials. The new external candidate
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-greek/video-reconstruction/Greek-H3-full-remaster-preview.mp4`
uses H3 for all three visual segments: dungeon, energy cylinder/transition,
and moonlit coast. The prompt specifies cracked limestone blocks, soot,
damaged flagstones, iron torch brackets, flame-lit haze, the carved circular
dais, fine rotating silver energy strands, and timed shot beats in the
official `[Shot N] At MM:SS.mmm` syntax. Source/SeedVR2 frames serve only as
visual references, not as footage in this edit. Manager jobs
`8c168518d1004d2eb2cc7c3823d7c280`,
`7ec31f760755404eb6ece313b17ecbf5`, and
`ec77d4c672fc4b1c98e047e0ff92a4d2` completed. The 1920×1440 preview is
399 frames/24 FPS, 16.624 seconds and fully decodes. Its archival MKV retains
the original PCM stream with SHA-256
`97bda8742f55dfaf8561cdbe905ecbbffcd7f608c172e27007f0fe22b90b17c7`.
Contact-sheet inspection confirms dungeon → cylindrical portal → moonlit
coast in order. This remains a creative interpretation, pending user review,
and was not installed in the game.

The user clarified that Greek should be a *source-constrained detail-density
restoration*, not a scene remake. The subsequent H3 Ref2VA workflow supplies
the SeedVR2 source clip itself as `<Video 1>` plus beginning, middle and ending
frames as composition anchors for each segment. Its prompts mark the video,
camera path, object count, geometry and timing `fully_preserved`, asking only
for finer detail inside existing stone, flame, energy and coastal surfaces.
The dungeon trial job `6245daa733fc47f38ec617169e89a872`, portal job
`4933aa76de7b492181f872ae2e13a698`, and coast job
`7593a790e1154e55944af8b04cc5f957` completed through Manager. The
external review file is
`D:/AI/LocalModelManager/media/magic-mayhem-fmv-20260928/h3-greek/video-reconstruction/Greek-H3-density-restoration-preview.mp4`.
Three H3 segments cover the full film; only source-aligned reference frames,
no SeedVR2 footage, are used in the finished image track. The portal segment
is retimed to fit the original 8.4-second coastal arrival. The preview is
1920×1440, 399 frames/24 FPS, 16.624 seconds and fully decodes. Its archival
MKV's PCM stream matches the original SHA-256 above. Contact-sheet review
shows the source scene sequence and broad composition retained; fine detail
gain and seam quality remain subjective review points. No game files changed.

The next review clarified the intended splice: H3 opening, original-derived
SeedVR2 middle, and H3 ending. The interim external preview
`Celtic-H3-SeedVR2-H3-splice-preview.mp4` uses the existing H3 column ending.
It restores the three-part structure and source PCM (377 frames, 15.707 s,
full decode), but the existing ending starts with a bright H3 portal and its
timing is not yet a close match to the source. A new seven-second ending
prompt and manager request are saved as `h3_timed_ending.py` and
`h3-timed-ending-request.json`. The prompt uses the official H3 syntax
`[Shot N] At MM:SS.mmm` with explicit doorway, column, and landscape beats.
The official guide says the first shot has no cut timestamp and later cut
times must increase within the requested duration. Manager job
`3f5f336f6077446a8da1a5c18f30d2b4` failed before generation because
available VRAM remained below its configured 27648 MiB dispatch threshold;
the threshold was not bypassed. On 2026-09-29 the user found the existing
three-part splice acceptable and explicitly stopped further H3 generation
for this film. Keep that external candidate; do not retry the timed-ending
job automatically. The Manager VRAM threshold was adjusted separately in
the LocalModelManager project.

After rejecting the composited energy effect, the user requested a direct
splice with the original SeedVR2 upscale. The external review candidate
`Celtic-H3-SeedVR2-splice-preview.mp4` uses the H3 reconstructed opening
through 5.8 seconds and crosses to the preserved 1920×1440 SeedVR2 film
over 5.5–5.8 seconds, where the original's bright energy obscures the cut.
The original-derived map dive, white doorway and columns then play in full,
with their original effects and timing. The H3 opening is scaled into the
same 1920×1440 canvas. The 377-frame/24 FPS preview fully decodes; its
`Celtic-H3-SeedVR2-splice-original-PCM.mkv` companion preserves source PCM
with the hash above. This is an external review candidate and is not installed.


## Shared isolated1.1 integration installed, 2026-10-01

User authorized integrating the completed worker delivery. Installed at
`playtests/remastered-1.1-p1/MagicMayhem-Remastered-1.1.exe` with five formal
`runtime/FMV/{intro0,Intro1,Celtic,Greek,Medieval}.mp4` files (2560x1440 H.264,
403,943,694bytes combined) and the unchanged production `runtime/fmv_h264.dll`.
Worker manifest hashes and exact production DLL/launcher hashes were verified;
all media and module files match the worker's tested delivery. No new inference
or re-encoding. Playback evidence is reused with the original scope described
in `assets/fmv-delivery-1440p-20261001/HANDOFF.md`: actual isolated startup
playback for Medieval/Intro1/intro0; component playback for Celtic/Greek.
Campaign triggers remain pending user testing.

The rebuilt launcher is based on the delivery source; reversing just its early
FMV injection delta exactly recovers the current teammate-portrait launcher
source. Current resource101 (corridor pathfinding) and resource102 (latest QoL,
UI, close and left portrait fixes) are copied byte-for-byte from the installed
entry. No stale worker runtime snapshot was installed. DLL pin:
9b86df83d71198afe02474fbeae5380f55da99746cc051e6ac169d9263108789.
New launcher SHA256:
a48b350d99a50c79b234f0a4578f19526d375fd62989a87ebe6e4138f0e5dc99.
Engine SHA256 remains42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.

Exactly six runtime files added; all previously installed runtime assets,
settings and saves preserved. Existing AVIs remain available for the original
movie path when the MP4 is absent or the decoder fails. Existing PlayFMV and
PlayFMVOut preferences were left unchanged (both TRUE at installation).
Runtime primary surfaces and UI/battle resolution policy are unchanged.
`fmv-h264-events.jsonl` is a narrow mutable log exception in integrity/capture
tools so actual playback logs do not invalidate static asset checks.
Full5888-file integrity passed; protected1.0/v38 unchanged. No game was launched
by this integration session, per user testing checkpoint.

Build verification and installation delta checks:
`build/remastered-1.1-fmv-h264/{verification,installation-checks}.json`.
Backup: `backups/remastered-1.1-fmv-h264/` (prior entry and manifest).
Rollback with game closed:
`python modernization/tools/build_11_fmv_h264.py rollback`.
It restores the prior launcher/manifest and removes only the six hash-verified
added runtime files, retaining player preferences/saves and any playback log.
Current launcher source for future builds is the FMV integration build folder;
retain the guarded early hook and production DLL pin. See launcher architecture.

Installation initially hit WinError5/32: the installer's own pefile resource
mapping kept the target EXE open. Explicit PE.close in the shared resource helper
resolved it. Failed attempts left the original5882-file package hash-verified;
no gameplay process was terminated. Final backup hashes and rollback inventory
were checked after the successful installation.
