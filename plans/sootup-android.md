# jimple2cpg on SootUp for Android (APK, DEX and bundles)

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/chen/issues/267 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [sootup.corpus.json](sootup.corpus.json) |

## Why

Android is where atom's bytecode support is weakest today (AppManager needs 12.7 GB and 216 s,
AppThreat/atom#328) and where SootUp is weakest too. Soot's own README says to stay on Soot for
"robust Android support". The spike measured SootUp's APK frontend on termux-api, termux, NewPipe
and AppManager:

| | Soot 4.7.1 | SootUp 3.0.1 | SootUp snapshot 2026-10-08 |
| --- | --- | --- | --- |
| locals typed with the default dex interceptors | all | none (`unknown`) | none |
| bodies that fail with `TypeAssigner` added (termux-api, NewPipe, AppManager) | 0, 0, 0 | 17, 138, 164 | 0, 0, not run |
| statements (termux-api) | 251,435 | 420,547 | 423,269 |
| methods whose line set differs from Soot's (NewPipe) | | 56,864 of 61,469 | 57,000 of 61,607 |
| named locals Soot keeps that SootUp loses (NewPipe) | | 52,147 of 102,186 | 52,479 of 102,614 |
| local type differences for same-named locals (NewPipe) | | 30,274 | 30,363 |
| time, termux / NewPipe / AppManager, IR only | 5.7 s / 21.6 s / 47.2 s | 4.3 s / 31.3 s / 61.9 s | 3.2 s (termux) / 18.1 s (NewPipe) |

Where the lines differ, `dexdump` agrees with Soot: SootUp attributes positions to the wrong
statements on R8-optimised dex (NewPipe's `NativePromise.lambda$makeThenFinally$4` has one
position, line 1, and SootUp reports 249). The October dex fixes on SootUp's develop branch (trap
handling, shared constants, the null transformer, thread safety: PRs #1776, #1836, #1845, #1849)
are not in any published build, so these numbers may already be better on develop. With a capped
heap SootUp needs less memory than Soot for APKs, because the APK path has no JDK location: termux
runs in a 512 MB heap in 3.2 s against Soot's 5.3 s.

## Scope

`.apk`, `.dex`, `.apkm`, `.apks` and `.xapk` inputs of jimple2cpg. The app/library boundary and
the callsites adapter for Android belong to the callsites plan
([callsites-jvm-android.md](callsites-jvm-android.md)) and are reused here unchanged.

## Deliverables

### D1. Measure develop first

Use the 3.0.2 release, or until it exists a local, unpublished build of SootUp's develop branch, and
rerun the IR probe and the line oracle on the four corpus APKs and the DEX fixtures. Classify every
remaining difference with the oracle (testing D4): SootUp wrong, Soot wrong, or both acceptable.
Report the SootUp-wrong classes upstream with a minimal DEX ([sootup-upstream.md](sootup-upstream.md)).
This deliverable decides whether D2 to D8 proceed on SootUp or whether v5 keeps Soot for DEX (the
overview's second decision). Finished when the classification table is in the epic.

### D2. APK, DEX and bundle inputs

`ApkAnalysisInputLocation` per APK (multidex is read through dexlib2's container), chen's existing
bundle extraction for split APKs, a plain `.dex` input, and duplicate classes across dex files
resolved the way Android's class loader does (first dex wins) with a log line. SootUp's APK
frontend keeps state in static singletons (`DexFileProvider`, `DexUtil.androidVersionInfo`): reset
or isolate them so two APKs in one JVM do not share a cache. The hostile inputs must fail cleanly.

### D3. android.jar and API level

SootUp only reads the API level from the manifest and does not load `android.jar` as a class
source. Add the platform jar as a `Library` location chosen from `--android-sdk`, which accepts the
`android.jar` file or the platforms directory (the API level from the manifest picks the jar,
falling back to the highest available). Without it, Android framework supertypes are missing and
the type assigner falls back to `java.lang.Object`.

### D4. Typed DEX bodies

Run a type-assigning interceptor list on DEX bodies (SootUp's dex interceptors plus the policy of
[sootup-jvm.md](sootup-jvm.md) D3). Fixtures assert the types of `this`, parameters, locals that
hold framework types, and locals whose only definitions are constants (the dex `const 0` that is
both `null` and `0`). Target: no more locals typed `unknown` or `java.lang.Object` than Soot gives
on the corpus APKs, with the remaining ones listed.

### D5. Correct line numbers

Statements get the line of the dex position that covers their instruction, as `dexdump` reports
it. A fixture built with D8 and one with R8 line compaction assert exact lines. If SootUp's develop
still misattributes them, fix it upstream (preferred) or correct them in chen from the dex debug
info, which chen can read with the same dexlib2.

### D6. Local names and statement count

Keep the debug-info names of locals (SootUp loses half of NewPipe's), and bring the statement count
close to Soot's: the extra statements come from untyped constants and from moves the dex
transformers leave. Measure with the IR probe; a fixture per shape.

### D7. Classes the APK bundles from the platform

R8 and D8 bundle desugared library classes (`java.util.function.*`, `java.nio.file.*`, `j$.*`) into
the APK. Soot treats `java.*` as library and drops them from the application classes; SootUp makes
them application classes (48 extra classes in NewPipe), where they collide with the JDK and
android.jar types. Mark them as bundled platform code with a tag rather than dropping them, so
callsites can still attribute them, and keep them out of the app's own classes.

### D8. Performance

Targets from AppThreat/atom#328 for AppManager, and no worse than Soot in wall time and peak memory
on the other APKs. The IR probe already shows SootUp faster than Soot on termux and NewPipe with
the snapshot; the CPG stage is measured once D2 to D7 work.

## Risks and open questions

- SootUp's APK frontend depends on `org.smali:dexlib2` 2.5.2 (2021, archived; issue #1810). Soot
  uses `com.android.tools.smali:smali-dexlib2` 3.0.9 in the same Java package, so the two cannot be
  on one classpath. During the transition one of them is shaded or loaded in its own class loader.
  Whether dexlib2 2.5.2 reads the newest DEX format versions is not yet checked; a fixture built for
  API 35 and 36 settles it.
- If develop does not fix the line attribution and a fix in chen is needed, chen would read the dex
  debug info twice; acceptable, but it couples chen to dexlib2.
- Building Soot's IR for AppManager takes 47 s of atom's 216 s; the rest is CPG passes, tagging and
  slicing, so the frontend change alone will not meet atom#328's target.

## Outcome

Filled in when the work ends.
