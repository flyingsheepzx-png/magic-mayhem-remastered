# Parameter selection modernization

Requested four sequential changes2026-10-01: resolution1920x1080/2560x1440;
replace Animation with windowed/borderless; game speed40/30/20 logic updates;
replace dialogue scrolling with60/120 rendered FPS. Complete and verify each
before working on the next. Preserve mixed internal geometry, existing Chinese
text, assets, saves and latest AI budget/danger refresh.

Item1 in development, not installed. Latest launcher source danger-refresh;
formal launcherfc904f765cc3e93bc5a7190230651adb0024a5f5b00a846963218973548f70b2;
QoL65329dfedab41828bdc17090841dd28a88dc7dad5b15211304ebdb4c1106410b.
Engine42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.
Wrapper latest source transition-present-v6, retain transition fixes.

Native screen: Interface/BattleOptionsScreen/screen (Battle Options).cfg.
RADIOBUTTON1/2 use STR22/23 from CFG/interface screens text.cfg. Preserve all
unrelated translation bytes; decoding/reencoding the whole file is unsafe.
Native apply4a9840 event0 reads radio group at object+63: vector+0/index+4/count+8,
selected control eventID+2d. At4a9905 event0 givesEAX1 (high),event1 givesEAX0.
4a990c..4a991e compares/writes6de6d5 and sets object+67 to rebuild resolution.
Output setting must bypass native resolution changes and retain high geometry.
Draft options_resolution.cpp writes independent display key and posts wrapper
message. Pending: full signature/ABI tests, wrapper receiver/load and window
lifecycle, restore radio selection from settings, labels, build/install checks.
Item1 now compiled and installed. `options_resolution.cpp` hooks apply4a990c
and selection initialization4a94b8 (native EBX read), with complete original
signatures. Selected state reads remastered-settings.ini display/resolution;
native6de6d5 and rebuild+67 unchanged. Wrapper dedicated registered message
validates1920/2560 and matching9:16 height, reinitializes output with native
dd_SetDisplayMode zero dimensions (existing primary retained). Config load
restores width/height, and dd.c bypasses minimum-native-size clamp only for
valid saved resolution. Existing mouse physical->primary then battle mapping
retained. LabelsSTR22/23 replaced bytewise with ASCII2560x1440/1920x1080;
unrelated translation bytes preserved. No full text reencoding.

Source `build/remastered-1.1-options-resolution-v2/` and
`tools/prepare_options_resolution.py`; install/rollback
`tools/install_options_resolution.py`.256 compiled x86 detour cases test
flags/registers/stack and unchanged native resolution marker; native Windows
profile persistence/load/live reset tests validate both sizes and reject bad
dimensions. Existing surface-registry/native-destruction checks pass in build.
No gameplay run; actual rendering and foreground interaction pending user QA.
Initial atomic installation encountered transient Windows1175; complete rollback
was hash-confirmed and5106 files verified before retry. Retried installation
succeeded; final backup `backups/remastered-1.1-options-resolution-v2/rollback.json`.
Current latest AI danger-refresh/budget sources retained; modules101/103 identical.
Items2-4 unstarted. Stop for item1 user feedback per project iteration rule;
goal remains active and full four-item scope is retained.


Item1 acceptance correction2026-10-01: user reported output ineffective and
explicitly requires agent-owned gameplay acceptance for each of four items.
This overrides user-only runtime testing for this task (recorded in AGENTS.md).
V2 target657c84 was not the game-owned main window (live HWNDs differed).
V3 enumerates only same-process windows and requires the wrapper display-message
handshake0x4d4d4450, exactly one responder, before posting the output change.
No native HWND address assumption remains. Wrapper zero-dimension handshake does
not reset display. Current signatures/AI modules101/103 and transition-v6 retained.
Actual menu confirmation tested both1920x1080 and2560x1440 with measured Win32
client sizes; both persisted across restart and restored the correct selected
radio (actual selected dot pixels128,132,128 vs8,8,8). Save14 loaded into battle
at both output sizes, primary remained2560x1440 with established battle controls.
Evidence: logs/remastered-ui/options-resolution-acceptance-v3/acceptance.json,
measurements.json, paired native screenshots.256 compiled detour cases and native
settings tests pass. Installed hash checked with backup options-resolution-v3;
repair/install tool tools/repair_options_resolution.py. Item1 accepted by agent;
items2-4 continue sequentially without waiting for user acceptance.


