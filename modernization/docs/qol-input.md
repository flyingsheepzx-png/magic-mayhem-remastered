# Single-player input improvements

## Tab roof control — 2026-10-02

User requested Tab to switch roof visibility. `hd11/roof_tab.inc` is dispatched
before ordinary spell bindings at the existing battle key hook0x46c194, after
native chat/text-input gating0x46c0d3. The native owner from stack+0x10 and LPARAM
from stack+0x34 are forwarded (pushfd/pushad offsets+0x34/+0x58); the adapter
calls thiscall0x46fc50(owner,0), including its ret4 ABI and native roof-button
refresh. Repeat keydown is consumed without cycling. Modified Tab and multiplayer
retain native handling. Ordinary menus do not use this battle callback.
Engine SHA42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.
Read-only Ghidra exports: D:/Tools/magic-mayhem-re/projects/roof-tab-20261002/.
95 compiled/native roof/main+teammate portrait checks pass; Windows key-state,
readability and native button refresh are explicit doubles. Native roof callback
and camera layer cycles execute. Gameplay acceptance pending; no game launched.
Installed by tools/build_11_roof_tab.py, backup backups/remastered-1.1-roof-tab/.
Latest resource102 source is build/remastered-1.1-roof-tab; subsequent roof ghost
iteration preserves it byte-for-byte.

## 1.1 main portrait right-click cancellation — 2026-10-02

User requires left-click self-casting and right-click cancellation on the main
player portrait. Its independent callback at0x4d2b80 previously remapped only
left release; right events still reached the native portrait casting branch.
`hd11/main_portrait_input.inc` now distinguishes native fallback, left casting,
and consumed events. During single-player targeting with a pending spell,
right down is consumed and right release calls native0x509bd0(unit,-1); the
detour consumes both without calling0x57ce70. Left release retains its native
cursor/target checks. Non-targeting and multiplayer fallback stay unchanged.

Build/install/rollback: `tools/build_11_main_portrait_cancel.py`; verification:
`tools/verify_11_main_portrait_cancel.py`. Build starts from the exact installed
options-render-v1 resource102 source and wrap-route-v1 launcher/resources,
preserving module101 wrapped routing/command-marker fixes and module103.
All three entry manifests/hashes are checked before installation, backed up to
`backups/remastered-1.1-main-portrait-cancel/`, and verified after replacement.
78 compiled/native main and teammate portrait checks passed, plus existing
native surface lifecycle/registry regressions. Windows readability and native
pending/queue APIs use explicit test doubles; actual native cast construction
is executed. Gameplay acceptance remains pending user testing; no game launched.
Rollback with game closed:
`C:/Python314/python.exe modernization/tools/build_11_main_portrait_cancel.py rollback`.

## 1.1 teammate wizard portrait input — 2026-10-01

User clarified the location is upper LEFT, second teammate wizard portrait.
The final installed correction matches it. User's test18 healing reproduction
exposed another control class: teammate wizard
portraits use vtable0x5c5c2c and callback0x463030, with represented unit pointer at
control+0x89. The prior main-player portrait hook0x4d2b80 never covers it. Native
left-release branch0x463030..0x463163 changes selection; native right-release
branch0x463236..0x46324f calls0x57ce70 on the represented unit. Engine identity:
42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da.

Owned background test18 baseline diagnostics in logs/remastered-ui/
test18-teammate-before-v3 confirmed second wizard targetindex32 and left-click
mode2->0 without mana/life change. Right click remained mode2 with no observed
mana/life change during the short window; do not claim healing execution from
this record. Native control geometry in this fixture places the two wizard
portraits on the left. Right HUD creature controls have a different class;
their proposed extension was not installed after the user's correction.
Native-surface screenshot
resolved which wizard portraits the fixture exposes.

New teammate_portrait.inc installs a gated detour at0x463030. During valid pending
single-player targeting it consumes mouse down, preventing native selection;
left release validates the represented active/alive/aligned unit through native
0x57cf40, then submits via0x57ce70. Cursor5 is supplied only after valid native
predicate, then restored. Right down is consumed, right release resets the
pending spell through0x509bd0. Hover/tooltips and non-targeting/native selection
remain original; no hardcoded spell ID or replacement target rules.

42 Unicorn checks execute the compiled adapter, native callback and original
portrait command constructor. They verify release-only commands, actual payload
spell41/caster77/target123 (different target from caster), registers/stack,
cursor restoration, invalid target rejection, right cancellation, and equality
with native behavior outside targeting/multiplayer/no pending spell. Native
eligibility and queue APIs are stubbed: actual treatment effect, repeated casts
and live cancellation remain user acceptance, not established by offline checks.

