# Remastered 1.0 release — 2026-09-30

## Formal1.1 portable compositor fix — 2026-10-01

The user accepted the surface-lifecycle exit correction before this work.
The formal release inherited wrapper SHA256
`d4beb210c7847bdf0a201b8f69a4fa6dc4adf65eb94a69ced52b6905c4827640`.
Its exact build source `build/remastered-1.1-p1/wrapper/src/mm_mixed.h`
allows only historical developer paths, including remastered-1.1-p1.
The formal release directory was omitted: battle1280x720 was painted into
the upper-left of the2560x1440 primary without presentation2x or input inverse.
Loading pixels remained outside the battle rectangle.

`wrapper-probe/mm_engine_identity.h` now validates the complete on-disk engine
SHA25642f2aac7, using Windows BCrypt and Unicode paths. Mixed mode still requires
MM_PROBE_MIXED_RENDER=1; the existing launcher sets this flag. The decision is
cached. Unknown/modified/missing engines cannot enable the compositor. Production
paths are no longer an identity guard. The legacy standalone diagnostic source
is preserved; `tools/portable_11_wrapper.py` applies the production guard, and
`build_remastered_11.wrapper()` invokes it for future builds.

New wrapper SHA256
`8c46de4da7ca74b2a63ba5f3fcd6bc296b0646d26d0481b1587bc5074ee9eecb`.
All other wrapper features/classifier/input math remain from the exact installed
source. `tools/build_11_portable_render.py` installs only wrapper and manifests
into formal release, frozen package and isolated candidate. Engine/launcher/
embedded modules, exit repair, FMV, art and player files are retained.
Rollback with `C:/Python314/python.exe modernization/tools/build_11_portable_render.py rollback`
while stopped; backups under `backups/remastered-1.1-portable-render`.

User-authorized save1 reproduction uses private background input and read-only
memory in separate copies. Static assets are hardlinked but never edited;
all mutable state and wrapper are independent copies. Diagnostic launchers
retain background flags; their embedded resources match the formal release
byte-for-byte. Both runs load save1SHA256
`5f636f953bbf908d679e601ece4259b08829863a2b189f07dc20d522f8717b8e`.
Before exact2x block fraction70.2720%; after100%. Cursor at requested output
(2000,1000) passes the established cyan-pixel check (388pixels). Native UI fonts
remain64/44/30; battle32/22/15. Save1 is a tutorial and consumes Escape, so this
test does not establish independent menu transition acceptance. Earlier capture
fields `cursor_coordinates` read unverified addresses and are not cursor evidence;
the subsequent `input` run replaces them with the verified surface check.
Known engine accepted in candidate/formal/moved Unicode directory; modified
and missing files rejected. All owned test processes stopped and mutable files
restored. Evidence under `logs/remastered-ui/portable-save1` and build verification.
Installed user acceptance remains pending; no gameplay after installation.

## Formal1.1 Alt+F4 surface lifecycle repair — 2026-10-01

Engine SHA256 `42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`.
Read-only evidence in `logs/remastered-ui/release-altf4-p35428`: two thread dumps
and three stable surface table samples establish a native WM_DESTROY CPU loop,
not a music-thread wait. Native 58acf0 repeatedly calls 58b3e0 on registry head
6f6950. The head object has null interfaces at +4/+8 and index44 at +1c,
although it occupies slot0; count at 6f8154 is44. Native Destroy immediately
returns when +8 is null and cannot advance this head. Native Create 58ad90
appends a registry entry without unregistering an existing incarnation; duplicate
ownership explains this failure, although the original offending caller has
not been captured. This is distinct from the earlier fatal-AV/OGG detach incident.

`runtime/hd11/surface_lifecycle.cpp` gates exact function prefixes, preserves
the native bodies with trampolines, unregisters before recreation, and compacts
duplicate registry entries/reindexes before destruction. A live object is
presented once to native Release; a dead object is removed immediately.
The launcher retains its engine hash gate; disk engine remains unchanged.

`tools/build_11_surface_lifecycle.py` builds from installed resource102 source
hash f0baf09b41fd5f74009b55816da6bc9a37352c4c8a2756fa48f234940bdf56a2,
preserves resource101 and both current FMV launcher implementations, and
transactionally installs the new resource102 into candidate and formal/frozen
release launchers with updated manifests. Sources/build provenance for this
new delta are authoritative under `build/remastered-1.1-surface-lifecycle`;
the original release provenance remains historical. Future launcher rebuilds
must retain this new module rather than extracting the pre-fix FMV launcher.

