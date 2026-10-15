# Community build reverse-engineering notes

Observed build SHA-256: `b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
`Chaos.exe` is a 32-bit x86 PE with image base `0x400000`. Its file size is 2,076,755 bytes. This hash is the only build examined; all address notes below apply only to it.

## Frame timing

`CFG/prefs.cfg` contains `MaxFramesPerSec=20`. The string at VA `0x5eb5ac` is read in the preferences load routine around `0x54c361`. The value is bounded to 200 and used to compute `1000 / fps` at `0x54c3c1`–`0x54c3cc`. The save routine references the same key near `0x54cadc`. This demonstrates that simply setting 60 changes a game timer; it does **not** establish that simulation speed, animation and rendering are decoupled. We have not enabled 60 in the installed game.

The user clarified the target as 30 logical updates and 60 distinct rendered frames. A short 20/30 comparison observed the loaded preference at VA `0x6de6fd` and derived intervals at VA `0x6de6f9`: `(20, 50 ms)` and `(30, 33 ms)`. The candidate menu scheduler interval at `0x6dbe95` stayed at 50 ms, and candidate menu counters advanced at the same rate in both runs. These counters are not proven gameplay/render counters, so no speed or true FPS claim follows. Test preference was restored to the baseline hash.

The game imports `timeGetTime` and `GetTickCount`; many callers use these clocks. `ddraw.ini` has separate `maxfps` (presentation) and `maxgameticks` controls. A `maxfps` value of 60 therefore does not prove 60 unique game frames. Timing calls and render surface updates still need runtime tracing.

### Repeatable battle probe, 2026-09-26

The user-provided `Save/test.sav` (SHA-256 `62adbfdbc9cb7402e53a26d2e7964d23d15c8801623116fe7a78437118e8e634`) loads into a forest battle map. `probe_session.py` starts the known executable, activates its window, retries opening the load menu until a screenshot changes, loads the save, and requires the characteristic green forest area before measurement. The first click after activation was consumed by the window; the retry corrected that false start. All four runs restored `ddraw.dll`, `ddraw.ini`, and `CFG/prefs.cfg` byte-for-byte and left the save unchanged.

The probe is built from cnc-ddraw commit `279a057ee7e1e4d584b56141c014ab01f3c6ee6d` with the patch in `modernization/wrapper-probe/`. `U` means the wrapper consumed a game surface update; `P` means it attempted to present. Counts below cover approximately eight seconds after the forest scene loaded:

| Logic setting | Wrapper maxfps | U | P | Approximate U/s | Approximate P/s |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 20 | community default | 74 | 74 | 9.3 | 9.3 |
| 30 | community default | 103 | 103 | 12.9 | 12.9 |
| 20 | 60 | 73 | 481 | 9.1 | 60.1 |
| 30 | 60 | 102 | 481 | 12.8 | 60.1 |

The stationary test scene and the wrapper's update coalescing mean `U` is neither a count of distinct pixel images nor an exact simulation tick count. `P` counts attempts, not successful or unique frames. The strong difference between U and P under `maxfps=60` shows that the compatibility layer mostly re-presents its current texture. It does not satisfy the requested 60 distinct rendered frames. The candidate display counter advanced 73 and 103 times in the default runs; its exact semantics remain unproven. A separate movement/cast timing experiment is needed before enabling 30 logic updates by default.

Static xrefs explain the observed scheduler change: at `0x46a4fa` the game divides 1000 by the preference at `0x6de6fd` and stores the result at `0x6dbe95`; the timed loop at `0x4e3f40` uses that interval and advances the counter at `0x6e80f4` around `0x4e3f9c`. This maps the preference to scheduling, but still does not prove that movement, animation or AI preserve wall-clock duration. The next runtime gate is a controlled movement/cast benchmark and identification of the game's simulation and draw call boundaries.

On a later session the probe repeatedly captured a black startup window while the display was allowed to turn off. After the user disabled automatic display sleep, both 20 and 30 preference sessions reached the main menu and loaded the `Test` forest save again. A fixed click sequence showed selection brackets and a move cursor, but the sampled screenshots did not establish that the unit actually changed position. Those images are not valid movement-speed measurements. The temporary files and save matched their original hashes after each run.

## Resolution

`CFG/prefs.cfg` explicitly describes `IsHighRes` as 640×480 or 800×600. Interface configuration files carry paired `Rect1` and `Rect2` coordinates for those resolutions. The executable reads `IsHighRes` at `0x54c072`. A scaled output window can be configured with cnc-ddraw, but that is not native widescreen. The 1920×1080 output preset was seen rendering a readable Chinese main menu on the current system; its window extended beyond the 3440×1440 primary display in the current multimonitor arrangement and was restored. Forcing `renderer=direct3d9` produced black output; retain the community `auto` renderer.

## Pathfinding and AI

The executable reads `MaxNodesForRouteFinding` at `0x4e551d` into global `0x5e174c`; another route-related limit is loaded nearby. The value is referenced near `0x512806` and `0x52aab5`. `SafeRoute` appears at `0x5ec7b8`. These are leads, not validated function signatures. The installed `CFG/Encrypted/chaos.cfg` and `ai.cfg` are binary/encrypted. The old plaintext `chaos.cfg` from the previous installation is not part of this baseline and cannot be presumed authoritative. Terrain passability, water, doors, height, creature movement types, and path-cache invalidation are not yet mapped.

The Python A* prototype in `modernization/pathfinding/` is deliberately not connected to the game. It must not be injected until the engine's navigation cell schema and passability callbacks are identified and verified. It does not alter the installed game.

## Audio and video

`FMV/` contains five AVI files. `Music/` contains `track02.ogg` through `track13.ogg`; `winmm.ini` maps the CDDA path to `Music`. `prefs.cfg` currently enables FMV and CD music. None of these files were altered.
