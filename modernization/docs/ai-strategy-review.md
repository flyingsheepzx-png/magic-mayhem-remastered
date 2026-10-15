# Native AI strategy review — 2026-10-01

## Destination marker correction, response-v2 — 2026-10-02

User reported improved responsiveness but stale ground destinations when attack
interrupts movement. Installed command-response-v2 from exact installed v1.
The rapid task commit skipped native50aa30's movement-effect cleanup: unit6e8
contains destination effect, queued task-tree8f9 nodes with kind2/offset40 also
own movement effects. Native5120c0 creates effect43 at current goal only for
Task2/NextTask2; it returns when6e8 already exists. Updating task/route without
removing this effect leaves the old destination visible.

`commit_redirect_task` now deletes6e8 through native4943f0, clears its ownership,
walks the native task list deleting only kind2 movement effects, then invokes
native5120c0 for selected units after final task/handler installation. Attack
Task3/NextTask0 does not recreate the movement marker; Task2 recreates the final
destination marker. Nonmovement queued effects remain intact. Cleanup runs only
after successful physical redirection; failure retains marker/native pending
command. The movement/occupancy transaction and symmetric player/AI eligibility
remain unchanged. Owner-based visibility is still native UI behavior.

43 compiled response checks plus37 previous path regressions pass. Five added
checks cover attack/move × selected/unselected effect cleanup, unrelated queued
effect preservation and failed-redirect marker preservation. Effect destructor
and marker renderer are explicit doubles in these offline lifecycle fixtures;
actual in-game disappearance/recreation is pending user save18 acceptance.
No gameplay launched. Latest resource101 source is
`build/remastered-1.1-command-response-v2/`; modules102/103/wrapper/assets/saves
retained. Install/rollback tool `tools/install_11_command_marker.py`, rollback
with game closed restores v1 from `backups/remastered-1.1-command-response-v2/`.

## Installed symmetric command responsiveness — 2026-10-02

User requested implementation after the save18 investigation and explicitly
required player/AI symmetry. Installed `build/remastered-1.1-command-response-v1/`
resource101 into formal1.1, frozen package and continuing candidate. This is the
current resource101 source chain, based on long-route-v2; retain its save17 search,
dynamic-fire detour, corridor/local route and all previous fixes. Resources102/103,
wrapper, assets, settings and saves are unchanged, including AI300/danger16-128.

`runtime/hd11/command_response.inc` applies the same eligibility checks to every
army in single-player. There is no owner, selection or command-caller privilege.
Ordinary width-one ground walkers with live units, movement action2/618=1 and
without native special/animation flags are eligible. Explicit attack intent
requests through50ad10, including autonomous native retargets, now run an adapter
after the original50aa30 request (signature-gated callsite50aef2). Ground movement
already uses the redirect hook50fcec; pursuit-task3→move2 now temporarily presents
the ordinary walking state to its planner and commits task2/handler510010 only
if physical redirection succeeds. Failure retains the pending native command.

Attack redirection applies only to native melee-pursuit units (type34=0);
ranged branch, flying targets and unsupported height changes retain native
behavior for both sides. Select the nearest currently free neighboring approach
cell around the enemy, run bounded local/corridor/native planning, then reuse
the existing validated redirect transaction. The enemy's own occupied cell is
not a destination. Attack planning skips the full-map long-route fallback to
bound extra work; native pursuit still handles long/unsuccessful approaches.
On success retain target64c and commit task3/handler50afa0. Task callbacks resume
at the normal movement boundary; they are not invoked halfway through movement.

The reused transaction validates the new edge and swept footprint, backs up unit
and touched cells, obtains a native new-segment reservation, releases the old
reservation only after success, retains current world XYZ and uses the existing
interpolator to continue toward the new endpoint. No general618 guard removal,
speed boost or forced segment completion. If no safe route/new edge is established,
the attack adapter restores the old route goal/restart/task and keeps native
pending attack. Same-first-edge cases still use native boundary processing;
not all units necessarily change visibly in the same frame.