Installed isolated1.1 via build_11_teammate_portrait.py: only launcher resource102
changes, all other embedded resources preserved;5882 runtime entries verified,
runtime bytes including game_handles_close=true retained; protected1.0/v38
unchanged. Final backup: modernization/backups/remastered-1.1-teammate-portrait-final.
Report: modernization/build/remastered-1.1-teammate-portrait/verification.json.
Rollback after closing game:
`C:/Python314/python.exe modernization/tools/build_11_teammate_portrait.py rollback`.
Stop after install for user test18 acceptance. Intermittent load hang remains next.

## Double-press self-cast — 2026-09-30 (v26 installed)

User requested two presses of a bound spell key to cast on self, using the
portrait behavior and preferably native eligibility. Two fresh WM_KEYDOWNs of
the same bound key within 400 ms form one pair. Auto-repeat never counts.
The first press retains the native spell-button callback. The second requires
the same wizard, spell and still-armed pending slot, then consumes the pair.
Different/unbound keys, modifiers, Portmanteau input, world mouse buttons,
portrait clicks and box selection clear the remembered pair. No multiplayer
change. Empty slots cannot resolve a battle spell.

Native portrait-hover evidence: `0x4fd209..0x4fd226` resolves the local wizard
via thiscall `0x466870` (ECX=`0x643a80`, stack player ID at `0x644520`) and calls
thiscall `0x57cf40` with the target in ECX. Its low-byte result is cursor 5 for
valid casting, 16 for invalid; it delegates to native `0x57c730` with the current
pending spell, caster and target. v26 calls this exact predicate with self as
target, and submits only result 5 via the existing `0x57ce70` portrait path.
No healing/lightning IDs are hardcoded. The spell's native target rules decide.

The portrait submitter checks global cursor `0x5e04c8`, which normally describes
the real mouse target. After successful self validation, v26 saves that value,
supplies 5 only during synchronous native command construction, then restores
it; mouse coordinates and visible cursor are not moved. This prevents a valid
mouse target elsewhere from authorizing an invalid self-target, and allows
self-casting regardless of current mouse position.

Static export: `D:/Tools/magic-mayhem-re/projects/qol-doublekey-export` from
community SHA-256 `b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
Installer compares relevant native code ranges to installed engine SHA-256
`43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`.
All addresses are preferred VA, image base `0x400000`.

Build and installation integrity passed; runtime acceptance remains with user
(W healing, E lightning, single presses and long holds). No game launched.
Only embedded QoL resource 102 changed, preserving all other launcher sections,
resources, engine, terrain DLL, saves and configs.
Entry SHA-256: `c23ec895ca1cb5dae31556a9e76713e4963e5125ca4501ed63a344f5ffbe2301`.
Backup: `modernization/backups/wide169/qol-refresh-1790705199263449500`.
Rollback to v25: `python modernization/tools/install_qol_double_key.py rollback`.

## Empty purchased slots — 2026-09-30 (v25 installed, acceptance pending)

The user reported v24 did NOT resolve the new-talisman binding issue. Its
live-item fix retained `item<0` rejection, so native empty slots (`+0x7e=-1`)
still could not bind. The renderer also hid their badges. Native `0x575c00`
constructs the purchased tray controls and `0x579710` sets -1 as an empty
control; empty slots remain valid tray/slot binding targets.

v25 accepts -1 in both hit testing and badge rendering, within the existing
native tray count and control bounds. Values below -1 or above 20 remain
rejected. Battle dispatch still requires an actual equipped spell, so an empty
binding cannot cast. Placement of a spell in the slot inherits its key.
This broadens empty-slot assignment consistently, rather than treating only
newly added slots differently. v24's tooltip order and full redraw remain.

Built and installed without gameplay testing per the user's standing policy.
Entry SHA-256: `a7928183cd379f8c0885413c3d6007a4409b99ba9884c1e994994e0ee3e05f60`.
Backup: `modernization/backups/wide169/qol-refresh-1790703668348727200`.
Rollback to v24: `python modernization/tools/install_qol_empty_slots.py rollback`.
The exact test11 flow still awaits user confirmation; v24's earlier claim of
resolving it must not be treated as successful runtime evidence.

## test11 live slots and badge refresh — 2026-09-30 (v24 installed)

User report: adding a Chaos talisman through character advancement while the
Portmanteau remains open requires reopening before hotkey assignment; transferring
a key leaves the old badge until hover; badges cover tooltips.

`hovered_equipped_slot` now reads control `+0x7e`, exactly as native hover lookup
`0x577240` does, rather than the open-time `ui+0xb4` tray cache. Native
`0x579710` writes that live item; `0x575890` copies live controls to the cache
when closing, so the existing battle lookup remains valid after exit.

Successful binding/transfer/Delete sets native `ui+0x248=1`. Portmanteau draw
`0x576830` restores the background and `0x5773d0` redraws all controls under
that flag, clearing the former owner's badge without requiring mouse hover.
Badges no longer hook final surface presentation `0x58bf40`. They draw before
the native tooltip call at `0x576d8b` (Portmanteau, UI in EBP) and `0x46ede1`
(battle). Both call `0x4db7e0` with ECX preserved; tooltip/cursor painting occurs
after badges. The Portmanteau call explicitly selects UI mode even when battle
selection still exists. Empty live slots do not display badges.

Static evidence: Ghidra read-only export in
`D:/Tools/magic-mayhem-re/projects/qol-refresh-export`; community input SHA-256
`b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
Installed engine SHA-256
`43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`;
preferred image base `0x400000`. New call-site signatures are respectively
`e8 50 4a f6 ff` and `e8 fa c9 06 00`, verified on that installed engine and
checked before hook installation. No new engine file patches.

