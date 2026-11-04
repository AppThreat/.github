# Native atom-parsetools: testing plan

Every change to the native type map is checked against outputs recorded from today's Node tools,
on the same inputs, under hard resource caps. The goal is that no difference reaches chen unseen, and that no run can take a
machine down.

Status (2026-11-04): levels 1, 2, 5 and 6 exist for JavaScript and TypeScript type maps, level 3 for
offsets and type map rules, level 4 as a harness outside the repositories, and level 7 for the native
type map only. With the types-only scope (overview), the Babel JSON, nikic JSON and `ruby_ast_gen`
JSON baselines, differs and fixtures this plan listed are no longer needed.
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
- PHP and Ruby inputs (symfony-demo, bookstack, koel, DVWA, mastodon, maybe, railsgoat) stay in
  the corpus list for the callsites scorer; nothing native runs on them.

## Levels

**1. Baselines.** Run astgen 1.10.6 with and without types on every JavaScript and TypeScript input
and keep: output trees as tarballs with per-file digests, the run manifests, wall time, peak RSS,
and for JS/TS projects atom's `usages`, `callsites` and `reachables` slices built from those outputs.
Rerun when the pinned parsetools release changes.

**2. Type map differ.** `lib/typemap/diff.mjs` reads baseline and candidate trees file by file,
compares per offset after normalizing union and object member order and quote style, and reports
exact, normalized-equal, baseline-only and candidate-only counts per node kind. It reads an allow-list
of reviewed difference classes (`test-fixtures/typemap-allow.json`); a class not on the list fails
the run.

**3. Unit and fixture tests** in the Go module: the type map rules, project configuration and
single-file components (`parsa/testdata/typemap/`), and offsets with CRLF, a byte order mark,
two-byte, three-byte and four-byte characters (surrogate pairs), and files that end without a
newline.

**4. Scoring.** The callsites scorer from the callsites evaluation (`harness/score.py`, with the
TypeScript binder oracle) runs on slices built from native and from TypeScript 6 type maps. Recall and precision must not drop.

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
