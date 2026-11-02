# SootUp migration: baselines, equivalence harness and test plan

| | |
| --- | --- |
| Epic | AppThreat/chen (opened with this plan) |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [sootup.corpus.json](sootup.corpus.json) |

## Why

Swapping the library under a frontend changes thousands of small things at once: local names,
statement order, line numbers, types, how lambdas are named. Corpus scores alone would hide a
regression in one of them behind an improvement in another. Every deliverable of the migration is
therefore gated by tests that compare the two engines directly, at three levels: the Jimple IR, the
CPG, and atom's slices. This plan builds those tests and records the baselines from main they
compare against. The other SootUp plans refer to it for their gates.

## Scope

Test tooling in chen and atom, oracles for line numbers and local names, recorded outputs from
main, and fixtures. No change to what the frontend produces.

## Test levels

| level | tool | compares | runs in |
| --- | --- | --- | --- |
| L1 IR | IR probe (D2) | per method: statements by kind, lines, locals and types, invoke targets; per class: supertypes, annotations, members | chen tests (fixtures), local corpus run |
| L2 CPG | CPG fingerprint (D3) | per method: multisets of node labels with key properties, AST and CFG edge shapes, call names and full names | chen tests on both engines |
| L3 frontend tests | the existing ~310 jimple2cpg tests plus the new fixtures (D5) | expected CPG facts | chen CI on Linux, macOS, Windows |
| L4 slices | `reachables`, GraphML, `callsites`, `usages`, `data-flow` | atom output against the main baseline (D1) | atom CI fixtures; corpus once per phase |
| L5 oracles | `dexdump` and `javap` line tables and local tables (D4) | which engine is right when they differ | local, recorded results in tests |
| L6 performance | atom `--perf-report`, max RSS, heap-capped runs | wall time, peak memory, operation counts | local; scaling tests in CI |
| L7 native image | jimple native corpus `run.sh` | native against JVM slices | atom release workflow |

Rules carried over from the callsites work: unit tests with bad and good twins for each shape;
a mutation table in each pull request (revert each fix and name the test that fails); equivalence
tests where output must not change; scaling tests count operations, never wall-clock time; the
corpus is a single before-and-after profile per phase, never a tuning loop. Reviews look for rules
keyed on corpus class or package names.

## Deliverables

### D1. Baselines from main (atom)

Run atom main (chen b5b6dccb, atom 7733d10, then again after the callsites bytecode tranche) on
every input in [sootup.corpus.json](sootup.corpus.json): build the atom with `usages`, then
`callsites`, `reachables`, and for S inputs `data-flow` and a GraphML export, all on the same
atom, with `--perf-report`. Record wall time and peak RSS. Store the outputs (gzipped) where the
review agents can read them, and record their SHA-256 in the manifest. Finished when every input
has all outputs, or a recorded failure, and the table of times and memory is in the epic.

### D2. IR probe in chen

Move the spike's probe into chen's jimple2cpg test tree as a tool with two backends (Soot and
SootUp) that writes one JSON line per class and per method in a shared shape: statements by kind,
lines, statements without a line, locals with names and types, invoke expressions with kind and
target signature, supertypes, annotations, member counts and body failures. A comparison script
reports, per input, the counts the overview table shows and the first examples of each kind of
difference. Finished when it runs on every corpus input with both engines and its report is
attached to the epic.

### D3. CPG fingerprint and equivalence tests

A test helper that reduces a CPG to per-method multisets that do not depend on node ids or on the
names of temporaries: node labels with `CODE`, `NAME`, `FULL_NAME`, `METHOD_FULL_NAME`,
`TYPE_FULL_NAME`, `LINE_NUMBER` and `ORDER`; AST child label sequences; CFG edge shapes;
`inheritsFromTypeFullName`; annotations. `$stackN` and `#N` local names are normalised. A suite runs
each jimple2cpg fixture through both engines and asserts equal fingerprints, with an explicit,
reviewed allow-list for the expected differences (lambda names, extra lines, split locals). The
allow-list is part of the test, so a new difference fails it.

### D4. Line and local-name oracles

For class files, read `LineNumberTable` and `LocalVariableTable` with ASM; for DEX, read the
debug-info positions and locals with dexlib2 or `dexdump`. Given a method and a statement, the
oracle says which lines and names are possible. Used by D2's report to say which engine is right,
and by fixtures to assert lines directly. Finished when the NewPipe and AppManager line
differences are classified as right or wrong per engine.

### D5. Fixtures for the shapes that differ

Small compiled fixtures, each with exact expected CPG facts, checked in with their sources and the
compiler version that built them:

- Java 8, 17, 21 and 25 class files: lambdas and method references (every `LambdaMetafactory`
  handle kind), string concatenation through `invokedynamic`, records (`ObjectMethods`), sealed
  types, nest mates, switch on strings, enums and patterns, try-with-resources, synchronized.
- Local variable slot reuse (two variables of different types in one slot), a method without a
  `LocalVariableTable`, and one compiled by ECJ.
- Parameter annotations on concrete and abstract methods, `MethodParameters`, type annotations,
  annotation element order, invisible and visible annotations.
- Scala 2.13 and 3 (`$anonfun`, lazy vals, `LambdaDeserialize`), Kotlin (`$default` methods,
  `@JvmStatic`, inline classes, coroutines).
- DEX: a multidex APK, an R8-optimised APK with line compaction, an APK that bundles desugared
  `java.*` or `j$.*` classes, duplicated classes across dex files, native methods, and the split
  bundles (`.apkm`, `.apks`, `.xapk`).
- Hostile inputs from the Android corpus (zip slip, zip bomb, deep bundles), which must fail
  cleanly without writing outside the temporary directory.

### D6. Determinism and scaling tests

Two runs of each fixture on the same engine give identical fingerprints and identical slices. A
scaling test builds the CPG for a generated jar with N classes and counts classes resolved and
bodies built, so a change that loads every JDK class on each run fails the test instead of only
showing up as memory.

## Risks and open questions

- Some differences have no right answer without a source file (R8 line compaction). D4 classifies
  them; the fixture tests then assert the behaviour chosen in the Android plan.
- The corpus APKs are GPL or MPL licensed. They stay in release assets and are not copied into
  chen's tests; fixtures are built from sources written for these tests.
- `usages` is not deterministic (lambda counters, order), so it shows trends only. `reachables`
  and GraphML are the outputs to compare.

## Outcome

Filled in when the work ends.