Checks:38 new compiled x86 adapter/ABI/role-parity/rejection/rollback checks plus
37 prior dynamic-wait/local/corridor regressions. New tests use actual captured
terrain/native validators; redirect-start/action/release helpers are explicit
doubles for transaction fixtures, and adapter plumbing also has an explicit
redirect double. These are not live occupancy/animation/combat acceptance.
Actual response-time improvement, melee approach choice, dense-group CPU cost,
animation and both armies' gameplay remain pending user save18 testing.
No gameplay acceptance run launched after this installation under the current
user-testing checkpoint. Build SHA, bounds and exact test limitations are in
`command-verification.json`/`verification.json` within the build.

Install/rollback: `C:/Python314/python.exe modernization/tools/install_11_command_response.py rollback`
with game closed. Hash-gated backups:
`modernization/backups/remastered-1.1-command-response-v1/rollback.json`.
Reject changed launcher/manifests or unknown engine; rollback newest iteration
before attempting earlier save17/options/AI rollback.

## Save18 player group-command latency review — 2026-10-02

User explicitly requested reproduction and investigation of moving units
switching to an enemy target apparently one per frame. No player runtime patch
was installed for this review. Used isolated formal1.1 copies, latest candidate
launcher with identical embedded resources, private mouse input and read-only
unit-pool sampling. Engine SHA remains
`42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`.
Installed formal launcher SHA:
`e5f7fb50df2fe1d936219ac563364674c35ba2b728dee65974ccb2ab464fabf4`;
diagnostic candidate SHA:
`2ddb84a2c7658d5c1686c328376e155a43b87637e37f0adbfabae1445aab62dc`.
Save18 SHA `0ae6a42ed5b64a72ac7569d4d522f7fc727402c72c52d2455040a59913ebf24d`.

Box selection confirmed seven units2/16/19/21/23/24/26, ArmyNum1; clicked
enemy8, ArmyNum0. At observed engine counter11960 all seven target64c fields
already equalled8. Units21/23 were already task3, five walkers retained task2
with NextTask3. Task3 activation delays from that observation:

| Unit | Delay(ms) | Engine counter |
|---|---:|---:|
|21,23|0|11960|
|24|270.6|11965|
|26|469.0|11969|
|2|525.8|11970|
|19|599.4|11972|
|16|863.9|11976|

This disproves a universal one-unit-per-update transition ceiling: two units
activate in the same observed counter. Polling is not an atomic instruction
trace; simultaneous target writes are observed in one pool snapshot, not proved
to occur at an identical CPU instant. Task3 is attack-target/pursuit intent;
Action2 remains movement until approaching melee range. Do not equate task3
activation with an actual weapon strike.

Second run switched the same group from attack pursuit to a ground destination.
New goals/NextTask2 were observed together at counter11990; two units immediately
activated task2, two more at11992, others at11994/11995/12007. Maximum observed
delay924.2ms. The staggered response therefore affects ordinary movement changes
as well as attack intent; it is not specific to enemy AI decision selection.
Measurements belong to these diagnostic runs, not a guaranteed production FPS
or fixed response time. Early exploratory `initial`/`immediate` runs did not
establish enemy picking and are excluded from the conclusion.

Native preferred-VA evidence (base400000, matching disassembly/Ghidra):

- `4fdad0` right-command branch loops selected units through `52a710`, appending
  command7/target IDs through `537bd0`; no per-unit frame yield appears in that
  branch. `537bd0` copies a message to its batch buffer, advances size/count and
  returns; buffer overflow is a separate error branch, not a one-command quota.
- `50ad10` accepts attack intent, writes target64c at50ae57 and requests task3
  through50aa30 at50aef2. Rejects/dead/special/animation guards remain relevant.
- `50aa30` at50aa5f checks unit618; when nonzero,50aa67 writes NextTask5f0 and
  returns, leaving task5ec and handler5f4 intact. It is a general state-request
  guard, not an AI300-budget check or a global once-per-frame counter.
- `50fae0` also queues a movement change while618 is nonzero, writing new goal,
  b6f restart marker and NextTask2. Cancellation50ab30 also requests task1 via
  the same guarded state function; animation50f590 has its own completion
  handling. Not every spell/special task was runtime tested.
- `5104b0` advances the current movement according to b63/b67/b6b and b3f
  progress; after progress exceeds191 it calls512460, then consumes NextTask
  (normal branch510ba1 onward). `512460` clears618 at512546, performs native
  destination occupancy/position settlement and advances route cursor. Native
  dump52a480 explicitly labels5ec/5f0/5fc as Task/NextTask/Action and174 ArmyNum;
  a8 is Type, not owner. Differing remaining segment progress explains differing
  switch times. Merely clearing618 would bypass necessary movement settlement.

