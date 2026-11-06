# callsites: status

Updated 2026-11-06. This page says what has landed, what is in review and what comes next, so the
work can be picked up from here. The design is in the other callsites plans, starting with the
[overview](callsites-overview.md), and the rules for what counts as a use are in
[decision 0001](decisions/0001-callsites-what-counts.md); this page does not repeat them. The epics
are AppThreat/atom#304 to #311 and AppThreat/chen#239 to #241, all on the AppThreat roadmap board
under milestone v4.0.0 Pelorus.

## Where it stands

Every atom language now has a `callsites` source: JavaScript and TypeScript, Python, Java source,
PHP, Ruby, JVM bytecode (jars, Kotlin and Scala classes, Android APKs) and C and C++ on both
frontends. Sprints 1 to 3 of the overview's order of work are done except
for parts of the language-versions plan and a few ground-truth tasks listed below. The
production plan is under way: output is deterministic, memory is checked and every language is
documented. cdxgen still runs `callsites` for JavaScript and TypeScript only;
its part and dep-scan's are now planned in their own organizations (see below).

The work was done in ten rounds. In each, one AI agent implemented a written brief and another
reviewed it, fixed what it found, measured again and opened the pull requests.

| tranche | pull requests | what landed |
|---|---|---|
| 1 | AppThreat/chen#260, AppThreat/atom#347 | the language-neutral core (`RecordCollector`, `BaseCallSiteSource`), the slice no longer fails on one bad node, TypeScript `implements`, the Python source and module-to-distribution mapping, pysrc2cpg shadowing and `import a.b` fixes |
| 2 | AppThreat/chen#261, AppThreat/atom#348 | the Java source, javasrc2cpg resolution gaps, several slices from one process (`atom usages --also-callsites`), tagging once per tagger input state (`atom-tag-state.json`), JS path-alias configs parsed once |
| 3 | AppThreat/chen#262, AppThreat/atom#349 | php2atom attributes, class constants, declared types, traits and positions, PHP 8.4 and 8.5 syntax, the PHP source, `vendor/` treated as dependencies |
| 4 | AppThreat/chen#263, #264, AppThreat/atom#350 | cpg2 3.1.2, ruby2atom constant references, names for calls on constants, heritage and mixins from gems, the Ruby source |
| 5 | AppThreat/atom#359 | the bytecode source with an application boundary for APKs and fat jars, the Android SDK path, synthetic line tables, class-to-artifact mapping from `META-INF` and the Gradle cache |
| 6 | AppThreat/edga#10, #11, AppThreat/chen#297, AppThreat/atom#364 | edga exports includes, macro uses and enumerators from the IL; c2cpg and edg2atom tag the declaring header of every call, reference, field access, constructor call and macro use; CDT parses C23 attributes, digit separators and C++23 explicit object parameters; the C and C++ source with builtin headers decided by where they resolved; `--external-paths` for C and C++ |
| 7 | AppThreat/chen#300, AppThreat/atom#365 | JavaScript and TypeScript records carry the SBOM's purl; `--external-paths` works on every source frontend through one x2cpg pass, and a BOM's component locations (`cdx:vendored:path`, `cdx:cmake:sourceDir`) mark vendored code too, with the component's purl on its records; c2cpg gives a translation unit's file-scope method the unit's own file instead of its first header's; Java `implements` is no longer reported as `extends` |
| 8 | AppThreat/atom#369 | byte-identical slices across runs and across separately built atoms (ties in `CallSiteRecord.dedupe` and in the JavaScript, Python, PHP and vendored-code sources broken on stable properties, checked on reordered graphs); `callsites` peaks at or below `usages` in memory on five large projects; the lesson, CLI page and help text cover every language, and a test runs the lesson's commands; CI keeps one macOS job per pull request (AppThreat/atom#370 asks for reliable macOS runners) |
| 9 | AppThreat/atom#374 | an import that binds no local name (`import 'x'`, a bare `require('x')`, or one passed straight to another call) is an `import` record; CommonJS interop helpers (`__importDefault`, `__importStar`, `_interopRequireDefault`, `_interopRequireWildcard`) are followed to the module they wrap; every source writes file paths with `/` on every platform |
| 10 | AppThreat/atom-parsetools#85, #86, #87, #88, AppThreat/chen#307, AppThreat/atom#378 | the JavaScript wrap-up ([callsites-js-wrapup.md](callsites-js-wrapup.md)): astgen streams large ASTs to disk and parses a file whose AST does not fit in a child process with more heap; TC39 auto-accessors parse and are class properties in jssrc2cpg; `release/1.x` gets the TypeScript 6 type budgets; jssrc2cpg types the receivers of member calls from the TypeScript 6 type map and tags every type reference; type positions are `decltype` records, a member a project class inherits from a package class is the package's, and Java method references are in `usages` and `callsites` |
| 11 | AppThreat/atom-parsetools#90, #91 | astgen lets a project's own compiler options win over its defaults, which `parseJsonConfigFileContent` used to apply as command-line flags; each nested TypeScript project (juice-shop's `frontend/`, a workspace package) is typed by a program built from its own configuration, and a solution-style root `tsconfig.json` hands the root to the configuration it references |

