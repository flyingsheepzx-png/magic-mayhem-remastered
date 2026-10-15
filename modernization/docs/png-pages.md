# PNG Grimoire page candidate — 2026-09-30

User requested investigation of changing BMP mode to PNG. A separate opt-in
candidate is installed at `D:/Games/Magic&Mayham_Remastered_1.0_PNG_Trial`.
Formal BMP release and active developer baseline are unchanged. This implements
only the 190 extra Grimoire pages; other native BMP resources are retained.
Stop at user gameplay acceptance before further format or size optimizations.

## Native boundary

Engine pinned to SHA-256
`43e122564fa126a2a6c99ae1a7a0d8cd6aa0d5178feec99ea3e2c6f54985543d`,
image base 0x400000. Call at preferred VA 0x4c532f has exact bytes
`e8 6c 7e 0c 00`, calling the BMP decoder 0x58d1a0. Original ABI is thiscall:
ECX=image and one stack filename; callee returns with ret 4. Replacement uses
fastcall with ignored EDX and one stack filename, preserving the same stack ABI.
No disk engine bytes changed. Hook is installed by a separately hash-pinned DLL
loaded after the unchanged enhancement, QoL and terrain modules. Existing call
signature is checked before any write; no hook is installed on unknown bytes.

Native BMP load at 0x58d1a0 gets surface via image+8, calls GetDC at vtable+0x44,
paints at origin with 0x486a80, then ReleaseDC at vtable+0x68. The native GDI helper
uses StretchDIBits/SRCCOPY, 1:1 image dimensions and no additional scaling.
The PNG path reproduces these calls with a top-down 24bpp BGR buffer. WIC
factory/decoder/converter produces exact BGR pixels in memory without colour
management transforms, new alpha treatment or dithering; the files have RGB only.
COM init is balanced when owned, existing apartment mode is tolerated, COM
objects/DC are released and buffers are local to each request. PNG decoding does
not run inside DllMain; DllMain only validates and installs the call patch.
No temporary BMP is generated. Missing/failed PNG returns to native BMP path;
outer engine JPEG fallback stays unchanged.

## Conversion and evidence

This is lossless file-format transcoding of existing art, not image generation
or pixel editing. No Qwen or substitute generation model invoked. For all 190
640x720 RGB pages, Pillow-decoded source/PNG pixel bytes compare exactly, so the
blue and magenta masks remain identical. Original BMP bytes: 262,666,260;
PNG bytes: 50,122,796; page-file saving: 212,543,464 bytes.

Independent x86 test harness loads only the test DLL (no game process). It calls
the actual fastcall loader, decodes all PNGs with Windows WIC, paints through
GDI into memory DIBs behind a mock surface GetDC/ReleaseDC interface, and compares
every drawn RGB pixel against the original bottom-up BMP bytes. 190/190 pass.
Null input, missing files, get/release DC failures, malformed PNG and a JPEG
masquerading as input are rejected; BMP fallback test returns a sentinel without
calling game memory. The production DLL retains exact native fallback.
This validates codec, orientation, keys and ABI; it is not game visual acceptance.
Actual DirectDraw format, page lifecycle and user interactions remain pending.

Final package: 491,767,082 bytes (491.77 MB), vs formal 704,204,965 bytes
(704.20 MB). Net saving 212,437,883 bytes, about 30.17%; added module, launcher
and documentation account for the difference from page-only savings.
5,067 payload files verified after installation. Original resource 101/102,
icon images, engine and terrain DLL compare identical. No game launched.

Source/tests: `runtime/png-pages/png_pages.cpp`, `offline_test.cpp`.
Build/conversion/pins/offline evidence: `releases/remastered-png-trial/`.
Rollback is switching back to the existing BMP release after closing the trial.
Trial Save/config are independent; preserve newly created saves before removal.
The candidate and final source changes are also stored in the existing verified
content-addressed checkpoint with a per-release restoration manifest.

## User acceptance and formal promotion — 2026-09-30

User tested the 190-page PNG candidate and reported no problems, explicitly
requested making it formal. Promoted to Magic&Mayham_Remastered_1.0, retaining
its existing saves/settings. Pre-promotion formal and actual played candidate
states are checkpointed at before-png-promotion. User play consumed/encrypted
loose CFG files as expected; promotion uses pristine hash-verified candidate
payload plus formal user state. All installed payload hashes pass and the old
190 BMPs are removed after backup. Further BMP loaders/resources remain a
separate newly authorized migration with acceptance pending user.

## General asset PNG extension — 2026-09-30

The user accepted the 190 pages and requested official promotion and remaining
BMP conversion. Formal now uses 240 PNG assets, no external BMP files; preserves
root launcher/icon and runtime subdirectory. Developer package is v38 and active
runtimes have the same PNG-aware storage. Exact new loader boundary, JPEG proxy,
770-copy tests, immutable exclusions, installed size and rollback are authoritative
in docs/png-assets.md. Newly generalized paths remain pending user testing.
