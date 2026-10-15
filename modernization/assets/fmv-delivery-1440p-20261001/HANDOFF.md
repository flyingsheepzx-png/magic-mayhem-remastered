# FMV delivery / 1.1 handoff — ready for integration

Latest user authorization: Medieval, Intro1 and intro0 use SeedVR2 at 2560×1440;
Celtic and Greek retain H3 reconstruction/mixed edits. Reuse existing completed
inference; all delivery video H.264. Ensure actual game playback. Creature assets
remain deferred; approved Phoenix CRT4x may be considered separately.

This directory is owned by the FMV worker. Shared 1.1 runtime/UI not modified.
`manifest.json` contains individually verified delivery paths and hashes.
`intro0-manager.json` owns job `8285e1ea070e41d68403da548ef2049b`; do not submit
another intro0 upscale. Model/input hashes, profile and idempotency key are saved.
The job completed and all five final MP4s passed full decode, timing, original
source hashes and PCM archival checks. No additional GPU work is required.
All five are 2560×1440 H.264 CRF18/slow/yuv420p, AAC192k; original PCM is retained
in companion MKVs. Total MP4 size is403,943,694bytes (about385.2MiB).
intro0 is new native4× SeedVR2; Celtic reuses H3/SeedVR2/H3; Greek reuses the
latest H3 two-shot whiteout edit and has no SeedVR2 middle footage.

Medieval and Intro1 are reused 1920×1080 SeedVR2 image areas, cropped from old
1920×1440 archives and Lanczos resized to 2560×1440. They are **not new native
4× inference**. Original decoded frame timing and original PCM archive checked.

`fmv_h264.cpp` and `build_player.py` are opt-in playback bridge/launcher under
`playtest/`. Windows MFPlay decodes H.264/AAC into a client-sized child window;
the native movie function at 0x469a00 is intercepted only in the separate owned
process. Missing MP4 / startup decoder errors fall back to existing native AVI.
Original disk engine remains SHA256
`42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`.
Launcher copies exact latest embedded QoL/repath resources, verifies current
package and module hashes, holds entry during early injection then resumes.
The shared loader/UI files are never edited. Build/check sources remain here.

Ghidra evidence: `4696e0.c`, `469830.c`, `469a00.c`, identified independent
project `D:/Tools/magic-mayhem-re/projects/fmv-h264-11-20261001`. Original path
uses AMMultiMediaStream/DirectDraw stream interfaces; VfW is downstream codec
compatibility, not a direct AVIFile import in the engine.

Playback evidence under `playback-checks/`: Medieval and Intro1 reached natural
end in the actual isolated game. intro0 played at2560×1440; the user confirmed
“是我退出的，播放没问题”, accepting playback and explaining the deliberate exit.
Celtic/Greek reached natural end using the same player component in a hidden
host (validation-only forced mute); campaign realm triggers remain untested.
Process audio endpoint samples confirmed nonmuted output, peak0.03829217.
Skip is Escape/Space/Enter/mouse; logs distinguish skips from natural ends.
`mixed-player-validation.json` records the component check scope. Final five
formal film names were restored and their runtime copy hashes verified.

Parent chat notification was attempted using the authorized app tool; it rejects
native ancestor messaging. This file is the concrete handoff until final result.

Shared 1.1 is not installed by this worker. The opt-in candidate is
`playtest/FMV-1440p-Playtest.exe`. Integration must carry production
`fmv_h264.dll`, the guarded launcher hook and all fiveMP4s, preserving native AVI
fallback, existing QoL/repath features and backups/rollback. Use
`player-build.json` for verified engine/launcher/DLL hashes. Restage against the
then-current 1.1 package; do not overwrite another agent's current runtime or
configuration with this earlier isolated snapshot. A recent rebuild encountered
the shared package's missing `runtime/CFG/ai.cfg`; that was not modified here.
Existing isolated artifacts remain verified. Rollback uses the unchanged
original1.1 launcher. Renaming MP4 to AVI alone is insufficient.
