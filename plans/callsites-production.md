# callsites: production readiness and release

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/311 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

The slice becomes the source of dependency-usage evidence in SBOMs, so it must behave like a
compiler pass: the same input gives the same bytes, one odd node never loses the whole slice, and it
fits in the memory cdxgen gives atom. Today one orphan identifier crashes it (core-js plan), and the
callsites process uses more memory than the usages process on the same atom.

## Deliverables

### D1. Determinism

Records are sorted by (file, line, col, module, path) and never depend on node ids, which the
streaming AST passes assign in completion order. Done when three runs on one project per language
give byte-identical slices.

### D2. Failure isolation

Per-file and per-record error handling with a counted warning and the failing node id; the slice is
always written. Tracked with the crash fix in the core plan (D1), which lands first.

### D3. Memory bounds

The callsites process stays within the usages process's peak RSS on the same atom. Done on
juice-shop, outline, DefectDojo, mall and bookstack.

### D4. Documentation

The callsites lesson and CLI help cover every language: what a record means, `via` and `kind` per
language, known limits. Done when the docs site builds with the new pages.

### D5. Release chain and full corpus run

overflowdb2 and cpg2 (if any schema change landed), chen, atom, then cdxgen and dep-scan. The full
corpus is scored on the release candidates and the table goes into the release notes. Done when the
release candidates meet every language plan's targets.

### D6. Decide what to retire

With callsites as the occurrence source, decide which parts of `usages` remain (services/OpenAPI,
UDT filtering, C includes) and plan their replacements.
