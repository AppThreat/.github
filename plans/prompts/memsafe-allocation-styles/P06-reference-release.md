# P06: reference release semantics

Load the "skill: dynamic workflow" skill (zcode's `dynamic-workflows`) and run this prompt with its `CreateWorkflow` tool, as `00-RULES.md` "Work as a workflow" describes; do not use the `Agent` tool for the pieces.

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D9 and the last risk in [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md), and the earlier reports in `~/work/memsafe-alloc-styles/reports/`.

Issue: AppThreat/chen#327. Branches: `memsafe/p06-refcount` in chen and atom, from `origin/feat/memsafe-alloc-styles` (or the branch the prompt that hands you this one names). Write the report to `~/work/memsafe-alloc-styles/reports/P06-report.md`.

## Measure first

Before writing code, run the CPython `Objects/` arm and count how many call sites of `Py_DECREF`, `Py_XDECREF` and `Py_CLEAR` reach the graph as calls with a resolvable body, as macro expansions, or not at all. Do the same for `kref_put` on the Linux arm and `decrRefCount` on the Redis arm. Put the counts in the report. They decide how much of this prompt rests on inference and how much on the P04 profile entries.

## Tasks

1. **Summaries.** In `MemorySemanticsPass`, summarise `release:<i>`: a method that decrements a field of parameter `i` and, under the condition that the field reached zero, frees `i`, calls a destroy function summarised as freeing `i` (P02), or calls a function pointer passed as another argument (`kref_put(&o->ref, release)`, where `&o->ref` locates `o` through `container_of`). Summarise `acquire:<i>` for a method that increments a field of `i`; the pass already records such methods as `grow:<i>:<field>`, so reuse that fact. Read the P04 profiles' `release` and `acquire` roles as declared versions of the same summaries.
2. **State.** In `AllocationStatePass`, add a per-variable count of references the method owns: one for a new allocation or a declared constructor's result, plus one for each acquire, minus one for each release. A release that takes the count to zero moves the variable to `freed`. A release of a variable whose ownership is unknown (a parameter, a field read, an unsummarised call's result) moves it to `maybe-freed` with a marker that the reference was borrowed.
3. **Rules.** A use after a release that reached zero is MS-ALLOC-002 at medium. A use after a borrowed release is MS-ALLOC-002 at low. A second release that reaches below zero is MS-ALLOC-001 at medium. Do not report a missing release; reference leaks are out of scope.
4. **Loops and error paths.** A release in a loop body, and the CPython idiom of releasing on a `goto error` path, are the negative controls that matter most. Write them before the rule.

Tests: the P01 reference fixture's bad cases are reported at the confidence D9 names, its good cases are not, and the probe's `refcount_uaf` is reported while `refcount_ok` is not, end to end in atom.

## Finish

Run the gates at `medium` and `low`. The CPython `Objects/` arm must gain no `medium` finding; read every finding it gains at `low` and every finding the Linux and Redis arms gain at any level.