Before editing, rebuilding the QoL source matched installed resource 102's
`.text`, `.data`, `.fptable`, `.reloc` exactly; the only `.rdata` differences
were three bytes of the debug timestamp. v24 replaces only resource 102 in
the exact v23 launcher. All other resources and non-resource sections compare
byte-for-byte, preserving terrain injection and the existing repath module.

MSVC x86 build and installation integrity checks passed. No game was launched:
the user requested direct installation and will perform gameplay acceptance.
The test11 flow, transfer/Delete refresh and tooltip overlap await user testing.
Installed entry SHA-256:
`69018495fde8109d18f4aea69aefc2e1b9eb762b4c50045d7a39fda34e5bdac5`.
Backup: `modernization/backups/wide169/qol-refresh-1790703372931353200`.
Rollback (game closed): `python modernization/tools/install_qol_refresh.py rollback`.
Saves, settings, binding config, engine and terrain DLL hashes remained unchanged.

## Accepted requirements (2026-09-27)

- Wait for the test5 HD correction before implementation; that task completed.
- Ctrl+1..9/0 stores groups; digits recall groups; Shift no longer stores groups.
- Hover an equipped Portmanteau talisman slot and press QWER/ASDF/ZXCV to bind.
  Delete clears. Bindings follow tray/slot identity, survive replacing its spell,
  and are shared across single-player saves in a separate config (no save changes).
  A duplicate key transfers from its old slot. Initially all keys are unbound.
- Bound letters override native actions; unbound letters retain them. Audit native
  shortcuts before shipping. Display bindings in Portmanteau and battle spell HUD.
- The user resumed targeting development and requested left-click cast, right-click
  cancel, the same mouse/keyboard spell-selection sound, and preserving selected
  units throughout casting. These requirements supersede the earlier binding-only
  scope; implement them only in the opt-in HD QoL entry.
- The user additionally reports that battle picking appears centred on the cursor
  sprite rather than its tip. Verify cursor frame origins, hotspots, wrapper scaling
  and native picking before changing coordinates; align arrow tip and interaction.
- Other improvements are suggestions only in this release.
- Config authority: `modernization/config/qol-hotkeys.json`. Slot identity is
  native tray type plus slot index, never battle icon order or screen position.
  Empty slots retain their binding but have no battle action. No initial bindings.
- Preserve all other Shift operations. Bound letters will have priority over native
  actions in the later casting phase; unbound letters continue native handling.
- Use verified original community image for address research; accepted HD test5
  engine hash is be56ceb3ca4f8eacd9414136237cd8d15899585f79a250203125d72f95c590c7.
  Preserve existing accepted runtime, backups, rollback, multiplayer and save format.

## HD development resumed (2026-09-27)

### Casting controls follow-up (2026-09-27)

Installed in `game/Chaos-HD60-QoL-Trial.exe` (exact hashes in
`../hd-qol-trial-installed.json`):

- Left mouse release in the battle viewport submits through the original cast path.
  A held left button does not cast. Crossing the native >32-pixel box-selection
  threshold cancels the pending spell immediately and continues native box selection.
  Right mouse down cancels the pending spell without selecting the clicked unit.
  Ordinary map input and spell HUD buttons retain native mouse handling.
- Keyboard spell activation plays the icon's native sound (`icon+0x51`, 820 in
  test7) through `0x56f000` with the same seven arguments as mouse selection at
  `0x4d3f1c`. This matches the native call; loopback audio/listening was not tested.
- Both mouse and keyboard spell selection preserve selected units, their count,
  selection indicators and the multi-selection flag. The local-wizard path in
  `0x509bd0` skips deselection while retaining native target state and spell index.
- Validity, range, mana, effects and repeated casting remain native. Selecting a
  spell does not guarantee a valid target. Target mode remains active after a
  cast, as in the native workflow, until cancelled or another action exits it.

`tools/verify_hd_qol_casting.py` passed a bounded background run with 19 recorded
checkpoints, including all four current Q/W/E/R mappings, cancellation with
selection intact, mouse spell selection, left-click creation of a new allied
bat (type 15, owner 1) in test7, and normal right-click movement in test2.
The release/drag follow-up verified no summon while holding left for 1.5 s,
summon only after release, and cancellation before a box drag was released
without a summon. Evidence: `../logs/hd-qol-casting.json`. Selection was sampled throughout the
summon wait. Wrapper/INI were restored, all seven saves remained unchanged, and
the user's Q/W/E/R config was unchanged. Multi-unit selections,
foreground audio and extended combat remain wider compatibility gates.

