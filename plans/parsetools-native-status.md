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
| AppThreat/atom-parsetools `feat/native-t5` (tranche 5) | the type map differ classifies every corpus difference (eight new classes, a greedy `refinesAny` for types with dozens of `any`, an import-qualified generic head), `npm run eval:typemaps` is the one command for the type map table and both score tables (#44), the 2.0.0 changelog and docs describe main as it is (`ASTGEN_VERSION` 4.7.1), and the corpus was measured again on main (the tables below) | in review |

atom-parsetools 2.0.0 is not published yet; the latest release is 1.10.6. To try the native type
map, build the binary (`npm run test:native` builds and tests it; `parsa/scripts/fetch-typescript.sh`
fetches the pinned TypeScript checkout) and point `ASTGEN_NATIVE_BIN` at it, or put it next to
`astgen.js` or on `PATH`. `docs/ASTGEN.md` ("Native type maps") documents the variables and the
manifest record a native run writes.

## Measurements (2026-11-09, main at 6408539)

On the 19 JavaScript and TypeScript inputs of [the corpus](parsetools-native.corpus.json), against
astgen 1.10.6 with its default file discovery, every run under the watchdog (10 minutes, 8 GB per
project). "Agree" is exact or equal after the differ's listed normalizations; "with improved" also
counts keys TypeScript 7 types where TypeScript 6 gave nothing or `any`. The full table with both
references, the lost share, the unclassified count and the 1-versus-8 check for every input is
`final-table.txt` in the evaluation workspace (`final-table-2026-11-03.txt` keeps the previous
round). Output is byte-identical at 1, 4 and 8 checkers and across two runs on every input, and no
input hit a cap.

| input | keys | agree | with improved | astgen 1.10.6 | native, 1 checker | native, 8 checkers |
|---|---|---|---|---|---|---|
| angular-realworld | 3,469 | 90.9% | 97.1% | 1.7 s, 386 MB | 0.26 s, 171 MB | 0.14 s, 192 MB |
| vue3-realworld | 5,109 | 97.3% | 97.9% | 3.5 s, 1,062 MB | 0.61 s, 320 MB | 0.33 s, 402 MB |
| nestjs-realworld | 6,188 | 83.6% | 98.8% | 1.0 s, 247 MB | 0.28 s, 110 MB | 0.09 s, 130 MB |
| node-express-boilerplate | 1,897 | 88.7% | 92.3% | 0.7 s, 222 MB | 0.08 s, 53 MB | 0.06 s, 30 MB |
| ver-js | 466 | 91.9% | 98.3% | 0.9 s, 330 MB | 0.10 s, 91 MB | 0.07 s, 92 MB |
| bulletproof-react | 17,323 | 97.5% | 99.5% | 2.7 s, 315 MB | 0.37 s, 113 MB | 0.13 s, 142 MB |
| juice-shop | 362,783 | 94.9% | 97.3% | 18.3 s, 1,960 MB | 6.0 s, 1,199 MB | 1.7 s, 1,770 MB |
| outline | 312,740 | 98.6% | 99.2% | 51.3 s, 1,625 MB | 5.9 s, 1,052 MB | 1.5 s, 1,398 MB |
| cdxgen | 552,732 | 6.3% | 100.0% | killed at 600 s | 22.0 s, 2,924 MB | 10.7 s, 4,190 MB |

The other ten inputs agree on 98.4 to 100 percent. cdxgen's low raw agreement is the 1.10.6
baseline's: it was killed before typing 368 of 438 files, so 93.6 percent of the compared keys exist
on the native side only; against main's TypeScript 6 mode (the second reference) cdxgen agrees on
97.6 percent. One key in the whole corpus falls in no difference class (juice-shop
`routes/chat.ts:9863`, a genuine disagreement about a Sequelize model attribute deep inside a 4 KB
union, past the differ's bounded comparison depth); on 2026-11-03 there were 523.

Against main in `ASTGEN_TYPES=ts6` mode, agreement is 97.3 to 100 percent on six of the nine
callsites inputs and lower on three: bulletproof-react 89.0, angular-spotify 91.5 and
vue-router-playground 83.7. The cause is #90, which types nested TypeScript projects with their own
configuration on the TypeScript 6 path only; astgen still runs `parsa` once for the whole input
with the root configuration. Bringing the nested projects to the native path is the remaining type
map work.

Two movements against the 2026-11-03 table have causes outside #85, #87 and #90: juice-shop
agreement 97.2 to 94.9 and nestjs-realworld 99.9 to 83.6. Both are the previous table's binary,
which predates the review fixes of the morning of 2026-11-03 (`58ce761` "match astgen's tsconfig
handling" among them): the current binary resolves the imports of juice-shop's nested `frontend/`
project and nestjs's compiled `dist/` output, so it types 5,614 and 887 more keys there than the
1.10.6 baseline has, and agreement against that baseline falls while "with improved" falls less.
Root files outside those directories are byte-for-byte the same key count as the previous round.

On the callsites subset (nine projects, scored with the callsites scorer against the untyped truth,
both engines on the same atom build, 2026-11-09):

| input | callsites recall ts6 | native | callsites precision ts6 | native | precisionNoType ts6 | native |
|---|---|---|---|---|---|---|
| svelte-realworld | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 | 1.000 |
| nestjs-realworld | 0.995 | 0.995 | 0.731 | 0.783 | 1.000 | 1.000 |
| express-boilerplate | 0.993 | 0.993 | 0.993 | 0.993 | 1.000 | 1.000 |
| bulletproof-react | 0.880 | 0.880 | 0.968 | 0.968 | 0.985 | 0.985 |
| angular-realworld | 1.000 | 1.000 | 0.709 | 0.679 | 1.000 | 1.000 |
| vue3-realworld | 1.000 | 1.000 | 0.613 | 0.620 | 0.780 | 0.780 |
| express-realworld | 0.982 | 0.982 | 0.724 | 0.688 | 1.000 | 1.000 |
| outline | 0.920 | 0.920 | 0.791 | 0.783 | 0.859 | 0.859 |
| juice-shop | 0.986 | 0.986 | 0.579 | 0.575 | 0.860 | 0.860 |

Recall is equal on every project; native precision is higher on nestjs-realworld and vue3-realworld
and lower on angular-realworld and express-realworld, by at most 0.037; usages scores move the same
way (the full tables are in the evaluation workspace). The vue3-realworld precision of 0.772 from
chen#298 is not a property of native type maps: against the untyped truth both engines sit at
0.780 with `via=type` records dropped, and the false positives that remain are, for both engines,
calls on receivers typed with `@playwright/test` classes (37 of 63 on native) that the untyped truth
cannot credit. Against the typed truth, which lists calls through receivers typed with an imported
package's class, precision is 0.996 to 1.000 on callsites for the projects that have one.

## Decisions taken

- Distribution (2026-11-04, settles decision 7): no npm packages for `parsa`. It reaches users
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

- One key in the corpus falls in no named difference class (juice-shop `routes/chat.ts:9863`), a
  genuine engine disagreement about a Sequelize model attribute, inside a 4 KB union past the
  differ's bounded comparison depth.
- Nested TypeScript projects are typed with their own configuration on the TypeScript 6 path only
  (#90). astgen runs `parsa` once per input with the root configuration, so on inputs with nested
  projects the native engine misses the nested configuration's resolution: bulletproof-react,
  angular-spotify and vue-router-playground agree 10 to 15 points less with main's TypeScript 6 mode
  than the other inputs.
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

1. Publish: `2.0.0-rc.1` (the changelog, the docs, the publish dry-run and the packed-tarball checks
   are done; the release notes are drafted for the maintainer), then `parsa` in cdxgen-plugins-bin's
   platform packages (cdxgen/cdxgen-plugins-bin#164), with cdxgen setting `ASTGEN_NATIVE_BIN` from it
   (cdxgen/cdxgen#4721), and in atom's images (AppThreat/atom#361); S2 in the ship plan, #65.
2. Nested TypeScript projects on the native path: run `parsa` per type project, or teach it
   `findTypeProjects`, so the native engine resolves nested configurations as the TypeScript 6 path
   does since #90.
3. chen's jssrc2cpg tests against atom-parsetools 1.x and 2.x in CI (AppThreat/chen#295), and atom's
   images with `parsa` and the version report (AppThreat/atom#361).
4. Releases: atom-parsetools 2.0.0, then chen and atom.

The upstream reports (#67) and the one unclassified key can run alongside. Each round follows the
testing plan's rules: every run under the watchdog with time and memory caps, one heavy job at a
time on a developer machine, baselines kept outside the repositories, and any difference either
fixed or allow-listed with a reason.
