# Native atom-parsetools: testing plan

Every change is checked against outputs recorded from today's Node tools, on the same inputs, under
hard resource caps. The goal is that no difference reaches chen unseen, and that no run can take a
machine down.

Status (2026-11-03): levels 1, 2, 5 and 6 exist for JavaScript and TypeScript type maps, level 3 for
offsets, level 4 as a harness outside the repositories, and level 7 for the native type map only.
See [parsetools-native-status.md](parsetools-native-status.md).

## Corpus

[parsetools-native.corpus.json](parsetools-native.corpus.json) lists the inputs, their pins and
sizes. It reuses projects already in `~/sandbox` and the callsites corpus, so scoring truth exists
for the JS/TS, PHP and Ruby entries:

- JavaScript and TypeScript: bulletproof-react, juice-shop, outline, cdxgen, angular-realworld,
  vue3-realworld, svelte-realworld, nestjs-realworld, node-express-boilerplate,
  node-express-realworld, and the `ver-js` syntax matrix.
- Frameworks with template handling, from `~/sandbox/frontend-corpus/samples`: astro-examples,
  ember-super-rentals, nuxt-movies, vue-router-playground, angular-spotify, qwik-examples,
  solid-realworld and lit-starter, plus the Vue, Svelte, Astro and Ember fixtures in
  atom-parsetools `test-fixtures/`. A Svelte 5 application of a few hundred components (immich
  `web/`, which the parsetools performance notes already measure) is to be added.
- Flow: no Flow corpus exists yet. Collect one pinned React Native release and a few `@flow`
  packages before the Flow decision.
- PHP: symfony-demo, bookstack, koel, DVWA, the PHP synthetic fixtures with `EXPECTED.tsv`.
- Ruby: mastodon, maybe, railsgoat, the Ruby synthetic fixtures with `EXPECTED.tsv`.

## Levels

**1. Baselines.** Run astgen (with and without types), phpastgen and rbastgen 1.10.6 on every input
and keep: output trees as tarballs with per-file digests, the run manifests, wall time, peak RSS,
and for JS/TS projects atom's `usages`, `callsites` and `reachables` slices built from those outputs.
Rerun when the pinned parsetools release changes.

**2. Contract differs.** One differ per output shape, each reading baseline and candidate trees
file by file:

- Babel JSON: compares node type, `start`, `end`, `loc`, child order and literal values, ignores
  key order, reports differences grouped by node type and path. Svelte's `svelteKind` and
  `svelteName` keys are compared like any other key.
- Type maps: compares per offset after normalizing union and object member order and quote style,
  and reports exact, normalized-equal, baseline-only and candidate-only counts per node kind.
- nikic JSON (PHP) and `ruby_ast_gen` JSON (Ruby): same approach, including `framework_facts`,
  truncation markers, `magic_comments` and the manifest fields.

Each differ has an allow-list file of reviewed difference classes. A class not on the list fails
the run.

**3. Unit and fixture tests** in the Go module: one fixture per Babel node type chen's jssrc2cpg
reads (164 today), per Prism node type and per nikic node type, each with expected JSON checked in.
Fixtures for offsets cover CRLF, a byte order mark, two-byte, three-byte and four-byte characters
(surrogate pairs), and files that end without a newline.

**4. Scoring.** The callsites scorer from the callsites evaluation (`harness/score.py`, with the
TypeScript binder oracle, the Prism oracle and the nikic oracle) runs on slices built from native
output and from baseline output. Recall and precision must not drop.

**5. Determinism.** Two runs give byte-identical output trees. For JS/TS, runs with 1, 4 and 8
checkers give identical type maps.

**6. Resources.** Every run in tests and in the harness goes through a watchdog that samples the
process tree's RSS every second and kills it past a wall time or memory cap, and Go runs also set
`GOMEMLIMIT`. Caps for the corpus: 10 minutes and 8 GB per project. Per project budgets (time and
peak memory at most the gate values in the overview) are checked in CI on the S inputs. cdxgen is a
permanent regression input: the run must finish under the caps, and a type it gave up on is
reported in the manifest, not hidden.

**7. Hostile inputs.** Minified bundles over 10 MB, generated files with 100,000-line arrays, nesting
deep enough to hit the depth cap, invalid UTF-8, binary files with source extensions, symlink loops,
and paths outside the input root. Each must end with a diagnostic, not a crash or a hang.

## Rules

- No run without caps, locally or in CI.
- One heavy job at a time on a developer machine.
- A difference is either fixed, or allow-listed with a reason and a reviewer.
- Baselines and probes live outside the repositories; only differs, fixtures, allow-lists and the
  corpus list are checked in.
