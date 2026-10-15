# Roof-hidden upper-layer units — 2026-10-02

## Save21 correction: native roof groups, installed v2

User reported v1 did not work and explicitly authorized agent save21 debugging.
Actual save21 actor0 is grid(89,75,10), world(2848,2400,160). Roof switch cycles
1/2, but scene+0x61 remains28 and scene+0x6d is1. v1 wrongly required policy0
and actor height above28, excluding this bridge. In policy1 native tile group
bits(tile+8)&3 compared to scene+0x65 determine the hidden roof family.
Native4f8960 sets local visibility false when the tile group exceeds the selected
group; ordinary units with+0x108<1 are skipped. v2 handles both native policies,
retains the flying exception, fog and active/alive checks, and excludes actors
already represented in native body commands. A bounded4096-bit stack array
avoids scanning the command list for each unit.

Latest resource101 source is `build/remastered-1.1-roof-ghost-v2/`;
resource102/103 remain byte-identical to installed v1 (Tab/casting/options/AI
preserved). Build/install/rollback: `tools/build_11_roof_ghost_v2.py`, backup
`backups/remastered-1.1-roof-ghost-v2/`.162 offline checks passed(58 ghost/RLE,
24 wrapped routes,43 command/marker,37 dynamic/local paths). Added group1/2/3,
flying exception and duplicate-native-body regression cases.

Authorized isolated background save21 runs: `logs/remastered-ui/save21-roof-`
`before-v2/`, `after-v2/`, `acceptance-v2/`. Read-only module telemetry confirms
ghost counts1→0→1 for roof1→2→1, including first loaded frame. Paired same-roof
2560×1440 output difference is confined to(1260,600)-(1320,728), the body contour.
The first manual crop used1280 scene coordinates on a2560 mixed-output capture,
so it showed the wrong region; corrected crop used2× output coordinates. Do not
equate native-surface screenshot dimensions2560 with battle scene expansion.
User observed effect working, questioned image assessment, and requested install
and own testing. Runtime proof is scoped to correct body emission and render
change; broader visual/movement acceptance remains with user. Owned diagnostic
processes stopped and disposable settings restored. No further gameplay after
that request. Actual installation hashes/resources verified across all3 entries.

Historical v1 design/verification below did not establish this group mode.

User requires units on hidden upper layers (including bridges counted as a
second layer) to remain visible as translucent bodies, and Tab to use the native
roof control. Installed engine SHA256:
42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.

Native tile traversal0x4f83f0 and sibling rotations gates layers through
scene+0x61 when scene+0x6d is zero. Hidden upper-layer units therefore never
submit commands to the existing terrain-occlusion body pass. Changing its
opacity alone cannot reveal them. Native0x4f8230 provides the traversal origin;
scene+0x39/+0x3d is camera grid centre, +0x5d traversal radius. Unit world
coordinates+0x14/+0x18/+0x1c and draw offsets+0xb7b/+0xb7f feed the same four
isometric projections. Native0x507190/0x507330 resolve normal/alternate animation
frames and draw offsets from unit+0xb4/+0xcc or +0x829/+0x841. These routines can
initialize native state, so the new collector instead reads established objects
and skips missing ones. Native frame table uses an inclusive last frame index.
Read-only Ghidra evidence outside Git:
D:/Tools/magic-mayhem-re/projects/roof-unit-20261002/functions/.

`runtime/hd11/roof_ghost.inc` scans existing alive, active, currently visible
units above scene layer limit in single-player clipped-layer mode. It respects
native tile exclusions, player visibility fields, paletted body appearance
modes0/31, frame offsets, dimensions, palette bounds and world wrapping. It
does not submit terrain/effect/shadow commands or invoke simulation. A bounded
4096-command private body list joins the existing redraw buffer before ordinary
body commands; the scene then receives the same37.5% RGB565 body blend as other
occluded units. Normal foreground bodies override private ghosts. Actor position
prediction remains shared with the established renderer. Normal scene queue,
selection/hit regions, roof setting, unit state and save format stay unchanged.
Missing/unsupported appearance objects retain native behavior; this is a body
display feature, not a new upper-layer picking/health-bar workflow.

Build/install/rollback: tools/build_11_roof_ghost.py. Latest resource101 source
is build/remastered-1.1-roof-ghost, copied from exact installed wrap-route-v1;
resource102 is the newly installed roof-tab module, resource103 unchanged.
156 offline checks passed:52 ghost/native RLE cases,24 wrapped-route cases,
43 command/marker cases and37 dynamic/local path regressions. Ghost tests cover
four camera rotations, wrap, frame bounds, layer/visibility/death/multiplayer
exclusions, no unit/scene mutation and actual RGB565 native RLE rendering.
VirtualQuery is an explicit double; the actual native camera anchor and rasterizer
execute. These do not establish visual acceptance in the user's latest bridge
save. No gameplay launched; acceptance remains with the user.

Hash-gated installation updates candidate/frozen/formal launchers and manifests,
backs up to backups/remastered-1.1-roof-ghost/, and verifies module equality.
Rollback with game closed:
`C:/Python314/python.exe modernization/tools/build_11_roof_ghost.py rollback`.
This keeps Tab. To also remove Tab, roll back it afterwards:
`C:/Python314/python.exe modernization/tools/build_11_roof_tab.py rollback`.
