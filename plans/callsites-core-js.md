# callsites: a language-neutral core, and the JS/TS gaps

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/305 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

On ten JS/TS projects, `callsites` finds 0.93–1.00 of the binding-resolved use sites (usages:
0.65–0.95). Against the typed oracle, with dependencies installed, its precision is 0.89–0.98 and its
recall 0.67–1.00 (median 0.82): typed calls are the remaining recall gap. Four defects stand out:

- It crashes on outline (large TypeScript app): `NullPointerException … "method" is null` in
  `CallSiteSlicing.useRecord`. jssrc2cpg leaves 7,296 identifiers in that atom with no AST parent,
  all from object-pattern parameters of arrow functions (`name: ({ t, isMenu }) => …`); they keep
  REF edges, so the binding resolver reaches them.
- `implements OnInit` is reported as `extends` (54 records with no run-time use on juice-shop).
- Vue single-file components: script records land on template lines (23 on vue3-realworld).
- `astgen -t ts` did not finish on cdxgen's repository in 40 minutes (`--ts-types false`: 49 s).

The slice is also JS-only by construction, so every other language needs a shared core first.

## Scope

atom's `CallSiteSlicing`, chen's jssrc2cpg where the frontend causes the defect, and atom-parsetools
for the astgen stall.

## Deliverables

### D1. Never fail the slice (atom, chen)

chen: object-pattern and array-pattern parameters of arrow functions and methods get AST parents,
like function declarations. atom: no record builder assumes `.method`/`.file`; enclosing methods come
from `_astIn`; one failing node is counted and skipped. Done when outline produces a slice and a
fixture that crashed on main passes.

### D2. Core split, JS output identical (atom)

`CallSiteRecord`, kind ranking, dedupe, positions and JSON in a core; one `CallSiteSource` per
language; dispatch on `metaData.language`. Every record carries a language-native `module` and a
`path`. Done when the JS slice is byte-identical on every fixture and two saved atoms.

### D3. `implements` is its own kind (atom, chen if needed)

Interfaces are type-only, but they are uses (decision 0001, P1): emit kind `implements`, read from the
TYPE_DECL rather than source text, and count it as evidence.

### D4. Vue/Svelte/Astro positions (chen, atom)

Records from single-file components carry the script block's real line. Done when every
vue3-realworld record lies inside a `<script>` block or on a template binding that uses the import.

### D5. Optional `purl` per record (atom)

With `--bom-file`/`--bom-dir`, records carry the package URL, reusing the existing package
attribution (`PackageAttribution`, CdxPass claim tables), never new heuristics. Empty when unsure.

### D6. Typed-call recall and the astgen stall (atom-parsetools, atom)

Measure typed recall with `node_modules` present before changing slice logic; fix what is in the
slice, and reproduce the `-t ts` stall on cdxgen with `ASTGEN_TYPE_TIMING=1` for a fix in
atom-parsetools. Done when typed recall is ≥ 0.85 on the typed-oracle projects and cdxgen's
repository types in under 5 minutes.

## Risks and open questions

- D6 may show that the gap is type availability (no `node_modules` in cdxgen's usual input), which
  no slice change fixes.
