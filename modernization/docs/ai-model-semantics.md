# Native AI model semantics

Engine42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da,
image base0x400000. Kernel4766b0 and4768f7–476b10;
serialization475cf0,475e60,476240. Read-only analysis, no gameplay launched.

The twelve serialized floats per feature are threshold, step and ten lookup
values. Inference takes an integer x and computes
`k = trunc(10 * (x-threshold) / step)` using native CRT truncation59bee0.
For k<0 substitute negative component limit; for k>=10 positive limit;
otherwise take lookup[k]. Each component has its own transform and matrix.

For transformed z, compute q=z^T M z with each accumulation stored as float32.
Let qmin be the minimum across components. Weight is
`exp(-0.5*(q-qmin))`, except gaps multiplied by0.5 >=20 get zero.
Normalize by the sum. If fewer than two components have positive leading
coefficient, return uniform probability. Those coefficients gate availability,
but are not multiplied into exponent weights. Their training meaning and
matrices' covariance/precision meaning require producer-side evidence.

`tools/ai_model_codec.py` losslessly roundtrips the observed Brain snapshot and
implements inference. `tools/verify_ai_model_native.py` runs the actual kernel
and native float-to-integer routine in an isolated x86 emulator, mapping real
engine constants and model data. Seven models ×four vectors =28 cases pass
with zero observed probability error, including zero/random inputs and near
positive/negative transform boundaries. These are offline kernel cases, not
campaign acceptance or comprehensive training validation. Evidence:
`ai-model-native-verification.json`.

Action score414ff0 combines output0 and output2:
`min(cap, weight2[action]*probability2 - weight0[action]*probability0)`.
Weights live at6c48fc+12*id and6c4904+12*id. Config4e4270 writes exactly
these addresses for each tactical action's OUTCOME_FRACTIONS first/third
values. The middle fraction is not consumed by414ff0; these are direct utility
weights, separate from Brain class frequencies. Labels' metric names remain open.
Subject preference40edb0 reads unit offsets936–956 for IDs6–14, applies
`(score+1)*preference/100-1`, caps high values at0.999 and low values at-1.
5065e0 initializes each preference to100. Profile590c10 reads GENERAL keys,
592170 supplies global PERSONALITY defaults,592780 copies profile60..80 into
unit936..956. Native names/current values are in `ai-tactical-actions.json`.

Experience records end with two unsigned integers: class count and label,
not floats. All 2500 observed records have three classes, labels0/1/2.
Native serializer4764d0, setter477040 and reader477d30 agree on this layout.
Retirement428b40 labels a recorded ratio <=0.58 as0, <=1.71 as1, otherwise2.
The ratio combines action baseline fields2b/2f/33 with the current subject
metric unit922/(unit926+1); those metrics' exact names remain unresolved.

## Training producer evidence

Trainer477d30 first counts samples per action/class. Range bounds use at most
100 periodically selected records per class (stride=floor(count/100) when
count>=100), with +/-0.5 padding. Each feature stores lower bound and span.
Ten bins accumulate sample weight exp(-remaining_record_count/1000).
Class coefficients are their weighted sample totals divided by overall total.
The record counter's decrement is global in the passes, not per action/class.

Each bin becomes a standard-normal quantile of its weighted cumulative mass
plus half its own mass. Leading/trailing empty bins copy the nearest nonempty
bin's quantile. Out-of-range limit is max(1,-quantile(1/(2*min(count,100)))).
Native479f80 approximates the normal quantile, returns -5/+5 outside input
1e-6..0.999999, and stops Newton-style iteration at delta<=0.01.

The next pass transforms samples using these bins and accumulates weighted
outer products exp(-2*remaining_record_count/1000)*z*z^T. It divides the
matrix by the class weighted total. It adds0.01 to each diagonal and floors
that diagonal at1, then invokes symmetric positive-pivot inverse47a0e0.
This is a regularized second-moment inverse; ordinary centered covariance
would additionally subtract a mean, which is not established here.
An empty class gets an identity matrix. Failed inversion aborts trainer
with -5; the inverse helper reports -1 for a nonpositive pivot, -2 for an
empty matrix. Full trainer IO/recovery and data update lifecycle remain open.

`tools/verify_ai_training_math.py` executes native479f80 and47a0e0 in bounded
x86 emulation:13 quantiles,2 endpoint clamps,4 matrix identity-residual
checks and4 rejection cases pass. Evidence: `ai-training-math-verification.json`.
Full training equivalence has not been tested. Constants' widths were checked
against disassembly:5c5f64 is float1000, not an overlapping double.

Isolated test18 runtime additionally provided137 model input/output pairs,
all matching recovered inference with zero observed error against pre-start
Brain snapshot. `ai-trace-model-verification.json` records source hashes.
This has a different Brain hash from the earlier offline snapshot; comparisons
correctly use each session's own data rather than the player's current file.

Remaining: outcome metric semantics, appended action feature values,
malformed-data recovery behavior, update timing and persistence, full trainer
roundtrip and numerical behavior on actual learned data.

## Heuristic feature utility and spell postprocessing

40ea00 takes selector inECX, integer feature inEDX, stack(weight,total*,score*).
Threshold and scale at abs(selector)*4 are truncated to integers by59bee0.
Let v=(x-threshold)/(scale+abs(x-threshold)); negate v for negative selectors.
It fuses features in log-odds space rather than taking an arithmetic average:
F(q,r)=((1+q)^r-(1-q)^r)/((1+q)^r+(1-q)^r).
Old term is0 if total=0, otherwiseF(old_score,total/(total+w)); new term
F(v,w/(total+w)). Result=(old+new)/(1+old*new), with nonpositive denominator
falling back0, and total+=w. Native intermediate float stores are significant.
59bcc0's x87 argument order was verified against disassembly and fixtures.
72 actual-native cases pass: signed selectors, both sides of thresholds,
fractional config truncation, first/repeated unequal weighting.
Evidence `ai-feature-utility-verification.json`; degenerate scale/weights remain
outside these cases and are not silently repaired in the runtime.

40ec70(caster,spell,total*,score*,multiplicity) rejects delay51e530>200 with-1.
Otherwise applies selector125/current caster mana>>8 at weight total*0.1;
selector-126/delay at weight updated_total; selector-127/configured spell
cost* multiplicity at weight next_total/6. Names125..127 are respectively
SC_MANA_REMAINING,SC_MANA_DELAY,SC_SPELL_COST. Current projected caster mana,
not a second local subtraction of cost, supplies remaining-mana input.
Apply adjustment k at spell stride0x2d1+base6b13e5:
score=((k+1)*score+k-1)/((k-1)*score+k+1).
Add ((RNG&0x7fffffff)%100-50)*0.001 and clamp[-1,1]. Neutral k=1 preserves
pre-adjustment score. 40 controlled-dependency cases execute real40ec70 and
40ea00; only delay51e530 and RNG54e200 are emulator test doubles.
Evidence `ai-spell-utility-verification.json`. Spell target selection remains
separate and incompletely recovered.

## Experience/model lifecycle

476e30 allocates from100 slots of29bytes atowner+10. Status0=free,1=pending,
2=labelled. Fields relative to slot:1 action key,5 vector object,15 class count,
19 label. It copies raw features and class count from the keyed model.
When all occupied it flushes labelled slots; if still full it reuses slot0.
477020 releases a slot;477040 sets status2 andlabel;477060 serializes only
status2 then clears it. Main update46afc0 flushes when tick&0x1ff==0;
471af0 flushes the previous world before load initialization.

477380 counts experience, and if>2500 renames it toTMPEXP.DAT, writes only the
last2500 records in batches100, closes streams and removes the temporary.
Return paths distinguish open/rename/read/write/close/delete failures; this
is not an atomic replace and automatic recovery from every failure is unproved.
479d40 requests retraining if experience exists and Brain is missing, or if
experience is newer than a non-read-only Brain. A read-only Brain suppresses
the timestamp-triggered retraining path. Missing experience returnsfalse.
470950 invokes trim/train/save when stale or Brain load failed. Train failure
calls4796f0/479d30, deleting experience/Brain respectively. Normal startup
471af0 reloads Brain, while malformed matrix dimensions at4766b0 retry load,
then train/save, then delete data and clear/recreate defaults. The native loader
does not implement the strict size/finite guards of the analysis decoder.
Player files were not modified to test these destructive failure paths.

ID0 native fallback is eligible iff group+39=0; evaluates once toscore-1,
preparation returns8, execute returns1 without issuing commands, commit and
retire no-op. 20 action/utility native cases pass including this lifecycle:
`ai-action-primitives-verification.json`. ID59 likewise issues no commands,
prepares40, and prioritizes missing wizard mana while penalizing danger;
descriptive name is mana recovery/wait, not a recovered original symbol.

## Group cursors and feature producer verification

All addresses below use the documented42f2aac7 engine/image base400000.
Group objects have unit pointer+35 (nonzero for leaves), parent+39, child-vector
begin/end/capacity+29/+2d/+31, round-robin cursor+3d, eight availability bytes
at+41, eight child pointers+49 and eight subordinate iterator IDs/leaf-consumed
flags+69. 407920 reserves the first free slot, otherwise reuses the round-robin
slot and advances modulo8. It recursively reserves a cursor in the first child.
4079f0 yields unit pointers depth-first;407a80 yields leaf group pointers;
407990 yields direct children without recursive flattening. Leaf+89 must be
at least global5d854c; structural children are traversable regardless of that
cutoff. The meaning of this rank field is still pending. Exhaustion frees the
cursor availability byte. Native13 cases cover nested traversal, cutoffs,
independent cursors, exhaustion and capacity reuse:ai-group-verification.json.

40b420 consumes five stack arguments(own_group,enemy_group,budget,vector,count),
then count integer varargs selectors; it clears the existing output vector and
appends raw integer values. It does not normalize feature values here. Native
276 direct-field fixtures verify24 own selectors and22 enemy selectors across
rank filtering, empty groups and illusions. Own selectors1..58 and enemy59..112
are not symmetric complete ranges: enemy mirrors only own1..54. Own55..58
danger/illusion/wizard-health additions have no enemy mirror;113 starts WA.
Direct aggregation sums count, mana capacity and total combat contributions;
averages use integer division toward zero. Own general melee/ranged fields90a/
90e and anti-undead fields912/916 are halved per illusion before aggregation;
enemy equivalents do not apply that reduction. This is native behavior, not a
new optimization or proof that the asymmetry is desirable.

Selectors37..54 and95..112 enumerate104 spell definitions of721 bytes,
category field6b14f1+721*spell+4*category. Positive values contribute only for
wizard leaves and an available spell with reported wait<=budget.144 controlled
availability cases verify18 categories on both sides, budget0/9/10/11 and
negative/unavailable exclusions; only40a950 is stubbed for these cases. Category
field names come from the native selector/config dictionary. The actual
availability function and all remaining producer helpers still require recovery.
Evidence:ai-feature-producer-verification.json (420 cases total).

## Cure action21 target and execution conditions

Initializer446150 requires a single-leaf unassigned group withgroup+5=0,
spell41 availability and a finite reported wait. It builds a same-owner target
group through40f910 or40f9e0 depending on caster+95a; the distinction between
those group builders remains under review. Evaluator446210 skips target+7c
illusions and target+78c existing effect. Target health+e4, native maxhealth
5075f0, forecast damage+8d5 and heal quantity6b85ed control the gate:
unsigned(health-trunc(forecast/2)) < unsigned(trunc(maxhealth/2)), or
unsigned(maxhealth-health)>=unsigned(heal_quantity). This unsigned comparison
matters when forecast subtraction underflows. The SC_DHEALTH selector129 input
is min(missing_health,heal_quantity)+forecast, plus50 when+114 nonzero and+f8
zero. The exact+114 status is not named yet. Critical wizard types0/24/25/26
start at score1,total1 before health and mana postprocessing; other targets
use the current-attacker group and selectors5/12/6/7,each weight1.
Path/spell validation40ad00 must return0. Evaluator yields one valid candidate
at a time within its deadline; commit4465f0 copies candidate15a toselected15e.

Executor4466f0 ends(return0) when health0 or exactly maxhealth. Otherwise it
continues(return1), waits for delay0, invokes51d570 if integer mana(e8>>8) is
below6b85e9, or revalidates and submits spell41 through57c6e0 once. Successful
submission setsaction+162 to prevent duplicate commands; blocked/delayed calls
keep it unset. Command payload contains native caster/target IDs and
multiplicity1. Native33 cases verify target gates, deadline, unsigned forecast
edge, all four critical wizard types, mana boundary, delay, validation failure
and duplicate prevention. World/path40ad00,delay51e530,recovery51d570 and
submission57c6e0 are explicit emulator doubles. Actual healing, full normal
target scoring and initialization availability are not validated by these tests.
Evidence:ai-cure-target-verification.json. Preparation446600 resets+162 and
computes wait+5+travel estimate; mode3 estimate isunsigned(type+19c-unit+1c+
16*6c549c)/12 + trunc(5e147c/2). Mode0 uses464c50/464ca0/464cb0/464ec0 path
iteration. Other mode branch reads a stack temporary without visible assignment;
supported mode values and that branch need caller investigation.

## Native spell availability and projected mana

40a950 ABI is ECX=context group,EDX=caster group,stack(spell,wait_out), boolean
returnAL. It initializes wait_out=INT_MAX, rejects structural caster groups and
non-wizard leaf types, then visits context units. Matrix6b13ed+721*spell+
4*(caster_owner+8*observed_owner) permits consideration; native51e6c0 predicts
the wait for each permitted observation and the minimum is returned. AL=true
means at least one permitted observation, even if its wait remainsINT_MAX;
initializers separately reject that sentinel. This matrix is observation-based,
not simply a globally known-spell Boolean.

51e530 checks base spell cost against mana capacity first (unsigned), then
compares fixed-pointmanae8 with256*cost*multiplicity. If deficient, active
type19 records among42 entries atunit+17c,stride24 contribute256*record_amount.
No deficit gives0. Otherwise only wizard types0/24/25/26 with positive global
mana yield5e1908 can recover: native unit enumeration uses412aa0 health!=0,
live slot+4, same owner and+fc!=0. Income is256*yield per qualifying unit;
wait=ceil(deficit/income)*5e1904. No usable income givesINT_MAX. Capacity is
checked against base cost, not multiplied cost; tested multiplicity2 preserves
this native distinction. The input/future mana is signed fixed-point internally.

51e6c0 delegates own-owner queries to51e530(spell,1). Other-owner queries use
unit+e2b+4*owner projected mana and observed power owners at6c5640,8 entries per
power, count6c5c84. Sufficient projection returns0 before capacity validation;
otherwise same ceil formula applies if observed income positive and base cost
fits capacity. 507fa0 updates projected mana: own-owner ignores delta and uses
actualmana+active type19 contributions (without capacity clamp); other owners
add delta and clamp to[0,capacity*256]. Native180 fixtures cover actual loops,
filtering, fractional mana, capacity/multiplicity, reserved records, availability
and projection update. No stubs:ai-spell-availability-verification.json.

Matrix producers located through full Ghidra instruction scan:506290 creature
initialization and509b60 innate-spell list insertion set own-owner diagonal
atowner*36; the latter excludes0/24/25/26 and caps list+56c at30, storing at570.
57b710 native spell execution sets matrix entries for caster visibility observers
(unit+24+4*observer), then updates their projected mana through507fa0. Thus
observing a spell can change a rival's inferred capabilities. Exported producer
509b60 has now passed15 native insertion/rejection/30-slot boundary cases.
Five native57b800..57b8ec loop-slice fixtures verify eight-observer visibility
masks, matrix indexing and predicted mana debit. UI notification suffix is
explicitly skipped; full57b710 execution is not covered. Total verification200
cases,195 complete helper cases without stubs and5 loop slices. Other producer
semantics remain provisional until instruction/native tests; scan artifact
outside Git:ai-spell-refs-expanded.tsv. Effect type19 and observed power table
construction/lifecycle remain active recovery work.

