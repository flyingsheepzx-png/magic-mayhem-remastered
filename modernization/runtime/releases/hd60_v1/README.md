# HD v13 plus 30/60 isolated candidate

This release snapshot combines the committed HD handoff
`codex/hd-ui-lab@123dc6f50aaad69e65291823c8a881c9bf7265f5` with the
accepted 800x600 slope/30/60 module. It has **not** replaced the installed
root `Chaos.exe` or the frozen `full60_v1` candidate.

| Artifact | SHA-256 |
| --- | --- |
| `Chaos-HD60-engine.exe` | `bd790add14ab1988471265e1e8d75f6d394e1166d83f009317127c63428636a4` |
| `combined_hd60.dll` | `2b48009ac9968b6c44310e3aec6850db72106ec7b1ac85dee193b0e5eed54ad5` |
| `Chaos-HD60-Trial.exe` | `8d350c61d8691c135028db334b7a1e6056341870706e48612c7e0eac2d49b0f0` |

The engine is HD v13 SHA-256
`d0e3f37b9e5513878de4b26856b2482daf45c5fd4780bb9c2e6429e63fe0034e`
plus the verified 600-search edit at `0x4e5543`. `tools/build_hd60_engine.py`
checks both input hashes, the route-site bytes and 12 runtime entry sites.
The only source change from the accepted DLL is
`runtime/combined_hd60/render_replay_trial.cpp`: full-surface buffers, row
copies, hashing, clipping, context height and UI overlay now use the verified
800x600 or 1120x840 dimensions. The other four source files are byte-identical
to `full60_v1`; the accepted binaries stay unchanged.

Built with `runtime/combined_hd60/build.cmd`, which embeds the combined DLL
as resource 101. The launcher starts only the hash-verified combined engine.
The tested files are staged in the isolated HD game copy at
`C:\Users\DEVELOPER\.codex\worktrees\hd-ui-lab\Magic&Mayham`. Run the
`Chaos-HD60-Trial.exe` there after selecting the 2K tier; removing those two
staged candidate EXEs rolls back this experiment. Original `Chaos.exe` in the
lab and original/accepted entries in the primary game directory are intact.

Verification:

- 11 runtime hooks loaded and surface read as 1120x840.
- Private-input test2/HUD regression, menu flow, Grimoire flow, and 21-order
  slope trial completed with diagnostic files restored and saves unchanged.
- Slope trial: 14 `redirect_slope` and 14 `occupancy_ok` events; 351 read-only
  world-position samples had maximum component step 9 pixels.
- In that window, 533 native + 528 replay compositions in 17.82 s
  (59.52/s); 1057/1060 adjacent full-buffer hashes differed. All 1113
  `ui_preserved` checks in the combined slope run were true (528/528).

Pending: user visual acceptance, longer combat and timing, save/load behavior,
FMV/OGG, alt-tab, camera rotation, uncommon UI screens and multiplayer. The
2K tier is 1120x840 native scene area presented at 1920x1440 by cnc-ddraw;
this is not native 1920x1440 game rendering.