Address evidence (verified community/accepted HD engine identities above):
`0x4fdad0` is the battle viewport handler; mode `0x6903e8 == 2` dispatches
right-down bit 4 to native cast submission at `0x4fdc0c`. The QoL entry remaps
left release bit 2 to native right-down bit 4 only inside that handler and calls `0x509bd0(unit,-1)` on right
cancel. Other controls bypass the hook. `0x509ca6` normally starts the local
wizard's unit deselection loop; the hook preserves selection and resumes at
`0x509d47`, which sets native target mode. The native box-selection threshold call at `0x4a54cf` is also hooked: it
clears the pending spell through the native reset and returns the original
selected-unit pointer before native drag selection continues. All hooks verify original bytes;
multiplayer retains the original deselection loop and mouse dispatch.

Rollback: `python modernization/tools/install_hd_qol_trial.py rollback` removes
only the verified opt-in launcher. The previous launcher, embedded QoL DLL,
manifest and bindings are preserved under
`../backups/hd-qol-trial/1ed8d1866d74331c015fad7b9190c6c1a6f6553331384db78090d746da272497/`.
The accepted HD60 launcher and engine are unchanged.

### Earlier battle shortcut evidence (superseded targeting limitations)

The separate opt-in HD QoL entry now routes a bound, unmodified letter key to
the matching native spell button callback. It uses the same tray/slot identity
as Portmanteau, reconstructs native equipped order, checks the live selected
player wizard's spell list, and accepts only one ordinary type-0 icon with that
spell. Temporary type-1 icons are excluded, including test7's duplicate spell
11. Unbound keys and Ctrl/Alt/Shift modified keys continue to native input.
No cast or target command is synthesized; the native button callback owns the
subsequent target interaction. This is installed only in
`game/Chaos-HD60-QoL-Trial.exe`.

The revised `test7.sav` is hash-gated in `../config/qol-fixtures.json` with
SHA-256 `c316775c27f57e625670e3def8c2edd43ea2df130286e57cf00b5ee0a31b3927`.
Its four equipped spells are 41, 74, 15, 11 in the same native tray/slot order
as test6. Q/W/A/Z mapped to battle icons 0/1/2/3 and moved `active_icon` from
-1 to the expected index; unbound E left it at -1. A fresh process with the
pre-test Q/W/E/R layout mapped R to icon 1. A repeated Q kept icon 0 active.
Four battle badges passed 1008 exact pixel checks, and the duplicate type-1
spell 11 icon received no badge. Evidence:
`../logs/test6-qol-identity.json`, `../logs/test7-qol-identity.json`,
`../logs/hd-qol-battle-keys.json` and the process-owned session log.

The native click callback clears unit selection while targeting. After a
background left click in target mode, `active_icon` returned to -1; this does
not prove a spell effect or successful cast. The diagnostic right-click did not
clear target mode, so right-click cancellation and selection preservation are
still open. Source replay for Ctrl/Alt/Shift and focus/menu contexts remains a
compatibility gate. The accepted HD60 entry, engine, saves and wrapper/INI
were unchanged by the owned sessions; the test config was restored.

The user explicitly resumed development after the directory migration. The old
pause/rollback entries below are historical and no longer prohibit this work.
Current opt-in entry: `game/Chaos-HD60-QoL-Trial.exe`; it pairs with the unchanged
accepted `game/Chaos-HD60-engine.exe` and embeds byte-identical accepted
`combined_hd60.dll` plus `runtime/hd_qol_trial/qol_bindings.dll`. The accepted
HD60 launcher itself is unchanged. Exact hashes are recorded in
`../hd-qol-trial-installed.json`.

### Passed live binding gates

`test6.sav` SHA-256 is
`4031940a5838ae30ca94c24e103521c2ccf9d8e45cf7f12b0d1d1cea2144209b`.
It loads the realm map; click its relocated Portmanteau control at native
(1090,30). Four equipped controls are confirmed by handler telemetry:
tray 0 slots 0/1 at (272,711,386,826)/(272,595,386,710), tray 1 slot 0 at
(144,711,259,826), tray 2 slot 0 at (17,711,132,826).

The earlier failed hover was reproduced: the handler's cached native mouse was
(315,640), while GetCursorPos/ScreenToClient reported (1698,1132), outside the
background game client. The corrected binding path uses the same native
`ui+0x9c/+0xa0` coordinates as original `0x577240`, with surface bounds checks;
it does not offset desktop/UI coordinates. All 12 keys QWER/ASDF/ZXCV wrote the
expected config; one-key-per-slot replacement, cross-tray unique-key transfer,
Delete clear and outside-control no-change passed. Restart reload followed by
Delete confirmed persistence. Four layout tests passed, including empty/replaced
slot semantics. The default config was restored empty after testing.