## Health/mana/event value function416d80

Ghidra's void/single-argument signature is incorrect. Native ABI: ECX=creature
type index,EDX=post-change health,stack(i32health_delta,f32post-change_mana,
f32mana_delta,f32event_weight); signed value returnedEAX,callee pops16bytes.
For wizard types0/24/25/26 it starts with
H=trunc((global6a5f98+1)^2*(1/(health-health_delta+1)-1/(health+1))
+double5c53e8). Note the max-health constant comes from global first creature
definition, not the selected type's own+18. Nonwizard path sums505c50 and
505bf0 over28 opposing types, uses unsigned sum/28, scales by40*health_delta,
then performs unsigned ceiling division by selected definition+18. Supported
meaning of negative nonwizard deltas is not established; don't silently replace
the unsigned arithmetic with signed division.

Mana stage C=trunc(H+180000*(1/(mana+30-mana_delta)-1/(mana+30)));
final value=trunc(C+1000000*event_weight). Native x87 extended intermediates and
staged truncation matter: mana0,delta5 returns1199 in the tested engine rather
than ideal-real1200.176 native cases reconstruct binary64-significand x87
rounding, including wizard negative changes, and verify stronger health value
at low health and stronger mana value at low mana. No native helpers stubbed.
Evidence ai-resource-value-verification.json andverify_ai_resource_value.py.

508040 updates projected mana per observed power and calls416d80 with health
and health_delta0,mana=projection/256,mana_delta=change/256,event0; it discards
EAX. Therefore this call alone does not prove learning-counter accumulation.
4181d0 explicitly adds its416d80 result toaction+2f on the identified branch;
action+33 producers still require investigation. The scalar valuation and
retirement ratio must not be conflated with a globally accumulated reward.

## Native retirement decision and classification

79 controlled native slice cases verify428b61..428c43 decision and428c54..
428cfc label recording, using real466870 wizard lookup,59bcc0 power and477040
sample setter. Only retire callback is a no-op double; destructive cleanup is
excluded. Group+4 enables learning,action+1b is score,action+c start tick,+10
deadline,+14 ended flag,manager+14 current tick. Metric is current wizard922/
(926+1), or0 if missing. RatioR=(baseline2b+.001)*(counter2f+1)/(counter33+1)/
(metric+.001). For learning actions withscore<1, early retirement occurs when
R^((now-start)/(deadline-start))<float5d8658(~.001). Otherwise manager+18 with
global6e1f0c=0 forces retirement; deadline reached invokes retire callback and
retires; ended flag also retires. Meaning of global6e1f0c remains provisional;
test calls it multiplayer only as a descriptive fixture label, not a verified
global symbol. Score>=1 bypasses the ratio interruption check.

At retirement, learning enabled and sample index23>=0 recordslabel0 if
float32(R)<=float5c5348(~.58),label1 if<=float5c534c(~1.71),otherwise2.
It storesstatus2 andlabel through477040 into29-byte sample slots. Missing
wizard therefore uses denominator.001 rather than skipping classification.
Semantic names for counters2f/33 and precise danger/safety producers remain
pending. Tests cover group-learning exclusions, missing/index exclusions,
deadline/ended/manager combinations, elapsed power andscore1 bypass.
Evidence:ai-retirement-verification.json. Full cleanup/container invariants
and scheduler event domains remain separate unverified work.

## Outcome counters: damage attribution

Whole-image Ghidra operand scan ai-outcome-field-refs.tsv located additional
counter writers absent from direct-call AI exports:467c80/468470/5076f0/
509e50/50d6f0/512460/514990. Offsets alone are candidate references, not type
proof; verified514990 ties them directly to active action pointers.

Nonfatal514990 first evaluates416d80 with pre-damage health and positive damage
delta, then subtracts health. If a source payload exists, its two command IDs
are looked up using416c30 in different manager contexts690600 and644550; each
matching action+2f receives the value, doubled when victim definition type is
0/24/25/26. Victim's membership pointers+678/+67c each traverse group+39 parent
links to the root; if root+5 has an action, its+33 receives the undoubled value.
Thus+2f is credited benefit and+33 credited loss in this domain. Both slots are
processed independently: when both lead to the same root action it is credited
twice, without deduplication. This native behavior is confirmed, not a proposed
patch.24 full nonfatal514990 fixtures pass with real416d80 and strength helpers;
the initial source-action lookup416c30 double has now been replaced by real
416c30/42e610 using synthetic manager trees, and all24 fixtures still pass
without stubs. Includes0/1/24 victim types,
0/2 ancestor depth, shared/distinct roots and present/absent source payload.
Evidence:ai-damage-attribution-verification.json.

Static5076f0 positive-healing branch credits the healed unit's two root actions
at+2f when its attribution flag is enabled.509e50 power income branch credits
the mana value to the power unit's root actions+2f.467c80 power acquisition
credits event yield/period to both membership actions. These branches are
identified but not validated by the damage fixtures. Fatal damage, owner change,
movement/lifetime losses and source lookup/container integrity remain open.

Source lookup416c30 is now separately verified in76 no-stub native cases.
ECX is manager; one stack argument is signed command ID. IDs<0 return0.
Manager+ba is a tree object, whose head pointer is manager+be.42e610 searches
signed lower_bound from head+4, using global5faf50 as nil, node+0 left,
+4 parent,+8 right,+c signed key,+10 action pointer.416c30 rejects head and
larger-than-requested lower bounds, therefore returns a pointer only for exact
keys. Empty trees, below/between/above missing IDs, negative IDs and INT_MAX
are tested with full memory nonmutation assertions. Native insertion/deletion
and red-black balancing are not implied by these read-only synthetic trees.
The nonfatal damage fixtures now resolve10 in manager690600 and11 in644550
through these real trees. Evidence:ai-action-lookup-verification.json and
updated ai-damage-attribution-verification.json. Source read lookup is verified;
container mutation integrity remains open.

## Healing and power-income reward feedback

ai-outcome-event-verification.json adds756 no-stub native cases:432 healing,
288 power income and36 power-acquisition reward suffix cases. Healing runs5076f0 from its entry until507b82 before
player UI suffix, or its real early return for global6e9858!=0/dead unit.
Power tests run the exact509fa4..50a0da slice with native466870 wizard lookup,
507f00 mana application and416d80 valuation. They do not validate the entire
509e50 update loop or fatal/healing UI effects.

Positive/zero healing clamps health to native5075f0 maximum. With attribution
flag (fourth stack argument) set,416d80 receives health AFTER healing and the
actual health gain (not requested gain). Credit goes to the HEALED unit's two
memberships678/67c: each ascends39 to the root, then adds value to action2f.
The caster/source payload does not select the recipient of this reward. Both
memberships are processed independently, so a shared root receives twice.
Missing memberships receive no reward. Flag unset still heals; frozen/dead
units neither heal nor credit. Zero gain credits zero; it is not a new sample
or a direct Brain update. Tests cover0/1/26 definition types,0/20/90/100 health,
0/5/20 requests, flag, shared/distinct/absent groups and global freeze. Native
valuation is separately checked against the reconstructed scalar formula.

Power-income gate requires unit+fc!=0 and unsigned global6c4830>unit+100.
Equality is not due. Once due, next tick+100 becomes now+5e1904 even when
owner profile+0c is-1 and prevents payout. Native wizard lookup uses owner174
and the manager's154-byte owner rows.507f00 applies5e1908<<8 and clamps actual
mana to[0,capacity<<8]; it marks wizard92e dirty. The tested wizard belongs
to a different player from644520, avoiding actual player UI calls rather
than replacing them.

Value uses integer mana gain=(after>>8)-(before>>8), while effective mana adds
active type19 amounts among42 six-dword records starting17c, then truncates
the fixed-point total to integer. It calls416d80 with health0/delta0/event0.
Thus fractional actual mana affects the capacity clamp but reward uses whole
mana units. Active reservations reduce marginal value through a higher
effective-mana denominator. Both POWER unit membership roots receive2f
credit independently, including duplicate root credit; it does not use the
wizard's memberships. Tests cover exact/not-yet/past deadlines, disabled
power/profile, caps10/100, fractional9.5/full100 initial mana, reservations0/20,
and all three membership arrangements. The deliberately over-cap fixture
also confirms a negative value can be added to2f when native clamp reduces
mana;2f is a signed arithmetic accumulator in these branches, not guaranteed
monotonic. Native owner-1 null-profile behavior is not exercised; ownership
validity is a separate lifecycle invariant.

Power acquisition467c80 first calls51e7d0(1), which sets unitfc=1 and100 to
now+period after49d120 world registration. The registration/map/UI dependency
is not tested here. The suffix467c8c..467cd0 computes event=float32(yield/period),
passes zero health/mana changes and this event to416d80, then uses native522770
to retrieve each membership root's action and credits2f.36 no-stub suffix
fixtures cover yield0/1/3/7,period1/20/30, absent/distinct/shared memberships,
and native return1. This acquisition reward is separate from the later
periodic mana-income valuation; float32 division rounding precedes event
scaling and truncation. All copied field mappings are unchanged.

Boundary caution: exported50d6f0 pseudocode starts inside a loss-credit loop,
uses uninitialized input registers and has no entry-frame setup. It is an
interior-code candidate, not presently an independently recovered callable
function. Its containing function and callers must be established before
fixture design or a whole-function semantic claim. Operand matches and
successful decompilation do not resolve this boundary issue.

## Eight targeted spell execution state machines

3456 native executor fixtures in ai-spell-execution-verification.json cover
actions21 Cure(spell41),39 Iron Skin(74),43 Scythian Bow(78),44 Lucifer's
Farewell(79),47 Excalibur(83),48 Ornithopter(84),51 Invisibility(85),52 Blood
Lust(42). Registered execute VAs and exact fields are in the report and
verify_ai_spell_execution.py. This is executor recovery, not complete target
evaluation, path acceptance or actual spell-effect verification.

All use current target+15e and caster+14a, returning0 when target health+e4=0.
Cure also ends when health equals native maximum5075f0. Iron Skin ends only
when signed effect+90>0; negative90 remains eligible. Lucifer's Farewell
requires78c=0, Invisibility requires8c=0 and Blood Lust requires94=0.
Scythian Bow/Excalibur/Ornithopter require native51fef0(target)=0, which is
exactly target+7cd (not a boolean copied from caster). Negative nonzero effect
values therefore reject those actions while Iron Skin accepts negative90.
The family uses submission flag+162: once set, an otherwise-valid action
continues returning1 without another wait, validation or submission call.
These methods assume target+15e points to a valid object; null-target and
lifecycle ownership protections must be established elsewhere.

Before initial submission they call native51e530(caster,spell,1). A nonzero
wait returns1 without recovering or casting. Once wait=0, they compare unsigned
whole actual mana (e8>>8) with native spell ManaCost. Below cost they call
51d570 recovery. Seven immediately return1; Iron Skin39 falls through into
target revalidation and potential command submission. Instruction sequence
44fa32..44fa3b confirms no return/jump after recovery44fa36. Active type19
reservations can make native51e530 return0 even when actual mana is below cost,
so this branch is reachable under the isolated availability fixtures. This
proves executor control flow, not that the real queue accepts an underfunded
cast:51d570 and57c6e0 are test doubles, and recovery's wider world effects and
command validation remain outside this result.

After mana checks, native coordinate constructors build caster coordinates and
40ad00 revalidates the current target. If permitted they submit command with
spell/caster ID/target ID/multiplicity1, then set162=1. Lucifer's Farewell44
additionally invokes51f5b0 and50fef0(target108==1) after submission. Their world
effects are traced but doubled, not recovered by these fixtures. Health or
effect changing across native wait/recovery is separate lifecycle work.

Tests use health0/50/200, effect-1/0/1, mana9/10/20, previous submission,
blocked validation, full native availability with and without active reserves,
and separate forced delay0/1 cases. Synthetic cost10 provides a common branch
threshold; it does not override the authoritative configured costs for analysis
or claim all spells cost10. Target/maxhealth/51fef0/coordinate constructors are
unmodified. Explicit doubles:40ad00 world validation,51d570 recovery,57c6e0
queue,44 post-submit51f5b0/50fef0, and51e530 only in forced-delay cases. No
player process, saves, learning records or shipped AI behavior are changed.

## Native mana-item recovery and executor integration

51d570 is not a passive mana regeneration mode.78 fixtures in
ai-mana-recovery-verification.json execute its full scan, native468b10 type19
item dispatch and507f00 mana application. It scans42 six-dword item records
from unit17c, selecting the FIRST record with active+14!=0 and type+0=19.
Selection precedes quantity+10 checks: an active first match with zero quantity
does not cause scanning to continue to later matches. Native inference uses
record+4 in mana availability, while actual use reads global item's configured
amount at6b1250+19*32 (when count6b1254>19). This distinction requires recovering
item initialization and normal invariants before calling a mismatch a bug.

For global6e1f0c<=1, quantity>0 dispatches item19. Native507f00 adds configured
amount<<8 and clamps actual mana to[0,capacity<<8], marks92e dirty. It decrements
quantity, sends effect notification564e90(7,unit,19,0,-1,-1), and when quantity
reaches0 clears active14 and decrements active-item count unit178. Missing,
inactive or wrong-type records do nothing. Tested slots0/5/41, quantities0/1/2,
route values-1/0/1/2 and mana0/90. Test amount25 is deliberately controlled,
not a assertion about installed item balance. Local player's item UI update
4d7180 is avoided by using another player's unit; effect564e90 is a sink.

For6e1f0c>1 it instead queues a packet through537bd0: header0,category8,
command14,unit's low ID byte and item-slot byte. It does NOT change mana,
quantity or active count locally, even if the selected record has zero quantity.
Packet delivery/validation is not tested;537bd0 is a capture sink. The routing
threshold is proved but global's complete multiplayer/session identity remains
pending. The no-item path never queues a command. Missing item-definition count
<=19 leads to a null-pointer load in type19 dispatch; valid initialization
invariants are not established by these controlled fixtures.

The targeted executor report now contains3504 cases: the original3456 plus48
integrations with real51d570/468b10/507f00. They use9 actual mana, an active
type19 record, common cost10 and configured item gains0/1/25, across eight
actions and blocked/unblocked world validation. Real recovery consumes the
item and changes mana before Iron Skin39 continues to submit. The other seven
return immediately despite sufficient replenished mana and would need a later
executor call. With gain0 Iron Skin still reaches submission when the validation
double permits it, so later queue/spell validation remains an independent gate.
These synthetic amount variations do not prove normally initialized item
values can violate costs. World validation, spell queue and effect notification
are explicit sinks; actual spell acceptance/effects remain pending.

## Targeted spell initialization and group construction

1824 full native initializer fixtures in ai-spell-initialize-verification.json
cover the same eight targeted actions. They reset eligibility149 and require
input group dword0==1, parent39==0 and assigned-action5==0.40a950 receives
the same group as both observer context and caster group, with the fixed spell
ID and output14e. A false availability or INT_MAX wait rejects initialization;
a finite positive wait is accepted. After success, caster pointer14a is group35.
These fixtures run real availability, wait, group count4078a0, cursor407920 and
deadline40eff0; only builders40f910/40f9e0 are replaced by controlled groups.
They cover structural0/1/2, parent/action flags, known/unknown diagonal spell
matrix, mana5/20, power counts0/2, definition types0/1/24,95a=-1/0/1 and
target counts0/1/2. Deadline16 becomes incoming tick100+30 for all eight IDs.
No valid target group means eligibility stays0 even after storing caster/group.
An eligible initializer reserves a fresh recursive cursor156 in that group.