Validation: compiled x86 registry tests cover dead heads, duplicate ownership,
1000 recreations and128-slot capacity. A separate x86 harness executes native
Destroy machine instructions with only absolute memory references relocated
out of Windows' low-address heap, against mock COM interfaces. It verifies
stale dead-head removal, stale live-index/duplicate correction, exactly two
interface Releases, and idempotent subsequent destruction. It does not launch
the game. Runtime exit acceptance remains pending user testing.

Backup and rollback: `backups/remastered-1.1-surface-lifecycle/rollback.json`;
run `C:/Python314/python.exe modernization/tools/build_11_surface_lifecycle.py rollback`
with game stopped. Saves/settings/art remain unchanged. The user explicitly
requires exit diagnosis first; upper-left battle/save1 debugging remains next,
after this installed fix's gameplay checkpoint.

Delivered to `D:/Games/Magic&Mayham_Remastered_1.0` from installed v37
`package-v37-speech-layout`. Player entry: `MagicMayhem-Remastered.exe`.
The paired `Chaos-Wide169-engine.exe` remains the native engine. Launcher
hash-gates the engine and terrain module, starts it with the release directory
as its working directory and loads the two embedded enhancement modules.
No development directory is needed. Only `modernization/config/qol-hotkeys.json`
is retained under that name because the existing module uses it as user state.

Functional modules are extracted from the installed launcher and preserved
byte-for-byte, rather than rebuilt from development DLLs. The development DLL
hashes in `current-baseline.json.latest_development.files` are stale relative
to the latest installed embedded resources; the installed launcher, engine,
terrain DLL and immutable package manifest all matched their pinned identities.
Do not use loose development DLLs as release inputs or promote their identities.
See `releases/remastered-1.0/provenance.json` and `verification.json`.

Only the launcher is rebuilt to use its own directory and remove historical log
rotation. It preserves existing injection order and compile-time behavior, uses
the current terrain hash, and pins engine SHA-256
`43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`.
Release launcher SHA-256:
`57396bda3f96f1785bf51c8f7e778e930da5d2c21c794ae6e8c1907a01f3c1d0`.
Resources 101/102 retain hashes:
`9c7a0a2511b7b5af63a1ece60ff4c0ecddff3c8c57ae7b940ddc7299ed3a4cbf` /
`af65b4ba36191bdb11840ff914cee314d7efc2b751c1028aab6ceee516b1b873`.

Static validation: x86 build, PE imports, embedded resource equality, engine and
terrain pinned hash strings, no old runtime directory in launcher, no junctions,
empty independent Save, MaxFramesPerSec=30, and all 5,065 release file hashes.
No game launched. Runtime acceptance remains pending user testing. The version
number does not close outstanding 60-distinct-frame, gameplay-time, native HD UI,
long-combat or multiplayer gates.

Asset policy: package files are verified before copying; current prefs, ddraw
settings and hotkey bindings are retained. Runtime-generated AI and encrypted
configuration differences use the immutable v37 package copies. Test saves,
screenshots, logs, lab markers, uninstall metadata, sources and build artifacts
are omitted. Community readmes are retained under Documentation.

Rollback: original development runtimes are untouched. Preserve release Save
and settings before restoring from `releases/remastered-1.0/runtime`; compare
`release-manifest.json` with `verify-files.ps1`. Distribution materials, build
source and verification are kept under `modernization/releases/remastered-1.0`.

## Player entry refinement — 2026-09-30

User chose to retain the launcher architecture, requested a game icon on
MagicMayhem-Remastered.exe and moving Chaos-Wide169-engine.exe into a subfolder.
This supersedes the prospective architecture simplification discussion; no
native-loader conversion is planned from that review alone.

The root now has one game executable. Existing four-frame game icon resources
were losslessly extracted from the community engine and embedded in the launcher;
no generated/edited artwork. Native engine, DLLs, assets and user state all live
under `runtime/`, with working directory and all previous relative paths intact.
`Documentation`, README and integrity helper remain at distribution root.
Launcher resource 101/102 and native engine/terrain hashes are unchanged.
New launcher SHA-256: 6f2d687127c3c8310e83c4ad1951b68910838a07034ce6034e17eb8664d6e295.

Full pre-change release saved as hash objects under checkpoint
`release-layout-before/manifest.json`; `restore_release.py NEW_DIRECTORY`
reconstructs that release without overwriting player state. All 5,065 installed
file hashes and local imports passed; icon resources and root executable count
checked. No gameplay launch; runtime acceptance pending user testing.

## Official all-asset PNG checkpoint — 2026-09-30

User accepted Grimoire PNG and promoted it. All remaining 50 external BMP assets
converted to PNG with compatible general native file-object loader. Formal now
482.07 MB; developer current immutable package v38 and in-use runtime directories
are BMP-free. Existing launcher mode/icon/runtime layout retained. Original source,
baseline/package/backups retained. See docs/png-assets.md for fresh evidence,
validation scope and rollback; general paths pending user testing.

