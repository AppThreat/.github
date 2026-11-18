# P02: every remaining deliverable, D2 to D10, in one session

Load the "skill: dynamic workflow" skill (zcode's `dynamic-workflows`) before anything else and run this prompt with its `CreateWorkflow` tool, as `00-RULES.md` "Work as a workflow" describes. Every piece below gets a developer subagent and a separate reviewer subagent, both on GLM-5.3-Flash. Do not use the `Agent` tool for the pieces.

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D2 to D10 and "Risks and open questions" in [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md), `~/work/memsafe-alloc-styles/reports/P01-report.md` for the fixtures, and `~/work/memsafe-alloc-styles/reports/P01-baseline.md` for the baseline and the arm findings already read by hand.

This prompt replaces the six prompts the plan used to have. It is long: the lead keeps its state in the plan file, not in its context (see "Resuming").

| | |
| --- | --- |
| Issues | AppThreat/chen#320 to AppThreat/chen#327, AppThreat/atom#414 |
| Branches | `memsafe/alloc-styles` in chen and atom, from `origin/main` |
| Plan file | `~/work/memsafe-alloc-styles/reports/P02-plan.md` |
| Report | `~/work/memsafe-alloc-styles/reports/P02-report.md` |

## Pieces and order

The overlay's logic sits in three large files under `platform/frontends/x2cpg/src/main/scala/io/appthreat/x2cpg/passes/taggers/` in chen: `MemorySafetyFindingPass.scala` (the rules), `MemorySemanticsPass.scala` (method summaries) and `AllocationStatePass.scala` (the per-variable state). Most deliverables change at least one of them, so most of the work is a chain. The parallel work is in the inventory, the front ends and atom.

| Piece | Work | Owns | Starts after |
| --- | --- | --- | --- |
| A | D2 items 1 and 2 (MS-ALLOC-006, MS-BOUND-004) | `MemorySafetyFindingPass.scala` and its tests | |
| B | D3 (destroy-function summaries) | `MemorySemanticsPass.scala`, `AllocationStatePass.scala` and their tests | |
| C1 | D7 items 1 and 2 (profile format and the seven profiles) | `MemApiVocab.scala`, `memory-apis.json` or new profile resources, their tests | |
| D | D4 (c2cpg emits cleanup calls) | `platform/frontends/c2cpg/.../astcreation/`, the AST cache version, the test comparing both front ends | |
| C2 | D2 item 3 (descriptor families) | the descriptor entries in `memory-apis.json`, `IntHandleFamilies` in `AllocationStatePass.scala`, the double-close check in `MemorySafetyFindingPass.scala` | A, B, C1 |
| E | D5 (cleanup in state and rules, steal summaries) | the three pass files; edg2atom, if the CFG needs a fix | A, B, C2, D |
| F | D7 items 3 and 4 (profile selection, `--memory-api-profiles`) | `MemoryApiPass.scala`, any include record in the front ends, atom's command option and its docs line | C1, D |
| G | D6 (offset allocator families) | `MemorySemanticsPass.scala`, `MemoryApiPass.scala` | E, F |
| H | D8 (regions) | the three pass files | G |
| I | D9 (reference release) | the three pass files | H |
| T | atom end-to-end tests | `MemorySafetyCommandTests` | each checkpoint |
| J | D10 documentation | the memory-safety docs in chen and atom, the test that loads the documented example | I |

The lead confirms or changes this table in `P02-plan.md` after reading the code, and may split a piece into two that run one after the other on the same branch. A piece starts when every piece it follows is merged and no running piece owns any of its files. Run at most three sbt-heavy developers at once. New corpus fixtures are new files; the plan file names each one and assigns it to one piece.

The lead does two things itself, before or while the first developers work: the reference-count measurement in D9 ("Measure first"), and the edg2atom comparison in D4 ("Background"). Both feed decisions that the plan file must settle before E and I start.

## Checkpoints

After merging a batch of pieces (A to D; C2, E and F; G; H; I), the lead:

1. runs `sbt publishLocal` in chen and `sbt stage` in atom, each in its own call, and checks the date on the staged chen jar;
2. hands piece T the merged batch: a developer writes the atom end-to-end tests for every rule change in it, a reviewer checks them, and the lead runs them;
3. runs `LEVELS=medium GATES=corpus OUT=out/gates-p02-<batch> tools/run_gates.sh` in the corpus. If recall or precision falls below the baseline, or a `@nofinding` line gains a finding, the batch is fixed before the next piece starts;
4. records the batch's merge SHA, the test counts and the corpus numbers in `P02-plan.md`.

The full gates run once, at the end ("Finish"). Arm checks that a deliverable names (SQLite and Redis free functions, the QEMU leak count, the nginx and pgvector region leaks, the CPython medium count) are read from the final gate run, not from runs during the session.

## D2: default-level false positives (pieces A and C2)

1. **MS-ALLOC-006** (`RuleOffsetFree`, recorded in three places near the `walkIncrements` and `defsAreOffsetArith` checks). Today any release of a pointer defined by pointer arithmetic is reported, at high confidence. Restrict it to arithmetic that moves a pointer forward from an allocation this method can see (a call tagged `mem-alloc`, a summarised allocator, or a walk forward through such a pointer). A pointer moved back from a parameter, or from a value whose definitions reach only parameters, is how a header-prefixed allocator frees its own block, and is not reported. Cover `free((hdr_t *)p - 1)`, `p--; free(p)`, `p -= 1; free(p)`, `free((char *)ptr - PREFIX_SIZE)` with `PREFIX_SIZE` a macro, and the same through a local copy of the parameter. Keep reporting `free(p + 1)` on a fresh allocation, a free after `while (*p) p++;` over an allocation, and a backward move from an allocation that was advanced first by a different amount.
2. **MS-BOUND-004** (`RuleIndexWrite`). An index `n` into a buffer whose extent is `alloc:` of `n + k`, with `k` a positive integer constant, is in bounds when `n` is the same variable, unmodified between the allocation and the write. Teach the comparison of index and extent this case rather than adding an exception to the rule. Keep reporting `buf[n + 1]`, `buf[n + k]` for `k` at least the constant, and `buf[m]` for an unrelated `m`. Overflow of `n + k` stays MS-INT-001's question.
3. **Descriptor families** (piece C2). `memory-apis.json` puts `open` and `close` in the `file` family with `fopen` and `fclose`, and `socket` and `accept` in a `socket` family, so `close()` on a socket is MS-ALLOC-007 at high (15 such findings on the Redis and nginx arms) and `close()` on a `FILE *` passes. Give descriptors one family (`open`, `openat`, `creat`, `socket`, `accept`, `accept4`, `dup`, `dup2`, and `pipe` outputs where modelled, released by `close`), keep `FILE *` in its own (`fopen`, `fdopen`, `tmpfile`, released by `fclose`), and check `closesocket` the same way. The family names are also read by `IntHandleFamilies` in `AllocationStatePass.scala` and by the double-close choice in `MemorySafetyFindingPass.scala`; change both to match. Fixtures: `close(fopen(...))`, `fclose` of an `open` result, and the matched pairs.

Use the terminator and header-prefix fixtures P01 added, plus focused tests in `MemorySafetyFindingPassTests` or `WrongDeallocationRuleTests`. In the final gates, check that SQLite's `mem1.c` and Redis's `zmalloc.c` free functions produce no MS-ALLOC-006, and read by hand every MS-BOUND-004 finding that disappears from any arm.

## D3: destroy-function free summaries (piece B)

The effect summaries are the `effect:frees-param:<i>` values in `AllocationStatePass.scala`, computed where a free has no incoming control-dependence edge; the name-level summaries are in `MemorySemanticsPass.scala` (a free wrapper "returns nothing and calls only known frees").

1. Accept a free of parameter `i` whose only controlling condition is a NULL test of that same parameter (`if (!p) return;`, `if (p == NULL) return;`, `if (p) { ...; free(p); }`), in both summaries. Any other controlling condition still blocks the summary.
2. Allow a destroy function to do other work first: free members of `i` (directly, in a loop over a list, or through another destroy function), call functions with no free effect, and assign to fields. It is summarised as freeing `i` only when every path to the exit, after the NULL guard, frees `i` itself.
3. The summary must not hold when `i` is freed on some paths only, when a member is freed but `i` is not, or when the free depends on a reference count or a flag (the flag case in `cwe416_destroy_function.c` is the control).

A call to the destroy function then moves the argument to `freed` through the existing machinery, and MS-ALLOC-002 reports a later use with no rule change. A wrong `frees-param` summary is a false double free at every call site, so the final gates list and read every MS-ALLOC-001 and MS-ALLOC-002 finding any arm gains.

## D4: c2cpg emits the cleanup calls (piece D)

**Background (lead).** edg2atom already does this. Read `platform/frontends/edg2atom/src/main/scala/io/appthreat/edg2atom/astcreation/AstForCpp.scala`, the section "destructors where scopes end": `ExitScope`, `withExitScope`, `withFunctionScope` (which also collects label positions for `goto`), `cleansUpAtScopeEnd`, `destructorCallAsts` and `cleanupCallAst`. Each cleanup becomes a call `fn(&var)` tagged `compiler-generated` and `lifetime-end` (valued with the variable name) at each exit of the scope. Run the probe and the P01 cleanup fixture through both front ends and compare. With edg2atom today, the probe's `cleanup_double_free` is reported as MS-ALLOC-002 on the explicit `free` line and `cleanup_return_dangling` is not reported. Find out why, record it in the plan file before piece E starts, and say so in the report.

**Piece D.** In `platform/frontends/c2cpg/src/main/scala/io/appthreat/c2cpg/astcreation/`, read the `cleanup` and `__cleanup__` attributes on a declarator, including through a macro, and emit the calls edg2atom emits, at the same exits, with the same tags, argument shape, `methodFullName` resolution and line numbers. The attribute handling that writes `storage-class=static` and `fn-attr` tags shows where CDT exposes declarator attributes. Bump the AST cache version that `AstCreationPass` checks. Cover each macro spelling in the P01 fixture (`__free(kfree)` through `DEFINE_FREE`, `g_autofree`, `g_autoptr(T)`, `_cleanup_free_`) and each exit: the end of a block, `return` with and without a value (computed before the cleanup), `goto` to a label outside the scope, `break` and `continue` out of a loop body, nested scopes (inner cleanups first), and two cleanup variables in one scope (reverse declaration order). If an exit kind cannot be found reliably from CDT, emit no call for it and list it under "Not done". The test builds the same fixture with both front ends and compares the cleanup calls (name, argument code, line, CFG predecessor and successor).

## D5: cleanup in allocation state and rules (piece E)

In `MemorySemanticsPass`, add a steal summary: a method that reads `*pp`, stores NULL into `*pp` and returns the value it read, for a pointer-to-pointer parameter `i`. Check which of glib's `g_steal_pointer`, systemd's `TAKE_PTR` and Linux's `no_free_ptr` (a statement expression assigning NULL, which `null-reset` should handle) work, and say so.

In `AllocationStatePass` and `MemorySafetyFindingPass`, for both front ends:

1. No leak (MS-ALLOC-003) for a variable a cleanup call releases.
2. A double free (MS-ALLOC-001) at the cleanup call when the variable was freed before that exit and not reset to NULL. The explicit `free` is neither the finding's line nor a use after free.
3. A use after free (MS-ALLOC-002) at the caller when a method returns a cleanup variable that is not stolen or reset, and that method is never summarised as an allocator (today the probe's `cleanup_return_dangling` gets `alloc:heap`). Storing the variable into a field or global that outlives the scope is reported the same way, at medium.
4. A cleanup call on one exit path must not change the state on another. If the edg2atom misreport comes from its CFG, fix it in edg2atom with a test there.

In the final gates, read every finding the QEMU and Linux arms gain or lose. The QEMU `block/` arm gains no leak finding at `low`.

## D6: offset allocator families (piece G)

1. A method whose every non-NULL value return is a known allocation advanced by one constant amount (`h + 1` with `h` of a struct type, `(char *)p + PREFIX_SIZE`, `p + sizeof(size_t)`) is an allocator of a new family named after the method (for example `offset:zmalloc`). Normalise the amount to bytes where the types allow, so `h + 1` and `(char *)h + sizeof(*h)` are the same amount. Carry over the size and nullable facts a plain wrapper gets.
2. A method that releases its parameter moved back by the same amount is that family's free. Pair them through the amount and the underlying family, never through names.
3. `MemoryApiPass` tags call sites with the new family, so `RuleMismatchedFree` reports `free()` on an offset allocation and the offset free on a plain allocation, with no rule change unless the family comparison needs one.
4. A wrapper that returns an allocation unchanged stays in its underlying family; `free(xmalloc(n))` is not reported.

Redis builds `zmalloc` differently depending on `HAVE_MALLOC_SIZE`: in the final gates, run the Redis arm once with it defined and once without (`--define`), and report both.

## D7: declared library profiles (pieces C1 and F)

The inventory is `platform/frontends/x2cpg/src/main/resources/memory-apis.json`, read by `MemApiVocab.scala`; `atom memory-safety --memory-api-config` merges an external file over it by API name.

1. **Format (C1).** Add a profiles section to the inventory, or one resource file per profile, whichever keeps `MemApiVocab`'s validation simplest. A profile has a name, the header names that select it, and entries in the existing format. Add the roles later pieces need as fields now: `region` (create, allocate with the region argument index, reset, destroy), `release` and `acquire` (with the parameter index), `steal`, and `cleanup` (a function that frees `*pp`). If the change cannot keep existing external configuration files valid, stop that part and put it under "Questions".
2. **Profiles (C1):** glib, the Linux kernel, PostgreSQL, APR, nginx, CPython and PHP, each entry citing the header and line, or the documentation page, that states its behaviour. At least: `g_new0`, `g_free`, `g_steal_pointer`; `kmalloc`, `kzalloc`, `kvfree`, `kfree`, `devm_kzalloc`, `kref_put`; `palloc`, `palloc0`, `pfree`, `MemoryContextReset`, `MemoryContextDelete`, `AllocSetContextCreate`; `apr_palloc`, `apr_pool_create`, `apr_pool_clear`, `apr_pool_destroy`; `ngx_alloc`, `ngx_free`, `ngx_palloc`, `ngx_create_pool`, `ngx_destroy_pool`; `PyMem_Malloc`, `PyMem_Free`, `Py_DECREF`, `Py_INCREF`; `emalloc`, `efree`, `zend_string_release`. Families say which frees are interchangeable: `kvfree` accepts `kmalloc` and `vmalloc` memory, and glib's `g_free` is `free` on every platform glib supports today (cite the glib release note).
3. **Selection (F).** A translation unit selects a profile when it includes one of the profile's headers. Find how c2cpg and edg2atom record `#include`; if neither does, add the smallest record that works for both. A body inferred in the analysed tree wins over a profile entry of the same name.
4. **Option (F).** atom's `memory-safety` gains `--memory-api-profiles <auto|none|name,name>` (default `auto`) and prints the selected profiles, with how many files selected each, where it prints the `MemorySemanticsPass` summary counts. Add the option to atom's docs for the command.

Tests: per profile, a file that includes its header gets one allocation, one free and one mismatch right; a file that includes none gets no profile entry; `none` turns selection off; an external config entry overrides a profile entry. In the final gates, profiles add knowledge, so findings may rise where a profile recognises an allocator: read every finding added on the QEMU, Linux, pgvector, nginx and CPython arms, and fix every false one at `medium`.

## D8: regions (piece H)

1. **Inference.** A method that returns a pointer computed by arithmetic on a field of parameter `i` (or of an object reached from `i`), with no allocation on that path, is `region-alloc:<i>`. A NULL return for exhaustion is allowed. A method that falls back to `malloc` when the region is full (nginx's large allocations) records both summaries, and the state carries both.
2. **Declared regions.** Read the profiles' `region` role: create, allocate (with the region argument index, or the current global context for PostgreSQL's `palloc`, where the region is `CurrentMemoryContext`), reset and destroy. `devm_kzalloc(dev, ...)` is a region allocation owned by `dev`.
3. **State.** A region allocation records its region: the node of the region argument, or a named global context. Region memory is never a leak. A destroy of the region (D3's `frees-param` summary or a declared destroy) moves every pointer allocated from the same region variable in this method to `freed`; a declared reset moves them to `maybe-freed`. Match regions by the same local, parameter or global only.
4. **Rules.** A heap free of region memory is reported by the existing wrong-deallocation rules (MS-ALLOC-005 or MS-ALLOC-007, whichever matches). A use after destroy is MS-ALLOC-002 at high when the destroy is unconditional on the path, and at medium after a reset. `pfree` of `palloc` memory is correct; `pfree` of `malloc` memory is a mismatch.

Tests: the P01 region fixture, and the probe's `pool_uaf` and `pool_free_mismatch` end to end in atom. In the final gates, the nginx and pgvector arms have no leak finding on a region allocation at any level; list their leak counts before and after and read every finding either gains.

## D9: reference release (piece I)

**Measure first (lead, at the start).** Run the CPython `Objects/` arm and count how many call sites of `Py_DECREF`, `Py_XDECREF` and `Py_CLEAR` reach the graph as calls with a resolvable body, as macro expansions, or not at all; the same for `kref_put` on the Linux arm and `decrRefCount` on the Redis arm. Record the counts in the plan file. They decide how much of piece I rests on inference and how much on the profile entries.

1. **Summaries.** `release:<i>`: a method that decrements a field of parameter `i` and, under the condition that the field reached zero, frees `i`, calls a destroy function summarised as freeing `i` (D3), or calls a function pointer passed as another argument (`kref_put(&o->ref, release)`, where `&o->ref` locates `o` through `container_of`). `acquire:<i>` reuses the existing `grow:<i>:<field>` fact. The profiles' `release` and `acquire` roles are declared versions of the same summaries.
2. **State.** A per-variable count of references the method owns: one for a new allocation or a declared constructor's result, plus one per acquire, minus one per release. A release that reaches zero moves the variable to `freed`. A release of a variable whose ownership is unknown (a parameter, a field read, an unsummarised call's result) moves it to `maybe-freed`, marked as borrowed.
3. **Rules.** A use after a release that reached zero is MS-ALLOC-002 at medium; after a borrowed release, at low. A second release below zero is MS-ALLOC-001 at medium. A missing release is not reported.
4. **Negative controls first:** a release in a loop body, and CPython's release on a `goto error` path.

Tests: the P01 reference fixture at the confidence D9 names, and the probe's `refcount_uaf` reported and `refcount_ok` silent, end to end in atom. In the final gates, the CPython `Objects/` arm gains no `medium` finding; read every finding it gains at `low`, and every finding the Linux and Redis arms gain at any level.

## D10: documentation (piece J)

1. Extend the existing memory-safety docs in both repositories (atom's docs for the `memory-safety` command and its rules, chen's docs for the overlay passes and `memory-apis.json`); start a new document only if none fits.
2. Describe each allocation style: what is inferred from bodies and attributes, what a profile declares, how scope cleanup is read from both front ends, how a region owns its allocations, how reference counts are tracked. One short C example per style, with the finding it produces and the correct version that produces none.
3. Document `--memory-api-profiles`, the profile list with the headers that select each, and how to declare an in-house region, release, acquire, steal or cleanup function in `--memory-api-config`, with a complete example file that `MemApiVocab` accepts and a test that loads it from the docs.

The reviewer of piece J checks every sentence against the merged code, and the lead removes any sentence that describes behaviour the code lacks.

## Finish

1. Merge piece J, run `sbt scalafmtAll` on the changed files in both repositories as the last commit, then `sbt publishLocal`, `sbt stage` and the atom end-to-end tests once more.
2. Run the whole-branch review from `00-RULES.md` and fix what it finds.
3. Run `OUT=out/gates-p02 tools/run_gates.sh` (every gate, `medium` and `low`), and the hand-written arm and the allocation-style fixtures with edg2atom as well. Then the arm checks each deliverable above names, from that run's findings.
4. Write the report. Section 3 ("Done when") has one subsection per deliverable, D2 to D10, listing every bad and good fixture function with its result. Section 11 ("Outcome") is one table per gate with the P01 baseline, the result and the difference, ready to paste into the plan's Outcome section, followed by the medium findings classified in P01 that changed and why.

## Resuming

The session may stop before the end. `P02-plan.md` is the record a new session resumes from, so the lead keeps in it, as it goes: the piece table with each piece's state (planned, developing, in review, merged), its branch and merge SHA, the decisions, the measurement and the checkpoint results. A new session reads `00-RULES.md`, this prompt and `P02-plan.md`, checks `git status` and `git log` in both repositories and in any worker worktree still present, and continues from the first piece not merged. It does not start a merged piece again.