Portmanteau labels use a small 5x7 bitmap badge drawn on the native 16-bit primary
surface immediately before presentation. A Q badge at (368,687)-(382,705)
passed all 252 expected pixel checks. The new handler/presentation hooks plus
11 accepted hooks passed (13/13). Drawing and binding hooks verify original
bytes; the launcher verifies the unchanged HD engine hash. Saves and accepted
wrapper/INI remained unchanged after each owned session.

Evidence: `../logs/hd-qol-live-binding.json`, `../logs/hd-qol-label.json`,
`../logs/hd-qol-startup.json`, `../logs/hd-qol-background-session.json`.

### Scope still open

This trial now activates native battle spell buttons through bound letters;
it is not a completed casting workflow. Live replacement/reorder,
load across different saves, ordinary foreground play, native text/menu focus
and sustained compatibility remain open. The casting-controls follow-up above supersedes the earlier targeting phase. The native Ctrl group path and all
other Shift operations are unchanged.

Run from project root:

```powershell
python modernization/tools/install_hd_qol_trial.py verify
python modernization/tools/hd_qol_background_session.py start
python modernization/tools/hd_qol_background_session.py load-test6
python modernization/tools/hd_qol_background_session.py click 1090 30
# Fresh process + empty backed-up layout required; test changes bindings.
python modernization/tools/verify_hd_qol_live.py
python modernization/tools/hd_qol_background_session.py stop
python modernization/tools/install_hd_qol_trial.py rollback
```

Rollback removes only the known opt-in entry and preserves config and the
accepted HD60 entry; rollback/reinstall was exercised. `stop` restores the
diagnostic wrapper/INI and checks all six save hashes. Never leave a diagnostic
session running after development. Trial install does not promote its entry or
change `current-baseline.json`.

### Native unit picking evidence

In test2, native click (536,341) selected unit 0 while the visible sprite is
lower/right. Read-only memory confirmed `selected_count: 0 -> 1`, `unit0+0x68:
0 -> 1`, unchanged grid (66,48,6), and cursor draw top-left exactly (536,341).
Pressing unassigned digit 0 clears selection before each probe without memory
writes. The 132-point pick grid shows a broad rounded region approximately
centred around (560,375), extending from y=325 through y=435; many accepted points
lie outside the visible body. Report: `../logs/test2-native-pick-grid.json`.
The grid spans x=510..610 and y=325..435 (10-pixel steps); its central
rows accepted all 11 sampled x positions, while the outer rows narrowed.
This reproduces an excessive native hit region; it does not establish a global
mouse-coordinate offset or prove its exact internal algorithm. No picking patch
or UI/cursor shift was installed. Next map native hit geometry/projection and
validate sprite-aware picking with overlap/terrain cases before changing it.

## Historical progress

**User-requested rollback, 2026-09-27:** QoL work is paused. The installed trial
and its build artifacts were restored to the pre-input-fix launcher
`13e2b5554a8c3001228fb48b31f74825336f0c9b3f2c7a35a35870f31384ddc7`
and module `03d79dfc15aa31ed2db9c55c2a5898b0c0d80fc610b313bcee1af6e5fc79be70`.
The later binaries and manifest are preserved in `backups/qol_trial/rollback-20260927`.
The diagnostic wrapper and INI were restored byte-for-byte; the session recorded
no save changes. Only agent-created fixture copies were removed. HD60 launcher
and engine remain in `C:/Users/DEVELOPER/.codex/worktrees/hd-ui-lab/Magic&Mayham`,
matching the accepted test5 hashes, with test4/test5/test6 still present. Source
changes remain research material and are not the installed build; do not rebuild
or reinstall without a subsequent user instruction to resume.

An isolated 800x600 trial entry now exists at root `Chaos-QoL-Trial.exe` with
`runtime/qol_hotkeys/qol_bindings.cpp`. It embeds the unchanged frozen full60
DLL plus a separate QoL DLL. Launcher SHA-256 is
`afa84b92079920a12512514dfa84d521cd297df871f62e624f6ddd0ec14c662b`;
QoL DLL SHA-256 is
`49414a7816f066cd3851c8da28a4398e98f5cf400b13398096b5887fc0143757`.
The installer is `tools/install_qol_trial.py`, with `install`, `verify`,
`status`, and `rollback`; rollback removes only the verified trial launcher
and preserves the layout file. The root main launcher and frozen runtime are
unchanged. An owned startup verified 11 existing and one new hook loaded.
Binding transition, empty-slot activation, transfer, clear and config reload
tests pass. **The trial is not accepted or feature complete:** live Portmanteau
binding, labels, HD composition and full regression have not passed.

