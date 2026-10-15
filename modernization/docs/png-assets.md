# General PNG asset migration and formal release — 2026-09-30

User accepted the 190-page PNG trial and requested formal promotion, checking
remaining BMP resources and converting all development BMPs. Promotion first
retained formal Save/settings; played-trial CFG consumption/encryption was
recognized as normal runtime mutation. User acceptance applies to those 190
pages; the additional general loader and 50 external assets need user runtime
acceptance. No game process was launched during this task.

## Current outcome

Formal: `D:/Games/Magic&Mayham_Remastered_1.0`, 482,071,093 bytes (482.07 MB),
5,069 manifest payloads plus manifest; 240 external PNG image files and zero
external BMPs. Original formal BMP distribution was approximately 704.20 MB;
accepted page-only PNG distribution was 491.77 MB. The original game executable,
existing enhancement/QoL/terrain modules and accepted png_pages.dll remain exact.
New hash-pinned general PNG loader and JPEG forwarding DLL extend compatibility.

Active directories `game/`, `game-wide169/` and
`modernization/playtests/mixed-ui-v4/game-wide169/` each have zero external BMPs.
770 copies (50 formal + 240 per three runtime roots) were converted losslessly.
Three active followup BMP derivatives also converted. Stale generated release
and intermediate runtime copies were archived with verified per-file recovery;
canonical release staging now mirrors the formal PNG distribution.
Whole active checkout scan found zero external BMPs, excluding intentionally
immutable original source, baseline, version packages, named before-* backups
and the verified content-addressed checkpoint. Those originals are retained.
PE bitmap/icon resources and encoded SPR files are not external BMP files.

Developer latest entry stays `game/Chaos-Wide169-Trial.exe`. Immutable package
v38 `package-v38-png-assets` extends v37, with prior engine identity unchanged.
`current-baseline.json.latest_development` and wide169-installed.json point to
its verified package and PNG loader hashes. Mixed candidate manifest remaps
converted asset entries to PNG and records newly pending compatibility gates.
Widescreen/followup generators now write PNG lossless derivatives. Historical
HD BMP selector explicitly refuses PNG-migrated runtimes rather than silently
regenerating obsolete formats; original inputs and backups remain available.
Formal packing template and provenance now follow v38 with loader hash pins.

## Native interface

Known engine allowlist (exact disk hashes, unchanged): original community,
accepted HD60, active wide v37/v38 and mixed UI v4. Values/signatures recorded in
releases/png-assets/static-hook-verification.json. Image base must be 0x400000.
Hook at native BMP file-object loader 0x486ae0 requires
`8b 44 24 04 83 ec 38`. Seven relocated instructions contain no PC-relative
operand; a trampoline jumps to 0x486ae7. 32 x86 emulation cases match original
registers, flags and stack. Fastcall wrapper preserves ECX object and one stack
filename (`ret 4`), ignoring EDX. BMP or PNG requests resolve same-basename PNG;
missing/invalid PNG invokes preserved original BMP routine through trampoline.

Object is two native-owned pointers: BITMAPINFO (0x428 allocation) and pixel
buffer. WIC converts PNG into 24bpp BGR without dither, alpha or colour transforms;
wrapper builds native positive-height bottom-up BI_RGB DIB with aligned pitch.
Buffers use native allocator 0x597880/free 0x5979b0 so original destructor and
GDI helper remain compatible. Both new allocations must succeed before replacing
old object buffers; failure preserves them. Unchanged native BMP helper draws
at 1:1 origin with StretchDIBits/SRCCOPY. No temporary BMP file is generated.

Native engine imports jpeg.dll before image use. Compatibility jpeg.dll imports
png_assets.dll so the general hook is installed during normal DLL loading;
its only JPEG export (same decorated name and ordinal 1) forwards directly to
the preserved `jpeg_native.dll` function. All original JPEG decode behavior is
retained. General loader installs only hash-gated code on process attach; actual
PNG decoding/COM/GDI do not run inside DllMain. Self-contained SHA-256 validates
the main executable without invoking an external crypto provider under the
loader lock. Formal/development launcher pin all three DLL identities before
starting the child. This retains the requested launcher architecture and lets
original fallback/mixed entries access the PNG-converted assets as well.

## Validation and limits

- 770 source/PNG RGB pixel comparisons are exact (dimensions and colour keys).
- Actual compiled x86 WIC loader produced exact native bottom-up DIBs and exact
  GDI drawn RGB for all 770 cases, from small portraits to 1920x1440 mixed UI.
- Repeated load, allocation failures, old-buffer preservation, null/missing/
  corrupt inputs, BMP fallback and fastcall stack behavior passed. Buffer balance
  returns to zero after each case.
- SHA-256 known vectors and all four actual engine files passed; production
  module refused an unknown test executable.
- JPEG forwarder resolves to the same actual native function; offline proxy
  loads test PNG dependency correctly. No JPEG reimplementation.
- PE imports/export/ordinal checked; package and all runtime module/engine hashes
  passed; all formal payload hashes passed; whole active BMP inventory is zero.
- Save/config contents preserved; immutable originals/backup hashes preserved.

Actual DirectDraw lifecycle and newly generalized map, Portmanteau, battle border,
portrait/cursor resource, native UI and multiplayer paths remain pending user
runtime testing. Original 190-page acceptance does not establish these new
paths. Existing 60-frame/gameplay-time/native-HD gates remain open.

## Backup and rollback

Checkpoint before-general-png has full `official.json`, `game.json`, `wide.json`,
`mixed.json` mapping to verified hash objects, control-file snapshots and stale
staging inventory. `restore_runtime.py RUNTIME NEW_DIRECTORY` reconstructs one
previous runtime without overwriting current state. In-place selective rollback:

```powershell
python modernization/releases/png-assets/rollback.py
```

Close all game copies first. Script validates current loader/PNG/launcher hashes,
restores previous JPEG/images and developer baseline/package controls, removes
only migrated/new image support files, and keeps current Save/config. Formal
rollback returns to user-accepted 190-page PNG edition with 50 original BMPs.
Latest installation, conversion, offline/static tests and removal/source evidence
are under modernization/releases/png-assets/. No next optimization until user
reports gameplay feedback on these new paths.