For seven actions, caster95a==0 chooses40f910; any nonzero value chooses40f9e0.
Lucifer's Farewell44 always chooses40f910 and does not branch on95a. The flag's
upstream meaning remains to establish; its effect here is the selection of
same-owner versus visible-related-owner candidate construction.

Builders are independently executed in18 full native cases in
ai-target-group-verification.json, each with48 synthetic units covering three
owners, active/inactive slot, alive/dead, visible/hidden and types1/27. CRT
allocation/free alone are doubled.419990 creates structural groups and419a10
unit leaves, inserting every new group into the action's owned-pointer vector
at3b/3f/43.52a710 enumerates active slots and calls412aa0, whose predicate is
only health!=0; it preserves unit-pool order.40f910 keeps units whose174 owner
matches the requested owner; it does not test visibility or exclude type27.

40f9e0 first requires requested owner in[0,7], visibility24+4*owner!=0,
unit typea8!=27, and relationship byte at643a80+owner*154+18+unit_owner!=0.
It does not infer relationship automatically for the observer's own units.
Eight relationship masks over owners1/2/3 and invalid observers-1/8 are tested.
Exact returned child order, leaf unit35, parent39 links, leaf rank89=3,
root eight free cursors, count4078a0 and action-owned vector are asserted.
Structural root and unit leaves are fresh allocations; vector reallocations
run native code. Native availability/initialization and builder construction
are independently proved in these fixtures, not a combined lifecycle test.
Alliance/visibility producers, constructor allocation failure, cleanup and
upstream meaning of caster95a remain open.

## Group detach and owned-group cleanup

34 native cases in ai-group-cleanup-verification.json verify full407780
detach, full407650 group destructor, and418050..4180c9 action-owned-group
cleanup prefix. CRT597870 is a free-recording sink; no player data or actual
allocation is freed.407780 acts only on structural parent(unit35==0) and an
exact child pointer in29..2d. It shifts remaining entries left, shortens end2d
by4, and clears removed child's39. For each reserved cursor(41+index==0),
if removal address precedes cursor49+4*index it subtracts4; equality does not
move it. Free cursors do not move.24 index/cursor/free fixtures plus missing
child and leaf-parent no-op fixtures verify these boundaries.

407650 saves global rank cutoff5d854c, temporarily sets it0, detaches eligible
direct children's39, detaches itself from parent via407780, restores cutoff,
frees its child-pointer vector and zeros29/2d/31. It does NOT recursively free
child group objects or units. Six fixtures cover caller cutoff0/5 and child
rank-1/0/3; negative-rank unit leaves are skipped even by this temporary0
cutoff. That synthetic case records behavior, not a proven valid production
rank invariant. Previously recovered419a10 constructs target leaves withrank3.

Two action-prefix cases run native418050 through4180c9 with root-first and
child-first owned-group ordering. Each calls407650 then frees each owned group
once; parent/child links end detached, units remain untouched, caller cutoff
is restored, and owned vector3b..3f becomes empty. Its buffer is not yet freed
at this boundary. Remaining destructor code frees feature trees and eventually
the owned-vector buffer. A zero-filled action is NOT sufficient for full
destructor validation: feature-tree heads require valid construction. Full
base/derived destructor and nonempty feature-container destruction remain
explicitly pending; this prefix evidence must not be promoted to full cleanup.

Follow-up: the same report now totals46 cases, adding12 legally constructed
full base-destructor lifecycles. Native422ec0 constructs action5, including
all base containers and valid shared tree heads, then native418050 runs to its
actual return. Fixtures instantiate1/2/5 simultaneous actions, destroy them
in creation/reverse order, with and without native419990/419a10 owned groups
linked through407710. Only CRT allocation/free are sinks; all native constructor,
container and destructor helpers execute. Tests assert each allocated pointer
is freed exactly once with no unknown frees, owned-vector fields3b/3f/43 zero,
and shared reference counts5faf30/5faf38/5faf48 decrement per destroyed action.
Shared nil heads5faf2c/5faf34/5faf44 persist until last owner, then are freed
and reset0. Initial emulated subsystem globals are explicitly reset before
construction, avoiding stale initialized disk-image pointers.

This closes full418050 cleanup for valid EMPTY feature containers and native
owned groups; the earlier zero-filled-object limitation is resolved by actual
construction, not by replacing feature destructors. Action5 constructor sets
ID5 and sample index23=-1; vtable5c58fc returns to base5c5358 during cleanup.
No additional derived resource destruction is claimed. Nonempty feature-tree
node/value lifecycles, all derived destructors and allocator failures remain
open. CRT free sinks track ownership without invalidating emulator memory;
the tests prove allocation/free matching, not use-after-free detection under
a real allocator.

## Registered constructors and additional derived ownership

ai-action-construction-verification.json covers all53 full registered native
constructors independently and two mixed53-object construction/base-teardown
orders.55 fixtures pass. Every constructor returns its input object pointer,
sets registry-matching action ID and vtable, initializes sample index23=-1,
and has empty owned-group vector3b/3f/43. CRT allocation/free are tracked
sinks; every nonnull base free is a known, not previously freed allocation.
All other constructor/helper code runs native. Fresh subsystem globals20..48
in5fafxx are reset to0 before each isolated emulated fixture.

For52 IDs, base418050 teardown releases every constructor allocation in the
empty fixture. Retreat12 constructor427810 additionally allocates a20-byte
shared nil node(5faf20/refcount5faf24) and a20-byte per-object head at object1a4;
count1ac starts0. These remain after base teardown in each isolated/mixed
fixture. Constructor export and native allocation tracking agree, so its
derived tree requires additional cleanup. This is not proof of a shipped
leak: base teardown was invoked explicitly, not the actual complete derived
cleanup path. Additional resources created later by initialization/evaluation
are outside the empty-constructor fixture. Actual derived cleanup dispatch,
nonempty trees/vectors/deques and failure paths remain pending.

Retreat cleanup follow-up: startup4022f0 constructs prototype5f9930 and
registers402310 with CRT exit-registration59b7e2.402310 guards prototype
cleanup through bit1 at5f4bdb then jumps to callable402330 with prototype ECX.
The full402330 function first erases its tree through42acc0, frees head1a4,
zeros tree head/count, decrements shared5faf24 and releases/resets5faf20 at
last owner. It then frees selected-vector18f and candidate-vector16b and zeroes
their begin/end/capacity triples, before executing inlined base cleanup.
Vtable entry0 is initializer, not a deleting destructor; do not invoke it as
destruction based on a C++ layout assumption. This prototype exit path proves
a complete derived cleanup function exists, but does not yet establish every
dynamic scheduler deletion dispatch uses it.

Constructor report now totals69 fixtures:55 earlier plus14 complete402330
lifecycles. Six cover1/2/5 Retreat objects in forward/reverse order, two cover
mixed53-action teardown using402330 for12, and six additionally populate both
Retreat vectors with four dwords each allocated by the tracked CRT sink.
All allocations, including Retreat extra tree heads/shared nil and nonempty
vector buffers, are freed exactly once in these complete paths.5faf20/24 end0.
Tree itself remains empty;42acc0 nonempty-node destruction, other derived
cleanups and actual dynamic deletion dispatch remain pending. Earlier report
cases intentionally invoking base-only retain their extra allocations as
recorded controls; they are not regressions or evidence of a runtime leak.

Further cleanup recovery: report now133 fixtures. For all53 registry entries,
hash-gated Capstone decoding starts at known startup boundaries and verifies
mov ECX=prototype, call=registered constructor, push=exit callback and
call59b7e2. Each callback's prototype assignment and direct jump identify a
callable full derived cleanup function. Exact callback/cleanup pairs are
stored in prototype_cleanup_map in ai-action-construction-verification.json.
All53 constructors are followed by their matching full cleanup individually,
plus two mixed53-object forward/reverse orders. Every tracked allocation is
released exactly once in these complete empty-derived paths, including shared
Retreat heads. Unlike base-only controls, no extra allocations remain.

Nine additional Retreat fixtures each build two objects with1/7/31 synthetic
tree nodes in balanced, left-chain or right-chain shape and populated vectors.
Native full402330/42acc0/42d4d0 frees every node exactly once along with both
heads, shared nil and vectors. Nodes are20 bytes: left0,parent4,right8,
scalar/key payloadc,colour/status10. The full-range erasure branch traverses
right subtrees recursively and iterates left descendants, then resets count
and head links. Synthetic tree construction does not validate native insertion,
red-black balancing or partial-range42d100 erase. It establishes full-range
destruction independently of shape. Whole feature-tree payload ownership and
dynamic scheduler's actual deletion dispatch remain required open work.

Complete cleanup evidence is confined to empty resources for the other52
actions; their later-created nonempty target vectors/deques need fixtures.
Allocation failure, exception unwinding and real-allocator invalid-access
detection are not tested by the successful allocation/free sinks.

## Dynamic retirement cleanup differs from prototype exit cleanup

This resolves the previously open deletion-dispatch question at the exact
retirement suffix:428e00..428e14 directly calls418050 and then597870(action).
It does not consult the action vtable, ID or prototype cleanup map. Static
416ca0 cancellation similarly calls418050 at416d5a, after command-map erasure,
sample release and clearing group+5.415ac0 manager cleanup also explicitly
calls418050 for candidate and active actions. Those other full functions are
not exercised by the suffix fixtures.

ai-dynamic-teardown-verification.json has54 native cases using actual53
constructors and the exact428e00..428e14 suffix. Action storage itself is
allocated through the tracked CRT sink and is freed. Every case calls real
base418050; only CRT allocation/free are sinks.52 empty derived constructors
leave no allocations. Retreat12 retains its20-byte head and shared20-byte
nil/refcount after its object is freed. A54th case fills AggressiveAttack6
candidate/current vectors with two16-byte allocated buffers; both remain
after object free. Native registered retire callbacks432fb0(AggressiveAttack)
and43b3e0(Retreat) are no-op exports, consistent with no callback cleanup,
but full pre-deletion workflow and real nonempty action lifetime still require
testing. The evidence proves local allocation ownership loss in this suffix,
not measured production leak rate or an explanation of previous player hangs.

This materially changes the analysis: successful prototype cleanup tests
cannot stand in for dynamic cleanup. Do not patch behavior or declare a fixed
leak during this analysis task. Next establish actual clone/commit allocation
provenance, preceding scheduler/map/group branches, alternate owners, runtime
hook effects and repeated isolated action retirement before classifying user
impact. Constructor-only allocations and synthetic populated vectors have
different evidence strengths and must remain distinguishable.

## Candidate-to-current action transitions

All53 registered commit methods are now executed in the hash-gated offline
engine emulator;615 cases pass in ai-commit-verification.json. This establishes
state transfer only, not all target/evaluation/execution semantics. The engine
SHA remains42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da,
preferred image base400000. Exact method VAs are in ai-action-registry.json;
field mappings and reproducible fixtures are in verify_ai_commits.py.

44 actions perform only dword/block copies or no-ops, with12 deterministic
random whole-object comparisons each. IDs28/53/59 commit no state. Cure21 and
BloodLust52 copy candidate+15a to current+15e; identical field layouts also
occur in39/43/44/47/48/51. These matching layouts alone do not prove matching
target rules. ID30 copies the full dword149 to14d, not just an eligibility byte.

Seven statistical tactics6/8/9/11/12/13/14 copy scalar prefixes and independently
assign vectors of dwords. Nine cases per method cover null/allocated empty
source, shrink, equal length, growth within capacity, and replacement allocation.
Source buffers remain unchanged; destination tails remain unchanged; only
expected object fields change. Reallocation frees the prior buffer and allocates
exactly4*source_size bytes, then sets end and capacity to the same address.
Native copying/construction helpers run unmodified. CRT allocation597850 and
free597870 are explicit emulator doubles, so allocator failure is not tested.

Haste54 commit45df20 is a different operation. It uses group+166 and real
407920/4079f0 recursive iteration, resets action+19a, clears the existing deque
at+16a, then collects each unit satisfying unit+4!=0, health+e4!=0,
owner+174 equal to caster+14a owner, and effect+778==0. It does not simply
copy a candidate target pointer. Deque count is+196; begin iterator fields
are16e/172/176/17a and end fields17e/182/186/18a. Each iterator stores block
begin, block end, current pointer, and map-slot pointer. Blocks are1000 bytes,
1024 dword entries. Initial map has two slots; first block starts at midpoint
+800. Twelve full-method tests cover0/1/2/12/80/3000 units, both initial build
and build-clear-empty-rebuild. They verify exact filtered ordering, count,
19a reset, block boundaries and native container clearing/reuse. Only CRT
allocation/free are doubled; all deque and group helpers execute native code.
The3000-unit fixtures cross both block and map-growth boundaries. Effect+778
is the Haste exclusion field in this action; broader effect lifecycle remains
separate work. No game process, player saves or AI learning data are touched.


## Registered clone slots are fresh-instance factories

106 cases in ai-action-factory-verification.json execute all53 registered
clone-slot methods with success and failure of the first object allocation.
They allocate a fresh action, initialize its identity/vtable/sample23=-1 and
empty owned-group vector, and do not copy or mutate arbitrary bytes at the
provided ECX source. The historical registry role name clone remains for schema
compatibility but its verified semantic role is create_fresh_instance. No
state-transfer claim follows from that label. Actual state copies elsewhere
remain independently tracked.

Every successful factory object's matching prototype-derived cleanup releases
all its constructor-owned resources; an explicit CRT free then releases object
storage. All tracked allocations match once. First allocation failure returns0
without constructing any subcontainers or changing fresh shared-tree globals.
Nested allocation failure and exception-unwind behavior remain unverified.
Per-action first allocation sizes and factory VAs are recorded in the report.
CRT allocation/free alone are emulator sinks; native factories and cleanup
helpers run intact.

Dynamic teardown report now107 cases: the earlier54 plus all53 real factory
creation followed by exact retirement suffix428e00..428e14. Retreat's extra
20-byte per-instance head/shared nil remain after base418050 and object free
in this REAL factory path as well. This strengthens allocation-provenance
evidence beyond a constructor applied to oversized synthetic storage. It still
does not validate scheduler registration, all prior retirement stages, other
owners, runtime hooks or production accumulation. Synthetic attack vectors are
still explicitly distinct from native-factory constructor allocations. No AI
behavior patch is made as part of this analysis.


## Scheduler candidate selection, two reservoir modes

1032 native428751..4288be slice cases in ai-scheduler-selection-verification.json
verify selection after evaluator acceptance and before next evaluator call.
ESI is manager,EBP the function frame. Incoming score frame+8,additive offset+10,
commit enable byte+18,skip-score1 byte+1c. Manager11ddc selects alternate mode,
11ddd stores best,11de1 tie counter,11fe9 accumulated weight,11fe5 selected
candidate-vector slot. Actual mode configuration upstream is still pending.

If skip-score1 enabled and incoming score EXACTLY1, selection is skipped BEFORE
adding the offset. Otherwise score+offset is stored float32. Default mode,
adjusted score1 or current best1 enters maximum selection. Below best rejects;
strictly above best resets tie count0; eligible ties increment count then draw
(RNG54e200&INT_MAX)%count. Remainder0 updates best, and when commit enabled calls
candidate vtable+c, stores selected slot11fe5 and sets local changed flag.
Commit disabled can still update best and ties, but does not update selected slot.

