# P03: scope cleanup in c2cpg and in the allocation-state rules

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D4, D5 and the first two risks in [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md), and the P01 and P02 reports in `~/work/memsafe-alloc-styles/reports/`.

Issues: AppThreat/chen#322 (task A) and AppThreat/chen#323 (task B). Branches: `memsafe/p03-scope-cleanup` in chen and atom, from `origin/feat/memsafe-alloc-styles`, or from the P02 branches if the prompt that hands you this one says they are not merged yet. Write the report to `~/work/memsafe-alloc-styles/reports/P03-report.md`.

## Background

edg2atom already does what c2cpg must do. Read `platform/frontends/edg2atom/src/main/scala/io/appthreat/edg2atom/astcreation/AstForCpp.scala`, the section "destructors where scopes end": `ExitScope`, `withExitScope`, `withFunctionScope` (which also collects label positions for `goto`), `cleansUpAtScopeEnd`, `destructorCallAsts` and `cleanupCallAst`. Each cleanup becomes a call `fn(&var)` tagged `compiler-generated` and `lifetime-end` (valued with the variable name), placed at each exit of the scope. Find where those calls are inserted for `return`, `goto`, `break`, `continue` and the end of a block, and note how the return value is evaluated before the cleanup runs.

Then run the probe and the P01 cleanup fixture through both front ends and compare the graphs. With edg2atom today, the probe's `cleanup_double_free` is reported as MS-ALLOC-002 on the explicit `free` line, and `cleanup_return_dangling` is not reported. Find out why before changing anything, and say in the report.

## Task A: c2cpg emits the cleanup calls (D4)

In c2cpg (`platform/frontends/c2cpg/src/main/scala/io/appthreat/c2cpg/astcreation/`), read the `cleanup` and `__cleanup__` attributes on a declarator, including when they come from a macro expansion, and emit the same calls edg2atom emits, at the same exits, with the same tags, argument shape, `methodFullName` resolution and line numbers. The attribute handling that already writes `storage-class=static` and `fn-attr` tags shows where CDT exposes declarator attributes. Bump the AST cache version that `AstCreationPass` checks, so cached fragments without the calls are rebuilt.

Cover each macro spelling in the P01 fixture (`__free(kfree)` through `DEFINE_FREE`, `g_autofree`, `g_autoptr(T)`, `_cleanup_free_`) and each exit kind: fall-through at the end of a block, `return` with and without a value (the value is computed before the cleanup), `goto` to a label outside the scope, `break` and `continue` out of a loop body, nested scopes (inner cleanups run first), and two cleanup variables in one scope (reverse declaration order). If an exit kind cannot be found reliably from CDT, emit no call for it, and list it under "Not done".

Write a test that builds the same fixture with both front ends and compares the cleanup calls (name, argument code, line, the CFG predecessor and successor) between them.

## Task B: allocation state and rules read the cleanup calls (D5)

In `MemorySemanticsPass` add a steal summary: a method that reads `*pp`, stores NULL into `*pp` and returns the value it read, for a pointer-to-pointer parameter `i`. Glib's `g_steal_pointer` and systemd's `TAKE_PTR` match this when their bodies or macro expansions are in the graph; Linux's `no_free_ptr` expands to a statement expression that assigns NULL, which the existing `null-reset` state should already handle. Check which of the three work and say so.

In `AllocationStatePass` and `MemorySafetyFindingPass`, make the rules behave as D5 says, for both front ends:

1. No leak (MS-ALLOC-003) for a variable a cleanup call releases.
2. A double free (MS-ALLOC-001) at the cleanup call when the variable was freed before that exit and not reset to NULL. The explicit `free` is not the finding's line, and is not a use after free.
3. A use after free (MS-ALLOC-002) at the caller when a method returns a cleanup variable that is not stolen or reset, and that method is never summarised as an allocator (today the probe's `cleanup_return_dangling` gets `alloc:heap`). Storing the variable into a field or global that outlives the scope is reported the same way, at medium.
4. A cleanup call on one exit path must not change the state on any other path. If the edg2atom misreport comes from the CFG, fix it in edg2atom and add a test there.

## Finish

Run the gates from the rules at `medium` and `low` with c2cpg, and the hand-written arm and the new fixtures with edg2atom as well. Read every finding that the QEMU and Linux arms gain or lose. The QEMU `block/` arm must gain no leak finding at `low`.
