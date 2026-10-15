# Final project layout — 2026-10-02

Development ended by user decision at the actually installed Remastered 1.1. The authoritative player package is `D:/Games/Magic&Mayham_Remastered_1.1`; its files and player data are preserved. `modernization/docs/source-index.json` identifies exact final module sources. All older runtime/backup/playtest locations below are historical and may no longer exist after authorized aggressive cleanup. Do not run an old installer/rollback against the final version. New work requires explicit authorization and a newly staged isolated copy of the actual final runtime.

The retained development project contains `game/` legacy resources and saves, `modernization/baseline/` immutable small originals, release source snapshots in `modernization/build/`, maintenance sources in `modernization/runtime/`, tools, tests, design/reverse-engineering records, immutable art sources and approved map masters. Unique saves rescued from retired copies are indexed in `modernization/preserved-player-data/index.json`; independent source recovered from retired backups is indexed in `modernization/releases/cleanup-20261002-recovered-source.json`. Installed development tools and global Skills remain available.

## Historical layout

# Current project layout and development baseline

## Latest development policy (2026-09-27, supersedes the initial migration decision)

Start from the latest development version unless the user requests another base;
preserve features from prior versions. Current entry is
`game/Chaos-Wide169-Trial.exe`, with independent runtime `game-wide169/`, merging
HD60 QoL and 1280×720 widescreen. Read `current-baseline.json.latest_development`
and `docs/wide169.md` for current identities, evidence and remaining gates. The
older HD migration inventory below remains historical and available for fallback.

## Decision (2026-09-27)

The user designated the latest HD lab `Chaos-HD60-Trial.exe` as the baseline for all future development and requested migration into the primary project. The active layout is:

```text
D:/Games/Magic&Mayham/
  .git/                      primary repository and existing history
  AGENTS.md                  working rules
  modernization/             plans, docs, tools, tests, sources and evidence
  game/                      HD runtime, assets, configuration and saves
    Chaos-HD60-Trial.exe      accepted development launcher
    Chaos-HD60-engine.exe     paired engine
    Chaos.exe                original community engine
    modernization/           junction to ../modernization for runtime compatibility
```

Launch the HD entry with working directory `game/`. Run development commands from the project root. The junction preserves existing launcher/DLL, screenshot and tool relative paths without duplicating development materials. Scripts resolve their own physical source path and now select `game/` as their runtime root. Avoid recursively scanning the junction during runtime asset inventories or backup copies; use `/XJ` with robocopy.

`current-baseline.json` records exact hashes, save inventory and adapted script names. The launcher and engine were migrated unchanged. HD wins conflicting development files; primary-only tools, baselines and research were retained. Both original working states have binary diff snapshots. Historical reports and manifests retain their historical paths intentionally; consult this document for the current location. The old HD worktree registration and `.git` pointer remain at the original location to preserve Git metadata; its runtime and development content have moved. Do not develop in that empty former worktree.

The current candidate renders to a native 1120x840 surface. User promotion does not close distinct-frame-rate, controlled timing, long combat, audio/video or other outstanding gates. Keep `MaxFramesPerSec=30`. QoL development resumed at user request in a separate HD trial; see `qol-input.md` for current gates. Old 800x600 installers and rollback scripts describe earlier candidates and must not implicitly replace this baseline.

## Commands

```powershell
Set-Location -LiteralPath 'D:\Games\Magic&Mayham'
Start-Process -FilePath '.\game\Chaos-HD60-Trial.exe' -WorkingDirectory '.\game'
python modernization/tools/verify_hd60_runtime.py --report modernization/logs/post-migration-startup.json
python modernization/tools/hd_background_trial.py --combined --load-test2 --select-unit0
```

The verification script terminates only its own engine child and launcher. The background trial temporarily installs its diagnostic wrapper/settings, uses the private acknowledged input protocol, captures the game surface and restores files in cleanup. Close other game instances first. Old `game_window.py` moves the desktop cursor and activates the window; it is not the default background path. Legacy `telemetry.py` is hash-gated to the original engine and must not be used against the HD child unchanged. See the global `windows-game-background-debug` skill for the preferred workflow.

## Backup and rollback

Migration backup: `D:/Games/MagicMayham-backups/restructure-20260927/`.

- `original/`: previous primary runtime, saves, configuration and development files.
- `hd-modernization-original/`: HD development directory before path adaptation.
- `hd-metadata/`: former HD rules and Git pointer; binary working diffs are at backup root.
- `migration-summary.json`: merged files and script adaptations.

To undo the directory migration, close all game/debug processes. Move the current `game`, `modernization`, `AGENTS.md` and `.gitignore` to a new sibling backup, leaving primary `.git` in place; then move every top-level item in `original/` back into the project root. Use PowerShell `Move-Item -LiteralPath`, verify exact source/destination paths, and stop on errors. Preserve newer saves separately before rollback. Do not run old executable installers as a substitute for restoring the complete layout. This rollback procedure is documented; it was not executed because it would replace the newly accepted baseline.

## Migration verification

Startup passed 11/11 hook gates, static UI/resource checks and native 1120x840. The Python private-channel test loaded test2 (125 units, unit0 grid 66/48/6), acknowledged all inputs, captured four native surfaces, did not steal foreground, restored diagnostic changes and left all baseline files and saves unchanged. Selection HUD pixel delta was zero, so this run is not independent evidence of selection/picking correctness. Reports: `../logs/post-migration-startup.json`, `../logs/migration-verification.json`, and `../assets/hd/background-trials/1790504791742302300/result.json`. Global Skill format validation passed. Primary historical notes differing from HD are under `history/primary-before-hd-20260927/`.