Alternate mode for scores/best other than1 assigns weight1 when adjusted score
is greater than-1, otherwise0. It adds weight to11fe9, then wins if sum==0 or
masked RNG * float5c5398(2^-31) < weight/sum. When commit enabled, winners commit,
store the slot and update best only if the adjusted score exceeds it. This is
binary eligibility-weight reservoir sampling, not softmax or score-proportional
sampling. A first zero-weight candidate with sum0 wins by the explicit zero-sum
branch; later zero-weight candidates with positive sum cannot win. With commit
disabled, alternate sum still changes but best does not, unlike max mode.

Tests cover incoming-1/-.5/0/.5/1,best-1/0/.5/1,ties0/2,RNG0/1/INT_MAX,
commit enable/disable, both modes,skip-score1 and offsets+/-.5,prior sums1/4
with additional half-range RNG. Native x87 comparisons and state writes run
unchanged. RNG54e200 is fixed and vtable+c callback captured, explicitly doubled.
Finite deterministic fixtures do not establish NaN/overflow behavior or native
RNG distribution. Prior switch/disaster gates4286xx, evaluation/resumption,
mode configuration and registration remain separate required work.

## Current-action replacement gate and whole outcome helper

Hash42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da,
base400000. Instruction boundaries40a3b0..40a412 and42867c..428751/4288be
verified before emulation. Evidence: ai-outcome-ratio-verification.json (864
whole-function cases, no doubles) and ai-switch-gate-verification.json (1371
cases:1083 ratio doubles plus288 real-helper integrations).

40a3b0 takes action in ECX and returns x87 ratio. Real466870 resolves owner+27;
metric is signed wizard922/(926+1), or0 if no wizard. With epsilon equal to
double5c5378, ratio=((float32 action2b+epsilon)*((signed action2f+1)/
(signed action33+1)))/(metric+epsilon). Native extended-precision rounding at
each arithmetic step was independently reconstructed before storing double.
Tests cover baseline0/.05/.1/1, metric numerator0/1/100/1000, denominator
1/100/1000, gains/losses0/3/10000, present/missing owner. Signed increment
overflow and singular/exceptional values are not covered; field producer
semantics are not established by this formula alone.

Switch gate runs BEFORE candidate offset addition. Missing current action or
current byte15 nonzero accepts immediately. Otherwise byte1a nonzero rejects
unless raw candidate score is exactly1. With raw candidate c and current score
s, denominator1-c*s must be positive and (c-s)/(1-c*s) must be strictly greater
than float5d8654 (about.9) to accept through relative improvement. If this fails,
current s<1 and outcome_ratio^((now-start)/(deadline-start)) strictly below
float5d8658 (about.001) accepts only when c>0. Otherwise rejects. Actual59bcc0
power runs in every fixture. Flag15/1a producers, duration0, NaNs and full
scheduler control flow remain pending. Player AI behavior has not been patched.

## Action registration-state installation

Evidence ai-registration-state-verification.json:864 native suffix cases at
428a5c..428b25, same hash/base as above, no doubled functions within slice.
This is part of4289e0, not a whole-function registration test. Inputs are ESI
manager, selected-vector-slot manager11fe5, EAX owner wizard (or0), EDI owner ID
and EBX prepare duration. Start tick goes to action+c; end tick to+10 with u32
wrap. Flags14/15 are cleared; action1a receives manager11ddc verbatim. Thus the
same mode byte controlling alternate candidate selection becomes the new
current action's replacement-protection byte. Mode configuration remains open.
Score11ddd goes to action1b, serial managerca to action1f, owner to action27.
Baseline2b is float32 wizard922/(926+1), or0 with missing wizard. Gain2f and
loss33 reset0; manager serial increments with u32 wrap. Sample index23 remains
untouched. Duration0/8/40,tick100/near-wrap,serial0/UINT_MAX,mode0/1/2,score
-1/.5/1,metric0/100 over1/1000,present/missing wizard tested. Mode2 is a synthetic
byte-preservation fixture, not evidence that upstream enables it.

Whole4289e0 first links action+8 and group+5, inserts serial/action into
manager+ba using42b210, calls selected prepare(vtable+10), derives owner via
407920/4079f0 and466870, then installs this state. Finally fresh factory
(vtable+4) replaces the selected candidate slot. These surrounding calls are
statically observed with verified disassembly; integrated tree/group/factory
and exception paths are not yet verified. Other+15 writers and mode producers
remain required; equal offsets in unrelated container types are not evidence
of action fields.

## Selection-mode producer in scheduler423590

Evidence ai-selection-mode-verification.json:4000 native4239e6..423a65 cases,
same engine hash/base. Boundaries derived by decoding from function423590;
2000 use lookup466980 double and2000 use real466980. RNG54e200 is an explicit
double throughout; its distribution is not validated by this test.
Global signed5d8650 policy0 writes mode11ddc=0; policy2 writes1. Policy1 writes0
if global689920 is1 or2. For other game-kind values it calls466980 on owner from
stack+5c; false writes0. True draws54e200, masks INT_MAX, takes remainder100,
and writes1 iff remainder strictly less than signed threshold at
6e200c+4*global689924. Otherwise writes0. Unknown policy values retain previous
mode byte. Tested policies-1/0/1/2/3,game-kind0..3,both predicate outcomes,
threshold-1/0/50/100/101,RNG0/49/50/99/UINT_MAX,both prior modes. These are bounded
synthetic fixtures; native RNG distribution, table bounds, configuration names
and game-kind/profile meanings remain open. Subsequent best-score reset at
423a65 to-2 and tie reset at423a6f are statically observed, outside tested slice.

Additional verified disassembly421f70 caller path:422270 forces mode0 before
4289e0 registration. After the latter replaces candidate slot via fresh factory,
422294..4222a5 compares the NEW candidate's action ID to5; if unequal it sets
REGISTERED group+5 action byte15=1. This static evidence links the previously
observed free-switch gate to this caller, but whole caller execution and branch
origins remain pending. Do not conflate this with any generic byte15 in feature
container constructors. Initial exploratory decode at4221f5 was misaligned and
discarded; boundaries were re-established from4221ad.

## Conditional-mode profile/relation predicate466980

Evidence ai-opponent-predicate-verification.json:1280 whole native466980 cases,
no function doubles, same hash/base. ECX profiles and stack argument owner index.
Scans exactly8 slots at stride154. Returns1 on first slot with dword+0 nonzero,
dword+4 nonzero AND relationship byte+18+owner equal0. Otherwise0. No explicit
self exclusion: relation matrix alone determines that behavior. This is an
existence predicate over active profiles and their relationship to the owner,
not a lookup returning the owner's type. Exact meaning of profile+4 nonzero
must be established from initialization/save/config writers before naming it
human/computer or interpreting game difficulty.

Fixtures cover owners0..7,all8 individual active slots,none/all active,role
0/1/2/UINT_MAX and relation0/1/2/255. Selection-mode integration uses eligible
profile in final slot7 to ensure traversal is exercised; all2000 prior mode
branch fixtures repeated with actual466980. Native RNG remains doubled. No
claim of complete relationship initialization,asymmetric alliances or profile
role semantics from these bounded cases.

## AIRandomness configuration and conditional selection

Same engine hash/base; existing whole initialization export004e4270.c was
cross-checked by disassembly from its known entry. Four DIFFICULTY keys
AIRandomness0/1/2/3 map to signed dwords6e200c/2010/2014/2018, respectively.
Native assignment blocks775c..7792,78d6..790c,7a50..7a86,7bca..7c00 within
4e4270 call GetPrivateProfileStringA with empty default,256-byte output6e2a88,
file path buffer6e2780; nonempty values pass to actual59c5a4 integer conversion.
Evidence ai-randomness-config-verification.json:32 cases with Windows API
explicitly doubled,real native integer conversion. Empty preserves prior value;
invalid nonempty becomes0; no range clamp. Input60/15/0/-1/101/space+50suffix
verified across all4 keys. OS disk/profile-file parsing is not tested here.

Formal runtime CFG/chaos.cfg lines231/240/249/258 currently60/15/0/0. These are
installed configuration values, not universal defaults. Hash-verified mapped
engine initial policy5d8650=1 and threshold dwords0 before initialization.
At4e873e..4e875a, command-token comparison59db40 against string5e3ef0='random'
sets policy2 on equality; static evidence only,command dispatch integration
pending. Global689924 indexes this difficulty threshold; exact difficulty
selection writer and all game-kind meanings remain open. AIRandomness applies
a probability of selecting alternate binary-eligibility reservoir mode when
its game-kind/profile preconditions hold. It does not inject this percentage
as score noise: mode feeds previously verified reservoir choice and registered
protection1a. Do not infer profile+4 denotes human solely from configuration.

## Difficulty-index menu propagation

Evidence ai-difficulty-ui-verification.json:240 whole native4b3420 cases, same
hash/base. External54eec0/557510/4bfb10/5908e0/594230 menu/campaign helpers are
explicit constant-return doubles; native dispatcher and item reads unchanged.
594230 callee stack cleanup ret4 matches call-site argument and avoids an
initial fixture ABI error; corrected test passes all cases.

Menu+5f is item pointer vector,+63 selected index,+67 count; item+2d carries
selected numeric difficulty. Except page ID22, dispatcher first reads this item
value. Page22 initializes value0. Events0/2/3 write that value to global689924;
event4 reads selected item again and writes item2d even for page22. Event5
(default branch) leaves global unchanged. Tests cover pages3/4/22,events0/2/3/4/5,
all4 selected vector positions and numeric difficulty0..3. Other helpers' state,
item construction/labels and invalid empty-vector inputs are not verified.

Read-only bounded Ghidra export at D:/Tools/magic-mayhem-re/
functions-difficulty-writers/ completed visited6,remaining0. It recovered
4b3420 and46bcb0. Requests47457d/4b31fc/4bf7bc pointed into raw operand references
and returned no-function; those sites are NOT considered parsed or boundaries.
Static46bcb0 checks inclusive difficulty min/max in data records with-1 sentinel;
whole script/item dispatch still pending. Native startup4e8734 sets difficulty0;
4e8916..4e8924 command path stores integer parsed from token without clamp.
Command key string5e3e80 and numeric label mapping remain to verify; direct
startup modes near4e8aa6/4e8b2d set difficulty3. Full writer inventory remains open.

## Difficulty and random command-token verification

Evidence ai-difficulty-command-verification.json:68 native slice cases, same
hash/base, no doubled functions. CRT locale flag6fa2e8=0 explicitly selects
native ASCII C-locale branch of59db40, verified disassembly59db40..59dbcb.
Non-C locale path is not covered. Dispatch4e8904 compares token ESI to literal
5e3e80='difficulty'; equality ignores ASCII letter case, passes EBP value text
to actual59c5a4 and stores result directly to signed689924. Equality branches
to4e8534; mismatch to4e8929. Parsed0/1/2/3/-1/4/101,empty,invalid,and space+2suffix
are verified; no clamp at this stage. This does not establish absence of later
startup validation or a reachable out-of-bounds read in production.

4e873e..4e875a compares EBP value to literal5e3ef0='random' with actual59db40;
equality sets5d8650 policy2, mismatch leaves prior0/1/2. random/RANDOM/Random
accepted; randomx/empty/other rejected. This is an interior command dispatch
branch, not evidence that a standalone '-random' spelling reaches it. Whole
argument tokenization and enclosing branch syntax remain pending. Together with
prior mode/config tests this establishes actual numeric policy and parser
behavior, while UI label/default selection/save restoration and role semantics
remain open. Player executable/configuration not modified.

## Whole action-registration lifecycle4289e0

Evidence ai-registration-lifecycle-verification.json:32 whole-function fixtures,
344 registrations,actions59 and21; same engine hash/base. Unlike prior suffix
checks, actual4289e0 calls run with real42b210/42da70 insertion/red-black balancing,
407920/4079f0 group cursor,466870 owner lookup,native action prepare and fresh
factory. Only CRT597850/597870 allocation/free are doubled. Synthetic initial
empty manager tree and one-unit group layout supplied; actual manager constructor
and full group ownership/destruction are outside scope.

All combinations mode0/1,owner wizard present/missing and1/2/8/32 sequential
registrations pass for each action. Action59 prepare returns40. Cure21 uses
real446600 and464c50 with global6b873a=3 and synthetic geometry:target definition
19c=12,target1c=0,global6c549c/5e147c=0,action14e=index; duration=index+6.
Other prepare-global modes are not validated by this integration.

For every registration, group+5 points to registered action and action+8 points
to group; owner/serial/start/end/protection/counters installed correctly. Real
factory replaces candidate slot with a distinct allocation of matching action
ID/vtable and sample index-1. Manager tree count and serial increase; actual
416c30 finds all earlier serials and rejects next missing key. Recursive audit
checks node parent links,ordered keys,black root,no red-red parent/child and
equal black height. This validates actual insertion/balancing in bounded serial
sequences,not arbitrary insertion orders/duplicate IDs/partial deletion.
Allocated synthetic world discarded with emulator; no production cleanup claim.
Failure/unwind,other51 actions,manager destruction/full scheduler still pending.

## Expanded targeted-spell registration and prepare geometry

ai-registration-lifecycle-verification.json now144 fixtures/1548 actual native
registrations:59 plus21/39/43/44/47/48/51/52. All earlier tree/group/owner/factory
checks retained; every targeted prepare resets action162 from1 to0. Conditional
mode globals confirmed by instruction decode at each known method entry before
fixture setup:21=6b873a,39=6be42b,44=6bf240,47=6bfd84,52=6b8a0b,all set3.
43/48/51 use unconditional geometry paths. Only CRT allocator/free doubled.
Other prepare modes,remaining44 registered actions and failures remain open.

Independent ai-targeted-prepare-verification.json adds648 whole prepare-method
cases with no doubles,actual464c50 where called. For nonnegative tested inputs,
duration=((target_definition19c-target1c)+global6c549c*16)/12 truncated integer
plus global5e147c/2 truncated integer plus action14e plus constant5,except
IronSkin39 constant8. Target pointer action15e,definition targetac. Every method
clears once-submission byte162 and preserves target pointer/action delay.
Fixtures difference0/12/120,global step0/2/10,global delay0/3/10,action delay0/5/40
across8 methods. Formula uses numeric field names:movement/animation meanings
still unproven. Conditional mode0 simulates via464ca0/464cb0/464ec0 and is not
validated here; signed-negative,overflow,other mode/global values also pending.
Hash/base unchanged; no player behavior changes.

## Mode0 targeted prepare through animation instruction interpreter

ai-prepare-simulation-verification.json:96 whole native prepare fixtures for
21/39/44/52,actual464c50/464ca0/464cb0/464ec0,no doubles,same engine hash/base.
Mode fields from prior evidence are set0. Directory6898d0 spell offsets
21:4a0,39:220,44:460,52:490 give animation ID and bank index. Bank base6894a0
plus index*114 passed to464ca0; bank+4 index vector and+8 instruction vector
used by464cb0. Synthetic bank0/id0 starts record0. Instruction stride2c.

