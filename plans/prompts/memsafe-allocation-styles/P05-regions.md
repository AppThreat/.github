# P05: region semantics

Load the "skill: dynamic workflow" skill (zcode's `dynamic-workflows`) and run this prompt with its `CreateWorkflow` tool, as `00-RULES.md` "Work as a workflow" describes; do not use the `Agent` tool for the pieces.

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D8 in [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md) and the earlier reports in `~/work/memsafe-alloc-styles/reports/`, P04 in particular for the profile format and the `region` role.

Issue: AppThreat/chen#326. Branches: `memsafe/p05-regions` in chen and atom, from `origin/feat/memsafe-alloc-styles` (or the branch the prompt that hands you this one names). Write the report to `~/work/memsafe-alloc-styles/reports/P05-report.md`.

## Tasks

1. **Inference.** In `MemorySemanticsPass`, summarise a region allocator: a method that returns a pointer computed by arithmetic on a field of parameter `i` (or on a field of an object reached from `i`), with no allocation on that path, is `region-alloc:<i>`. A NULL return for exhaustion is allowed. A method that falls back to `malloc` when the region is full (nginx's large allocations do) is a region allocator on the region path and a heap allocator on the other; record both and let the state carry both, rather than picking one.
2. **Declared regions.** Read the P04 profiles' `region` role: create, allocate (with the region argument index, or the current global context for PostgreSQL's `palloc`, where the region is `CurrentMemoryContext`), reset and destroy. `devm_kzalloc(dev, ...)` is a region allocation owned by `dev`.
3. **State.** In `AllocationStatePass`, a region allocation gets a state that records its region: the node of the region argument, or a named global context. Region memory is never a leak. A destroy of the region (D3's `frees-param` summary of a destroy function, or a declared destroy) moves every pointer allocated from that same region variable in this method to `freed`. A declared reset moves them to `maybe-freed`. Match regions by the same local variable or parameter, or the same global; do not guess aliasing beyond that.
4. **Rules.** A heap free of region memory is reported by the existing wrong-deallocation rules (MS-ALLOC-005 or MS-ALLOC-007, whichever matches what the region allocator returned). A use after destroy is MS-ALLOC-002 at high when the destroy is unconditional on the path, and at medium after a reset. PostgreSQL's `pfree` of `palloc` memory is correct, and `pfree` of `malloc` memory is a mismatch.

Tests: the P01 region fixture's bad cases are reported with the right rule and confidence, its good cases are not, and the probe's `pool_uaf` and `pool_free_mismatch` are reported end to end in atom.

## Finish

Run the gates at `medium` and `low`. The nginx and pgvector arms must have no leak finding on a region allocation at any level; list the leak counts on both arms before and after. Read every finding either arm gains.