Broader scheduling remains layered: native path-search continuation is bounded
(existing600/601 per-request modernization), NOTIONAL AI has installed300
allowance, and danger refresh has installed16-unit/128-cell caps. These are
independent from this movement guard. This review does not claim every engine
subsystem has been audited or that no other delayed work exists.

Recommended next iteration: improve ordinary player-command responsiveness at
the movement boundary, investigating preparation of the pending attack/move
before completion and safe shortening/interruption of a segment. Retain terrain,
occupancy reservations, position continuity, animation, script/special-task and
multiplayer guards. Do not globally remove the618 check or raise AI budgets as
a presumed fix. No responsiveness patch prepared/installed yet.

Repro tool `tools/probe_save18_group_command.py`; offline summary/invariant check
`tools/analyze_save18_group_command.py`. Accepted investigation evidence:
`logs/remastered-ui/save18-command-attack/` and `save18-command-move-followup/`
(samples/events/selected/identity/group-summary). Static exports/field-reference
inventory outside Git:
`D:/Tools/magic-mayhem-re/projects/group-command-20261002-export/`.
Existing Ghidra project was opened read-only with noanalysis; no baseline promoted.

## Scope and identity

Read-only review of formal1.1 `runtime/AI` and `runtime/CFG`; no runtime,
save, configuration or AI data modifications, and no gameplay launched.
Static engine SHA256:
`42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`.
Image base/preferred VAs below: `0x400000`. Disk pseudocode does not include hooks.
Ghidra project and selected exports are outside Git at
`D:/Tools/magic-mayhem-re/projects/ai-review-20261001`.

## What the files contain

* `Brain.dat`: serialized statistical decision models, not readable behavior
  scripts. The examined layout has seven keyed records, IDs 6,8,9,11,12,13,14;
  respective feature dimensions 72,73,71,71,71,73,73. Each has three components,
  coefficients summing approximately to one, per-feature records of twelve
  32-bit values, a scalar and a square floating-point matrix. Examined matrices
  are symmetric. Do not describe these as neural-network layers; component and
  matrix semantics remain provisional.
* `EXPERIEN.DAT`: variable-length experience records: 32-bit key, 32-bit feature
  count, that many 32-bit integer feature values, then 32-bit class count and
  32-bit outcome class label. Earlier two-float interpretation was incorrect;
  serialization, label setter and training use confirm integer fields.
* `Train.wbt`: legacy loop launching `Debug/Chaos /win/train`, copying logs.
* `BugSearch.wbt`: analogous endless legacy bug-search runner with
  `/win/bugsearch=7500`. Neither WBT is the live tactical policy. Do not execute
  these as an optimization or reuse them with the formal launcher without a
  separate controlled training design.

`inspect_ai_data_11.py` provides a read-only structural decoder; it checks bounds,
finite values, matching dimensions and complete file consumption. Both observed
data files decoded to exact EOF. Each read creates its own immutable byte
snapshot; the pair is not an atomic snapshot of live gameplay. These are mutable
data, not fixed release assets. Controlled comparisons must freeze/restore both
files together and record their hashes.

## Confirmed code evidence

| Preferred VA | Evidence |
| --- | --- |
| 0x479a10 | Brain loader: repeated key + model decoding until EOF |
| 0x476240 | Model header and component vector decoding |
| 0x475e60 | Component decoding, feature records and square matrix |
| 0x475cf0 | Twelve 4-byte values per feature record |
| 0x4764d0 | Experience serializer: key/dimension/integer vector/u32 class count/u32 label |
| 0x4766b0 | Decision scoring uses a quadratic form over features/matrix, exponential transformation, then normalized probabilities |
| 0x471af0 | Session/load initialization calls Brain loader |
| 0x477060 | Buffered experience write/flush path |
| 0x477380 | Experience rewrite path using TMPEXP.DAT |
| 0x407f60 | ai.cfg threshold/scale parser via GetPrivateProfileStringA and two-float parsing |
| 0x4e4270 | chaos.cfg global options parser, including AI settings |
| 0x46b5be | Normal update passes AI_timelimit/2 to each of two scheduler objects |
| 0x4075b0,0x407600 | Budget initialization/query: notional work counts or calibrated RDTSC time |