Native interpreter op0 emits current frame pointer without nonzero event;
op1 sets unsigned delay; op5 emits argument as return event; op6 clears active
state and frame pointer and returns1. Test programs [(0,0),(1,d),(0,0),(6,0)]
for d0/1/5/30 require d+3 step calls to first nonzero. Replacing third opcode0
with(5,2) returns2 on second step call regardless of delay because the setting
and event execute within one interpreter call before wait comparison resumes.
Whole prepare loops until ANY nonzero return,so event2 ends preparation before
opcode6 termination. Duration=action14e+base+step_count,base8 forIronSkin39,
5 otherwise. Delays action0/7/40 and both programs tested across4 spells;
byte162 resets1->0. VM steps independently exercised before full prepare call.

This is actual bounded animation interpretation,not simulated helper returns.
Bank/directory contents are synthetic; real asset format/loading,loop/jump
opcodes2/3/4,fast-forward24 branch and other prepare global modes remain open.
Do not claim total animation duration:code measures first nonzero-event time.

## Prepare animation loops, branches and non-frame initialization

ai-animation-control-verification.json:45 native fixtures,same hash/base,no
doubles.27 bounded synthetic programs/247 step states compare actual464ec0
against an independent instruction interpreter,with native464c50/464ca0/464cb0
initialization. All opcodes0..6 covered,including loop count0/1/2/7,delays0/1/4,
relative jumps-1/-2 and conditional-latch values0/1/2. Every tick verifies return,
active flag,delay,elapsed,loop counter,branch latch,instruction cursor and frame
pointer; inactive next call returns0. Pointers stride44; jumps relative to current
record,not absolute index. Opcode2 sets loop count;3 if unsigned count>0
decrements and jumps by arg records,otherwise falls through. Opcode4 jumps by
arg if latch20==0,otherwise clears latch and falls through. Delay check occurs
before consuming a batch of control instructions; a newly set delay does not
interrupt that same batch. Events/end/frame stop batch as previously observed.

18 additional fixtures exercise non-frame entry through actual465000 invoked
by464cb0. Programs loop-count command,event5,then frame0 or terminal6 show
initialization consumes event5 and continues until first frame or end; ordinary
464ec0 stops and returns event5 instead. Initialization leaves instruction cursor
after frame/end; a frame-start bank directly sets frame without advancing,
matching earlier mode0 tests. Thus initialization and regular stepping have
different event and cursor behavior. Fast-forward24/reset464d70,real loaded
animation programs and malformed/infinite-program handling remain unverified.
Decoded table bytes at464fdc are data,not instructions; evidence uses known
function entry and jump targets,not apparent disassembly through table.

## Animation reverse-count replay mode

ai-animation-replay-verification.json:30 native differential fixtures,same
engine hash/base,no doubles,actual464cb0 fast initialization and464ec0 fast
branch with464d70 reset/recursive ordinary stepping. Synthetic delay0/1/4,
loop0/1/3 and event0/2/9 plus3 negative opcode4 programs covered. Reference
executes plain native stepping explicitly; normal VM separately compared to
independent interpreter in ai-animation-control-verification.json. This test
validates replay orchestration,not an independent normal-VM implementation.

Fast init argument1 scans ordinary updates until active clears,event EXACTLY2,
or pre-update instruction is opcode4 with negative argument. It counts stepsL,
restores cursor/frame to before stopping update,forces active1 and stores total
2c=L,counter28=L-1,flag24=1. Events other than2 do not stop this scan. On each
fast update counter>0 decrements;counter0 wraps to totalL. It temporarily clears
fast flag,uses464d70 to restart instruction state,then performs counter ordinary
updates,returns last event (or0 for counter0),and re-enables fast flag. All state
fields0/4/8/c/10/14/18/1c/20 compare to explicit plain reinitialization and replay;
fast flag,total/counter separately checked. Event/end/negative-jump boundaries
match. The word fast is descriptive; actual behavior is descending-count replay,
not a speed multiplier. Production caller semantics and real animation banks
still need verification. Malformed/unbounded programs remain outside fixtures.

## Installed effect animation records, read-only native stepping

ai-animation-assets-verification.json:13 formal runtime Sprites/Effects0..12.ani
files,671 sequence entries with before/after SHA256 identical. Raw record bytes
staged into actual464c50/464ca0/464cb0/465000/464ec0,no doubled functions,engine
hash/base unchanged. Structural observation for all files:magic ANI NUL,declared
size at4 equals disk length,record count8,versionc=5,reserved10,index count14,
sprite basename bytes18..2b. Index table2c lengthindex_count*4,sorted first0/final
record count; remaining bytes exactlyrecord_count*44,all opcodes0..6. This is
empirical parser evidence,not native disk-loader equivalence. Last index acts as
terminal boundary in this interpretation;671 sequences are index_count-1 per
file. Sprite lookup/record rendering fields not consumed by tested VM path.

Ordinary first-event stepping after real initialization classifies270 sequences
with nonzero event,337 with repeated complete VM state before any event,and64
inactive during initialization. State cycle check uses48-byte VM state;iteration
budget10000, no sequence reached budget. Cycles are valid observed behaviors,
not automatic bugs:looping visual effects may never emit a prepare event and
spell directory may select different sequences. Exact animation-to-spell ID
mapping,loaded bank transformations and mode selection still required before
claiming any production prepare hang. No player process launched or files altered.

Read-only Ghidra functions-animation-loading export completed18 requests with
no missing functions,identifying534640/543970/543ee0/544350 as directory consumers
and helper464b30. These are consumers,not yet the file loader. Export names
remain provisional; native loader and spell mapping must still be located.

## Configured mode0 preparation using installed animation instructions

ai-configured-prepare-verification.json:12 whole prepare fixtures for21/39/44/52,
no doubles,same hash/base. Read-only installed CFG/effectani.cfg hashed before/
after; individual ANI hashes match previous asset evidence. Native callers use
directory6898d0+offset; config section ANI_offset/16 supplies AnimationNo and
AnimationFileRef. Python stages this inferred directory/bank manually with bank
index normalized0,raw ANI index/record bytes preserved. Native config/disk loader
mapping or transformations have NOT yet been verified,so interpretation is
conditional on this explicit staging,not a live production acceptance claim.

Cure21 offset4a0 ->ANI_74/EFFECTS3 animation14:31 updates,event1.
IronSkin39 offset220 ->ANI_34/EFFECTS5 animation9:17 updates,event1.
LuciferFarewell44 offset460 ->ANI_70/EFFECTS3 animation12:18 updates,event1.
BloodLust52 offset490 ->ANI_73/EFFECTS11 animation1:30 updates,event1.
All actual mode0 prepare methods measured those sequences at delays action14e
0/7/40;duration=updates+delay+5 except39 adds8. Submission flag resets in all.
These four configured sequences terminate rather than entering observed asset
zero-event loops. This narrows mapping candidates but does not validate every
spell mode/asset or conclude that no production prepare hang is possible.
Native loader identification remains required. Pointer sites534640/543970/
543ee0/544350 exported last turn are consumers,not loading constructors;
689494 reference in4e4270 is unrelated AllCreaturesLit config and discarded
as a loader lead. Player environment untouched.

## Whole native version5 animation loader4644d0

ai-animation-loader-verification.json:26 whole loader fixtures,13 installed
Effects ANI files,first load/reload,same engine hash/base. File open4a1120,
read59c359,close59c4c3,descriptor5b74d8,length59d9eb and allocation597880/free
5979b0 explicitly doubled using immutable input bytes. Native processing unchanged.
Bank+0c=0 excludes associated sprite loading. Whole loader is thiscall with
ret8,fixture passes filename and extra0; actual open uses ECX filename/EDX mode.
Verified instruction boundaries4644d0 and complete dispatch/tail paths before
emulation. Loader reads header44,header14*4 index bytes,remaining file bytes;
version5 stores remaining bytes directly without instruction conversion. Header
size must equal actual44+indices+remaining; sequence terminal boundaries require
opcode6 at index[i]*44-44. Successful sources pass all native checks.

Assertions compare header,index and EVERY instruction byte to source for each
load. Reload frees all3 prior buffers exactly once; only3 current allocations
remain. Open/close counts match and full source consumed. Before/after files
identical. This confirms earlier raw-record staging for version5 under modeled
successful file IO. OS file lookup/errors,associated sprite loading and failure
allocation/read handling remain unverified. Older version3/4 conversion and1/2
unsupported handling statically exported but not tested.

Read-only Ghidra functions-effect-config-loader recovers49c5b0 effectani config
loader plus4644d0 disk loader and464b90 helper. Native49c5b0 reads NumberofAnimations,
allocates16-byte directory entries and initializes114-byte bank array; ANI_N
AnimationNo and case-insensitive EFFECTSN mapping observed statically. Decompiled
register aliases around loop are unreliable; mapping writes require disassembly
and native test before replacing manual-directory caveat. Config loader whole
and sprite association remain required work,not established by disk loader test.

## Animation-loader failures and native cleanup

ai-animation-loader-verification.json now156 whole loader fixtures:26 prior
success/reload plus130 failure cases (13 files,initial or after good load,
open failure/header short-read/index short-read/record short-read/declared size
mismatch). Inputs corrupted only in emulator IO stream,never disk. Open/IO/CRT
remain explicit doubles; native loader branches and cleanup464480 unchanged.
All failures return0. Reload always releases old buffers before attempted open;
open failure leaves all3 pointers0 and has no handle to close. Short header
leaves1 allocated bank pointer;short index2;short records and size mismatch3.
Each open-success failure closes handle exactly once. Residual partial buffers
are bank-owned,not automatically identified as leaks.

Actual464480 invoked twice after ALL156 fixtures. First call frees every remaining
allocation once and nulls bank0/4/8;second call frees nothing. Full allocation
ledger matches. This validates destructor behavior,not that production error
callers reliably invoke it. Production failure dispatch remains required;alloc
failure/associated-sprite IO and old versions are still outside this matrix.
Instruction boundaries464480..4644c7 verified before cleanup invocation. Before/
after hashes of all installed source files unchanged;player runtime not operated.

## Native effect config animation/file mapping

ai-effect-mapping-verification.json:282 native49c8c3..49c9aa slice fixtures,
222 installed CFG/effectani.cfg entries plus60 boundary cases,same hash/base.
AnimationNo API result/text provided at slice entry;AnimationFileRef Win32 API
explicitly doubled. Native59c5a4 integer conversion,59de2f decimal formatting,
59db40 case-insensitive ASCII C-locale comparison unchanged. Frame+14 points to
directoryentry+8;frame+18 is number of files13. Nonempty animation text writes
entry0;otherwise leaves it unchanged. Loop builds EFFECTS plusdecimalindex,
compares against file reference and writes entry4 on equality. Zero/negative file
count or unmatched/empty reference preserves priorentry4. Edges include empty,
-1/0/101 animation,case-mixed files0/12,out-of-range13,bad/empty,count0/1/13.
Native slice does not validate animation bounds or clamp numeric values.

All222 entries'animation/bank mappings executed,including previously tested
four spell preparations. verify_ai_configured_prepare now asserts matching
engine/config hashes and native mapping results before staging. Twelve prepare
cases rerun pass;manual memory allocation/staging caveat remains for whole
initialization,while these two fields'conversion semantics are now native-tested.
Printerentry8/dataentryc and whole config allocations/bank initialization/file
loading are still pending. OS profile parser semantics are doubled,not verified.
Source config and assets unchanged. Ghidra loop variable aliases from49c5b0
were not relied on:disassembly from known entry established49c8c3 boundaries,
actual writes [esi-8] and[eax-4] relative toentry+8.

## Effect directory printer and auxiliary data fields

ai-effect-render-fields-verification.json:262 native49c9aa..49ca92 fixtures,
all222 installed effectani.cfg entries plus40 edges,same hash/base,Win32 profile
text API explicitly doubled,actual59db40 ASCII C-locale compare and59c5a4 integer
conversion unchanged. ESI=directoryentry+8. SpritePrinter exact case-insensitive
names map NORMAL->31,TRANSPARENT->2,TRANSPARENT25->3,TRANSPARENT50->4,
TRANSPARENT75->5,storedentry8. Other nonempty or missing strings preserve existing
field;no fallback assignment in this slice. Data1 nonempty parses signed integer
and storesentryc;invalid nonempty text0,missing preserves existing. Fixtures
mixedcase,suffix mismatch,bad/missing strings and data empty/0/-1/99/invalid.
Entry0/4 remain unchanged. Actual render dispatch/colour-key meaning outside
scope;enumeration names recovered from literal comparisons,not inferred pixels.

Disassembly49ca92..49caa4 advances destination by10hex and loops over declared
animation count,confirming16-byte directory stride shared with previous mapping.
Thus all four directory fields now have native writing evidence for222 actual
configured entries across two separate slices. This is not whole49c5b0 config
initialization:allocation/constructor failure,bank loads,printer invocation,
OS text parser and production reload still required. Scope ledger preserves
that distinction. Installed files hashed unchanged.

## Whole effect configuration through native spell preparation

`ai-effect-config-loader-verification.json` verifies whole preferred-VA49c5b0
on engine SHA25642f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da,
image base400000. Seven offline fixtures use all222 installed effectani.cfg
entries and13 actual version5 Effects ANI banks. Win32 cwd/profile APIs, CRT
allocation/file IO, and sprite resource acquisition57d310/binding57d690 are
explicit doubles. Native integer/decimal/case conversion,59c441 array construction,
49cc40 sprite initialization,49cc70/464460 bank initialization,464b90 association,
and4644d0 ANI transformation execute unchanged. Allocations are deliberately
poisoned with A5 to distinguish assigned fields from assumed zero defaults.

Directory pointer is owner+438,16 bytes per entry; bank pointer owner+8 with
114hex stride; sprite array global6de4dc has24hex stride. Both arrays carry
count prefixes at-4. NumberOfEffectsFile is clamped to at least1. All four
directory fields match the installed configuration. Every loaded bank header,
index table and record buffer matches source bytes. Source hashes checked before
and after; no player process or configuration is changed.

Important structure correction:464b90 stores the associated sprite element at
bank+110hex, not bank+c. Constructor464460 initializes only0/4/8/c; constructor
argument0 makes+c zero here. Until association,+110 retains poisoned allocator
contents in these fixtures. This is an initialization observation, not a proved
production defect. Earlier+c=0 loader fixtures remain valid for that constructor
field but must not be described as eliminating the separate+110 association.

Success outputs feed actual globals6898d0(directory)/6894a0(banks) without
normalizing bank indices. Twelve whole mode0 prepare calls for Cure21,IronSkin39,
LuciferFarewell44,BloodLust52 at delays0/7/40 reproduce31/17/18/30 ticks to the
first event1, respectively, plus action delay and5(or8 for IronSkin). No additional
prepare/VM doubles. This closes the previously manually staged directory/bank
gap for those four paths, subject to the declared OS/sprite resource boundaries.

Sprite acquisition failure or ANI open failure at index0/6/12 returns0. Already
loaded banks remain intact, unvisited banks keep constructor-null0/4/8, and
allocated directory/arrays remain owned at return. No automatic teardown is
executed inside this failure path. This does not establish leakage: production
caller cleanup remains unverified. Reloads, allocator failure, OS profile/IO,
sprite rendering,other prepare actions/modes and broader AI coverage remain open.

## Danger contribution and decision consumers

`ai-danger-contribution-verification.json`, same engine SHA256 as above and
preferred image base400000:257 whole529e40 fixtures,257 whole52a0f0 integrations,
720 whole52a3a0 fixtures. These execute native466870 owner-wizard lookup,
40e250 movement descriptor construction,coordinate wrappers,40a6b0 distance,
59bee0 numeric conversion and5075f0 fallback maximum-health path. Only542810
reachability is doubled in contribution/relative-score fixtures; low-health
fixtures have no doubles. Synthetic wrapped-coordinate extents4096 and two
294hex-stride cells are staged. No live game or player data is touched.