On 2026-09-27 a live test exposed an assembly argument bug in the Portmanteau
detour: the first build read wrong stack offsets and stored its result in the
saved flags instead of saved EAX. Original code at `0x578610` confirms a
`thiscall` UI pointer in ECX and four stack arguments. The detour was corrected
and rebuilt; the current launcher and DLL hashes are above. The installer now
backs up each known prior trial launcher by SHA-256 before replacing it.
Compilation, install/verify, all 12 startup hooks and four layout tests pass.
These checks still do not establish live binding. A copied test4 victory save
reached the Portmanteau, but its first-open tutorial overlay obscured the slots.
No live key-to-slot write or on-screen label was verified. The temporary save
copy was removed, and all three pre-existing save SHA-256 hashes matched their
pre-test records in `logs/qol-save-before-test4.json`.
A subsequent launch briefly displayed a black game client and Escape ended that
process. A fresh normal launch then reached the title menu. This does not
establish Portmanteau input or regression safety.
A later live Q press while the mouse remained over the visible middle equipped
talisman did not modify the empty JSON layout. Clicking that talisman advanced
the tutorial overlay. Therefore the earlier overlay-blocking explanation is
not established: inspect handler delivery, UI pointer and live native control
rectangles before declaring hover binding functional. The game was closed and
the copied fixture removed; original saves again matched their recorded hashes.

## Verified native input evidence

- Original community engine SHA-256:
  `b1eccc46cc16065d57c277fca9c0993635b7b645b3b3b7717759d8bf1c800291`.
  Its `0x46c070` message handler dispatches key down (`0x46c0c5`) and key up
  (`0x46dd02`) separately. `0x52abc0` reads Shift through `GetKeyState(0x10)`
  and Ctrl through `GetKeyState(0x11)`; Ctrl writes group field `unit+0x8e9`.
  Shift adds members during group recall. The original engine already implements
  the requested Ctrl+digits behavior. In test2, all ten Ctrl+1..9/0 presses
  wrote group IDs 1..9/0 to unit 0. Shift+2 did not replace group 1. Keep this
  native function and other Shift actions unchanged; no group address patch.
- Letter keydown dispatch: Q `0x46dc4f` coordinate diagnostic; W `0x46d1dd`
  wizard selection/locating; A `0x46d0c6` toggles `0x6e1f28` when Alt is not
  down; S `0x46d1ae` cycles `0x5e140c`; Z `0x46d3a8`, X `0x46d6e5` cycle
  selection; C `0x46da1c`, V `0x46da33` locate selected units; E/R/D/F have
  no dedicated ordinary keydown target in the verified jump table. The trial
  does not consume letters in battle, so native actions retain priority until
  the later casting phase. One-wizard test2 could not establish full Z/X/C/V
  behaviour. Menu/text/focus and keyup remain native in this trial.
- Portmanteau handler `0x578610` is distinct from battle input. The trial hook
  verifies its original seven bytes before replacing them; it only considers
  first keydown (no repeat) for 12 letters or Delete and leaves all other
  messages native. Hover checks live native control rectangles at `ui+0x218`,
  their three native tray counts at `ui+0x84`, and equipped spell IDs at
  `ui+0xb4`; slots are indexed within tray and do not depend on screen position.
  These structures are static leads from `0x575890`, `0x576830`, `0x577240`
  and still require live slot-by-slot confirmation. No manual invented screen
  rectangle is used. The config starts empty and is save independent.

## Cursor alignment investigation

- User clarification (2026-09-27): UI clicks are accurate; only unit picking
  feels offset. The official original also reproduces it. In the supplied test2
  screenshot the arrow tip is above-left of the selection box, yet a left click
  selects the unit. Use test2 for hit-region measurement and test6 (four equipped
  talismans in the HD lab Save directory) for binding validation. Prefer Python
  background input and read-only memory telemetry for both.

- The actual battle cursors use `Bitmaps/cursors.bmp` and `CFG/cursors.cfg`.
  Default, selection, move and spell cursors specify hotspot `(0,0)` and the
  arrow tip is at the top-left of its 40x40 atlas tile. External `.cur` files
  have `(1,1)` hotspots and are a separate Windows cursor path.
- Original draw code `0x4a49cd` gets screen cursor position, converts it with
  `ScreenToClient`, then subtracts the configured hotspot at `0x4a4a18`.
  In a live 800x600 trial, Windows client cursor `(650,527)`, engine mouse
  queue `(650,527)` and cursor draw top-left `(650,527)` matched exactly.
  This refutes a global cursor-centre hotspot offset for that state.
- A test3 click near overlapping wizard/creature sprites selected a different
  unit, but that battle ended before a controlled pick-grid comparison. Unit
  hit shape, scene projection, wrapper scaling at HD and target-specific
  picking are open. Do not move the cursor artwork or shift all click coordinates
  without measuring the exact failing target and native hit result.

## Remaining gates and later suggestions