Disassembly confirmed serialization widths, matrix loop dimensions and budget
splitting. Decompiled calling conventions/register parameters are imperfect;
do not compile the pseudocode or patch these addresses without further checks.

## Configuration surface

`CFG/ai.cfg` provides threshold and scale pairs for own/enemy group features
(`OG_`/`EG_`), army/wizard state (`WA_`), and spell context (`SC_`). Inputs include
health, creature counts, melee/ranged strength, resistance, mana, intelligence,
bravery, wizard danger, spell cost/range, health change and success chance.
These are feature parameters, not direct rules such as “heal below 20 HP”.
Empty values skip the assignment and retain the existing value. Do not fill them
blindly. Suspicious colon-suffixed empty keys do not establish a gameplay bug.

Current `CFG/chaos.cfg`:

| Setting | Value | Intended role from config and parser |
| --- | --- | --- |
| AI_timesystem | NOTIONAL_TIME | Work-count budget, not wall-clock milliseconds |
| AI_timelimit | 30 | Per-update planner allowance; normal path splits 15/15 |
| AI_interrupt1 | 0.1 | Interrupt current action when a substantially better action appears |
| AI_interrupt2 | 0.1 | Disaster/action interrupt control |
| AI_div_g_limit | 10 | Group-division master-list limit |
| AI_div_q_limit | 5 | Group-division priority-queue limit |
| AI_danger_excess_limit | 100 | Danger excess for abandoning an action, percent of local safety |

Creature role categories are in `CFG/creature.cfg` (SCOUT/ATTACKER/DEFENDER).
AI planner budget is separate from movement pathfinding. Increasing it does not
directly correct the protagonist's detours. REAL_TIME uses legacy calibrated
RDTSC code; changing modes requires timing validation on the current machine.

## Optimization candidates, ordered by evidence and risk

1. **Instrument decisions before tuning.** Recover ID names and feature mapping;
   record selected action, alternatives, score, interrupt reason, work consumed,
   decision latency and unsuccessful execution. This establishes whether poor
   behavior comes from scheduling, scoring, switching, or execution/pathfinding.
2. **Planner scheduling.** Measure exhausted budgets and urgent response delay.
   Compare one increased notional allowance or urgency-aware scheduling, keeping
   fixed logic timing. A blanket increase may waste CPU without improving play.
3. **Action stability and emergencies.** Measure repeated target/command changes,
   delayed retreat and interrupted casts. Tune only the relevant threshold, or
   add hysteresis after confirming current switching code. Existing interrupts
   already exist; do not claim the native AI has no stability logic.
4. **Spell utility and role decisions.** Evaluate wasted healing, ineffective
   attacks against resistance, mana reserves and scout/defender assignment.
   Relevant feature inputs exist, but no defect in these behaviors is established
   by this static review. Add a tactical rule only after replay evidence.
5. **Statistical model/data quality.** Inspect coverage by action and situation,
   label/outcome meaning, update rules and forgetting before retraining. The
   examined experience distribution is uneven, but action frequencies need not
   be equal. Changing dimensions/scales with the old Brain may invalidate its
   interpretation. Preserve the original learned data and use separate AI profiles.

Recommended first implementation is optional decision telemetry, followed by
one evidence-driven behavioral change. Evaluate identical initial save/data/RNG
conditions as far as available, decision latency and tactical outcomes, CPU cost,
and save compatibility. Keep AI difficulty opt-in; preserve campaign scripting
and multiplayer behavior until separately tested. This review does not establish
better AI or authorize a release change.

## Authorized telemetry implementation — 2026-10-01

Installed optional resource103 `ai_diagnostics.dll`, SHA256
`4e63e0d8452f2bfbcfef52e1838e17575d2bf7cddf37c4a1213dbe6f2ac95c17`.
Ordinary launch clears inherited diagnostic environment and does not load it.
Launch formal `MagicMayhem-Remastered.exe --ai-trace` to snapshot original
Brain/experience and relevant configs before engine startup into
`runtime/AI/diagnostics/session-<pid>-<tick>/`; trace.bin uses version1,
80-byte header and 400-byte events, capped at32MB. Decode using
`tools/read_ai_diagnostics_11.py <trace.bin>`. No scheduling, strategy, RNG or
learned data is changed by the observer. Multiplayer is excluded.

