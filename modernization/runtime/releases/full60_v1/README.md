# Frozen single-player 30/60 candidate v1

This directory freezes the exact DLL and trial launcher the user accepted after
the UI correction. The installed root launcher uses the same embedded DLL and
runtime flags, changing only the path resolution needed at the game root.

- `full_trial.dll` SHA-256: `3d0c7101d825fb14e885b9acf2f9e44383c2d9706c27c31a999187add066f59b`
- Accepted `Chaos-Full-60-Trial.exe` SHA-256: `e7841ad3087061a7b87bea51050272a6550a4eb284ffaddf3ec91f4de29354a0`
- Root `Chaos-Optimized-60.exe` SHA-256: `3b43276d2fae6851f37f21cbca37f564dc633ea100025ddec39a6a16b06030ad`

The source files were copied at the freeze checkpoint. The preserved binary is
authoritative: rebuilding with MSVC may change linker timestamps and hashes.
Individual source SHA-256 values are recorded in `source-hashes.json`.
`build_release_module.cmd` builds a comparison DLL; `build_release_launcher.cmd`
builds the installed launcher with the frozen DLL as resource 101.

The user manually compared combat against the original game and reports that
attack timing now appears correct, and that movement interpolation is smooth.
Controlled combat-event counts, 60 distinct frames/s, save/load, FMV, long
combat and alt-tab remain unverified. This candidate is single-player only.

Install/rollback: `python modernization/tools/install_full60.py install` or
`python modernization/tools/install_full60.py rollback` from the game root.