- Reach a non-tutorial Portmanteau screen with equipped slots, confirm the
  handler hook fires, bind/transfer/Delete with runtime config and pixel checks,
  then add labels to both slot controls and battle spell icons. The new-game
  tutorial blocked Portmanteau testing; test2/test3 did not expose it.
- Validate each of the twelve binding keys, empty and replaced slots, config
  reload across saves, 800x600 and accepted HD test5, menu/text focus, mouse
  input, ordinary commands, selection and rollback. HD test5 uses an isolated
  engine and requires a separately hash-gated launcher plus hook conflict audit.
- Casting/targeting, left/right click isolation, success/failure/cancel state,
  preserving selection and native mana/target checks now follow the casting
  implementation above; wider compatibility remains open.
- Later optional ideas: double-digit group camera centering (low to medium,
  conflicts with rapid normal digit recall); append/remove group membership
  (medium, requires preserving Shift recall); remap displaced native functions
  (medium, conflicts with the twelve-key layout); better range/mana/invalid
  target feedback (medium, depends on cast-result hooks); instant cast at mouse
  (high, conflicts with target validation and click isolation).

## Conditional movement click passthrough — 2026-10-02

User requested all occluding terrain, conditional on the original destination
being unreachable, replacing the initially proposed tree-canopy whitelist.
Implemented in runtime/hd11/canopy_pick.inc (historical file name retained).
Native terrain mask calls 4f8aee/4f8b26/4f8b5e still return their original hit
result and collect up to128 actual hit cells, reset at4f83f0 per render pass.
No global visual hit priority or cursor-coordinate transform changes.

Ordinary single-player right-down movement, kind1, without modifiers: verify
the last hit matches native picked terrain and the map still matches; normalize
solid type94=16 to the native above-surface destination. Selected normal walking
units use native514360 kind0 transition edges in a bounded A* (4096 nodes,
24000 total validator calls shared across original and up to12 alternatives).
A successful path preserves the original destination. Only a proved failure
(no incoming edges or exhausted connected component) permits fallback. Budget/
node exhaustion means unknown, preserving native behavior. Behind alternatives
are actual terrain-mask hits at the same pixel, nearest/frontmost first, no
neighbor snapping, no teleporting or collision bypass. Selected groups retain
the original if any supported unit can reach it or any result is unknown; a
replacement must be reachable by all selected supported units. Groups>32 or
unsupported movers retain native behavior. Units/items/spells/force modifiers
and multiplayer keep native dispatch; this covers terrain occluders, not forcing
clicks through enemy units or interactable item targets. Structural passability
uses native transition rules; transient-state classification is not separately
proven.

114 compiled/native regression checks pass (19 conditional-pick,95 existing
roof/main/teammate), plus existing native surface lifetime tests at build.
Isolated save22 evidence logs/remastered-ui/save22-pick-conditional-final:
logical(672,344) native pick(81,89,7), old destination(81,89,8); fallback
submits(80,88,5), while subsequent rendering still picks the foreground canopy.
A separate unoccluded(688,312) click retains the original destination(79,87,5).
No claim of portal transition or full gameplay acceptance; user testing pending.
Build/install/rollback: tools/build_11_canopy_pick.py; backups/remastered-1.1-canopy-pick.

## Save23 native-HD Portmanteau binding repair — 2026-10-02

Reproduced user report in an isolated copy of formal1.1 using save23.
Mouse(884,1318) was inside tray0/slot0 rectangle(786,1220,982,1416),
but hovered_equipped_slot rejected the primary2560x1440 because it still
required width<=1280,height<=840. Old Q remained assigned to slot1. This
predates and is independent of the battle-only conditional-click hook.

Replace that old cap with mm_ui_fit(current primary width,height) content
bounds and a positive/8192 safety limit. Mouse and native packed rectangles
already share UI coordinates: no inverse scaling or battle factor is applied.
The current1920x1440 content at x320 and future primary sizes use the same
shared viewport geometry. Existing occupied/empty slot validation, uniqueness,
configuration load/save and full-page redraw remain unchanged.

Build/source: build/remastered-1.1-port-bindings-hd from exact canopy-pick
module102 source, preserving101 roof-ghost-v2,103 and all input/AI/options fixes.
Tools/build_11_port_bindings_hd.py supplies hash-gated install and rollback;
backup backups/remastered-1.1-port-bindings-hd. Verification196 checks:
82 compiled event/real-save23 rectangle checks plus114 earlier terrain/roof/
portrait regressions; config I/O and PtInRect are explicit emulator doubles.
The isolated live save23 test separately validates real config writing: Q
reassignment removes W from the same slot, Q transfer, and Delete unbind.
Evidence logs/remastered-ui/save23-bindings-before and save23-bindings-after.
Installed player hotkey file and save23 hashes must remain unchanged. Broader
playability/visual acceptance stays with user after installation.

## Save24 fully obscured floors — 2026-10-02

