# jimple2cpg on SootUp for JVM bytecode

| | |
| --- | --- |
| Epic | AppThreat/chen (opened with this plan) |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [sootup.corpus.json](sootup.corpus.json) |

## Why

See [sootup-overview.md](sootup-overview.md). For class files the spike found SootUp equal to Soot
or better on what the CPG reads: the same classes, methods and bodies, no body failures, lines on
every statement of commons-lang3 (Soot leaves 9,653 without one), the same named locals in 96 to
99 percent of cases and 10 to 241 local type differences per project. The work is in the details
listed below, each of which changes the CPG unless handled.

## Scope

`platform/frontends/jimple2cpg` in chen for `.class`, `.jar`, `.war`, `.ear`, `.zip` and class
directories, including Scala and Kotlin output. DEX and APK are in
[sootup-android.md](sootup-android.md). atom's flags and native image are in
[sootup-atom.md](sootup-atom.md).

## Findings from the spike that shape the work

1. **Input layout.** SootUp's directory input derives class names from paths. A directory that is
   itself a package (`java-jdkclasses-21/demo`) yields no classes and no error. chen's
   `extractClassesInPackageLayout` already rebuilds the package layout in a temporary directory and
   must stay in front of SootUp. Soot also read `META-INF/versions/9/module-info.class` from a
   multi-release jar as a class; SootUp does not.
2. **The JDK is the memory cost.** The `TypeAssigner` builds a type hierarchy that loads every class
   of every input location. With `JrtFileSystemAnalysisInputLocation` that is the whole JDK:
   scala-steward does not finish in a 1 GB heap (Soot runs it in 512 MB), and without the JDK
   location it runs in 512 MB in 2.3 s against Soot's 3.0 s. The JDK must be an input location that
   resolves classes on demand and is not scanned.