## Player README — 2026-09-30

Distribution README now contains only player launch instructions, visible changes,
spell hotkey usage, display settings and save migration. Development history,
internal modules, hashes, offline test logs and rollback internals are excluded.
Removed the obsolete Release-BMP-readme.txt from distribution and both staging
copies; technical history remains in modernization documentation and backups.
Packaging README and file manifests are synchronized.


## Formal Remastered1.1 release — 2026-10-01

User explicitly requested current1.1 release to
`D:/Games/Magic&Mayham_Remastered_1.1` and removal of temporary assets.
Target existed empty; no player files were overwritten. The capture helper was
first asked to stop and confirmed DETACHED=1 captured=0; game remained running
and under user control. No gameplay launch or visual acceptance run for release.

Distribution has a single root game entry `MagicMayhem-Remastered.exe` with the
original four-frame community icon, plus readme, Documentation, integrity helper
and release-manifest. All engine/DLL/asset files are under runtime; launcher uses
that folder as working directory, retaining relative resource paths. No repository
or development directory is required. Independent Save is empty; user can copy
old sav files into runtime/Save. Existing window/settings and hotkey preferences
retained, MaxFramesPerSec30. The eleven consumed plaintext CFG files are copied
from hash-verified source/base when missing; encrypted runtime caches omitted.
AI data uses verified immutable package copies rather than live training state.

Native UI content1920x1440 at origin320,0, battle1280x720 scaled to2560x1440
retained. Approved SeedVR UI, Qwen map/terrain selection, restored portal artwork,
latest corridor/portrait/minimap/UI fixes and all five2560x1440 H.264 films retained.
Native AVI fallback and production FMV hook/DLL remain. Resources101/102 are
byte-identical to current candidate and its FMV integration build. Only launcher
is rebuilt to add original icon and clear inherited diagnostic input/trace flags;
functional feature flags and module order remain. No DLL functionality rebuilt.

Clean manifest-only package excludes test saves, screenshots, traces, dumps,
sources, caches, uninstall/lab metadata and superseded community root readmes.
Community readmes moved to Documentation. No broad repository deletion performed:
active development sources, approved/generated production art, immutable inputs,
worker deliverables, original backups and recoverable troubleshooting evidence
are retained outside the player distribution. Existing active source runtime and
its save/settings were not edited by the release operation.

4438 release files; verification helper checks4422 immutable resources and permits
known player-state/consumed-CFG changes after gameplay. Full initial file hashes,
x86 architecture, locally resolved imports, exact embedded modules, four icon
frames, no junctions, no temporary file extensions, empty Save and source/delivery
inventory equality passed. Protected1.0/v38 unchanged.

Build recipe: `tools/release_remastered_11.py`.
Frozen files: `releases/remastered-1.1/package/`.
Provenance/verification: `releases/remastered-1.1/{provenance,verification}.json`.
Known limitations: `releases/remastered-1.1/known-issues.md`. Intermittent load
access violation and secondary OGG exit wait remain unresolved; later attached
capture did not reproduce AV. Chapter video triggers, multiplayer, gameplay-time/
true60render gates remain unverified. Roof visibility save and native selectable
1K/2K/4K profiles are unfinished. Player README mentions read-load issue and does
not claim configurable output scaling changes native rendering policy.

Rollback uses preserved prior1.0 release; keep current player's runtime/Save and
settings before switching versions. Reconstruct1.1 in a new empty directory from
frozen package and verify hashes rather than overwrite a live player's folder.
Future patches start from the current1.1 features; verify release/candidate engine
and manifest identities before address-based changes.


## 1.1 new-game packaging correction, 2026-10-01

User new-game report showed “Could not find map section specified in config
file”. Release cleanup incorrectly excluded all .map suffixes as linker output,
including683 native Realms map section data files. Earlier4438-file verification
was self-consistent but incomplete: it validated a filtered manifest rather than
checking mandatory game-data retention. This was a packaging defect, not evidence
of the previously investigated intermittent AV.

Restored all683 hash-verified Realms MAP sections to the player release and frozen
package. Total5121 release files; static integrity helper checks5105 immutable
files. Launcher/modules unchanged; player settings/saves retained. No game launched
for acceptance. User new-game retest pending. Cleanup no longer excludes .map;
future release build also asserts exact native MAP inventory against source.
`tests/test_release_asset_policy.py` protects map retention and temporary-output
exclusions. Both regression checks passed, full static release verification passed.

Repair recipe: `tools/repair_release_11_maps.py`.
Backup of pre-repair manifests/provenance/verification and exact added-file hashes:
`backups/remastered-1.1-release-map-sections/installation.json`.