Twelve signature-checked observation points cover scheduler, raw model vectors,
candidate evaluation, budget yields, commits, execution returns and retirement.
43 offline checks pass, including a real x86 callback fixture preserving GPRs,
flags/DF, complete x87 state, XMM/MXCSR and LastError. No gameplay launched;
runtime acceptance is pending user diagnostic gameplay. Candidate eligibility
is not selection; zero evaluator/execute returns do not establish failed spells;
retirement flags do not establish exact reasons. Numeric IDs/features remain
partially mapped and measured duration includes observer overhead.

Build/install/rollback: `tools/build_11_ai_diagnostics.py`. Backup:
`backups/remastered-1.1-ai-diagnostics`. Subsequent UI builds must retain
resource103 and diagnostic launcher behavior.

## Bounded optimization review (current priority)

The user redirected work from exhaustive multi-week recovery to an at-most
one-hour practical optimization review. Full recovery remains incomplete and
its evidence is retained, but is no longer a prerequisite for the first narrow
performance iteration. No AI behavior/config/runtime modification was made in
this review; no player process was launched or touched.

Evidence: `ai-budget-opportunity-verification.json`, reproducible with
`tools/analyze_ai_budget_opportunity.py`, using the hash identified above.
Ten nonnegative budget values were executed through the real normal-update
caller slice (scheduler call explicitly doubled), real scheduler split slices,
and whole NOTIONAL budget initializer/query without doubles. Current total30
becomes15 for each scheduler, then planning7 and execution8. Total120 becomes
60 each, planning30 and execution30. NOTIONAL work counts do not expand with
CPU speed. These are operation allowances, not unit counts or milliseconds;
one evaluator can consume multiple work operations.

Historical test18/test7 native traces were re-read with hash-preservation checks,
pairing scheduler entry/exit and per-call candidate budget yields. Main context
690600 normal calls yield321/339 (94.69%) and521/575 (90.61%). Other context644550
yields0/339 and101/575 (17.57%). All adjacent scheduler-local tick deltas are1:
the observed delay is not a scheduler skipping its own updates. In all-call
samples, main scheduler P95 is217/267us including observer overhead; peaks are
6051/11159us. The latter include startup samples and are not grounds for
unlimited budgets. Longest yield streak39/68 calls is across scheduler work,
not proof that one group/unit waited that long. There is no increased-budget
gameplay comparison, no measured speedup, and no causal proof for every idle unit.

| Priority | Candidate | Expected benefit / evidence | Risk | Estimated implementation effort |
| --- | --- | --- | --- | --- |
| 1 | Keep NOTIONAL_TIME, total30 -> 120 | 4.29x planning allowance and3.75x execution allowance; high observed continuation pressure with low typical CPU time | Low relative to policy rewrites; changed decision timing/RNG ordering/difficulty and CPU spikes need user testing | 1–2h including a single-player guard, backup/rollback and offline installation checks |
| 2 | Allocate more of fixed total to context690600, or transfer unused allowance | Main/other pressure is strongly asymmetric in the two fixtures; avoid spending equal allowances everywhere | Medium: native scheduling boundaries, accounting and fairness; no unchanged-behavior guarantee | 2–4h; defer until first-iteration feedback |
| 3 | Increase perception/danger-map refresh throughput separately | Native producer is capped at4 processed units and32 publication cells per invocation; may reduce stale threat estimates | Medium: separate from AI_timelimit, increased CPU and altered tactical decisions; live stale-data evidence absent | 2–4h for focused producer/caller validation and one reversible iteration |
| 4 | Small watchdog for proven idle command/target stalls | Potentially quick recovery from a measured failure while retaining native planner | Medium/high: distinguish intentional wait/casting/scripts from stuck work; no specific stall established yet | 3–6h after a reproducible idle fixture |
| Defer | Replace whole AI, retrain Brain, retune spell/interrupt coefficients, legacy REAL_TIME | Benefits unproven for the requested latency issue | High compatibility/behavior cost; existing interrupt protection and learning already exist | Outside this first iteration |

First iteration should use the existing configuration mechanism, not replace
the planner or globally accelerate simulation. Start at120 rather than jump
to unlimited work. Preserve Brain/experience,30Hz logic, spell cooldowns,
animation timing, all HD modules/assets and multiplayer's original budget.
A global config change alone could affect multiplayer: an installation design
must either explicitly limit it to single-player launch or provide a guarded
single-player override. Keep the existing original profile and rollback.

