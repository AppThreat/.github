# callsites: consumption in cdxgen and dep-scan

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/310 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

cdxgen runs `callsites` only for JS/TS (`lib/evinser/evinser.js`, `JS_LANGUAGES`) and reads three
fields of each record (`module`, `file`, `line`), mapping npm packages through the BOM's
`ImportedModules`. Records are not filtered by `--exclude`, not embedded by `--annotate`, and
dep-scan does not pass a callsites file to cdxgen. dep-scan never reads slices for occurrences; it
reads `evidence.occurrences` from the BOM, and its reachability evaluation script compares against
its own previous output rather than real labels.

`usages` still feeds things `callsites` does not replace: OpenAPI and services (atom-tools reads
`objectSlices`), user-defined type filtering for usages and data-flow attribution, and C include
attribution.

## Scope

cdxgen's evidence pipeline and dep-scan's cdxgen invocation and reachability evaluation. OpenAPI,
services and UDT filtering keep reading `usages`.

## Deliverables

### D1. Run callsites for every atom language

Python, Java/JAR/APK, PHP, Ruby and C/C++ as each language plan lands, from the same atom, then
through the single-process run (performance D1). Done when `--evidence` writes a callsites slice for
each language in repotests.

### D2. Attribute records to packages per ecosystem

Generalise `attributeJsCallsites`: npm as today; pypi by top-level module through
`ImportedModules`; maven by class through the Namespaces DB; composer and gem by namespace/constant
through `Namespaces`; C/C++ by header through the include resolver. Builtin records (decision 0001, P3) go to the runtime or standard
library component when the BOM has one. Prefer a record's `purl` when atom
filled it (core-js plan D5). Done when poku tests cover each ecosystem and repotests assert
occurrences for a project per ecosystem.

### D3. Filters and annotations

Apply `--exclude` to callsites records (`file`), embed the slice under `--annotate`, add it to the
slices-file checks. Done with poku tests.

### D4. dep-scan passes the callsites slice

`set_slices_args` passes `--callsites-slices-file`; the file is kept with the other slices.

### D5. Occurrences from callsites by default

Switch occurrences to callsites for every atom language once each language meets its targets;
usages stays for services, UDT and C includes. Done when repotests pass and BOM occurrence recall
against the ground truth is at least the slice's.

### D6. Real labels for dep-scan's reachability evaluation

`contrib/reachability_eval.py` scores `direct_purls` and reached purls against the ground-truth
corpus instead of its previous snapshot.

## Risks and open questions

- Release coupling: cdxgen pins an atom version. The v4 atom (Scala 3.10, chen 4) is planned for
  cdxgen at the end of 2026, so D1–D5 land on cdxgen's branch that tracks atom v4, not on its
  current release line. Decide the branch before D1.
- No schema versioning: field changes in atom and the cdxgen reader must merge together.
- Each slice is a separate process with its own 20-minute budget; D1 of the performance plan
  changes how cdxgen accounts for timeouts.
- These deliverables live in cdxgen/cdxgen and owasp-dep-scan/dep-scan, outside this organization's
  board automation; their issues are added to the board by hand.
