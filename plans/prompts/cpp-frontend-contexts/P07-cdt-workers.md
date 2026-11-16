# P07: CDT workers

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D11 and the worker-overhead risk in [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), and the P01 report in `~/work/cpp-frontend-contexts/reports/`. This prompt does not depend on P02 to P06.

Issue: {D11}. Branches: `cfc/p07-cdt-workers` in chen and atom, from `origin/feat/cpp-frontend-contexts`.

## Background

Read `x2cpg/passes/frontend/AstCacheStore.scala` (keys, fingerprints, the fragment format and how a hit is absorbed), c2cpg's `passes/AstCreationPass.scala` (the parse pool, timeouts, `cacheFingerprint`, `fileFingerprint`, the warm-restore path and `succeeded`), and how edg2atom runs edga processes with a timeout in `parser/EdgaRunner.scala` and `passes/EdgAstCreationPass.scala`, which is the model for supervising a child process. Read how c2cpg is started (`Main.scala`, `C2Cpg.scala`) so a worker can be started with the same classpath and configuration.

## Task: worker mode (D11)

Implement the worker mode D11 describes. The parent writes nothing new to the cache that a normal run would not write, and loads worker output only through `AstCacheStore`. A worker reads its configuration from the parent (a file or standard input, not a long command line) so Windows command-line limits do not apply. Workers must not inherit the parent's heap size; give them their own.

Write the failure tests with a test-only system property that names a file on which the worker exits, loops without checking for interruption, or allocates until it runs out of memory. Each case: every other file is in the graph, the named file has a parse-report record with the reason, the retry happened once, and the pool size was restored.

Compare the graphs from worker mode and normal mode on the D1 fixtures and on leveldb, FILE by FILE; they must be identical.

## Finish

Run the gates in normal mode (unchanged) and the hand-written arm in worker mode.
