# callsites: one occurrence slice for every atom language (overview)

| | |
| --- | --- |
| Epic | Each plan below has its own epic; this file is the map |
| Owner | @prabhu |
| AI use | Auto: implementation agents write each deliverable, a reviewing agent verifies, refactors and opens the pull request, a maintainer approves |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

cdxgen turns atom's `usages` slice into `evidence.occurrences`, and dep-scan reads those occurrences
to decide which dependencies a project really uses. Measured against compiler-grade ground truth on
the callsites corpus (JS/TS, Python, Java, PHP, Ruby, C/C++, Android APKs and Kotlin/Scala jars), `usages` finds 46–77 % of external use sites in Java, JavaScript and Python (median
recall), 1–19 % in PHP and none in Ruby, and its JavaScript and Python output is 34–38 % noise, most of
it import lines and misplaced lines. The `callsites` slice, added for JavaScript and TypeScript in
v4 (AppThreat/atom#293), reaches 0.99 recall there. Measurement prototypes of the same design for
Python and Java reach a median 0.90 and 0.83 recall at 0.99 precision, and for Android APKs and
Kotlin/Scala jars 0.83–1.00 (where `usages` finds almost nothing in APKs). C/C++ `usages` already does
well on calls with both frontends, CDT and EDG, but misses external globals, enum constants and
(on EDG) macro constants. PHP and Ruby need frontend work before any slice can be accurate.

## The plans

| plan | epic repository | what |
| --- | --- | --- |
| [callsites-ground-truth.md](callsites-ground-truth.md) | atom | corpus, oracles per language, scorer, gates, CI fixtures |
| [callsites-core-js.md](callsites-core-js.md) | atom | robustness, a language-neutral core, the JS/TS gaps |
| [callsites-python.md](callsites-python.md) | atom | Python adapter and type-recovery fixes |
| [callsites-jvm-android.md](callsites-jvm-android.md) | atom | Java source, JARs (Kotlin, Scala bytecode) and Android APK/DEX |
| [callsites-c-cpp.md](callsites-c-cpp.md) | atom | C and C++ on both frontends, CDT and EDG |
| [callsites-php.md](callsites-php.md) | chen | php2atom names, attributes, types, vendor handling, then the adapter |
| [callsites-ruby.md](callsites-ruby.md) | chen | ruby2atom constant references, then the adapter |
| [callsites-language-versions.md](callsites-language-versions.md) | chen | syntax coverage per language version, in every frontend and oracle |
| [callsites-performance.md](callsites-performance.md) | atom | tag once, one process for several slices, usages cost |
| [callsites-consumers.md](callsites-consumers.md) | atom | cdxgen and dep-scan consume callsites for every language |
| [callsites-production.md](callsites-production.md) | atom | determinism, failure isolation, memory, docs, release chain |

## Order of work

```
sprint 1  ground truth (rest) ‖ core-js D1–D3 ‖ python ‖ performance D1–D3      → corpus run
sprint 2  jvm-android (Java source first) ‖ consumers D1–D4 ‖ core-js D4–D6     → corpus run
sprint 3  php ‖ ruby ‖ c-cpp ‖ jvm-android (bytecode, APK) ‖ language-versions  → corpus run
sprint 4  production ‖ consumers D5–D6                                          → full corpus, release
```

Chen-side deliverables of each language plan can start at once: they need only the oracles and
their own tests. The atom adapters build on core-js D2 (the core split).

## How work is checked

Every deliverable is gated by tests in the repository it lands in, never by corpus scores alone:

- unit tests with bad and good twins for each shape (a fixture of a few lines with exact expected
  records);
- a mutation table in the pull request: revert each fix and name the test that fails;
- equivalence tests (byte-identical slices and tags) for any change meant to keep output;
- scaling tests that count operations, never wall-clock time.

A five-minute corpus subset runs once per iteration. The full corpus is scored at the end of every
sprint and is mandatory before the release. Reviews also look for benchmark gaming: rules keyed on
corpus project, package or method names, thresholds tuned to one project, and detectors that read
source text instead of the graph.

## Maintainer rules that bind every plan

1. No schema versioning: atom and cdxgen change together, and fields may be renamed outright.
2. `usages` stays and is fixed where it is touched; `callsites` is the additional, better slice.
3. Accuracy over time: no type budgets and no skipped analysis. Performance work keeps output
   byte-identical.
4. Tagging runs for every command. Make it cheaper with identical tags; never skip it.
5. Detectors read the graph, not source text.

## Cross-cutting risks

See [callsites-risks.md](callsites-risks.md): environment and permission blockers, schema changes
that ripple through overflowdb2, cpg2, chen, atom and cdxgen, oracle limits, package-mapping
ambiguity, release coupling with cdxgen and dep-scan, and the policy decisions a maintainer has to
make (what counts as a use).
