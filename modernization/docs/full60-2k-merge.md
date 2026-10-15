# Main entry and 2K merge contract

## Installed checkpoint (2026-09-27)

The user authorized installing the accepted 30/60/slope candidate into the main
program and preparing integration with the separate 2K session.

- `Chaos.exe` is now a main launcher, SHA-256
  `ca93f3bd89c5770668021ebb04cd60e5684a9074512bceee86374ec54e22de84`.
- It starts the hash-verified `Chaos-singleplayer-600.exe`, SHA-256
  `856c0a21f45e4ad41bb90d87416dc9d510e10200381c1c1412b17bc24fd2f9bd`,
  and embeds the exact frozen `full60_v1/full_trial.dll`, SHA-256
  `3d0c7101d825fb14e885b9acf2f9e44383c2d9706c27c31a999187add066f59b`.
- Main-launcher source: `runtime/main_full60/launcher.cpp`. The behavioral
  change from the frozen launcher is ignoring its own PID in the existing
  game check; otherwise naming the launcher `Chaos.exe` would block itself.
- Original main bytes remain at `backups/full60_main/Chaos.exe` and
  `baseline/Chaos.exe`, SHA-256
  `b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
  Use this original engine for multiplayer; the installed main entry is single player.
- Installer/rollback: `python modernization/tools/install_full60_main.py install`
  or `rollback`. Record: `full60-main-installed.json`.
- Startup read-only verification passed all 11 hooks using
  `python modernization/tools/verify_full60_runtime.py --main`.
  Rollback and reinstall passed. Wrapper, preference, game child and saves
  were hash-verified unchanged during installation.

## Other session and ownership

The active HD session `01a0df6e-7ac9-7e51-bdc7-d34539c87c7b` develops in
`C:\Users\DEVELOPER\.codex\worktrees\hd-ui-lab\Magic&Mayham`.
Keep its original-community executable as the basis for address patches;
the installed root `Chaos.exe` is now a launcher and must never be treated
as the engine image. That session owns its HD layout, assets and build tools.
This session owns the frozen 30/60 behavior, main entry and combined candidate.

The current HD selector reports a **1120x840 native game surface** displayed
at **1920x1440**. This is expanded native view plus output scaling; it does
not establish native 2560x1440 rendering or complete UI adaptation.

## Concrete integration requirements

An isolated combined candidate was built from HD commit `123dc6f` on
2026-09-27. See `../runtime/releases/hd60_v1/README.md` for hashes, source
changes and automated validation. The root main entry is unchanged.

1. Receive the HD engine binary, original and output hashes, exact address
   edits (expected bytes and replacements), resource manifest, launch flags,
   and verified input/HUD/menu/save behavior. Validate every patch against
   the original community image before composing with the 600 search edit.
2. Compare HD modifications with the 11 runtime hook sites and QPC import
   replacement. Do not let two independent patches overwrite the same
   instruction stream or import slot. Native addresses and expected bytes
   are documented by the frozen sources, not by the main launcher.
3. Adapt a **new candidate** of `render_replay_trial.cpp` to queried surface
   width, height and pitch, bounds-checked allocations and clipping. Current
   code copies 600 rows at 1600 bytes/row, scans 800 pixels/row, and has an
   800x600 replay guard. `background`, `complete`, `final_surface`, UI merge
   and draw-context handling all require review. Removing the guard alone
   is insufficient and unsafe. Preserve frozen v1 unchanged.
4. Preserve the shared actor/health-bar anchor, camera projection, view
   rotation, draw ordering, input coordinate mapping and Chinese UI at the
   expanded dimensions. Keep HD texture scale separate from logical size.
5. Make a separate combined candidate entry with its own hashes, backups,
   opt-in flags and rollback. Verify redirects on the long ramp, occupancy
   and sprite/bar continuity with memory telemetry; verify actual full
   surface compositions/hashes, full-sized UI, accurate selection/targets,
   save/load, audio/video and alt-tab. Check gameplay timing against the
   original rather than counting animation draws.
6. Update the main entry only after combined-candidate acceptance. Retain
   the original engine and accepted 800x600 candidate as fallbacks.

Rare complex-terrain drift and controlled combat/save/FMVs/alt-tab gates
remain open. Approximately 60.7 compositions/s with 55.8 adjacent changes/s
in a reversal-heavy sample is not evidence by itself of visible stutter;
integer-pixel quantization and reversals can repeat a frame. Do not change
the accepted interpolation solely to force every adjacent hash to differ.

## test5 HD layout follow-up (2026-09-27)
The playable HD lab corrected the user-reported realm toolbar, Portmanteau slot/category positions and character talisman clipping. Launcher SHA-256: 1ebb20d0f53f5e73532c02edfd68d81f4b3f7cf06c99081e90b3d6548807c4bf; engine: be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7. Combined DLL is unchanged. test5 navigation/three-icon pixel checks and test2 roof/four-edge scrolling passed; 11 hooks, 1120x840 and MaxFramesPerSec=30 verified, saves unchanged. Authoritative evidence and rollback are in the lab modernization/docs/hd-integration.md and modernization/tools/rollback_hd60_test5.py. Main installed entry is unchanged.
