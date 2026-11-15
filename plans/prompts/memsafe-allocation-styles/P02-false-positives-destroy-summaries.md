# P02: default-level false positives and destroy-function summaries

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D2 and D3 in [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md), and the P01 report at `~/work/memsafe-alloc-styles/reports/P01-report.md` for the baseline and the new fixtures.

Issues: AppThreat/chen#{{D2}} (task A) and AppThreat/chen#{{D3}} (task B). Branches: `memsafe/p02-false-positives` in chen and atom, from `origin/feat/memsafe-alloc-styles`. Write the report to `~/work/memsafe-alloc-styles/reports/P02-report.md`.

## Task A: the two default-level false positives (D2)

All code is in `platform/frontends/x2cpg/src/main/scala/io/appthreat/x2cpg/passes/taggers/` in chen.

1. **MS-ALLOC-006** (`RuleOffsetFree` in `MemorySafetyFindingPass.scala`, recorded in three places near the `walkIncrements` and `defsAreOffsetArith` checks). Today any release of a pointer defined by pointer arithmetic is reported, at high confidence. Restrict it to arithmetic that moves a pointer forward from an allocation that this method can see (a call tagged `mem-alloc`, a summarised allocator, or a walk forward through such a pointer). A pointer moved backwards from a parameter, or from a value whose definitions reach only parameters, is how a header-prefixed allocator frees its own block, and is not reported. Cover `free((hdr_t *)p - 1)`, `p--; free(p)`, `p -= 1; free(p)`, `free((char *)ptr - PREFIX_SIZE)` with `PREFIX_SIZE` a macro, and the same through a local copy of the parameter. Keep reporting `free(p + 1)` on a fresh allocation, a free after `while (*p) p++;` over an allocation, and a backward move from an allocation that was advanced first by a different amount.
2. **MS-BOUND-004** (`RuleIndexWrite`). An index `n` into a buffer whose extent is `alloc:` of `n + k`, with `k` a positive integer constant, is in bounds when `n` is the same variable, unmodified between the allocation and the write. Find where the rule compares the index with the extent and teach that comparison the case, rather than adding an exception in the rule. Keep reporting `buf[n + 1]` and `buf[n + k]` for `k` at least the constant, and `buf[m]` for an unrelated `m`. Integer overflow of `n + k` stays MS-INT-001's question; do not suppress MS-INT-001 here.

Use the terminator and header-prefix fixtures P01 added, plus focused tests in `MemorySafetyFindingPassTests` or `WrongDeallocationRuleTests`. On the arms, check that SQLite's `mem1.c` and Redis's `zmalloc.c` free functions no longer produce MS-ALLOC-006, and list every MS-BOUND-004 finding that disappears from any arm, each read by hand, so the report shows no true finding was lost.

## Task B: destroy-function free summaries (D3)

The effect summaries live in `AllocationStatePass.scala` (the `effect:frees-param:<i>` values, computed where a free has no incoming control-dependence edge) and the name-level summaries in `MemorySemanticsPass.scala` (a free wrapper "returns nothing and calls only known frees").

1. Accept a free of parameter `i` whose only controlling condition is a NULL test of that same parameter (`if (!p) return;`, `if (p == NULL) return;`, `if (p) { ...; free(p); }`). Any other controlling condition still blocks the summary. This matters for both the effect summary and the name-level free summary.
2. Allow a destroy function to do other work first: free members of `i` (directly, in a loop over a list, or through another destroy function), call functions with no free effect, and assign to fields. It is summarised as freeing `i` only when every path to the exit, after the NULL guard, frees `i` itself.
3. The summary must not hold when `i` is freed on some paths only, when a member is freed but `i` is not, or when the free is controlled by a reference count or a flag. The `cwe416_destroy_function.c` good case with a flag is the control for this.

Then a call to the destroy function moves the argument to `freed` at the call site through the existing machinery, and use after it is reported by MS-ALLOC-002 with no rule change. Check this end to end in atom for the probe's `pool_destroy` and for each bad case in the destroy fixture.

Watch for the defect that the earlier summary work warned about: a wrong `frees-param` summary is a false double free at every call site. For each arm, list any MS-ALLOC-001 or MS-ALLOC-002 finding that appears, and read each one.

## Finish

Run the gates from the rules, at `medium` and `low`, and record them against the P01 baseline. Every fixture that P01 marked for D2 and D3 must pass; list each bad and good function with its result.
