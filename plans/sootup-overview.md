# jimple2cpg on SootUp (overview)

| | |
| --- | --- |
| Epic | Each plan below has its own epic; this file is the map |
| Owner | @prabhu |
| AI use | Auto: implementation agents write each deliverable, a reviewing agent verifies, refactors and opens the pull request, a maintainer approves |
| Corpus | [sootup.corpus.json](sootup.corpus.json) |

## Why

chen's `jimple2cpg` turns JVM bytecode (jars, class directories, WARs, Scala and Kotlin output) and
Android bytecode (APK, DEX and split bundles) into a code property graph through
[Soot](https://github.com/soot-oss/soot) 4.7.1. atom uses it for `-l jar`, `-l apk`, `-l dex` and
the bytecode half of `-l scala`. Soot's README names
[SootUp](https://github.com/soot-oss/SootUp) as its successor: a rewrite with an immutable IR, no
global `Scene`, a pluggable list of body interceptors in place of the `jb` packs, and
per-input-location sources. The same README says SootUp is not yet feature-complete and that Soot
lives on for projects that need "robust Android support", which the spike below confirms.

Soot's design costs atom today:

- One global `Scene`, `Options` and `G.reset()` per run, so two frontends cannot run in one JVM
  and jimple2cpg must reset Soot after every CPG (chen's `build.sbt` runs test suites one at a
  time partly because of Soot's `Scene`).
- Soot rewrites every `invokedynamic` lambda into a synthetic class named from a global counter
  (`Main$$_anonfun_run_1__5.bootstrap$`). The counter changes from run to run, so slices that
  name lambdas are not reproducible, and the real target method is lost. On scala-steward the
  `usages` slice holds 7,900 such names.
- 9,653 of 49,735 statements in commons-lang3 carry no line number in Soot's Jimple; SootUp
  gives a line to every one of them.
- A small APK (InsecureBankv2, 3 MB) needs 43 s and 11 GB to build its atom; AppManager needs
  12.7 GB and 216 s (AppThreat/atom#328).

SootUp is not a drop-in replacement. A spike in a chen worktree (branch `spike/sootup`, never
pushed) dumped the IR of both libraries for the same inputs and compared them method by method.
It found the following, against SootUp 3.0.1 and the 3.0.2 snapshot of 2026-10-08.

| input | methods | Soot statements without a line | SootUp | bodies that fail in SootUp 3.0.1 / snapshot | named locals Soot keeps that SootUp loses |
| --- | ---: | ---: | ---: | ---: | ---: |
| commons-lang3 3.18.0 | 4,917 | 9,653 | 0 | 0 / 0 | 650 of 11,119 |
| scala-steward (Scala 2.13 classes) | 11,741 | 26,313 | 4,213 | 0 / 0 | 204 of 21,389 |
| termux-api (APK) | 20,075 | 53,214 | 58,314 | 17 / 0 | 1,322 of 16,512 |
| NewPipe (APK, R8) | 65,483 | 158,173 | 133,873 | 138 / 0 | 52,479 of 102,614 |
| AppManager (APK) | 225,118 | 1,053,199 | 1,532,812 | 164 / not run | 18,280 of 187,328 |

For class files, SootUp is equal or better on everything the CPG reads, with known, fixable
differences. For DEX it is not ready: with its default dex interceptors every local is typed
`unknown`; adding the `TypeAssigner` types them but leaves about 900 locals per mid-size APK as
`java.lang.Object` (including `this`), the statement count grows by 70 to 80 percent, and on
NewPipe the line numbers differ from Soot's in 57,000 of 61,607 methods. Checked against
`dexdump` positions, Soot's lines are right and SootUp's are wrong (for example
`NativePromise.lambda$makeThenFinally$4`, whose only position is line 1, comes out at line 249).

## The plans

| plan | epic | what |
| --- | --- | --- |
| [sootup-testing.md](sootup-testing.md) | [AppThreat/chen#265](https://github.com/AppThreat/chen/issues/265) | baselines from main, the IR probe, CPG fingerprints, oracles and the test plan every other epic is gated by |
| [sootup-jvm.md](sootup-jvm.md) | [AppThreat/chen#266](https://github.com/AppThreat/chen/issues/266) | jimple2cpg on SootUp for class files, jars, WARs and JVM languages |
| [sootup-android.md](sootup-android.md) | [AppThreat/chen#267](https://github.com/AppThreat/chen/issues/267) | APK, DEX and bundles on SootUp, with typed bodies and correct lines |
| [sootup-atom.md](sootup-atom.md) | [AppThreat/atom#351](https://github.com/AppThreat/atom/issues/351) | atom on the new frontend: slice parity, CLI, native image, consumers, removing Soot |
| [sootup-upstream.md](sootup-upstream.md) | [AppThreat/chen#268](https://github.com/AppThreat/chen/issues/268) | the SootUp fixes and releases this work depends on, reported and contributed upstream |

All items carry the `v5.0.0` milestone in chen and atom.

## Order of work

```
phase 0  testing D1–D4 (baselines, probe, fingerprints, oracles)  ‖  upstream D1–D2 (report, release)
phase 1  jvm D1–D8 behind engine=sootup                            ‖  upstream D3–D5
phase 2  android D1–D8 behind engine=sootup                        ‖  atom D1–D3
phase 3  atom D4–D6: default engine sootup for jar, then apk; Soot removed when every gate passes
```

The work starts after the callsites tranche for JVM bytecode and Android (AppThreat/atom#326,
#327, #328) has merged, because both change `jimple2cpg/passes/AstCreator.scala`. That tranche's
outputs become part of the baseline.

## How the switch stays safe

Both engines live side by side during v5 development. `jimple2cpg` gets an `engine` setting
(`soot` or `sootup`, through `--frontend-args engine=` in atom) and the test suites run against
both. The default moves to `sootup` per input kind (class files first, then DEX) only when that
kind passes every gate in [sootup-testing.md](sootup-testing.md). Soot and its `smali-dexlib2`
are removed in the last deliverable of [sootup-atom.md](sootup-atom.md). The two libraries cannot
share a classpath for DEX: SootUp 3.0.1 depends on `org.smali:dexlib2` 2.5.2 and Soot on
`com.android.tools.smali:smali-dexlib2` 3.0.9, which use the same Java package. The transition
therefore isolates the DEX path of one engine (a shaded copy or a separate class loader), which
the Android plan settles.

## Gates for changing the default

1. Every jimple2cpg test passes on both engines, and the new fixture tests pass on SootUp.
2. The IR probe shows no body failures, no fewer lines and named locals than Soot on the corpus,
   and every remaining difference is listed and explained.
3. `reachables` and GraphML on the S inputs are identical to main, or each difference is listed as
   a fix (for example a lambda resolved to its implementation method).
4. `callsites` recall and precision on the bytecode projects are no worse than after the callsites
   tranche for bytecode.
5. Two runs give byte-identical reachables and GraphML.
6. Wall time at most 1.0x and peak memory at most 1.2x of main on every M and L input; AppManager
   meets the target of AppThreat/atom#328.
7. The native image and the JVM build give the same slices on the jimple native corpus, on Linux,
   macOS and Windows.

## Decisions for a maintainer

1. **Which SootUp to build against.** The fixes this work needs (line attribution, local names
   when a slot is reused, annotation and member order, parameter annotations, SourceFile, the dex
   transformer fixes) are on SootUp's develop branch, 485 commits after 3.0.1, and the snapshot
   repository stopped at 2026-10-08. Decided (2026-11-02): wait for the 3.0.2 release rather than
   publish a build of a develop commit. Work that does not need those fixes (the test plan, the
   upstream reports, measurements) goes ahead; the port of `AstCreator` (jvm D4) starts on 3.0.2.
2. **What to do if DEX does not reach parity in time.** Ship v5 with SootUp for class files and Soot
   for DEX (isolated), or hold the release. The Android plan measures this early so the decision
   can be made with numbers.
3. **The v5 milestone.** The epics carry the `v5.0.0` milestone in chen and atom.

## Risks

See the Risks sections of each plan. The cross-cutting ones are SootUp's release lag and API churn
(develop already changes the `ApkAnalysisInputLocation` constructor and hash-conses identifiers),
the memory cost of SootUp's type hierarchy scanning every class of every input location (with
the JDK as an input location, scala-steward does not finish in a 1 GB heap; without it, it runs
in 512 MB in 2.3 s), and the collision with the callsites bytecode tranche in `AstCreator.scala`.