All eleven rounds are merged; the last, AppThreat/atom-parsetools#90, merged on 2026-11-06.

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

JavaScript and TypeScript reached 0.99 recall on binding uses before this work (AppThreat/atom#293).
Against the typed oracle, with `node_modules` installed and type-only imports counted (decision
0001, P1), round 10 moved callsites recall / precision as follows, with TypeScript 6 types as on
`release/1.x`:

| project | before round 10 | after round 10 | after round 11 | after round 10, runtime built-in misses left out |
|---|---|---|---|---|
| angular-realworld | 0.621 / 1.000 | 0.911 / 1.000 | 0.915 / 1.000 | 0.946 |
| vue3-realworld | 0.441 / 1.000 | 0.567 / 1.000 | 0.567 / 1.000 | 0.944 |
| nestjs-realworld | 0.854 / 0.996 | 0.914 / 0.996 | 0.914 / 0.996 | 0.993 |
| express-realworld | 0.333 / 0.938 | 0.611 / 0.965 | 0.611 / 0.965 | 0.902 |
| juice-shop | 0.400 / 0.973 | 0.555 / 0.976 | 0.591 / 0.977 | 0.804 |

Round 11 was measured with chen and atom from main and astgen from `release/1.x` before and after
AppThreat/atom-parsetools#91; the before column reproduces round 10's figures exactly. On
juice-shop the `frontend/` app now gets its own types: 211 more true positives and one more false
positive, a `src/app/...` import through the app's `baseUrl` that atom takes for a package
(#382). The misses left are runtime built-ins (`console`, `Math`, `Array`), which the type map
names without a module. The bytecode and C tranches also checked records
at member level and the `builtin` flag against the oracle, because the package-level score hid
errors in both. On a built atom `callsites` takes less time than `usages` on every C project above.
Every tranche compared the other languages' slices with main and kept them identical, apart from
changes it intended (tranche 1 reports TypeScript `implements` as its own kind).

The scores come from a harness kept outside the repositories (decision 0001): oracles per language,
a scorer, member and builtin checks, and the corpus in
[callsites-corpus.corpus.json](callsites-corpus.corpus.json). Making it reproducible by others is
AppThreat/atom#312.

Package coverage (decision 0002) is measured separately: for each JavaScript and TypeScript corpus
app and the frontend apps, the harness lists the declared packages the sources reference through
code (imports, `require`, dynamic `import()`) and the share the callsites slice names. With
tranche 9 the lowest share is 0.57 (astro-examples, whose misses are configuration files), and the
gate is 0.55. ngx-admin went from 0.69 to 0.84. The share of packages with BOM occurrences after
evinse is the same with and without the callsites slice on every app; that part is cdxgen's.

## Decisions taken

- Decision 0001: every reference is a use (declared types, `implements`, C macros, generated code);
  a typed call is attributed to the receiver's static type, with the declaring class kept as
  `declaringModule`; standard library uses are in the slice with `builtin` set; vendored code is
  external where it can be recognised, plus a path-regex option and the BOM's component locations.
  Without either, every slice is byte-identical to what it was before tranche 7.
- `usages` stays and keeps being fixed where it is touched; `callsites` is the additional slice.
- A header, class or module is builtin by where it resolved (SDK, sysroot, compiler, standard
  library, platform jar), never by its name.
- C and C++ projects own the headers under the input root and under the compilation database's
  build directories; atom stores those directories in the atom (`callsites-c-layout.json`).

## Open work by epic

- Ground truth (atom#304): #313 is done; every language has its test suite. #312 (a
  reproducible harness), #314 (typed oracles for JS and Python), #315 (complete Java and C/C++
  truth) and #316 (a dynamic recall floor) have not started.
- Core and JS (atom#305): #321 (JavaScript purls) and #322 (typed-call recall) are done.
  AppThreat/atom-parsetools#33 (type generation stalls on cdxgen's repository) is fixed on
  `release/1.x` by AppThreat/atom-parsetools#88, and AppThreat/atom-parsetools#89 (nested
  projects) on both branches by #90 and #91. #320 (Vue, Svelte and Astro positions) is fixed in
  astgen on both branches and tested in atom; it closes when the end-of-November release pins the
  new 1.x version in atom.
- C and C++ (atom#308): #346 is done; every source frontend has the vendored-code option and
  reads BOM component locations.
- Language versions (chen#241): atom-parsetools#34 (TC39 auto-accessors) and atom#334 (Java
  method references; Lombok's generated members already resolve) are done. #255 (report files
  that could not be parsed) and atom#335 (version matrix fixtures) have not started.
- Performance (atom#309): #339 (the cost of `usages` on large Java and Python projects).
- Consumers: moved out of this organization. cdxgen#4690 to #4693 are under cdxgen/cdxgen#4718
  (milestone 13.8.0, plan `plans/cdxgen-callsites-evidence.md` in cdxgen/.github), and
  dep-scan#552 and #553 under owasp-dep-scan/dep-scan#555 (milestone v7.0.0 Lodestar, plan
  `plans/depscan-callsites.md` in owasp-dep-scan/.github). The consumers epic atom#310 is closed.
- Package coverage (decision 0002): done. Side-effect imports are records (#367) and the harness
  has the package-coverage gate and the frontend apps (#368). The cdxgen side of the same report,
  duplicate occurrences on Windows from mixed path separators and `offset` and `symbol` on each
  occurrence (cdxgen/cdxgen#4726), merged in cdxgen/cdxgen#4727 for 13.7.0. cdxgen's own
  `callsites` run needs an atom release with the command, which is cdxgen/cdxgen#4690.
- Production (atom#311): #340 to #342 are done. #373 (every source writes `/` in paths on every
  platform) is done. #343 (the release
  chain) and #344 (what `usages` keeps) are the maintainer's.

## Known gaps

Each gap is an issue on the AppThreat roadmap board, in the Backlog with no milestone.

- CDT's C++ recall on leveldb (0.279, against EDG's 0.781) has not been analysed
  (AppThreat/chen#304).
- CDT misses curl's `bool` macro (1,459 rows of the recall gap on curl, AppThreat/chen#305).
- On curl, EDG's reachables went from 31 flows on main to 267 with tranche 6; the edg2atom change
  that caused it was not isolated (AppThreat/chen#306).
- Python precision on httpie (0.949) is held down by typed attribute reads, `super()` into external
  bases and quoted `TYPE_CHECKING` annotations, which the Python oracle does not attribute yet
  (#314).
- The scorer cannot attribute PHP names with one segment (`sprintf`, `PDO`, `config()`), which
  holds PHP recall under the default settings far below the gate (#375).
- PHP and Ruby calls on untyped top-level locals get no record, with or without `--external-paths`
  (#376), and Python imports of namespace packages inside the project (a directory without
  `__init__.py`) are recorded as dependencies (#377).
- Bytecode renamed by R8 needs `mapping.txt` (atom#360), and calls through lambdas and method
  references are missing from reachables and callsites (atom#354). The SootUp migration
  (atom#351) will replace the Soot frontend these slices run on, in v5.

Ruby's recall ceiling from `db/migrate` is gone: ruby2atom scans migrations by default since
AppThreat/chen@42023446.

- JavaScript runtime built-ins (`console`, `Math`, `Array` methods) get no record; the type map
  names their types without a module, and which module such a record names needs a decision
  (#379).
- Imports through a project's own path alias or `baseUrl` are taken for packages when the alias
  sits in a configuration other than `tsconfig.json` or `jsconfig.json`, comes through `extends`,
  or is a bare `baseUrl`; type-only imports through a root `paths` alias also keep the alias in
  their `decltype` records (48 records on juice-shop, #382).
- On Windows the PHP example of the lesson test misses one `extends` record, on main too (#380).

chennai, the terminal explorer built on chen, does not read the callsites slice yet
(AppThreat/chennai#4, Backlog).

## Next

The JavaScript wrap-up is done: [callsites-js-wrapup.md](callsites-js-wrapup.md) has the outcome.
The end-of-November release publishes atom-parsetools 1.x with the wrap-up's astgen changes, pins
that version in atom's container images and workflows (which closes #320) and runs the full corpus
once. After it come a reproducible harness (#312) and the typed oracles (#314). The release chain
(#343) and the decision on what `usages` keeps (#344) remain the maintainer's.

Each round follows the overview's rules: tests with bad and good twins, a mutation table, equivalence
tests for changes that keep output, member-level and builtin checks beside the package score, and a
corpus subset per iteration with the full corpus at the end.