User requested the marked wall/roof-edge cell to permit conditional movement
click passthrough. Native hit-stack capture could contain only the upper roof;
the lower floor was not drawn/hit. Preserve the unreachable-only gate and add
up to32 lower layers: first supported same-column floors, then native64x32
isometric floor footprints derived from the final hit anchor, mouse pixel,
rotation and16-pixel elevation steps. Fixed-point inverse projection handles
all4 rotations and map wrapping. Only known solid-support type94=16 cells
without fog/hidden flags qualify; native514360 reachability still decides,
with the existing total24000-call/4096-node cap and unknown preserving native.
This picks a floor destination; it never permits walking through a solid wall.
Actual opaque-hit fallback remains last. Original reachable roof/bridge targets
remain unchanged.

Source/build remastered-1.1-roof-click-floor over exact port-bindings-hd; only
canopy_pick.inc changed. Resource101/103 and all recent bindings/options/AI/roof
fixes preserved.205 compiled regressions include4 inverse-projection rotations,
vertical floor fallback, single-hit stacks, fog rejection/reset/native-hit ABI,
and previous196 input/binding checks. Updated save24 SHA
25f15ddc36667c63c5e8347cc0e36fc3f8bd4c51c99dc3a74adda9da5320f3cd:
logical(698,354) pick(99,97,9) had only one opaque hit; now submits floor
(96,95,6), standing destination(96,95,7), status6. Private-input/read-only evidence
logs/remastered-ui/save24-pick-final-v2. First final diagnostic startup exited,
a fresh isolated retry passed; no general startup reliability claim.
Build/install/rollback tools/build_11_roof_click_floor.py; backup roof-click-floor.
Broader gameplay and precise user-marked destination acceptance pending user.

## Save24 projection correction — 2026-10-02

User reports that fallback responds but selects the wrong cell, including walls
and rotated views. The earlier205 checks did not establish correct native pixel
ownership. Supersede the same-column priority and old inverse-footprint formula
above; do not reintroduce them in future builds.

Three defects confirmed in `canopy_pick.inc`: supported same-column floors were
accepted without testing the click pixel; a second camera rotation was applied
to native picker/map coordinates; and inverse-grid footprints used an overlapping
L1 radius64 rather than disjoint square ownership. Surface height also used
z-1 instead of the supported standing plane z+1, shifting the prediction32 pixels.

Hash-verified engine42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da:
existing Ghidra4f83f0 export checked against native instructions; actual4f83f0
traversal and4f8230 camera-origin emulation confirms picker axes X(+32,+16),
Y(-32,+16), elevation(0,-16) in all four camera states. Sprite processing4f8960
is a capture-only test double. Native4f8c3e directly copies scene7d/81/85 into
6c5488/6c5484/6cbb64, so these are the SAME coordinate space used by movement
and reachability. Changing view does not justify another inverse rotation on
offsets already expressed relative to this picker grid.

For support floor z, calculate px=mouseX-anchorX and
py=2*(mouseY-anchorY+16*(z+1-raw.z)); inverse coordinates dx=py+px,dy=py-px.
Tile offset(ix,iy) owns -32<=dx-64ix<32 AND -32<=dy-64iy<32. Half-open edges
choose one cell consistently. Select highest reachable projected top plane;
never prefer an arbitrary reachable vertical column. Original-reachable targets,
bounded native514360 search, fog/modifier/spell/unit/item gates and actual opaque
hit fallback retain their earlier semantics. Walls remain collision geometry.

Candidate `build/remastered-1.1-pick-projection/` derives102 from the exact
installed roof-click-floor, retaining AI/options/bindings;101/103 and launcher
sources come from latest movement-timing. Timing iteration1 remains intact;
movement smoothing iteration2 is paused until user feedback.

907 offline checks pass:196 prior input/roof/portrait/binding cases plus711
projection/traversal cases. These cover four views, signed/wrapped offsets,
unique pixel ownership/edges, rejection of a same-column hijack, fog and native
reachable-target preservation. Real captured save24 terrain and native514360,
with Windows/readability doubles, now select floor(97,96,6), standing(97,96,7),
adjacent to protagonist(97,97,7), at logical mouse(684,338). Previous probe's
logical(698,354) is a different pixel and is not substituted for the marked
cell. Tests do not launch the game; rotated live gameplay remains user acceptance.
Report `build/remastered-1.1-pick-projection/verification.json`.

Build/install/rollback: `C:/Python314/python.exe modernization/tools/build_11_pick_projection.py install`
or `rollback`; backups `backups/remastered-1.1-pick-projection/`. Hash guards
refuse changed launchers/manifests or a running game; rollback retains the
preceding movement-timing iteration. Canonical runtime/hd11/canopy_pick.inc
updated with the corrected projection to prevent later-source regressions.
Installed into formal1.1, continuing playtest and release staging; all three
launcher/manifest/resource hashes verified.205 protected runtime/settings/save/AI
files unchanged; installed-verification.json and rollback.json record checks.
