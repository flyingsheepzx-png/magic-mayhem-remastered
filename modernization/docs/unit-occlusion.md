# Occluded unit reveal — 2026-09-30

## test13 correction: v36 installed

User reported v34 had no effect and explicitly authorized gameplay diagnosis.
Read-only test13 capture confirmed 1501 commands but zero eligible bodies:
hero command 812 mode 1 was the projected shadow; command 813 mode 31 was the
actual body, submitted by the second appearance call (return `0x4fa703`).
The previous assumption that only primary mode 0 was a body was wrong.
`0x57e540` is a sheared/darkened shadow rasterizer, not an opaque body.

Recognize opaque modes 0/31 only at appearance return sites `4fa622`, `4fa703`,
`4fa7c9`. Keep other effects/shadows excluded. Mode 31 above the floor uses the
command palette; the native hardcoded palette 1 belongs only to its lower
floor pass. An intermediate v35 incorrectly reused it and tinted visible units;
paired inspection caught this and final v36 restores the command palette.

Final build passes 30 offline cases, including actual compiled body tagging.
Runtime evidence: `logs/wide169/1790710616602298800/`, six eligible bodies,
hero body tagged and shadow excluded; screenshot confirms translucent hero
through the stone. Off comparison: `1790710438367176700/`. Cropped pair:
`logs/wide169/occlusion-test13-pair.png` (off left, final right). This validates
the reported stationary test13 case; broader effects/rotations remain user QA.
Final run reports `changed_protected: []`; temporary FMV disabling restored
exact prefs bytes/timestamps, PlayFMV TRUE and MaxFramesPerSec 30. Posted Esc
failed to skip FMV; early intro-only captures were discarded as non-evidence.
Harness inventory now prunes the modernization junction before traversal.

Current package: `build/wide169/package-v36-occluded-units-final`.
Launcher: `6614d8876879755d25d2b0744d59dafd320c463bd0997e71b6b29b5045703f7d`.
Resource101: `716c004dd13a6525c1c41e15a4bbf94302a11ce4b01d82ad8cb43c6190034a69`.
Backup: `backups/wide169/path-review-1790710601334736100`.
`python modernization/tools/install_occluded_body.py rollback` restores v35;
to disable reveal without that intermediate tint use `MM_OCCLUDED_UNITS=0`.
The first v36 install attempt detected concurrent diagnostic prefs changes and
automatically restored v35/manifests; final installation ran serially and passed.

The following records the superseded v34 design and its initial test limits.

## Requested behavior and installed candidate

The user requested translucent units visible through tall trees/walls. v34 adds
a 50% RGB565 body reveal to the existing trial entry, retaining v33 movement
and QoL behavior. User performs gameplay acceptance; no game was launched.

Reuse only the original primary body submission at return site `0x4fa622`,
tagged by the existing queue hook `0x4fff41`. Require a valid active/live unit
slot and native command mode 0 (opaque). This includes all sides and unit sizes
when they already have an eligible native draw command; it does not enumerate
hidden units or bypass native visibility submission. Effects, shadows, corpses,
nonopaque bodies and special crop animations are excluded from the extra pass.

After scene composition, copy the viewport into a private surface, redraw
eligible bodies in their original sorted order, then average differing pixels
with the ordinary scene. Equal pixels remain bit-identical; RLE transparent
gaps never become rectangles. Preserve the original floor boundary, viewport,
surface stride and all seven global rasterizer context values. Extra drawing
runs before health bars and HUD. Both native and replay frames use the existing
unit projection offsets, including camera rotation and redirect prediction.
The working buffer is bounded to 1280x840x2 bytes. No simulation, picking,
collision, unit order, save or input code is changed.

Scope follows the existing captured-scene gate: supported battle surfaces,
single player and enabled native command replay. `MM_OCCLUDED_UNITS=0` disables
the reveal. The authorized experimental trial enables it by default; fallback
entries are unchanged.

## Static evidence

Engine SHA-256 `43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`,
preferred base `0x400000`. Original community input
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
Read-only Ghidra exports: `D:/Tools/magic-mayhem-re/projects/path-review-export/`.

- `0x4ffd30` emits 36-byte commands; +4 sprite, +8/+12 screen XY,
  +0x10 signed shade, +0x12 palette selector, +0x18 render mode,
  +0x1c floor split and +0x1e special crop/offset. Sentinel is -30000.
- `0x5002a0` mode 0 invokes the selected optimized blitter and falls back to
  `0x57de00`, a cdecl five-argument software opaque RLE sprite rasterizer.
  Call ABI verified at `0x50044d..0x50045c`. Sprite +4/+8 are dimensions,
  +0xc/+0x10 anchor offsets and +0x1c palette-chain pointer.
- The native floor split is command Y + sprite height - sprite anchor Y +
  signed command +0x1c. The reveal draws only above this boundary and does not
  repeat the native lower/floor-blended portion.
- `0x57dc20` sets surface/pitch/height; `0x57dc60` sets the clip rectangle.
  Saved globals: `658174,6a2dc8,6def50,6cbb6c,6e0008,6a49b8,656618`.
- Installer verifies original/current byte equality at `57de00..57e53f`,
  `57dc20..57dc7f`, `4fa61d..4fa62c`; existing hook signatures remain checked.

## Validation and limits

`tools/verify_occluded_units.py` passes 26 offline cases executing the compiled
reveal function, original native RLE rasterizer and compiled body tagging.
Checks cover 50% blending, unchanged visible pixels, transparent gaps, floor
and viewport clipping, padded pitch, global context restoration, overlapping
bodies, four camera projections at an intermediate replay fraction, excluded
modes, inactive/dead units, multiplayer and the disable switch. The scene and
sprite fixtures are synthetic; this is not gameplay or visual acceptance.
Report: `build/occluded-units-v1/occlusion-verification.json`.

This is a color-comparison reveal, not a new depth buffer or a tree/wall-only
occluder classifier. Other scene drawings over a body can also cause a reveal;
spell overlaps need user review. It cannot reveal units entirely culled before
native submission, and does not reveal originally translucent/invisible render
modes. Unsupported special sprite formats retain original behavior. Verify
trees/walls, partial/full cover, crowds, spell effects, four rotations and moving
units. Performance overhead is bounded but has not been measured in gameplay.

## Installation and rollback

Package: `build/wide169/package-v34-occluded-units`.
Launcher SHA-256: `58fb56c9b85e08842d76ec857462b211a4df51fd50098693f352af084ba1ad54`.
Resource101 SHA-256: `71154da488547b05965af630db6028c9fe932c667330ffa6ce701acc679a0bb1`.
Only `runtime/wide169/render_replay_trial.cpp` changed among bundled sources.
Other embedded resources, engine, terrain module, save/configuration files and
non-resource launcher sections are preserved by the installer checks.
Backup: `backups/wide169/path-review-1790709724750090100`.

From project root, with game closed:
`python modernization/tools/install_occluded_units.py rollback`
restores the exact accepted v33 entry and manifests.
