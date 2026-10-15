# Static analysis and incremental source recovery

## Preparation decision — 2026-09-27

The user approved tool deployment and reusable agent/Skill preparation. Another
session is working on the game, so freezing or promoting a new baseline is
deferred. This preparation neither changes the accepted HD60 baseline nor proves
any game function recovered. Static inspection copies identify an analysis input;
they are not automatically accepted development baselines.

Use persistent Ghidra databases to recover names, types, cross references and
function boundaries, and combine them with version-specific runtime evidence.
Recover modules incrementally. Decompiled C is pseudocode, not automatically
compilable source or evidence of compatible behavior.

## Installed toolchain

Portable installation: `D:/Tools/magic-mayhem-re/`.

| Component | Version / location |
| --- | --- |
| Ghidra | 12.1.4, `ghidra_12.1.4_PUBLIC/` |
| Java | Temurin JDK 21.0.12.1+1, `jdk-21.0.12.1+1/` |
| Deployment provenance | `toolchain.json` |
| Ghidra projects and exports | `projects/` outside the source repository |
| Existing lightweight inspection | `inspect_pe.py`, `inspect_flow.py`, `hd_disasm.py` |
| Reusable Codex Skill | `C:/Users/DEVELOPER/.codex/skills/magic-mayhem-static-analysis/SKILL.md` |

Ghidra came from the official NSA GitHub release. Download SHA-256 was verified
against its release page:
`ddac49f903da9d5bac833e5cc79395098b9c33cfd3279be5f31bd00387d2d4db`.
JDK came from the official Adoptium release, verified against its API checksum:
`f9d6e191ab098c0d416e7d588a24420a8621cd2f4720dab2459b8b7b2d2d8b4e`.
Downloads and source metadata remain under `downloads/`. No system Java install
or persistent PATH modification was needed. Existing Python has pefile 2024.8.26
and capstone 5.0.7; the repository requirements request capstone 5.0.9. This
preparation did not change that shared environment; Ghidra does not depend on it.

## Use

Open the GUI when interactive naming or structure work is needed:

```powershell
& './modernization/tools/ghidra/Open-Ghidra.ps1'
```

For a new import, specify an independently established input hash and a fresh
project name. Example template (replace both placeholders):

```powershell
& './modernization/tools/ghidra/Invoke-StaticAnalysis.ps1' `
  -InputFile 'D:/stable-copy/engine.exe' `
  -ExpectedSha256 '<64 hexadecimal characters>' `
  -ProjectName '<new-version-name>' `
  -AnalysisTimeoutSeconds 180 -MaxFunctions 100
```

The wrapper checks SHA-256 before copying, verifies source and copy after copying,
and imports only that copy. Each run gets a new database and export folder. It
refuses existing outputs. Never pass a freshly computed hash as a substitute for
checking an expected baseline identity when preparing patches.

Paths passed to Ghidra's batch files must avoid cmd.exe metacharacters, especially
the `&` in this project's name. The wrapper stages its Java script outside the
project and changes its working directory for launch. It uses process-local Java
environment settings, restores them afterwards, and caps analysis to two CPUs.
It performs static import only; it does not launch the analyzed executable.

Export includes:

- `functions.tsv`: entry addresses, names and individual decompilation status.
- `calls.tsv`: resolved direct relationships; unresolved indirect calls can be absent.
- `pseudocode/*.c`: provisional C, with individual failure messages where needed.
- `export-complete.json`: total/exported function counts, failures and analysis timeout.
- `provenance.json`: exact input identity, toolchain, limits and source unchanged check.
- Ghidra and script logs. A completion marker means the exporter finished, not
  that analysis was exhaustive. Default exports are limited to 100 functions.

The wrapper creates new imports only. To continue a named database, open its `.gpr`
in the GUI. Keep one writer per database; close the GUI before headless access.
Back up databases before bulk changes. Preserve version tracking rather than
refreshing an old project with a different binary.

## Evidence rules

Distinguish launcher, disk engine and runtime hooks. The wrapper can inject or
patch code that is absent from the engine on disk. Track corresponding wrapper
source/manifests when reconstructing actual behavior.

Useful findings should include engine SHA-256, preferred image base, RVA/VA,
calling convention, byte signature, structure fields, supporting evidence and
confidence. Runtime addresses also require the load base. Function matches across
versions are provisional until code, references and relevant layouts agree.

The existing `reverse-engineering.md` contains original community-build addresses;
they must not silently become HD60 address maps. Address patches still require
the current accepted manifest, backups, reversible changes and known versions.

Keep bulk databases, executable copies and generated pseudocode outside Git.
Record verified conclusions and compact function/type maps in `modernization/docs/`.
Use `windows-game-background-debug` for runtime confirmation under its existing
hash and process ownership gates.

## Verification

Compiled `tools/ghidra/smoke.c` using the installed MSVC x86 compiler with no CRT,
then statically imported it. The test executable was never executed. Successful
project: `D:/Tools/magic-mayhem-re/projects/smoke-20260927-v2.gpr`.
Two functions exported, zero failures, no analysis timeout. `re_probe` recovered
the conditional `value > 10`, multiplication by three, and addition of seven;
the entry function's call relationship was retained. Source SHA-256 stayed
unchanged. No game binary, save, configuration or baseline manifest was modified.
Bad-hash imports and attempts to overwrite an existing project were rejected.
The global Skill passed the skill-creator validator using an isolated validation
venv under the tool directory; shared Python packages were not modified.

## Next work after concurrent development settles

- Confirm the accepted launcher/engine pair and explicitly capture the next
  immutable development baseline when requested.
- Import that exact engine into its own database; add runtime hook sources to
  the analysis context, without treating the launcher as the engine.
- Start with native unit hit testing, simulation/render boundaries or spell
  input dispatch according to the user's priority.
- Recover named functions and types with evidence, then consider bounded,
  independently tested compilable replacement modules.