Acceptance should compare the same user idle scenario with30 and120, log budget
yield ratio and actual time-to-command/visible response, inspect target switching
and frame-time spikes, and confirm read/save/exit behavior. Commit counts and
lower yields alone are not proof of better tactics. Under the project workflow,
install one change after offline checks and leave gameplay acceptance to the
user; do not bundle perception, watchdog or policy changes before feedback.

## Retained comprehensive recovery progress

### Installed danger refresh iteration:16 units /128 nodes

User authorized perception refresh acceleration, then questioned provisional320
nodes. Accepted final fourfold limits16 units/128 finalized nodes. The earlier
40/320 build was never installed and was superseded in its development directory.
Nodes are world-coordinate/adjacency records with per-owner seven-byte evaluation
channels, not screen pixels; camera/output resolution do not set this allowance.
This change does not enlarge range or alter contribution/effect formulas.

Latest build `modernization/build/remastered-1.1-danger-refresh/` starts from the
exact installed budget300 module set. Current module102 SHA256:
`65329dfedab41828bdc17090841dd28a88dc7dad5b15211304ebdb4c1106410b`.
Preferred-VA signature-gated detours41dbfd and41d3fc implement single-player
processed-unit16/finalized-cell128 caps; nonzero multiplayer6e1f0c retains4/32.
All old source modules except the installer chain are copied byte-for-byte;
budget300 remains included, embedded101/103 unchanged, assets/config/saves/learning
data unchanged. Native frame cadence and danger calculation formulas unchanged.

Necessary continuation correction at41d486: after a completed owner cycle uses
all8 rotation attempts, native code returns with an exhausted unit cursor and
cleared scratch. Faster batches exposed the next invocation publishing that
owner's empty scratch again (two-owner0/7 fixture,relations0/filters0). On the
single-player exhausted boundary only, set manager12098 restart marker1. Next
native41d270 initialization resets owner=-1/cellcursor/accumulator and clears only
scratch, leaving published per-owner maps intact; scan starts a new cycle. Do not
increase rotation limit or otherwise alter multiplayer. This fix is required for
the accelerated continuation, not a separate tactical policy optimization.

Offline verification:72 compiled comparison/register/flags/stack cases,18 compiled
rotation-marker cases,60 publication fixtures (boundaries through257 nodes,
explicit finalizer double for large maps, actual69/70/91 effects through65 nodes),
144 whole native producer fixtures (only CRT allocation/free doubled;5/9/17units,
graph/status/type/owner/effect domains) and32 asymmetric two-active-owner fixtures.
Independent expectations check selected units/contributions/allseven channels,
published values/other-owner isolation/scratch clear and repeated cycles; compiled
surface lifetime/registry tests also pass. Test observations now identify actual
publication via542be0, distinguishing the shared41d476 skip/rotation site.

Installed formal/frozen/candidate with known engine/launcher/manifest hash checks,
backup and rollback. No gameplay launched; actual frame-time/response improvement
and tactical acceptance pending user testing, not inferred from offline throughput.

Rollback from project root:
`C:/Python314/python.exe modernization/tools/build_11_danger_refresh.py rollback`.
Backup: `modernization/backups/remastered-1.1-danger-refresh/rollback.json`.
This restores the immediately preceding budget300 version. Roll back iterations
in reverse order; earlier budget300 rollback intentionally refuses changed files.

### Installed first budget iteration:300

User explicitly selected10x original budget, total300 instead of proposed120.
Installed formal, frozen package and continuing candidate using
`tools/build_11_ai_budget.py`; based on exact latest portrait-ready module102,
not earlier minimap-only sources. New module102 SHA256:
`d67a1bf249447e49c40d1f2b74d287fea160d9864e7f8bd00b00ec2a9bf8fd7b`.

Two signature-checked normal-update load detours at preferred VAs46b5be/46b5d3
override EAX to300 iff multiplayer global6e1f0c==0 and time-system6e1f64==0
(NOTIONAL). Original configuration global5e15f4 is not mutated: CFG still says30,
but these single-player normal-update calls use300. Each scheduler receives150,
then planning75/execution75. Multiplayer,REAL_TIME/unknown modes and the separate
unlimited startup path retain native behavior. No logic-rate, cooldown, scoring,
learning data, save or asset change. Install fails on signature/hash mismatch.

