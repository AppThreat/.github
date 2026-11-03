# Native atom-parsetools: status

Updated 2026-11-03. This page says what has landed, what is in review and what comes next, so the
work can be picked up from here. The design is in the other plans
([overview](parsetools-native-overview.md), [JS/TS](parsetools-native-js.md),
[testing](parsetools-native-testing.md), [Ruby and PHP](parsetools-native-ruby-php.md),
[ship](parsetools-native-ship.md)); this page does not repeat it. The epics and tasks are issues in
AppThreat/atom-parsetools (#35 to #67), AppThreat/chen#295 and AppThreat/atom#361, all on the
AppThreat roadmap board under milestone v5.0.0.

## Where it stands

Step 2 of the order of work (the type map on typescript-go, behind `ASTGEN_TYPES=native`) is done,
together with the JavaScript and TypeScript half of the testing work. Babel still parses every file,
and nothing changes unless `ASTGEN_TYPES=native` is set. Steps 3 to 6 (the Babel-shaped AST, Ruby,
PHP, packaging and the default switch) have not started.

The work was done in two rounds by AI agents, each implemented by one agent and reviewed, fixed and
measured again by another.

| pull request | what it did | state |
|---|---|---|
| AppThreat/atom-parsetools#68 | Go module (now `parsa/`, command `parsa js --types-only` since #71), typescript-go through a generated shim over `microsoft/TypeScript` `tsc/` pinned at 622d4f7 (`parsa/third_party/typescript.pin`) with one patch (`parsa/patches/0001-*`: builder budget, interrupt, work limit, printer cache release); astgen integration with fallback to TypeScript 6; type map differ and allow-list (`lib/typemap/`, `test-fixtures/typemap-allow.json`); watchdog and `npm run test:native`; CI job on Linux and macOS; package version 2.0.0, `ASTGEN_VERSION` 4.6.0 | merged |
| AppThreat/atom-parsetools#71 | the native binary renamed `parsa` (module `parsa/`, `parsa js --types-only`) and `CHANGELOG.md` with the breaking changes of 2.0.0 | auto-merge on |
| AppThreat/atom-parsetools#69 | `.typespans` next to each `.typemap`: the type of each node keyed by `"start:end"`, native runs only (`docs/OUTPUT_FORMATS.md`) | merged |
| AppThreat/chen#296 | jssrc2cpg reads native type maps; `TypeStringNormalizer` writes both engines' strings in one canonical spelling | merged |
| AppThreat/chen#298 | jssrc2cpg types every node from `.typespans`, `TYPE_FULL_NAME` is one name or `ANY` in both modes (`TypeNames.scala`), type recovery starts from those names | in review, auto-merge on |
| AppThreat/atom#363 | atom option `--frontend-args astgen-types=native` (or `ts6`), passed to chen and astgen as `ASTGEN_TYPES` | in the merge queue |

atom-parsetools 2.0.0 is not published yet; the latest release is 1.10.6. To try the native type
map, build the binary (`npm run test:native` builds and tests it; `parsa/scripts/fetch-typescript.sh`
fetches the pinned TypeScript checkout) and point `ASTGEN_NATIVE_BIN` at it, or put it next to
`astgen.js` or on `PATH`. `docs/ASTGEN.md` ("Native type maps") documents the variables and the
manifest record a native run writes.

## Measurements

On the 19 JavaScript and TypeScript inputs of [the corpus](parsetools-native.corpus.json), against
astgen 1.10.6 with its default file discovery, every run under the watchdog. "Agree" is exact or
equal after the differ's listed normalizations; "with improved" also counts keys TypeScript 7 types
where TypeScript 6 gave nothing or `any`.

| input | keys | agree | with improved | astgen | native, 1 checker | native, 8 checkers |
|---|---|---|---|---|---|---|
| angular-realworld | 3,469 | 90.9% | 98.0% | 1.7 s, 386 MB | 0.27 s, 171 MB | 0.15 s, 183 MB |
| vue3-realworld | 5,109 | 97.3% | 98.1% | 3.5 s, 1,062 MB | 0.57 s, 312 MB | 0.29 s, 461 MB |
| node-express-boilerplate | 1,897 | 88.7% | 95.6% | 0.7 s, 222 MB | 0.08 s, 54 MB | 0.05 s, 57 MB |
| ver-js | 466 | 91.9% | 98.9% | 0.9 s, 330 MB | 0.09 s, 88 MB | 0.06 s, 87 MB |
| bulletproof-react | 17,317 | 97.5% | 99.5% | 2.7 s, 315 MB | 0.42 s, 108 MB | 0.15 s, 144 MB |
| juice-shop | 357,170 | 97.2% | 97.9% | 18.3 s, 1,960 MB | 4.9 s, 986 MB | 1.5 s, 1,321 MB |
| outline | 312,740 | 98.6% | 99.2% | 51.3 s, 1,625 MB | 5.4 s, 1,032 MB | 1.4 s, 1,412 MB |
| cdxgen | 552,720 | n/a | n/a | killed at 600 s | 21.0 s, 2,442 MB | 12.1 s, 3,689 MB |

The other eleven inputs agree on 98.3 to 100 percent. Output is identical at 1 and 8 checkers and
across two runs on every input. On the callsites subset, scored with the truth extended by calls
through receivers typed with an imported package's class, native types give callsites precision of
0.947 to 1.0 on eight projects and 0.772 on vue3-realworld, recall equal to or above TypeScript 6
everywhere, and precision within 0.03 of TypeScript 6 where it is lower (details in chen#298).

Against the gates for changing the default in the overview: type map agreement, callsites, wall
time, memory, caps and determinism are met for the type map. The AST gate does not apply yet
(Babel still parses), and running without Node is step 6.

## Decisions taken

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

Decisions 3 (PHP parser, #61) and 4 (Flow, #56) are open.

## Known gaps from the type map work

- 523 of 728,991 compared keys fall in no named difference class (juice-shop 294, outline 163).
  The differ reports them as `different:unclassified`.
- A bare import specifier that only resolves through `baseUrl` is untyped: TypeScript 7 dropped
  `baseUrl` as a module root and only `paths` aliases are emulated.
- A type alias that one engine prints by name and the other expands is not yet a normalized class.
- The cdxgen evolving-array reproducer has not been reported to TypeScript (#67).
- Baselines, differs and node-type fixtures exist only for JavaScript and TypeScript type maps:
  nothing yet for Babel JSON, nikic JSON or `ruby_ast_gen` JSON (#41, #42, #43).
- The callsites scores come from a harness kept outside the repositories; there is no single
  command in atom-parsetools for it yet (#44).
- Hostile-input tests cover the native type map (invalid UTF-8, binary files, a huge array literal,
  a large file, symlink loops, output outside the output directory) but not the Node tools (#46).
- vue3-realworld callsites precision (0.772) is the lowest of the subset and has not been looked at.

## Next

The recommended next round is epic #37, the Babel-shaped AST from the tsgo parser (D6 in the JS
plan, task #53), started together with the Babel parts of #41, #42 and #43, because the AST work
cannot be gated without Babel baselines, a Babel differ and per-node-type fixtures. Order within it:
TS/JS, JSX/TSX, then the templates in #54. Ruby on Prism (#38) does not depend on it and can run in
parallel. PHP waits for decision 3 (#61). Packaging and the default switch (#40) come after.

Each round follows the testing plan's rules: every run under the watchdog with time and memory caps,
one heavy job at a time on a developer machine, baselines kept outside the repositories, and any
difference either fixed or allow-listed with a reason.
