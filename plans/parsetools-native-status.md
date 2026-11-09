# Native atom-parsetools: status

Updated 2026-11-09. This page says what has landed, what is in review and what comes next, so the
work can be picked up from here. The design is in the other plans
([overview](parsetools-native-overview.md), [JS/TS](parsetools-native-js.md),
[testing](parsetools-native-testing.md), [Ruby and PHP](parsetools-native-ruby-php.md),
[ship](parsetools-native-ship.md)); this page does not repeat it. The epics and tasks are issues in
AppThreat/atom-parsetools (#35 to #92), AppThreat/chen#295 and AppThreat/atom#361, all on the
AppThreat roadmap board under milestone v5.0.0.

## Where it stands

The scope is the type map only (2026-11-04, see the overview). Steps 1 to 3 are done and step 4 has
landed: native type maps are astgen's default (#80, `ASTGEN_VERSION` 4.7.1), TypeScript 6 is the
fallback, and the TypeScript 6 phase has per-file and per-program budgets (#81). Babel still parses
every file. What remains of step 5 is publishing: `parsa` into the cdxgen-plugins-bin platform
packages and atom's images (#65), then the 2.0.0 release (the changelog, the docs and the publish
checks are ready; `2.0.0-rc.1` notes are drafted for the maintainer).

The work was done in rounds by AI agents, each implemented by one agent and reviewed, fixed and
measured again by another.

| pull request | what it did | state |
|---|---|---|
| AppThreat/atom-parsetools#68 | Go module (now `parsa/`, command `parsa js --types-only` since #71), typescript-go through a generated shim over `microsoft/TypeScript` `tsc/` pinned at 622d4f7 (`parsa/third_party/typescript.pin`) with one patch (`parsa/patches/0001-*`: builder budget, interrupt, work limit, printer cache release); astgen integration with fallback to TypeScript 6; type map differ and allow-list (`lib/typemap/`, `test-fixtures/typemap-allow.json`); watchdog and `npm run test:native`; CI job on Linux and macOS; package version 2.0.0, `ASTGEN_VERSION` 4.6.0 | merged |
| AppThreat/atom-parsetools#71 | the native binary renamed `parsa` (module `parsa/`, `parsa js --types-only`) and `CHANGELOG.md` with the breaking changes of 2.0.0 | merged |
| AppThreat/atom-parsetools#72, #73 | release builds: `parsa/scripts/build-release.sh` cross-compiles six targets, `.github/workflows/parsa-release.yml` runs them on their platforms, pushes them to `ghcr.io/appthreat/parsa` on every push to main and attaches them to releases with hashes, provenance and a post-build SBOM (Go toolchain in the formulation) | merged |
| AppThreat/atom-parsetools#69 | `.typespans` next to each `.typemap`: the type of each node keyed by `"start:end"`, native runs only (`docs/OUTPUT_FORMATS.md`) | merged |
| AppThreat/atom-parsetools#80, #81 | native type maps as astgen's default with the TypeScript 6 fallback (`ASTGEN_TYPES`, `ASTGEN_NATIVE_BIN`, `ASTGEN_NATIVE_MEMORY_MB`, the manifest record, `docs/ASTGEN.md`), and per-file plus per-program budgets on the TypeScript 6 phase (`ASTGEN_TYPE_FILE_TIMEOUT_MS`, `ASTGEN_TYPE_PROGRAM_TIMEOUT_MS`, `type_budget` records) | merged |
| AppThreat/atom-parsetools#83, #85, #87, #90 | Vue templates that keep their positions (void elements, slot shorthand, JSX-rejected attribute names), AST JSON written in chunks with a larger-heap child process for huge files, TC39 auto-accessors, and nested TypeScript projects typed with their own configuration on the TypeScript 6 path | merged |
| AppThreat/chen#296 | jssrc2cpg reads native type maps; `TypeStringNormalizer` writes both engines' strings in one canonical spelling | merged |
| AppThreat/chen#298 | jssrc2cpg types every node from `.typespans`, `TYPE_FULL_NAME` is one name or `ANY` in both modes (`TypeNames.scala`), type recovery starts from those names | merged |
| AppThreat/atom#363 | atom option `--frontend-args astgen-types=native` (or `ts6`), passed to chen and astgen as `ASTGEN_TYPES` | merged |
| AppThreat/atom-parsetools `feat/native-t5` (tranche 5 and its review) | `parsa` types each nested project with its own program and lets a project's own compiler options win over astgen's defaults, as astgen's TypeScript 6 path does since #90; the type map differ names differences from evidence (package versions read from node_modules, a `--reference` tree from main's ts6 mode) instead of from where a file sits; `npm run eval:typemaps` is the one command for the type map table and both score tables (#44); the 2.0.0 changelog and docs describe main as it is | in review |

atom-parsetools 2.0.0 is not published yet; the latest release is 1.10.6. To try the native type
map, build the binary (`npm run test:native` builds and tests it; `parsa/scripts/fetch-typescript.sh`
fetches the pinned TypeScript checkout) and point `ASTGEN_NATIVE_BIN` at it, or put it next to
`astgen.js` or on `PATH`. `docs/ASTGEN.md` ("Native type maps") documents the variables and the
manifest record a native run writes.

## Measurements (2026-11-09, `feat/native-t5` after review)

On the 19 JavaScript and TypeScript inputs of [the corpus](parsetools-native.corpus.json), every run
under the watchdog (10 minutes, 8 GB per project). Each native run is compared with two references:
astgen 1.10.6 with its default file discovery, and main's astgen in `ASTGEN_TYPES=ts6` mode, which
shares the native path's file discovery, compiler options and programs per nested project. "Agree"
is exact or equal after the differ's listed normalizations; "with improved" also counts keys
TypeScript 7 types where 1.10.6 gave nothing or `any`. The full table is `final-table.txt` in the
evaluation workspace (`final-table-2026-11-03.txt` and `final-table-glm-2026-11-09.txt` keep the
earlier rounds). Output is byte-identical at 1 and 8 checkers on every input, and no input hit a cap.

| input | keys | agree, 1.10.6 | with improved | agree, main ts6 | astgen 1.10.6 | native, 1 checker | native, 8 checkers |
|---|---|---|---|---|---|---|---|
| angular-realworld | 3,469 | 90.8% | 97.1% | 99.4% | 1.73 s, 386 MB | 0.30 s, 168 MB | 0.13 s, 192 MB |
| vue3-realworld | 5,119 | 97.4% | 98.2% | 98.5% | 3.54 s, 1,062 MB | 0.61 s, 288 MB | 0.39 s, 320 MB |
| nestjs-realworld | 6,188 | 83.6% | 98.8% | 90.1% | 0.96 s, 247 MB | 0.22 s, 89 MB | 0.07 s, 113 MB |
| node-express-boilerplate | 1,897 | 88.7% | 92.2% | 88.7% | 0.73 s, 222 MB | 0.10 s, 52 MB | 0.06 s, 28 MB |
| ver-js | 466 | 91.8% | 98.3% | 97.4% | 0.86 s, 330 MB | 0.16 s, 83 MB | 0.13 s, 92 MB |
| bulletproof-react | 18,495 | 88.8% | 97.3% | 97.4% | 2.65 s, 315 MB | 0.53 s, 122 MB | 0.21 s, 126 MB |
| vue-router-playground | 902 | 83.7% | 96.9% | 98.6% | 1.56 s, 524 MB | 0.22 s, 84 MB | 0.11 s, 116 MB |
| angular-spotify | 16,956 | 91.5% | 98.5% | 98.8% | 3.28 s, 287 MB | 1.45 s, 92 MB | 1.33 s, 93 MB |
| juice-shop | 362,809 | 94.6% | 97.0% | 97.6% | 18.3 s, 1,960 MB | 5.19 s, 705 MB | 1.65 s, 935 MB |
| outline | 312,747 | 98.6% | 99.2% | 98.7% | 51.2 s, 1,625 MB | 5.64 s, 1,098 MB | 1.41 s, 1,482 MB |
| cdxgen | 549,574 | 6.1% | 99.7% | 98.5% | killed at 600 s | 20.6 s, 2,968 MB | 12.4 s, 3,856 MB |

The other eight inputs agree with 1.10.6 on 98.4 to 100 percent. cdxgen's raw agreement with 1.10.6
is low because 1.10.6 was killed before typing 368 of 438 files. Agreement with 1.10.6 fell on the
inputs whose own tsconfig or nested projects astgen now honours in both engines (#90): 1.10.6 typed
bulletproof-react's apps, angular-spotify's libraries and juice-shop's `frontend/` with the root
program and astgen's default options. Against main's TypeScript 6 mode, which types them the same
way, agreement on those inputs is 97.4 to 98.8 percent. nestjs-realworld's 887 native-only keys are
mostly in its compiled `dist/` output, which neither TypeScript 6 run types.

One key in the corpus falls in no difference class: juice-shop `routes/chat.ts:9863`, the `event`
of `for await (const event of result.fullStream)`, where TypeScript 6 expands the AI SDK's stream
part union member by member and TypeScript 7 prints it through `ToolApprovalRequestOutput<...>`,
both near the 4,096 character limit. A difference from 1.10.6 that no other class names, where the
native answer equals main's TypeScript 6 answer for the same key, is `reference-agrees` (at most
0.57 percent of an input's keys, on bulletproof-react).

On the callsites subset (nine projects, the callsites scorer against the untyped truth, both engines
on the same atom build), the scores of the reviewed binary equal those of the tranche-5 binary to
three decimals, although its slices differ (bulletproof-react's usages slice grew by 33 KB), apart
from juice-shop's usages precision, 0.388 to 0.387:

| input | callsites recall ts6 | native | callsites precision ts6 | native | usages precision ts6 | native |
|---|---|---|---|---|---|---|
| svelte-realworld | 1.000 | 1.000 | 1.000 | 1.000 | 0.662 | 0.662 |
| nestjs-realworld | 0.995 | 0.995 | 0.731 | 0.783 | 0.656 | 0.691 |
| express-boilerplate | 0.993 | 0.993 | 0.993 | 0.993 | 0.730 | 0.730 |
| bulletproof-react | 0.880 | 0.880 | 0.968 | 0.968 | 0.718 | 0.718 |
| angular-realworld | 1.000 | 1.000 | 0.709 | 0.679 | 0.472 | 0.462 |
| vue3-realworld | 1.000 | 1.000 | 0.613 | 0.620 | 0.515 | 0.538 |
| express-realworld | 0.982 | 0.982 | 0.724 | 0.688 | 0.438 | 0.403 |
| outline | 0.920 | 0.920 | 0.791 | 0.783 | 0.679 | 0.676 |
| juice-shop | 0.986 | 0.986 | 0.579 | 0.575 | 0.386 | 0.387 |

Recall is equal on every project; native precision is higher on nestjs-realworld and vue3-realworld
and lower on angular-realworld and express-realworld, by at most 0.037. The vue3-realworld precision
of 0.772 in chen#298 is not a property of native type maps: with `via=type` records dropped both
engines sit at 0.780, and the false positives left are, for both engines, calls on receivers typed
with `@playwright/test` classes that the untyped truth cannot credit.

## Decisions taken

- Distribution (2026-11-09, changes decision 7): `parsa` ships as npm platform packages,
  `@appthreat/parsa-<os>-<cpu>`, optional dependencies of atom-parsetools that astgen finds on its
  own, so no consumer sets `ASTGEN_NATIVE_BIN` (AppThreat/atom-parsetools#94, ship plan S2). This
  replaces the 2026-11-04 entry below.
- Distribution (2026-11-04, superseded on 2026-11-09): no npm packages for `parsa`. It reaches users
  through the cdxgen-plugins-bin platform packages and a direct download in container images. astgen
  does not search for those itself: cdxgen and the images point it at `parsa` through
  `ASTGEN_NATIVE_BIN` (or the images place it next to `astgen.js`). This replaces the 2026-11-03 entry below.
- Scope (2026-11-04): only the type map is native. Babel and `hermes-parser` keep writing the AST
  in Node, phpastgen, rbastgen and scalasem stay, and Node stays a requirement. The decisions below
  on commands, scalasem, Svelte, Ruby and PHP, cgo and Flow belonged to the earlier no-Node scope
  and are superseded; they are kept as a record.

- Decision 1: Go hosts the binary.
- Decision 2: an AppThreat shim generated against `microsoft/TypeScript` `tsc/`, not the tsgolint
  pin. `parsa/scripts/bump-typescript.sh` moves the pin and reruns the tests.
- Decision 6: TypeScript 7's member order is kept. chen's `TypeStringNormalizer` spells both engines
  the same way, and since chen#298 chen stores one name per node, so ordering no longer reaches the
  graph.
- New: astgen writes the type of each node by its extent (`.typespans`), and chen uses every native
  type, accepting graph changes where they make types more precise. That is the goal for v5.

- Distribution (2026-11-03): no per-platform npm packages. Binaries go to `ghcr.io` on every push to
  main and to GitHub releases with hashes, and cdxgen-plugins-bin bakes them into its platform
  packages (cdxgen/cdxgen-plugins-bin#164, cdxgen/cdxgen#4721). See S2 in the ship plan.

- Decision 5 (2026-11-03): the Svelte handling is ported to Go, with no Node fallback (#55).
- scalasem (2026-11-03): ported to Go as well, keeping the Java TASTy helper, so that cdxgen can drop
  the npm package.

- Commands (2026-11-03): one binary, `parsa` ("parse for atom"), with the subcommands `js`, `php`,
  `rb` and `scala` and no wrappers under the old names. chen, atom and cdxgen are changed to call it,
  and `CHANGELOG.md` lists every breaking change. The Go command is renamed before 2.0.0 is
  published, so `atom-parsetools-native typemap` never ships.

- Ruby and PHP (2026-11-03, settles decision 3): the parsers are not rewritten. `parsa rb` and
  `parsa php` are `rbastgen.js` and `phpastgen.js` in Go, running `ruby_ast_gen` and nikic in the
  user's Ruby and PHP, with the gem bundle and the nikic tree embedded in the binary as a tarball.
  See the [Ruby and PHP plan](parsetools-native-ruby-php.md).
- cgo (2026-11-03): allowed. Nothing planned uses it yet.
- Flow (2026-11-03, settles decision 4): Hermes's C++ parser compiled to WebAssembly for WASI and
  run inside parsa by wazero, with the conversion to Babel shape in Go (#56). Linking it with cgo,
  swc, a Node fallback and dropping Flow were the other options. AppThreat/atom-parsetools#75
  builds and measures it. Flow files in projects not marked as Flow need a routing rule before the
  JavaScript default changes (see D8 in the [JavaScript plan](parsetools-native-js.md)).
- atom-parsetools 1.x and 2.x (2026-11-03): chen and atom v5 work with both (S3 in the
  [ship plan](parsetools-native-ship.md)). The `release/1.x` branch, from v1.10.6, takes 1.x fixes
  and publishes under the npm dist-tag `release-1.x` (AppThreat/atom-parsetools#77, #78).

## Known gaps from the type map work

- One key in the corpus falls in no difference class (juice-shop `routes/chat.ts:9863`, see
  Measurements).
- A bare import specifier that only resolves through `baseUrl` is untyped: TypeScript 7 dropped
  `baseUrl` as a module root and only `paths` aliases are emulated.
- The cdxgen evolving-array reproducer has not been reported to TypeScript (#67).
- The callsites scores now have one command in the repository, `npm run eval:typemaps`
  (`docs/TESTING.md`); the scorer and its truth stay outside, passed as arguments (#44).
- Type maps for files with syntax tsgo does not parse (Flow, `do` expressions, `export v from`)
  have not been measured: tsgo checks its recovered tree, so some nodes may be untyped or typed
  from the wrong span.
- atom's usages slice on outline peaks at 8.2 GB (JVM plus astgen), above the corpus cap of 8 GB;
  the harness and the eval command need a 16 GB cap for that one project.

## Next

1. Publish `2.0.0-rc.1` with the six `parsa` npm packages: a maintainer runs
   `parsa/scripts/setup-npm-trusted-publishing.sh` once, then tags the release (#65,
   AppThreat/atom-parsetools#94). Then install it on each target and check that astgen runs the
   packaged binary.
2. atom: images and CI on atom-parsetools 2.x, and the atom-parsetools and `parsa` versions in its
   version and perf reports (AppThreat/atom#361); chen already tests jssrc2cpg against 1.x and 2.x
   (AppThreat/chen#295).
3. Releases: atom-parsetools 2.0.0, then atom, then cdxgen on atom-parsetools 2.x (cdxgen/cdxgen#4721).

The upstream reports (#67) and the one unclassified key can run alongside. Each round follows the
testing plan's rules: every run under the watchdog with time and memory caps, one heavy job at a
time on a developer machine, baselines kept outside the repositories, and any difference either
fixed or allow-listed with a reason.