3. **Interceptors change the IR.** SootUp's default list runs `CopyPropagator` and
   `ConstantPropagatorAndFolder`, which replace named locals with literals (SootUp issue #1395), and
   no `UnusedLocalEliminator` or `LocalPacker`, which leaves about twice as many `$stack` locals as
   Soot. `LocalNameStandardizer` renames every local and must never run.
4. **Lambdas.** Soot rewrote each `invokedynamic` through `LambdaMetafactory` into a synthetic class
   (`Hasher$lambda_describe_0__2.bootstrap$`) named from a run-wide counter. SootUp keeps the
   `invokedynamic`, naming it `sootup.dummy.InvokeDynamic.<name>` with the bootstrap arguments,
   which include the handle of the implementation method. String concatenation and record methods
   stay `invokedynamic` in both.
5. **Metadata.** SootUp 3.0.1 does not keep `SourceFile` (develop does, PR #1787), gives no line for
   classes, fields and methods (Soot did not either for bytecode), merges visible and invisible
   annotations into untyped `AnnotationUsage` maps, and stores parameter annotations on the
   parameter locals (develop adds `getParameterAnnotations`, PR #1755). Annotation element and
   member order follow `HashMap` in 3.0.1 and are fixed on develop.
6. **Errors.** There is no `ignore_resolution_errors`: an interceptor that fails throws from
   `getBody()`, and in 3.0.1 a broken control flow graph made `getStmts()` recurse until the stack
   overflowed (17 to 164 bodies per APK; none with the 2026-10-08 snapshot). `StackOverflowError`
   is fatal for Scala's `Try`, so failures must be caught as `Throwable` per method.
7. **Threads.** `JavaView.getClass` is synchronized, and the type hierarchy's caches are plain
   `HashMap`s built lazily. chen's `ConcurrentWriterCpgPass` builds ASTs in parallel.
8. **Identity.** SootUp's `Local.equals` compares names, statements compare by identity. Maps keyed
   by `Local` merge same-named locals.

## Deliverables

### D1. Engine switch and dependencies

Add SootUp (`sootup.java.bytecode.frontend`, `sootup.interceptors`, and later the APK frontend) next
to Soot, behind `Config.engine` (`soot` default, `sootup`), with `--engine` on jimple2cpg's command
line. The Soot code path does not change. Finished when both engines build the existing test CPGs
and the test fixtures run once per engine.

### D2. Input locations and the JDK

Build a `JavaView` from: the package-layout temporary directory as `Application`; the Scala SDK jar
and any `--dynamic-dirs` as `Library`; the JDK as a `Library` location that resolves single classes
on request (jrt:/ on the JVM, `JImage` and `jmods` in the native image, `rt.jar` for JDK 8) and
returns nothing from a full scan. `JrtFileSystemAnalysisInputLocation` opens jrt:/ in a static
initialiser and cannot be used in the native image. WAR and EAR keep chen's extraction. A scaling
test (testing D6) asserts that the number of JDK classes resolved grows with the classes the input
references, not with the size of the JDK.

### D3. Interceptor policy

An explicit list instead of `BytecodeBodyInterceptors.Default`: `NopEliminator`,
`EmptySwitchEliminator`, `CastAndReturnInliner`, `LocalSplitter`, `Aggregator(true)` (which only
folds `$` stack locals), `TypeAssigner`, then a chen interceptor that drops unused `$` stack locals
and keeps unused named ones (SootUp's `UnusedLocalEliminator` drops both). No constant propagation
or folding, no copy propagation into named locals, no `LocalNameStandardizer`. Each choice comes
with a fixture that shows the effect. If a body fails with this list, retry once with the minimal
list (no aggregation) and log it; if that fails too, emit the method without a body as Soot's path
does for a body Soot cannot read.

### D4. AstCreator on SootUp

Port `AstCreator` to SootUp's API: statements (`JSwitchStmt` replaces table and lookup switches;
branch targets come from the body's graph), expressions and references, traps from the exceptional
successors (no public trap list in 3.0.1, issue #1812), modifiers, supertypes, fields, parameters
and their names, annotations with element values (one visibility, sorted elements), parameter
annotations, `lineNumberEnd` from `Body.getPosition()` instead of counting printed lines. The two
creators share everything that does not touch the library, so the transition does not duplicate
1,300 lines. Finished when the existing suites pass on SootUp, with any changed expectation listed
in the pull request and justified by the oracle.

### D5. invokedynamic

Resolve `LambdaMetafactory` and `altMetafactory` call sites to the implementation method from the
bootstrap handle: the call keeps `DYNAMIC_DISPATCH` and names the functional interface method, and
a reference to the implementation method (a `METHOD_REF`, as javasrc2cpg emits for method
references) carries its full name, so data flow and reachables can follow it. String concatenation
becomes the same `<operator>.addition` chain or `StringConcatFactory` call javasrc2cpg would give,
records' `ObjectMethods` become calls to the generated methods. No name depends on a counter. This
removes the 7,900 unstable lambda names from scala-steward's `usages`.

### D6. Metadata parity

`SourceFile` on every type declaration (needs SootUp with PR #1787, or chen reads it with ASM
from the class bytes it already extracts), annotation order, generic signatures for `TYPE_DECL` and
`METHOD` where the CPG has a place for them, inner and outer class relations. Each is a fixture
test against the oracle.

### D7. Concurrency, determinism and failure isolation

Resolve classes and bodies with a bounded number of threads that does not corrupt shared caches:
warm the type hierarchy once before the parallel pass, or resolve bodies serially and build ASTs in
parallel, whichever the measurements in D8 favour. Members are sorted before AST creation. Each
method is built in isolation: any `Throwable` is caught, logged with the method signature, and the
method is emitted without a body. Two runs give identical fingerprints (testing D6).

### D8. Performance and memory

Measure each input of the corpus on both engines with atom's `--perf-report`, peak RSS and
heap-capped runs (512 MB, 1 GB, 2 GB). Targets: no worse than Soot in wall time; peak memory at
most 1.2x of Soot; every S and M input completes in the heap Soot needs. Profile with JFR where a
target is missed. The numbers go into the pull request and the epic.

## Risks and open questions

- The SootUp release this depends on (see the overview's first decision). Develop's API already
  differs from 3.0.1 (hash-consed identifiers, PR #1745), so pick the version before D4 starts and
  port once.
- `TypeAssigner` falls back to `java.lang.Object` when a supertype is missing, where Soot kept the
  phantom type. With partial classpaths (most jars) local types may get coarser. D2's library
  locations and a fixture with a missing dependency measure it.
- Line numbers: SootUp's PR #1763 fixed lines shifted during operand conversion after 3.0.1;
  without it some statements get the line of a neighbour.
- Kotlin and Scala output is not covered by SootUp's own tests; the fixtures in testing D5 are the
  only check.

## Outcome

Filled in when the work ends.