529e40(unit,cellIndex,owner) first reads the owner's profile relation byte
+18+unitOwner; zero returns0. Missing owner wizard also returns0. Wizard-like
definition types0/24/25/26 use a generic movement descriptor. Other tested type1
selects generic or unit-derived movement parameters via definition+34 and unit
state conditions. Failed reachability returns0. With admitted nonnegative test
inputs, contribution before the final factor10 is the truncation of
`20*((unit.e8 & 0xffffff00)+unit.91e)/(10000+2304*sqrt(distanceSquared))`.
The value is then halved with signed truncation if unit+7c is nonzero, followed
by factor10. Actual e8/91e producer meanings are still pending; fixture variable
`energy` names the supplied raw e8 value only. Distance is native wrapped
coordinate distance; fixtures use x0/100,y0,z0 without crossing a wrap boundary.
This is a verified fixture-domain formula, not a claim about overflow inputs.

52a0f0(unit,cellIndex) obtains that unit owner's wizard; missing or self wizard
returns float constant5c5bb0. For a distinct wizard it calls real529e40 and returns
`(contribution-unit.92a)/(unit.922+1)` with signed integer arithmetic before x87
division. Fixtures verify missing and distinct wizard,including failed contribution
gates,with baseline92a=50 and922=99. Self and singular denominator pending.

52a3a0 returns1 only for definition types0/24/25/26,unit+7c zero, unsigned current
health e4 <= unsigned half of signed max-health result, and signed
`unit.922/(unit.926+1) > 0.5`. The comparison is strict: equality does not pass.
Tests include health49/50/51,max100/101,danger0/1/2/100,safety0/1/99 and excluded
type1. Maximum health uses the actual5075f0 owner=-1/definition+18 fallback.
Profile-equipped maximum-health and negative/overflow/singular cases remain open.

Static41d270 shows529e40 output stored per unit+92a and added to manager+120a9,
eventually published to wizard+926. Static41a060 publishes manager+12084 to wizard
+922. These full producer loops and map/accumulation rules are not established
by the present consumer tests. Similar offsets in unrelated wizard/template
configuration objects must not be treated as the same runtime fields.

## Danger publication budget, continuation and player rotation

`ai-danger-publication-verification.json`, same hash/base:144 native publication
slice fixtures(41d3a2..41d476 or early epilogue41dc10),184 continuation rounds.
Native542be0 publishes seven bytes per294hex-stride cell from temporary28c to
player destination24c+7*owner. Native542ba0 clears the same seven temporary
bytes; actual466870 identifies the owner's wizard. Only4202e0 per-cell finalizer
is doubled with distinct seven-byte outputs; its semantic formula remains open.

Owner profiles are active,+4 zero,+c valid. manager120a1 is the cell-finalization
cursor; each invocation processes at most32 cells. If cells remain, the native
path returns via41dc10,retains that cursor and120a9 accumulator,does not publish
cell data or overwrite wizard926. A later invocation resumes at the retained
cursor. Once all cells are finalized,120a1 becomes0,542be0 publishes the owner
map,wizard926 gets120a9,542ba0 clears temporary map data,then120a9 becomes0.
Exactly32 remaining cells complete and publish in that invocation;33 leaves
one cell for the next. Fixtures cover owners0..7,cell counts0/1/31/32/33/64/65,
initial cursors0/middle/end. Cursor-at-end still publishes staged temporary data.
These are function-call budgets; actual scheduler/frame frequency is unverified.

162 no-double rotation-slice fixtures41d476..41d505 or41dc10 verify up to eight
player-selection attempts per invocation using stack-local38. Starting owners
-1..7,eligible masks0/1/128/255/85/170,and prior attempts0/7/8 establish wrap8->0,
skip inactive slots,and first eligible selection within remaining budget. On
selection,manager1209d resets0 and120a5 receives first unit pointer from global
6def58 when6def5c is nonzero. Exhausted budget returns without resetting those
unit fields. Restart flag12098,profile+c invalid/+4 nonzero combinations,zero
unit count and contribution processing remain separate unverified paths.

These fixtures intentionally execute known-entry-derived instruction slices,
not whole41d270. Full unit accumulation,4202e0 finalization and map consumers
are needed before describing the entire danger subsystem as recovered.

## Native cell finalization and persistent spell effects

`ai-danger-cell-effects-verification.json`,same engine hash/base,880 whole4202e0
fixtures without doubles. Synthetic circular effect list global6898e4 uses
node+8 effect pointers; real429b50 iterator dereference,coordinate normalization
and419920 wrapped-distance radius comparison execute unchanged. Effect+4c is
the spell ID; radius is read from6b13c9+721*ID; effect+8/c/10 coordinates and
cell+4/8/c coordinates feed the spatial test. Profile owner+18+effect212
relationship byte must be nonzero. The tested relationship values0/1/255 prove
zero/nonzero gating,not the diplomatic label of that table.

Within inclusive distance<=radius, ID69 adds30 to cell28f,ID70 adds20 to290,
ID91 adds25 to291. Each byte saturates255; unrelated type68 is ignored. Tests
use distance9/10/11 with radius10,lists of1/3 repeated effects,empty/mixed lists,
initial bytes0/224/230/235/250/255 and owner0/7;extra mixed/empty cases cover all8
owners. The complete294hex-byte cell comparison confirms no other byte changes.
Installed spells.cfg sections identify69 as Totem of Life,70 as Guardian,91 as
Totem of Fear,with configured Radius SMALL/SMALL/MEDIUM. These section names
provide static identity context; actual radius parsing/loader mapping is not
proved by fixtures with staged radius10.

Publication verifier now adds96 no-double integrations using all three real
effect types through actual4202e0,542be0,542ba0 and466870. Owners0..7,counts
0/1/32/33/65,cursors0/middle/end preserve the32-cell continuation boundary and
publish incremented values then clear scratch. Map metadata6eaf0c(index bound)
and6eaf10(finalization loop bound) are both explicitly set to count; previous
doubled-finalizer fixtures did not require the former. This closes the finalizer
test-double gap for these effect-list fixtures,not whole41d270 unit accumulation,
effect creation/lifetime/ownership,map consumers or scheduler invocation timing.

## Danger unit eligibility and contribution cursor commit

`ai-danger-unit-cursor-verification.json`,same hash/base:256 no-double native
41d2be..41d505/41d3a2 slice cases. The current profile is active,+c valid,+4 zero.
The fixed scan boundary is manager1209d==125 (7dhex),unit stridee4bhex. Candidate
requires unit+4 nonzero,e4 health nonzero,and de7 cell index !=-1. Same-owner
units bypass foreign-owner relationship conditions. Foreign units require both
their profile+28+currentOwner and+18+currentOwner bytes nonzero. Only zero/nonzero
meaning established;do not assign diplomatic/visibility labels without producer
evidence. Fixture variable `visibility` supplies+28 but is not a recovered name.

If rejected,manager120a5 advances e4b and1209d increments,continuing scan in the
same invocation. At boundary125 it enters publication/player transition41d3a2.
If accepted it enters unit-evaluation41d505 without advancing the cursor. Tests
stage125 uniform slots and vary all gates,start0/1/124/125;complete unit-array
snapshot comparison confirms filtering does not mutate them. Actual unit-count
global is not consulted by this scan slice;valid initialization/lifetime remains
necessary separate evidence before alleging out-of-bounds production behavior.

48 native41dba3..41d2b8/41dc10 suffix cases double only529e40 return value. Real
commit logic stores returned contribution in unit92a,adds it to manager120a9
with32-bit wrapping,advances120a5 and1209d,and increments invocation-local3c.
At four processed units it returns41dc10;otherwise continues41d2b8. Inputs
0/10/-1/INTMAX,totals0/100/UINTMAX and prior processed0..3 cover stored words and
wrap. Negative contributions are injected arithmetic-domain fixtures,not proved
ordinary529e40 outputs. Earlier real529e40 tests validate that routine separately;
these suffix tests do not prove full producer integration or map accumulation.
Skipped units do not increment this processed counter;the32-cell budget belongs
to later finalization and the8-attempt budget to player rotation.

## Map-channel accumulation over selected cell trees

`ai-danger-map-accumulation-verification.json`,same engine hash/base,512 native
slice fixtures,no doubles.256 generic41db06..41dba3 fixtures traverse actual
42d7d0 tree successor over synthetic balanced cell trees rooted at manager1208c.
Node+c holds cell pointer;sentinel global5faf20. Each visited cell28c gets signed
32-bit addition of supplied contribution,then clamp0..255. Cell28d gets the same
addition only if cell20c==0 or unit104!=0. Initial0/128/250/255,deltas-300/-1/0/
1/30/255/300/INTMAX,unit1040/1 and1/3/7/31-cell trees cover both saturation ends,
unchanged conditional channel and signed overflow. Complete cell byte comparisons
and tree snapshot comparisons verify only expected channels change. Negative
and extreme deltas are injected arithmetic domains,not established normal inputs.

256 additional41d836..41d8a3 fixtures use actual tree walk for auxiliary channel
28e. Unit114==0 skips it;otherwise global6bcad6 is added and clamped identically.
Entry ESI255 and EBP0 are explicitly staged because the clamp upper/lower values
are inherited from earlier code. These fixtures do not establish every producer
of those registers. Unit114 semantic name and6bcad6 configuration source remain
open. No other cell byte changes in these fixtures.

Selection/tree construction and contribution normalization preceding these loops
are separate unresolved work. This evidence establishes arithmetic/tree traversal
for the identified slices;it does not claim all map channels or whole41d270 have
been recovered. Existing publication tests independently establish seven-byte
copy/clear,including these channels,without proving a complete world-to-map path.

## Contribution normalization and complementary map-path gates

`ai-danger-normalization-verification.json`,same hash/base:1152 no-double first
slice41d505..41d5af/41d8a3 fixtures and1152 separately staged second gate
41d8a3..41d8fd/41dba3 executions. Actual411e50 returns1 for definition types
0/24/25/26. The normalizer is exactly unsigned arithmetic:
`floor(u32(20*u32((unit.e8 & 0xffffff00)+unit.91e))/10000)`.
Disassembly uses high-half unsigned multiply by d1b71759 then shift13;tested
payloads including UINTMAX prove unsigned floor and prior wrapping,not signed
truncation or division before multiplication. Unit de7=1 resolves cell base+294
through6eaf08/6eaf0c;normalization stored local34.

Let W mean wizard-like type with unit7c==0;D mean definition34!=0;O mean
unit a8==18 and108!=0;A mean unit114!=0. First map path41d5af is admitted by
`W || (D && !O) || A`. Second41d8fd is admitted by `!W && (O || !D)`.
Thus primary conditions are complementary;A can additionally admit first path
while second remains admitted. Unit114 does not suppress second path. Tests
cross all six type IDs0/24/25/26/1/2,status0/1,mode18 flag,108,definition34,114
and six raw e8/91e payloads. Field semantic names and configuration defaults
remain unestablished;do not call definition34 an attack or movement capability
solely from these branches.

Second gate is executed with manager/local1c restaged;intervening first-path map
tree construction is not run here. These gates plus earlier accumulation slices
do not establish complete normalization-to-map integration. Earlier auxiliary
clamp fixtures stage ESI255 explicitly;its whole-path producer still needs proof.

## Integrated first map path: topology selection, tree and accumulation

`ai-danger-first-map-path-verification.json`,same engine hash/base:288 integrated
41d505..41d8a3 fixtures. Only597850 CRT allocation is doubled;native normalization,
411e50,42abb0 unique pointer insertion,42d540 red-black balancing,42ba50 returned
iterator copy,42aba0 and42d7d0 execute unchanged. Fixtures stage wizard type0,
status0,empty manager12088 tree,one valid unit cell and four map cells.

The first path inserts the unit's own cell,then examines18 adjacency records
per cell,stride1chex beginning cell+10. Active record+0 nonzero plus either
record+8 nonzero/record+9 signed positive or record+b nonzero/record+c signed
positive permits record+4 destination index. Every admitted first-hop cell is
inserted and its18 records receive the same test;admitted second-hop cells are
inserted. It stops after two edges,not an unrestricted flood fill. Chain0->1->2->3
selects0/1/2;diamond0->1/2->3 selects0/1/2/3 once;disconnected selects0 only.
Gate values0/1/255 demonstrate signed positive comparison (255 rejected),and
both adjacency capability channels are exercised. Invalid indices remain open.

Pointer-key uniqueness suppresses repeated destination3 in diamond paths.
Fixtures verify in-order selected pointers,count/allocated nodes,parents,root
blackness,red-parent rule and equal black heights. Contribution from real
normalization adds to28c and28d for every selected cell;unit114 additionally
adds global6bcad6=30 to28e. Raw values0/256/8192/UINTMAX,initial channels0/250,
unit1140/1 cover zero/positive/saturation. Complete cell-array comparison checks
topology and unselected cells remain unchanged.

Exit ESI255 and EBP0 are now observed from the actual first path,closing their
staging gap for the earlier auxiliary accumulation fixtures on this domain.
Existing nonempty-tree cleanup,other unit classes/conditions,second-path graph
selection,cell creation/configuration and whole41d270 producer remain open.

## Integrated second map path: unit descriptor and one-hop selection

`ai-danger-second-map-path-verification.json`,same hash/base:2304 integrated
41d505..41dba3 fixtures,onlyCRT597850 allocation doubled. Type1,definition34=0,
unit114=0 select second path. Actual normalization,411e50,40e250 descriptor,
42abb0/42d540 tree insertion/balancing and42d7d0 successor run unchanged.
Fixture descriptors use definition+c requirement1/2,definition+8 index1,
definition44 mode0..3,unit1040/1. Unit723 and5ec special flag inputs are zero.

The path inserts own cell unconditionally,then tests its18 adjacency records.
Admitted destinations are inserted without expanding their neighbors. Thus
chain0->1->2->3 selects0/1,diamond0->1/2->3 selects0/1/2,disconnected0 only.
Unique pointer tree and red-black invariants are checked as in first path.

Record+0 must be active. In cell-relative coordinates,admission occurs if
flag18!=0 and signed byte18+descriptorIndex >= requirement;or unit104!=0 and
flag1b!=0 with byte1b+index >= requirement. Otherwise mode2 tests flag1e and
byte1e+index >= requirement,mode3 flag21 and byte21+index >= requirement.
Mode1 tests flag24 and `byte26+index <= requirement <= byte24+index`.
Mode0 has no fallback. Signed comparison is established with threshold bytes
0/1/2/255;mode1 lower bounds1/3 cover accepted and rejected intervals for
requirements1/2. All5 channels,all4 modes,graph shapes andunit104 combinations
are crossed. Field design names remain pending;the description uses offsets.

Every selected cell28c receives normalized16 from raw e8=8192. Cell28d receives
the same only if cell20c==0 orunit104!=0;all cells are compared byte-for-byte.
This connects prior conditional accumulation evidence to actual descriptor-
selected trees. The verified first/second path coverage difference is two hops
versus one hop;it does not yet explain intended game design or all unit abilities.
Wider descriptor indices,other state/type/114 combinations,nonempty-tree cleanup,
full41d270 contributions/rotations/publication and caller timing remain open.

## Repeated first-path evaluation and old selected-tree cleanup

