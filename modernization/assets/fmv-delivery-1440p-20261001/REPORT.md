# 2560×1440 FMV delivery — completed 2026-10-01

Authorized selection: Medieval / Intro1 / intro0 SeedVR2; Celtic / Greek H3
reconstruction with mixed/spliced footage. H.264 delivery and actual gameplay
movie compatibility are required. Shared game/runtime/UI assets stay untouched
while the separate playback candidate is verified. All five deliveries are now
complete. No further inference is needed. Shared 1.1 integration remains separate.

## Final delivery

| Film | Frames | Duration (s) | MP4 bytes | Method |
|---|---:|---:|---:|---|
| Medieval | 642 | 42.001 | 63,449,621 | Reused SeedVR2 3× + Lanczos to 1440p |
| Intro1 | 997 | 63.124989 | 114,390,547 | Reused SeedVR2 3× + Lanczos to 1440p |
| intro0 | 1756 | 112.251438 | 192,037,672 | New SeedVR2 4× inference |
| Celtic | 377 | 15.707 | 19,634,713 | Reused H3 / SeedVR2 / H3 splice |
| Greek | 399 | 16.624989 | 14,431,141 | Reused latest H3 two-shot whiteout splice |

All MP4s are 2560×1440 H.264, with full decode, original source hash,
decoded-frame timing and archival PCM checks passed. Greek has no SeedVR2
middle footage. H3 edits retain creative changes in geometry/action and cannot
be described as faithful detail-only restoration. `index.html` provides all five
videos and full-resolution stills. `manifest.json` records commands and hashes.
The final five named copies in the isolated runtime and the production player/
launcher hashes were rechecked after removing test startup aliases.

## Completed now

Medieval: 642 decoded frames, 42.001s. Intro1: 997 decoded frames, 63.124989s.
Existing full SeedVR2 3× outputs reused, original 16:9 image cropped out of the
old 4:3 canvas, resized with Lanczos to 2560×1440. This is existing 3× neural
restoration plus conventional delivery resize, not fresh 4× inference. H.264
libx264 CRF18 / slow / yuv420p with AAC192k stereo 22050Hz. No motion
interpolation; original held-frame timing preserved, maximum frame PTS error
0.5ms. Full-stream decode passed; MKV companions preserve source PCM identity.
Individual original/input/output hashes are in `manifest.json`.

## Full intro0 inference

Owned authenticated Manager FIFO job `8285e1ea070e41d68403da548ef2049b`.
Input is the preserved source-derived 640×360 intermediate, 1756 decoded images.
Output requested 2560×1440. Full effective request/profile/model SHA256 in
`intro0-manager.json`. SeedVR2 7B Sharp FP8, model SHA256
`4261d18fd9c331f4c8f14b475c9148bd8c3f1512240ace55fe31a179e0a960b0`.
Manager batch9, uniform batches, 180-frame chunks with temporal overlap3, Lab
colour correction, CPU tensor offload, tiled VAE encode/decode. Installed CLI
default seed42, input/latent noise0; seed is not explicit in Manager's payload.
The job completed in approximately94minutes,10chunks total. Bounded1200s poll
stages resumed the same ID without duplicate submission. The preserved raw
result SHA256 is `afaf179cf5681e3223924fdeaf5f66a65ebbe36cbdd23a05f78f362b9d7f7e36`.
`finish_delivery.py` collected and verified it before producing the H3 deliveries.

## Playback bridge and evidence

`fmv_h264.cpp` implements opt-in Windows MFPlay H.264/AAC playback in a game
client-sized child window. Same native film entry serves startup and realm films.
Original executable and AVIs remain intact; missing MP4 / decoder startup errors
fall back to the native film path. Current inspected 1.1 engine hash:
`42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`.
Ghidra decompilation establishes the original AMMultiMediaStream / DirectDraw
stream route; engine has no direct AVIFile import. Compatibility codecs are a
downstream issue. Simply renaming H.264 files to AVI is not integration.

`build_player.py` verifies the current package and copies exact existing embedded
repath/QoL resources rather than rebuilding stale feature code. It builds only
this directory's launcher/DLL and stages a separate complete runtime. All original
engine disk bytes remain unchanged. Guarded pre-entry injection installs the
movie bridge before startup films. Later shared UI changes must be restaged and
manifest-verified before merge; the captured package is not frozen/promoted.

Actual isolated game playback:

- `playback-checks/medieval-intro1-full-v2/events.jsonl`: Medieval naturally ended
  about42.2s after play, returned1, then entered Intro1. Full2560×1440 client
  screenshots show readable Chinese subtitles and no old4:3 black bars.
- `playback-checks/intro1-full-v3/events.jsonl`: Intro1 naturally ended about
  63.266s after play, returned1, then entered Medieval. Frames vary through the
  whole film. Original first-v2/v1 trials include skips and are not completeness
  evidence. Broad any-key skipping was corrected and specific keys logged.
- `playback-checks/audio-skip-final/`: MF audio stream present/selected;
  process-owned audio sessions sampled200times, peak0.03829217, not muted.
  A right mouse message triggered normal skip return0. This establishes audio
  rendering, not subjective speaker loudness or lip-sync acceptance.
- `playback-checks/final-intro0-greek/`: intro0 played in the actual isolated
  game at2560×1440 with audio selected. The user explicitly confirmed
  “是我退出的，播放没问题”. Its interruption was deliberate user exit, not a
  decoder failure. This is user playback acceptance, not a full natural-end run.
- `mixed-player-validation.json`: Celtic and Greek both reached natural end
  and returned1 through the same player component in a hidden2560×1440 host.
  The separate validation DLL differs only by forced mute to avoid desktop
  audio interference; the production DLL is unchanged. Selected audio and
  decode/render/timing setup passed. Realm campaign triggers were not tested.

Capture uses process-window PrintWindow at full2560×1440. Some early/occluded
captures are black and do not prove output failure; observed moving frames plus
MF playback/end events are used. No battle acceptance or campaign film trigger
was claimed. Unrelated/shared game instances are never terminated.

## Reproduce / resume

From project root:

```powershell
python modernization/assets/fmv-delivery-1440p-20261001/deliver.py Medieval Intro1
python modernization/assets/fmv-delivery-1440p-20261001/intro0_manager.py
python modernization/assets/fmv-delivery-1440p-20261001/finish_delivery.py
python modernization/assets/fmv-delivery-1440p-20261001/build_player.py
```

These commands document reproduction; all outputs already exist. Do not rerun
inference for delivery. `intro0_manager.py` resumes the saved jobID.
Collector creates later H3 deliverables only after all three SeedVR deliveries
pass. Generated temporary crop media and final media live in this project review
folder; Manager inference inputs/outputs remain underD:/AI/LocalModelManager/media.
Weights remainE:/AI; no downloads, Manager edits or shared GPU bypass.

## Integration handoff / rollback

Not yet installed into shared1.1. `playtest/FMV-1440p-Playtest.exe` is an isolated
candidate. Rollback is launching the unchanged original1.1 entry; no accepted
runtime overwritten. Main-parent notification tool rejected native ancestor
messaging; `HANDOFF.md` is saved for parent retrieval. Final integration must carry
the player module and hash-verified launcher changes as well as fiveMP4 files.
