# callsites: status

Updated 2026-11-03. This page says what has landed, what is in review and what comes next, so the
work can be picked up from here. The design is in the other callsites plans, starting with the
[overview](callsites-overview.md), and the rules for what counts as a use are in
[decision 0001](decisions/0001-callsites-what-counts.md); this page does not repeat them. The epics
are AppThreat/atom#304 to #311 and AppThreat/chen#239 to #241, all on the AppThreat roadmap board
under milestone v4.0.0 Pelorus.

## Where it stands

Every atom language now has a `callsites` source: JavaScript and TypeScript, Python, Java source,
PHP, Ruby, JVM bytecode (jars, Kotlin and Scala classes, Android APKs) and, once AppThreat/atom#364
merges, C and C++ on both frontends. Sprints 1 to 3 of the overview's order of work are done except
for the language-versions plan and a few JavaScript and ground-truth tasks listed below. Nothing of
the consumers plan (cdxgen and dep-scan) or the production plan has started, and cdxgen still runs
`callsites` for JavaScript and TypeScript only.

The work was done in six tranches. In each, one AI agent implemented a written brief and another
reviewed it, fixed what it found, measured again and opened the pull requests.

| tranche | pull requests | what landed |
|---|---|---|
| 1 | AppThreat/chen#260, AppThreat/atom#347 | the language-neutral core (`RecordCollector`, `BaseCallSiteSource`), the slice no longer fails on one bad node, TypeScript `implements`, the Python source and module-to-distribution mapping, pysrc2cpg shadowing and `import a.b` fixes |
| 2 | AppThreat/chen#261, AppThreat/atom#348 | the Java source, javasrc2cpg resolution gaps, several slices from one process (`atom usages --also-callsites`), tagging once per tagger input state (`atom-tag-state.json`), JS path-alias configs parsed once |
| 3 | AppThreat/chen#262, AppThreat/atom#349 | php2atom attributes, class constants, declared types, traits and positions, PHP 8.4 and 8.5 syntax, the PHP source, `vendor/` treated as dependencies |
| 4 | AppThreat/chen#263, #264, AppThreat/atom#350 | cpg2 3.1.2, ruby2atom constant references, names for calls on constants, heritage and mixins from gems, the Ruby source |
| 5 | AppThreat/atom#359 | the bytecode source with an application boundary for APKs and fat jars, the Android SDK path, synthetic line tables, class-to-artifact mapping from `META-INF` and the Gradle cache |
| 6 | AppThreat/edga#10, #11, AppThreat/chen#297, AppThreat/atom#364 | edga exports includes, macro uses and enumerators from the IL; c2cpg and edg2atom tag the declaring header of every call, reference, field access, constructor call and macro use; CDT parses C23 attributes, digit separators and C++23 explicit object parameters; the C and C++ source with builtin headers decided by where they resolved; `--external-paths` for C and C++ |

AppThreat/atom#364 is in CI with auto-merge on. It points atom's CI back at chen main, which already
has chen#297.

## Measurements

Package-level recall / precision of `callsites` against compiler-grade oracles, from each tranche's
pull request. `usages` is shown where the pull request measured it.

| language | project | callsites | usages |
|---|---|---|---|
| Python | vulpy | 0.866 / 0.990 | 0.654 / 0.568 |
| Python | dvpwa | 0.965 / 0.994 | 0.659 / 0.644 |
| Python | pygoat | 0.984 / 0.992 | 0.889 / 0.711 |
| Python | httpie | 0.874 / 0.949 | 0.429 / 0.462 |
| Java | petclinic | 0.949 / 0.985 | 0.543 / 0.628 |
| Java | sec-code | 0.896 / 0.997 | 0.666 / 0.999 |
| Java | webgoat | 0.932 / 0.992 | 0.680 / 0.995 |
| Java | mall | 0.982 / 0.993 | 0.707 / 0.998 |
| Java | shiro | 0.955 / 0.969 | 0.667 / 0.985 |
| PHP | DVWA | 1.0 / 1.0 | 0.374 / 0.957 |
| PHP | symfony-demo | 0.992 / 1.0 | 0.504 / 0.977 |
| PHP | koel | 1.0 / 1.0 | 0.581 / 0.98 |
| PHP | bookstack | 1.0 / 1.0 | 0.625 / 0.878 |
| Ruby | railsgoat | 1.0 / 1.0 | 0.0 |
| Ruby | maybe | 0.992 / 1.0 | 0.0 |
| Ruby | mastodon | 0.952 / 0.998 | 0.0 |
| bytecode | termux-api APK | 0.999 / 1.0 | |
| bytecode | termux APK | 0.998 / 0.999 | |
| bytecode | NewPipe APK (file level) | 0.998 / 1.0 | |
| bytecode | AppManager APK | 0.999 / 1.0 | |
| bytecode | detekt-formatting jar | 1.0 / 1.0 | |
| bytecode | scala-steward classes | 1.0 / 1.0 | |
| C, CDT | curl | 0.858 / 0.987 | |
| C, EDG | curl | 0.995 / 0.970 | |
| C, both | libuv | 1.0 / 1.0 | |
| C, CDT / EDG | openssl apps | 0.984 / 1.0, 0.992 / 1.0 | |
| C, CDT | jq | 0.912 / 0.918 | |
| C, EDG | jq | 0.945 / 0.924 | |
| C++, CDT | leveldb | 0.279 / 0.979 | |
| C++, EDG | leveldb | 0.781 / 0.937 | |