First-map-path report now additionally contains72 three-round fixtures(216
native path executions),unit starts0/3/0,graphs/gates/channels/initial/aura crossed.
Actual42e440/4298e0 form full iterator range and42fde0/42acc0 erase old nodes;
only597850/597870 CRT allocation/free are doubled. Every previous live allocation
is freed once before new selection;remaining allocations equal reachable new
tree nodes,red-black invariants and exact pointer selections hold each round.
Complete cell-array comparisons establish accumulation across evaluations:
selected-tree cleanup does not clear cell channels. Publication clear is a
separate operation verified earlier. Current selected nodes remain owned at
fixture end;this is intentional pending next evaluation/manager teardown.

Fixture correction:initial empty header color+10 must be0(red),nil color1(black).
Previously staged header1 sufficed for insertion-only paths but fails native
header-aware predecessor logic42e440 during full-range cleanup. Disassembly
427901..427930 creates black nil,42794d..42796e initializes header+10=EBX0,
parent=nil,left/right=self in constructor427810. Both first/second map verifiers
now stage header0 and all288/2304 initial cases rerun pass. The failed black-
header fixture was a test setup error,not evidence of stale production selection.

Actual first-path reuse covers oldtree cleanup and cumulative byte arithmetic on
the stated wizard domain. Second-path reuse,cross-path transitions,manager-owned
tree construction/destruction,full125-unit scan/publication and caller timing
remain necessary open integration work.

## Whole danger producer across calls

`ai-danger-pipeline-verification.json`,same engine hash/base:30 whole41d270
fixtures,240 entry-to-return native calls.125-slot unit pool,active counts1/2/4/
5/9,cell counts4/33,one active role0 owner0 profile,three domains type0/status0,
type1/status0 andtype0/status1. Native restart12098,unit eligibility,normalization,
first/second graph selection,unique red-black tree creation/cleanup,529e40
contribution/commit,player rotation,4202e0 empty effect list,542be0 publication,
542ba0 clear and466870 lookup run unchanged. OnlyCRT597850/597870 allocation/free
and542810 positive reachability are doubled. This supersedes the integration gap
for these synthetic domains;not every branch of41d270 is thereby verified.

Independent event oracle checks unit indices in order across invocation resumes,
raw8192 yields contribution160(status0) or80(status1),manager120a9 before each
commit and wizard926 at each completed publication. Full seven scratch-channel
bytes for every map cell are checked after every unit evaluation. Type0/status0
selects cells0/1/2 in chain0->1->2->3;type1/status0 andtype0/status1 select0/1.
Both selected channels accumulate16 per unit independent of the contribution
status halving. At publication,expected owner-map channels equal min(255,16*active
units),others0,scratch cleared,accumulator0,wizard926=160(or80)*active units.
Each fixture publishes at least twice across eight calls;reachability-call count
matches committed units and remaining tree allocations equal manager12094.

Per-invocation processed-unit count never exceeds4. Cell count33 exercises
finalization continuation beyond32 and retains pending contributions until
publication. Restart at first call is included;mid-cycle restart is still open.
The event oracle does not assume a fixed number of frames per publication.
For the all-type1 domain,profile wizard pointer is deliberately staged to a type1
unit to isolate native path combination;this is not evidence that real player
profiles normally point there. Native profile construction and actual scheduler
timing remain separate requirements. Other owners/relationships,real reachability,
persistent effects during this whole producer,restarts/save/network cases remain
open and coverage remains incomplete.

## 542810 is greedy spatial progress, not complete reachability

`ai-greedy-reachability-verification.json`,same hash/base:240 whole542810 cases,
no doubles,preallocated native vector. Five directed topologies(straight chain,
route requiring an away step,equal-distance branches,equal-distance first step,
disconnected),all4x4 start/goal pairs,adjacency gate0/1/255. Descriptor index1,
requirement1,mode0,wrapped extents4096,z0. Actual coordinate differences,vector
clear/insert and adjacency threshold logic execute unchanged;all cell bytes
remain unchanged. Gate255 is signed negative and rejected.

The routine clears its scratch vector at map-object+6a0d,appends start index,
then iterates from current cell. Among descriptor-admitted neighbors it chooses
the one with smallest squared distance to goal strictly below current distance.
Tied closest candidates retain the first encountered because only strict
improvement updates selection. It appends that cell and repeats. If no improving
neighbor exists,it returns0 and output remains-1,even when a directed route
exists via an equal-distance or initially farther cell. It has no backtracking
or complete BFS/A* in this function. This is algorithm semantics established
offline,not by itself a newly proved gameplay bug.

On success it returns1 and outputs vector index floor((pathLength-1)/2),the
middle cell on the recorded greedy path. Same start/goal succeeds with one-cell
path. Failed calls retain their partial path in scratch. Positive topology oracle
and output/vector assertions cover all fixtures. Heights,wrapped boundary crossing,
descriptor modes/indices beyond current domain,signed distance overflow,vector
growth and invalid input behavior remain open.

Whole41d270 pipeline verifier now runs actual542810 instead of forced success.
All30 fixtures/240 calls rerun pass;onlyCRT allocation/free remain doubled.
Those pipeline endpoints are same-cell,with preallocated scratch vector. This
closes their positive-return boundary but does not prove nontrivial spatial
greedy paths inside the producer. Previous documentation calling542810 a
reachability test is descriptive call-site shorthand and must not imply complete
topological reachability. Full AI/pathfinding behavior is not changed.

## Spatial and persistent-effect domains in the whole producer

Whole41d270 verifier now covers62 fixtures/496 native calls:previous30 same-cell
cases,24 spatial cases and8 with persistent effects. OnlyCRT allocation/free are
doubled;actual542810,529e40,4202e0 and all producer operations execute unchanged.
Spatial cases alternate unit cells index%4 with x0/10/20/30,goal wizard cell0,
directed reverse chain3->2->1->0 or away chain0->1->2->3. Per-unit independent
oracle combines actual topology expectation,first/second path depth and
`trunc(163840/(10000+2304*distance))`,halved before factor10 if status nonzero.

Reverse chain yields type0/status0 contributions160/40/20/20 for cells0..3;
away chain yields160/0/0/0 because greedy progress fails from nonzero cells.
Type0/status1 applies integer halving before factor10. Each actual return,total
before commit,published wizard926 and complete seven-channel scratch/map bytes
are checked. Importantly,failed542810 zeros the per-unit92a/wizard926 contribution
but does not suppress local map28c/28d accumulation derived from normalization
and selected adjacency tree. These are distinct native computations,not equivalent
representations of a single danger number.

Eight effect integrations stage69/70/91 at origin,radius10,active5 units,4/33 cells,
type0/status0 ortype1/status0,same-cell orreverse topology. Actual4202e0 adds30/
20/25 to28f/290/291 only within inclusive spatial radius;all published channels
are independently compared and scratch cleared. In33-cell tests cells beyond
index3 have default origin coordinates and correctly receive effects. Finalizer
continuation across32 remains included. Staged effects/radius/profile pointers
do not prove real effect spawning/configuration/lifetime or live player acceptance.
Other owners/relations,restarts,save/network and scheduler invocation remain open.

## All owner segments and interrupted-cycle restart

Wholeproducer report now has110 fixtures/880 entry-to-return calls.48 additional
first/secondpath spatial-effect fixtures cross owners0..7 and restart conditions
none/after4units/after32of33 finalizations. Each scene has one active role0 profile
at the chosen slot,125 units with5 active,reverse spatial chain,three persistent
effects and33 cells. Native fullscan/player rotation automatically reaches that
slot;actual466870 uses its profile+c unit0 pointer. Tests set chosen profile+18+
chosenOwner for contribution and+18+effectOwner0 for effects,without inferring
relationship labels. OnlyCRT allocation/free remain doubled.

At every completed publication,each of the seven bytes at cell24c+7*owner is
checked independently;all seven other owner segments remain zero. Own unit
contribution sequence,index resumes,pending totals,seven scratch bytes and tree
allocation ownership remain checked as before. This is allslot addressing and
single-active-owner rotation evidence,not yet multiple active players sharing
the producer's temporary buffers.

Restart fixtures set manager12098 at an invocation boundary. After first call,
4units have been processed andcellcursor0. After second call,all5units have been
processed and32of33cells finalized,with persistent-effect bytes partially added.
Report records both discarded cursor values0/32 and unfinished totals. Native
restart clears scratch,sets playercursor-1,cellcursor0,total0 and rescans from
unit0;subsequent percommit comparisons andpublication prove no abandoned unit/
effect contribution survives. Previous selected-tree allocations are cleaned
normally when reevaluation begins;no double frees/stale ownership observed.
Unit92a and prior published maps are outside the temporary reset claim;production
save/event producers of12098 and restart timing still require separate recovery.
Multi-active-player relations,save/network and scheduler timing remain open.

## Two active owners sharing scratch, asymmetric table directions

`ai-danger-multiowner-verification.json`,same engine hash/base:32 whole41d270
fixtures/640 calls. Owners0/7 active role0 with separate wizard pointers unit0/1;
seven active wizard-type0 units alternate owner0/7 in125 slots. Map4/33 cells,
same-cell contributions andfirstpath chain,three persistent effects owner0.
All4 cross-owner+18 masks andall4 cross-owner+28 masks are tested;diagonal+18=1.
OnlyCRT alloc/free doubled;all native producer,greedy,contribution,map effects,
rotation,continuation/publication/clear execute unchanged. Each fixture publishes
each owner at least twice across20 calls.

Per-owner independent oracle computes admitted unit sequence:
own units always pass;foreign source ownerS requires both profile[S].18[E]
andprofile[S].28[E] nonzero for evaluated ownerE. Once admitted,529e40 tests
profile[E].18[S],the reverse direction,for contribution. Thus asymmetric matrices
can admit a foreign unit into localmap accumulation while contribution92a is0.
Persistent effectowner0 likewise tests evaluatedprofile[E].18[0]. This distinction
is actual native table access semantics,not a claim that real gameplay normally
uses asymmetric relations or that their design labels are known.

At every commit,unit index/returnvalue/accumulator andall scratch channels match
the current owner's oracle. At every publication,chosen wizard926 matches its
expected total,eight owner-map segments match each owner's last completed cycle,
other inactive segments remainzero,andshared scratch is cleared. Previously
published otherowner data survives the new publication. Selected-tree ownership
and4 processed-unit invocation budget are checked across returns. No cross-owner
contamination appears in these domains. Real profile/relationship initialization,
human/computer role meaning,network variants andscheduler caller remain open.

## Profile reset and symmetric relation mutators

`ai-profile-defaults-verification.json`,same hash/base:24 whole465440 reset
fixtures and288 whole465500/465570 setter fixtures,no doubles. Profiles at643a80
stride154hex;completeaa8-byte array/tail snapshots verify writes and preserved
bytes. Reset tested every slot with prior fills0/A5/FF:fields0/4/8 become0,
c/10/14 become-1,all8 bytes18..1f become1,20..27 and28..2f become0,and eight
words30..4f become0. Name50 andremainingprofile fields are untouched by reset.
This is direct default evidence;role4 meaning remains unassigned.

465500(thisProfile,otherSlot,value) writes relation18[other] and mirrors the
same byte tootherProfile18[thisSlot],unlessotherSlot==thisSlot.465570(thisProfile,
value) does the same for all7 other slots. Both use global5fbf28 toderive slot
index andotherprofile address;value truncates tobyte. All8x8 pair cases andall8
alltarget cases with values0/1/255/256 comparecompleteprofiles;selfbytes remain
priorA5. These two writers preserve offdiagonal symmetry but do not initialize
self orproveeverywriter/import/save path preserves symmetry.

Static initializers4661c0/466420/4665b0 also contain direct symmetric18table
writes.4665b0 sets profile0+4=1 andadditionalprofiles+4=0 fromname setup,while
466420 sets allcreatedprofiles+4=1;this is provisional role-source context,not
yet full-native initialization evidence or confirmedhuman/computer labels.
20/28table meanings,setters/event producers andsave/network load remain open.
# Player selection and initializer verification checkpoint

Engine SHA256 `42f2aac7ee8f61c000f85b92ee6d6afa42f2dcfcdd95188d55f041bac8a517da`,
preferred base `0x400000`. `verify_ai_profile_selection.py` verifies 300 whole
`4667c0` calls without doubles and 108 whole `466420` calls with only CRT
`59c1fd` sprintf doubled. Complete `0xaa8` array snapshots, returns, stack
cleanup and global pointer writes are checked; no player files or process touched.

`4667c0(this, selected)` resets `this+aa0` to -1 before validating selected
0..7. For valid inputs it considers only profiles with both +0 and +4 nonzero:
selected gets +8=1 and other eligible profiles +8=0; ineligible profiles preserve
+8. Return is whether aa0 differs from -1. Eligibility reads through ECX, while
+8 writes use fixed `643a80`; tests use that same base. Caller alias requirements
and alternate-base behavior remain open, so this is not a general array API.

`466420(this,count,selected)` writes global `5fbf28=this`, resets all eight
profiles via actual `465440`, then sets aa0=-1 and aa4=0 even for invalid inputs.
Valid count is 1..7, selected is 0..count-1. Created profiles get +0=1, +4=1,
formatted name copied at +50, and index at +150. Each created profile clears
its offdiagonal +18 relationship bytes in both directions against all eight
slots; diagonals remain 1. It invokes real `4667c0` to mark selected +8.
Untouched name tails and inactive-slot fields remain preserved as reset specifies.
Return is AL boolean, callee pops 8 argument bytes. sprintf fixture output checks
copying and slot order; actual localization/formatting is not covered.

An additional 24 whole `4665b0` no-double fixtures verify all eight presence masks
of global label slots 1..3 at `658f10+307*slot`, with three poison fills. It resets
all profiles, creates local slot0 with +4=1/+8=1, then creates non-sentinel slots
1..3 with +4=0/+8=1. Sentinel comparison uses global `6ead98`. Names are copied,
+18 relations cleared symmetrically for created slots, but +150 is preserved.
Its final `4667c0(0)` leaves foreign +8=1 because their +4=0 makes them ineligible
for selection updates. Thus +8 alone cannot identify the locally selected player.
These are synthetic label fixtures, not evidence of actual campaign configuration
producers or localized content; real `465440/466a80/4667c0` execute throughout.

Fourth initialization path `465c60`, precise role +4/+8 meaning, relationships
+20/+28, label producers, save/network writers and caller contracts remain open.

## Global-mode initializer and AI admission

`verify_ai_profile_global_initializer.py` adds 432 whole native `4661c0` calls
for the same hash above. Only sprintf is doubled; 108 mode1 cases never invoke
that double. Full profile snapshots, return AL, stack and global pointer checked.
It resets all eight slots first. When global `6e1f0c=1`, it ignores count/local
globals (including invalid values), creates slots0/1 with +4=0/+8=1, copies names
through `5c5c54/58`, and sets +150 to1/2. aa0 remains -1.
For other modes, global `656630` must be1..7 and `656634` within that count.
Created profiles have +4=0/+8=0 and +150=slot. Actual `4667c0` consequently cannot
select any eligible slot, returns0 and leaves aa0=-1, yet initializer returns AL1.
Invalid inputs return AL0 after reset. Synthetic names verify copying, not actual
localized resources. This observed distinction is not by itself a production bug.

Verified disassembly `470a93..470ae3` dispatches all four initializers with fixed
ECX=`643a80`: nonzero `6e1f0c`→4661c0; otherwise nonzero `68991c`→466420(global
count/local); otherwise `689920=1`→4665b0; all other cases→465c60. Thus this caller
satisfies fixed-global selection aliasing. Whole470950 and all other callers are
not verified. 465c60 reads INI configuration via Win32 APIs and remains open.

