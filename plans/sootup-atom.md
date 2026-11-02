# atom on the SootUp frontend

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/351 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [sootup.corpus.json](sootup.corpus.json) |

## Why

atom builds every JVM bytecode and Android atom through jimple2cpg, and cdxgen and dep-scan read
its slices. A frontend change is only finished when atom's outputs are at least as good, its
native image works on every platform, and the flags that only made sense for Soot are gone.

## Scope

atom's `createJimple2Cpg`, its CLI and `--frontend-args`, the native-image configuration, the CI
workflows, the documentation, and the check that cdxgen's `evinse` and dep-scan still read the
bytecode slices. The frontend itself is in [sootup-jvm.md](sootup-jvm.md) and
[sootup-android.md](sootup-android.md).

## Deliverables

### D1. Slice parity report

Run atom with `--frontend-args engine=sootup` on every corpus input and compare with the main
baseline ([sootup-testing.md](sootup-testing.md) D1): `reachables` and GraphML must match or every
difference must be explained; `callsites` recall and precision against the bytecode oracle must be
no worse; `usages` and `data-flow` differences are summarised by kind (lambda names, lines, types).
The report is regenerated at the end of each phase and attached to the epic.

### D2. Lambda and method-reference flows

With lambdas resolved to their implementation methods (jvm D5), reachables can follow a flow into
a lambda body, which Soot's synthetic `bootstrap$` classes hid. Add fixture tests in atom for a
source reaching a sink inside a lambda and a method reference, in Java and Scala, and a callsites
test that a library method called only through a method reference is a use.

### D3. CLI and configuration

- `--full-resolver` set Soot's whole-program options and call-graph phases, but atom never ran
  Soot's call graph. Keep the flag as a no-op with a deprecation note, then remove it in v5.0.0.
- `--android-sdk` accepts the `android.jar` file or the platforms directory.
- `--frontend-args engine=soot|sootup` during the transition; `dynamic-dirs` and `dynamic-pkgs`
  become library locations.
- `CHEN_JIMPLE_IGNORE_DIRS` keeps working.

### D4. Native image and platforms

The native image cannot use jrt:/ and SootUp's `JrtFileSystemAnalysisInputLocation` opens it in a
static initialiser, so the JDK location from jvm D2 is used there. Update `reflect-config.json` and
the resource configuration for SootUp (Guava, slf4j, the interceptors), build the native image in
the release workflow, and run the jimple native corpus with native and JVM builds, comparing slices
with its `compare.py`. CI runs the bytecode fixtures on Linux, macOS and Windows.

### D5. Consumers

Check that cdxgen's `evinse` and dep-scan's reachability read the bytecode slices built on SootUp:
the purls and occurrences for the bytecode projects of the callsites corpus match the main build
except for the differences listed in D1. Lambda names change from `...__N.bootstrap$` to the
implementation methods; any consumer rule that matched the old names is updated.

### D6. Default and removal

Switch the default engine to SootUp for class files when every gate in the overview passes for
them, then for DEX. When both have switched, remove Soot, `smali-dexlib2`, the `engine` setting and
the Soot code path from chen, and the related options from atom. Release notes describe the changed
outputs (lambda names, lines, local types) with examples.

## Risks and open questions

- Users who script against `bootstrap$` names in `usages` will see them change; the release notes
  must say so.
- The native image may need more configuration than the JVM run shows; the native corpus run is the
  check, not the build succeeding.

## Outcome

Filled in when the work ends.