JavaScript and TypeScript reached 0.99 recall before this work (AppThreat/atom#293); the JS gaps
below are about positions, typed calls and purls. The bytecode and C tranches also checked records
at member level and the `builtin` flag against the oracle, because the package-level score hid
errors in both. On a built atom `callsites` takes less time than `usages` on every C project above.
Every tranche compared the other languages' slices with main and kept them identical, apart from
changes it intended (tranche 1 reports TypeScript `implements` as its own kind).

The scores come from a harness kept outside the repositories (decision 0001): oracles per language,
a scorer, member and builtin checks, and the corpus in
[callsites-corpus.corpus.json](callsites-corpus.corpus.json). Making it reproducible by others is
AppThreat/atom#312.

## Decisions taken

- Decision 0001: every reference is a use (declared types, `implements`, C macros, generated code);
  a typed call is attributed to the receiver's static type, with the declaring class kept as
  `declaringModule`; standard library uses are in the slice with `builtin` set; vendored code is
  external where it can be recognised, plus a path-regex option.
- `usages` stays and keeps being fixed where it is touched; `callsites` is the additional slice.
- A header, class or module is builtin by where it resolved (SDK, sysroot, compiler, standard
  library, platform jar), never by its name.
- C and C++ projects own the headers under the input root and under the compilation database's
  build directories; atom stores those directories in the atom (`callsites-c-layout.json`).

## Open work by epic

- Ground truth (atom#304): #313 gets its last language, C and C++, with atom#364. #312 (a
  reproducible harness), #314 (typed oracles for JS and Python), #315 (complete Java and C/C++
  truth) and #316 (a dynamic recall floor) have not started.
- Core and JS (atom#305): #320 (Vue, Svelte and Astro positions; the cause is astgen masking void
  elements), #321 (purls: filled for Python, Java, bytecode, PHP and Ruby, missing for JavaScript
  and C/C++), #322 (typed-call recall) and AppThreat/atom-parsetools#33 (type generation stalls on
  cdxgen's repository; the native type map work handles that input, see
  [parsetools-native-status.md](parsetools-native-status.md)).
- C and C++ (atom#308): #346 asks for the vendored-code option on every frontend and for BOM
  component locations; only C and C++ have it.
- Language versions (chen#241): #255 (report files that could not be parsed),
  atom-parsetools#34 (TC39 auto-accessors), atom#334 (Java method references and Lombok) and
  atom#335 (version matrix fixtures).
- Performance (atom#309): #339 (the cost of `usages` on large Java and Python projects).
- Consumers (atom#310): cdxgen#4690 to #4693 and dep-scan#552, #553, none started.
- Production (atom#311): #340 to #344, none started.

## Known gaps

- CDT's C++ recall on leveldb (0.279, against EDG's 0.781) has not been analysed.
- CDT misses curl's `bool` macro (1,459 rows of the recall gap on curl).
- On curl, EDG's reachables went from 31 flows on main to 267 with tranche 6; the edg2atom change
  that caused it was not isolated.
- Python precision on httpie (0.949) is held down by typed attribute reads, `super()` into external
  bases and quoted `TYPE_CHECKING` annotations, which the Python oracle does not attribute yet
  (#314).
- PHP names with one segment cannot be attributed by the scorer, and Ruby's recall has a ceiling
  because ruby2atom excludes `db/migrate` by default. Whether that default should change has not been
  decided.
- Bytecode renamed by R8 needs `mapping.txt` (atom#360), and calls through lambdas and method
  references are missing from reachables and callsites (atom#354). The SootUp migration
  (atom#351) will replace the Soot frontend these slices run on, in v5.

## Next

The recommended next round is the consumers plan, deliverables D1 to D4: cdxgen runs `callsites`
for every atom language (cdxgen#4690), attributes records to packages per ecosystem (#4691),
honours `--exclude` and `--annotate` (#4692), and dep-scan passes and keeps the slice
(dep-scan#552). That is the point of the work, and every language source it needs is on main. The
JavaScript and C/C++ purls (#321) belong in the same round, because cdxgen's attribution reads them.
After it, the production plan (#340 to #344, ending in the full corpus run and the release) and then
consumers D5 and D6, as the overview orders them. The language-versions and ground-truth tasks can
run beside either round.

Each round follows the overview's rules: tests with bad and good twins, a mutation table, equivalence
tests for changes that keep output, member-level and builtin checks beside the package score, and a
corpus subset per iteration with the full corpus at the end.