`modernization/build/remastered-1.1-ai-budget300/verification.json` records216
compiled detour cases checking flags, non-EAX registers, stack and conditional
exclusions;27 integrations execute real disk caller/split slices with scheduler
entry explicitly doubled. Existing native surface lifecycle/registry tests pass.
All previous source modules except the installer chain are retained byte-for-byte;
embedded101/103 remain byte-identical. Installation verifies all three launcher
and manifest hash pairs and module102, and is refused while a game is running.
No game was launched. Runtime behavior/speedup acceptance awaits user feedback.

Rollback (from project root):
`C:/Python314/python.exe modernization/tools/build_11_ai_budget.py rollback`.
Backup/provenance: `modernization/backups/remastered-1.1-ai-budget300/rollback.json`.
Do not perform another AI optimization before gameplay feedback.

User authorized isolated diagnostics and tooling without repeated confirmation.
Current verified evidence: `ai-model-semantics.md`, `ai-config-dictionary.json`,
`ai-feature-vectors.json` and `ai-action-registry.json`.
130 configuration bindings recovered (58 nonempty assignments). Six unused
config keys differ by spelling/colon and are empty; this establishes mismatch,
not a behavior defect. No config change made; empty values retain defaults.

IDs6–14 use the same ordered67-selector base feature vector. Native40ea00
indexes configuration by abs(selector), confirming dictionary positions.
Action-specific suffix values are not yet fully named. Existing Brain dimensions
imply4–6 suffix values for its seven models.

Static registry5d8474 contains53 prototypes, IDs5–59 except7/10. All constructors,
vtables and seven method entries recovered from hash-verified disk code. It does
not register7/10, consistent with their absence from Brain; no defect inferred.
Internal/default action classes and53 registered families still need semantic
recovery before claiming complete analysis. Method labels are provisional.

Direct-call exports outside Git: functions-deep299 visited, functions-extra259
visited; bounded queues empty. Counts overlap and omit indirect targets unless
seeded explicitly. Native model kernel verified in28 cases, zero observed error.
Training and overall AI recovery remain incomplete.

Native tactical names now recovered through config/global -> wizard profile ->
unit field -> action score/eligibility evidence:6 AggressiveAttack,
7 CautiousAttack (unregistered),8 OccupyPowerPoint,9 CollectMana,
10 EvadeDetection (unregistered),11 Scout,12 Retreat,13 CollectFood,
14 ProtectWizard. See `ai-tactical-actions.json` for exact bindings and current
configuration. Unit constructor defaults are100, but actual wizard profiles
can override them; installed global personality is100/0/120/120/0/90/100/90/90.
This replaces anonymous tactical IDs; target/evaluator internals remain open.
Native trainer quantile/inverse helpers verified in23 further offline cases.
Producer math and experience labels are recorded in `ai-model-semantics.md`.

## Isolated runtime evidence

Authorized test18 observation completed with latest1.1 launcher/resource103 in
a hash-verified fresh full copy. Private background input, no unit commands,
read-only process sampling. Final trace after process exit contains680 scheduler
begin/end pairs,44 commits,137 model pairs,991 execution returns and321 budget
yields. IDs0/6/11/12/14/59 committed. Native default ID0 vtable5c53c0 confirmed.
All137 recorded probability vectors match recovered inference using the session
Brain snapshot with zero observed error. This verifies model observations and
inference in this fixture, not all AI behavior or improved strategy.
Evidence `logs/ai-review/isolated-test18-v1/`; restoration has zero cleanup errors,
all source mutable hashes unchanged. `ai-trace-model-verification.json` records
model comparison. Runtime telemetry acceptance for this fixture now passes;
ordinary/no-observer and other campaign fixtures remain outside this run.

Second isolated test7-legacy fixture records1152 scheduler pairs,91 commits,
318 model pairs and1524 execution returns. Commits additionally cover
OccupyPowerPoint8,CollectMana9,CollectFood13,summon15 andIronSkin39.
All318 model outputs match their own session Brain snapshot exactly; source
mutable bytes unchanged, no cleanup errors. Combined two-fixture model
comparison455 cases pass. See ai-trace-test7-model-verification.json.
72 feature fusion and40 spell postprocessing native fixtures pass, with explicit
delay/RNG test doubles for the latter. Details in ai-model-semantics.md.