`verify_ai_unit_admission.py` executes native `416590` gates in 3072 fixtures:
2904 refused calls run to native return; 168 admitted calls stop at41660c before
group scanning. No doubles. All eight valid owners are covered. Admission requires
profile+c != -1 OR unit+8e5 !=0; profile+4=0; unit+704=0; unit+a8 !=22; and either
signed global mode<=1 OR owner equals `656634`. Complete manager/unit/profile
snapshots remain unchanged. In particular +4 nonzero suppresses this AI admission
path; modes>1 admit only the configured owner here. Wider field labels and network
ownership semantics need producer/caller evidence. Invalid owners, full admitted
group construction and scheduler behavior remain open.
## Realm INI profile initialization

`verify_ai_profile_ini_initializer.py`, same engine SHA above, verifies whole
`465c60` in 252 synthetic cases and all 40 REGION sections across shipped Celtic,
Greek and Medieval cfg files. All production cases pass; config hashes checked
unchanged. Only GetCurrentDirectoryA/GetPrivateProfileStringA, sprintf and error
display are doubled. Native CRT strtok/strchr/isdigit/atoi/stricmp execute using
disk C-locale tables; full aa8 snapshots, AL return, stack, global pointer and
error-message identities are checked against an independent parser oracle.

The function resets all eight profiles first, aa0=-1/aa4=0. It assembles cwd plus
global `6ddd58` config path; three cwd slash forms are covered. It reads
REGION(global656620), Army_0 through Army_7, stopping at the first empty/missing
entry. Created slots get +0=1/+8=1, +4 remains0. Name is the first token using
comma/space delimiter set; `=` truncates individual tokens. Color +150 accepts
a digit-leading token with atoi result0..7; digit suffixes are tolerated. Invalid
or missing colors warn, default0 and restart tokenization so relations start
immediately after the name. This supports historical no-color rows if their
following F/E/X tokens form a valid relation vector.

Case-insensitive F/E write +18 bytes1/0 symmetrically; X preserves defaults/current
values. Self entries always stay1. Later row writes overwrite previous pair values,
so contradictory config resolves by row order. Each row's relation token count
(maximum8) must equal the number of created slots. No armies, missing name,
unrecognized relation or final count mismatch returns AL0 through distinct error
messages. Invalid color only warns before continuation. Errors retain partial
profile state rather than rolling it back. Empty/gapped entries, malformed tokens,
color overflow/wrapping, name `=` truncation,8slots and poisonfills are covered.

This verifies all four identified initializer bodies in their stated domains, not
all caller lifecycles or every possible Win32/encoding behavior. Subsequent role,
wizard-index and +20/+28 writers, save/network and runtime integration remain open.
## Named-profile relationship counter

Same hash, `verify_ai_relation_counter.py`: 2739 whole `4656c0` calls without
doubles, complete aa8 snapshots and stack checks. Native ABI is
`thiscall(profile, delta, targetIndex)`, callee pops8. This argument order is
confirmed by stack offsets and unequal-argument cases, not pseudocode alone.

It skips self, source+18[target]=0, or source+28[target]!=0. The source name at+50
must equal the exact case-sensitive `Cornelius` string at5d96f4, or target must be
the first matching profile found by scanning all eight fixed-global names.
Tests cover unique placement at every slot, no match and lowercase mismatch.
Neither active flags nor role flags enter the recovered gates.

For admitted pairs, source+30+4*target adds delta with 32-bit wrap; signed total
>=100 clears +18 in both directions. The counter itself is only updated in the
source profile. Negative increments/values, just below/at threshold, already-over
threshold and signed overflow are covered. Source+28 nonzero suppresses the whole
operation rather than only the final relationship change.

This is a verified named-player counter/relationship transition, not yet a proved
damage, theft or hostility-event formula. Event callers and delta units, duplicate
names, invalid indices, alternate global-array aliasing and all other relationship
writers/save/network remain open. The +28 suppression here does not establish a
single universal label for that field across its other consumers.
## Nonfatal damage event and secondary relationship setters

`verify_ai_damage_relation.py` adds651 no-double integrations of `5076f0`,
same hash. Enabled cases stop at507b82 before the UI suffix; dead/frozen cases
run to the real early return. Real `514990` nonfatal damage, `416d80` value and
`4656c0` counter execute. Domain is definition type1, global689920=0, no group
memberships, damage-attribution pointer0 and unit660=1 (bypasses UI notification).
Independent health/fullprofile/counter-call checks cover both named-player
directions, self, absent source(-1), status7c0/1, freeze, health0 and thresholds.

Negative health delta is negated into requested positive damage. At507b01 it
calls source-owner profile `4656c0(damage, victimOwner)` when source!=-1 and
victim+7c=0. This proves a damage source for the previously unlabeled counter,
but not that every counter increment is damage. Nonfatal health falls by the
requested amount; tested1/10/49 againsthealth50. Fatal damage, other types,
campaign stats, group outcome attribution and UI/save/network remain open.

Static exact calls at48c07e and48d11d also pass delta100 and a target-unit owner
into4656c0. Their enclosing action/spell identities and full conditions are still
unresolved, so no semantic label is assigned yet. Byte-based direct-call scanning
finds these plus507b01; this is not proof against indirect/additional callers.

`verify_ai_profile_defaults.py` now additionally verifies512 whole no-double
calls of4655e0 (+20) and465650 (+28), all8x8pairs andvalues0/1/255/256. Each
mirrors byte writes offdiagonal, truncates values, and preserves self and other
fields. Complete aa8 snapshots checked. This proves setter behavior, not universal
symmetry in the presence of other writers.

Static560da8 invokes465650(target=global644520,value=1) on a profile obtained via
466900 name lookup. Static56af83/56b051 invoke4655e0 with value1/0. Full caller
identities/events, meaning of+20/+28, other direct writers and serialization remain
necessary work; the setters alone do not justify naming these tables.
## Lure/Subversion relationship events

Read-only Ghidra export of containing functions identifies both fixed100 calls
inside `48b0f0`. Its disassembly reads effect+4c as spell ID at48b173 and uses
byte map48ead0 plus pointer table48ea2c. Hash-gated
`inspect_ai_relation_event_sources.py` verifies ID50→mapindex10→48d033 and
ID54→mapindex12→48be83. Shipped spell cfg labels are Lure and Subversion,
respectively; config hash and callbytes are saved in ai-relation-event-sources.json.
Lure calls4656c0 at48d11d; Subversion at48c07e; both push delta100. The large
Ghidra export has unreachable-block/type-propagation warnings and is not complete
recovered source or evidence of full effect correctness.

`verify_ai_lure_relation.py` adds1152 no-double entryprefix integrations from
48b0f0, using actual CRT itoa and4656c0. Stops at48d03a for dead target or48d122
before graphics for live target. All8x8 ownerpairs, uniqueCorneliusnone/0/7,
casterindex-1/0/2 against2slots, targethealth0/10 are covered. Native target
resolution writes effect+198; live target gets +780=syntheticduration1234 and
+788=-1. Fullprofile snapshot and observed counter arguments checked.

Lure calls target-owner profile `4656c0(100,casterOwner)`, provided caster index
is valid and target is alive. Missing/out-of-range caster leaves the target field
writes but skips the counter. This counter direction differs from health damage's
source-profile/victim-owner direction; symmetric relationship writes alone would
hide the distinction. Owner indices -1 and other invalid domains are not covered.
Subversion's probability/gates/ownership conversion remain open, as do whole Lure
graphics/world suffix, duration production/expiry, save/network and other callers.

Containing-function recovery also places560da8 (+28 setter) in5606f0 and both
56af83/56b051 (+20 setter) in56a8d0. Their higher-level command/event identities
are still unresolved and remain in the coverage inventory.
## Subversion native gates, probability and failure resistance

Same hash, `verify_ai_subversion_gates.py`:3300 no-double entryprefix cases from
48b0f0 plus30 early phase/target cases. Actual CRT itoa,466870 player-wizard lookup,
54e200 RNG and4656c0 execute. Stops48c083 before world conversion on success,
48c285 after native failure resistance update, or48cbb0/48c3e5/48cd47 for early
gates. RNG uses synthetic indices0/1 and buffer words producing a controlled XOR
sample; actual index progression from disk table5eb940 and all four state words
checked. This is actual native RNG execution, not a substituted random function.

Effect+48=-1 skips first. Effect+28 states6/7/11/30 take another early branch.
An out-of-range target or zero health takes the target failure path. For a live
target, any of spell fields6b13d5/d9/dd +721*ID nonzero enables the check:
unsigned `floor(u32(100*S)/u32(S+MR))`, with S at6b1274+721*ID and target MR+84.
Masked native random sample `(r&7fffffff)%100` must be strictly below that value.
All flags zero bypasses the probability test and does not advance RNG here.
Tested strengths0/1/8/100 and MR0/8/100 with nonzero sum; individual flag masks
0/1/2/4 and samples0/49/50/99/ffffffff. Zero denominator/overflow not covered.

Target definition types0/24/25/26 never pass the conversion gate. A caster-owner
wizard resolved by466870 blocks conversion when signed wizard+8f5 >= wizard+8f1;
absent wizard permits this gate. These are verified raw fields; their complete
producer/capacity semantics still need evidence. Probability check precedes these
type/capacity gates, so eligible checked casts consume RNG even when later blocked.

Admitted conversion first calls target-owner profile4656c0(100,casterOwner), same
direction as Lure, then reaches56c650 and51ec80(casterOwner). Neither world call
executes in this fixture. Disassembly51ec80 writes unit+174 but also invokes unit
registration, state/selection/task cleanup and other callbacks; full semantics
remain necessary work. Rejected ordinary targets reduce MR by unsigned truncated
`MR*antiMR/100`; fixtures stageantiMR30. Excluded wizard types preserve MR.
Fullprofile/counter/RNG/MR independent checks pass. Graphics/world suffix, other
owners/indices/invalidcasters, real config-field production, save/network pending.
## Ownership helpers: visibility fields and counted units

Same hash, `verify_ai_owner_bookkeeping.py` verifies400 whole51a880 and3468
whole522340 calls without doubles. Complete unit/pool and profile snapshots check
the expected writes. No UI functions execute:522340's UI suffix is suppressed
by fixture local-owner644520=-1, not replaced with a stub.

51a880 initializes eight unit words+24..40: owner always30; each other slot30
iff owner-profile+18[target] and+20[target] both nonzero, otherwise0. Eight words
+48..64 become0. All8owners, five asymmetric masks per table andtruth1/255 are
covered. Thus+20 participates in relationship-gated per-player visibility state;
this alone is not complete evidence of every visibility consumer or table writer.

522340 resolves this unit's owner wizard through real466870, scans6df180 pool
slots, and counts those with+4!=0,health+e4!=0,sameowner aswizard, unitID+0 different
fromwizardID, and type+a8!=27. It stores this count in wizard+8f5. Missing wizard
leaves the pool unchanged. Valid tests cover all8owners, exclusion masks, duplicate
IDs, scan sizes0/1/8/32, and full pool snapshots. This proves+8f5's owned-unit
count producer, connecting Subversion's8f5>=8f1 gate to that count. Exact +8f1
limit production, type27 design identity, live timing and UI notifications remain
open. The count depends on IDs rather than pointer inequality.

Static51ec80 calls522340 before owner+174 changes and again after, with51a880
between them. Later it clears state, invokes51edf0, retires two membership groups
via407b90, then requests416590 admission in manager690600 and also644550 for
ordinary-status wizard definition types. It updates attached effect+212 for
unit+7cd=2. These orchestration steps are static evidence, not yet whole-native
ownership verification. Task cleanup, selection callbacks, old/new pool counts,
group transitions, effect ownership/save/network still require integrated work.
## Ownership task cleanup orchestration

Same hash, `verify_ai_owner_task_cleanup.py`:1280 whole51edf0 calls. Actual
5178c0,4970b0 lookup and50eb60 reference release execute; native50db60 receives15
but unit618=1 guard returns early. 50ab30 and task callback are explicit no-op
event doubles. Thus this verifies caller gates/writes/order, not full command or
callback semantics. Complete four-unit pool/profile snapshots, calls and stack
are asserted. Matrix covers command0/8/10/20, target match, attachment, activity,
health, friendship, states0/3/9/10/11 and pending0/3.

First5178c0 scans active units irrespective of health/friendship. Matching
command10 target64c or command20 target6a8 with664!=0 clears664, releases the
referenced unit668 counter via actual50eb60 (signed decrement clamped0), then
invokes50db60(15). Matching command8 clears164 and invokes15 even without664.
This stage can affect a unit that the subsequent friendship/health scan skips.

The second51edf0 scan requires active+4 and live+e4. It includes matching unitID
directly, otherwise requires changed-owner profile18[scannedOwner]!=0. Command20
target6a8 matching changedunitID clears6a4, sets6a8=-1 and invokes callback5f4
withECX=unit+5f8. Matching64c withstate5ec3/9/10/11 invokes50ab30; matching64c
withpending5f0=3 clearspending. Relation/health gating and callback order verified.

Fixtures' changed unit has no own command/reference and distinct IDs. Its own
cleanup domains, duplicate IDs, invalid references, fullungated50db60,50ab30 and
callback sideeffects are still open. Whole51ec80 integration,group transitions,
selection/attached effects andsave/network remain required work.
## Command cancellation checkpoint

Same engine hash, verify_ai_command_cancel.py verifies864 whole50ab30 no-double
calls with actual54dce0 animation removal/CRTmemmove,50eb60 reference release and
50aa30 state request. Full two-unit snapshots cover health0/10, animation0/1/2/3,
pending0/3/8, command0/10/20, attached0/1, special10c0/3 and referencecount0/1/10.
Animationa0=1/2 removes animationcode4/1; othernonzero resetsa0/9c withoutremoval.
Pending8 skips remaining cleanup after animation handling. Attached commands10/20
release target668 count(clamp0). Movement/targetflags reset and currentposition
copied tobc3/bc7/bcb. Native50aa30(1) with fixture618=1 queuespending1 foralive,
while dead units ignore that request. Unguardedstatecallbacks, otheranimationlist
domains, invalidreferences andwholeownership integration remainopen.
## Unit state callback dispatch

Same hash, verify_ai_state_dispatch.py verifies21 whole50a930 selectors without
doubles and300 whole50aa30 transitions with only selected callback bodies doubled.
Fullunit snapshots, ret4 stackcleanup andcallback ECX=unit checked. Callback
selector returns EDX=0 for all testedstates. State-to-handler map:

| State | Handler VA |
|---|---|
|1|50acb0|
|2|510010|
|3|50afa0|
|4|50ccd0|
|5|50d580|
|6|50d840|
|7|50d860|
|8|50d850|
|9|50d870|
|10|50d8f0|
|11|51c510|
|12|0|
|13|51c230|
|14|521750|
|15|521770|
|16|521780|

Outside1..16 also returns0. These are raw callback identities, not asserted
design names. Transition50aa30 ignoresdead-unit requests except16 or5whenoldstate
isnot5; dead5→5 isignored. Accepted requests withunit618nonzero writepending5f0
only. Unguarded requests installstate5ec,callback5f4,offset5f8=0,clear pending
unlessnewstate8/14, then invokecallback withECX=unit. Previousstate2 cleanup is
coveredonlywithemptyeffecttree/effect0. Matrixprevious0/2/5/8/14,health0/10,
guard0/1,all15 nonnullstates. Nullcallback invocation,nonemptyeffectcleanup and
all callback internal behaviors remainopen; this replaces guessed dispatch
semantics withnative evidence butdoesnot closewholeownership integration.