Item2 candidate options-window-v1: original animation radio group object+63+10
initializes from6de6f1 at4a950c (EDX), writesECX at4a9943. Both6-byte native
signatures checked; replacement setup loads saved window mode and apply writes
independent display/window_mode (windowed/borderless) without changing native FMV
animation. Wrapper same-process handshake from item1 used for targeting.
Windowed gives normal title/frame; borderless removes them at selected output
size (not automatic desktop-sized fullscreen). Both are nonexclusive and retain
selected resolution. STR17/24/25 replaced bytewise with GBK Chinese labels.
Current source tools/prepare_options_window.py retains accepted item1 plus
AI modules101/103 and transition wrapper.256 compiled x86 detour cases pass;
runtime four resolution/mode combinations checked actual client and style bits.
Final restart/save14 acceptance and install follow in this iteration.

Item2 final: both modes restart/save14 pass, selected dots verified from screenshots. Runtime evidence logs/remastered-ui/options-window-acceptance-v1; runtime-acceptance.json hashes exact tested binaries. Installed backup options-window-v1. Native animation6de6f1 unchanged. Item2 complete; item3 next.


Item3 options-speed-v1 updates native thresholds4a9571/4a9584 from20/17 to40/30
and native apply constants4a9a04/0b/12 from14/17/20 to20/30/40. Every whole
instruction signature checked against known engine. Native apply retains writes
to6de6fd/6dbe99 and1000/rate to6de6f9/6dbe95, plus existing prefs saver. Radio8-10
use newSTR95-97 GBK labels, avoiding shared dialogue speed labelsSTR26-28.
Existing resource101/game-time/movement compensation unchanged as requested
speed changes are part of this task, not a timing rewrite. Diagnostic-only
MM_PROBE_OPTIONS_LOGIC counter wraps the exact existing game loop tick hook
46b488, retaining resource101 detour10007c80 by verified signature; exposed
counter is read-only to controller. Production environment never enables it.
Actual save14 battle measured six seconds per rate:40~39.998,30~30.331,20~19.999
logic iterations/sec. Middle33ms native integer scheduler explains~30.3 instead
of mathematically exact30; changing general scheduler precision deferred.
Settings persistence and restart/radio visual checks are part of acceptance.
Evidence logs/remastered-ui/options-speed-acceptance-v2, tools/probe_options_speed_live.py.


Item4 accepted/installed options-render-v1. Native setup4a9537 loads the saved
render60/120 choice (EAX); apply bypasses whole4a9949..4a99dc dialogue block after
checking all148 native bytes, reads group+20 selected event4/5, leaves6de6f5
unchanged. Third legacy radio slot retained zero-size to preserve event IDs for
speed/border. Render settings use independent display/render_fps with default60.
Wrapper config sets maxfps60/120,minfps=-1,vsyncFALSE; live message restarts owned
render thread through existing dd_SetDisplayMode. Direct3D9 keeps existing
transition composer; counter counts only successful actual Present calls.
Runtime save14 samples:60~58.94/s,120~115.40/s, logic~30.05/s in both. Restart
restores both rate selections;256 compiled hook ABI cases pass. Rendering rate
is wrapper presentation frequency, may repeat source textures, not60/120 unique
simulation/animation images. Do not claim that broader unfinished goal satisfied.
Evidence logs/remastered-ui/options-render-acceptance-v1; backup options-render-v1.

User approved English for the two ambiguous Chinese labels2026-10-01. Original
configuration bytes do correctly encode logic frame/Render frame rate, but the
legacy glyph rendering makes frame look like certificate. Font root cause is
not resolved; use scoped English labels rather than expanding font work.
Installed Game speed,Fast40/Medium30/Slow20 logic FPS,Render FPS via bytewise
STR19/20/95-97 substitutions. No font/assets changed. Backup options-english-v1,
tool tools/install_options_english.py. Actual full-resolution menu screenshot
visually verified English labels fit and clearly render.
Final combined regression logs/remastered-ui/options-final-matrix-v2:1920x1080
borderless+40logic+120render measured40.11logic/116.52successful presentations;
2560x1440windowed+20logic+60render measured20.01logic/59.87presentations, actual
client/style assertions and save14 battle pass. First combined harness attempt
loaded too soon after simultaneous reset; repeated with confirmed settled menu
and two-second wait passes, no production change. All four requested settings
are implemented/installed and independently runtime accepted by agent.

Integrity: formal verify-files.ps1 checks5106static release files. Three-target
manifest audit checks5117static files each, exact entries/wrappers and preserved
modules101/103. Older build_remastered_11.verify fails only at historical missing
1.0 path; current manifest audit and formal verifier pass. All player saves and
configuration excluded from installation changes. Four option provenance fields
restored independently after discovering old generic installer used same field
name; tools/install_options_resolution.py now supports per-item metadata fields.
