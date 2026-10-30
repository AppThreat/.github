# callsites: performance with identical output

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/309 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

Profiled on a saved juice-shop atom (three runs plus a JFR recording, identical output each time),
the `callsites` command spends about 80 % of its samples re-running `ChennaiTagsPass` on an atom the
`usages` command already tagged; the slice itself is about 5 %. Each run allocates 12.4 GB (usages:
4.4 GB), and the process peaks at 6.3 GB RSS against 5.0 GB for usages. cdxgen runs each slice as a
separate atom process with its own timeout budget.

`usages` is the slow slice on large projects: 360 s on mall (Java), 224 s on koel and 215 s on
bookstack (PHP, 12.9 GB), 66 s on DefectDojo. PHP spends most of it on `vendor/`, which atom parses
as project code.

## Scope

Tagging, atom's command structure, the PHP ignore rules and the hot spots profiling finds in both
slices. No tagger's output may change (maintainer rule: tagging runs for every command; make it
cheaper, never skip it).

## Approach

Profile first, with `--perf-report` stage numbers and JFR attribution on saved atoms, repeated three
times. Every change carries an equivalence test (slices and tags byte-identical) and a scaling test
that counts operations.

## Deliverables

### D1. One process, several slices

`atom usages` can also write the callsites slice (one flag), building or loading the atom once and
tagging once. Done when the two slices are byte-identical to two separate runs and cdxgen can use
it (consumers plan).

### D2. Tag once per input state

After tagging, store a marker in the atom with a hash of everything the taggers read (given BOM
files, validation config, chen version). A command on a reused atom whose marker matches already has
identical tags and does not re-run the pass; a changed input re-tags. Done when tags after the skip
equal tags after a fresh run on four saved atoms (JS, Python, Java, PHP), and changing the BOM
re-tags.

### D3. JS tagger hot spots

`JsPathAliases.configs` re-parses tsconfig/jsconfig files repeatedly (top allocator); memoise per
graph. Remove the per-call `Object.assign(this…)` code regex in the callsites binding resolver.
Done when a scaling test shows K config parses for K config files.

### D4. PHP: vendor is a dependency, not project code

Exclude `vendor/` by default as Ruby already does; if declarations from it are needed for types,
load them as external stubs. Done when symfony-demo, koel and bookstack build in a fraction of the
current time and memory with identical in-scope slices.

### D5. usages cost on Java and Python

Profile usages on mall and DefectDojo; fix the hot spots (repeated `method.ast` walks per
declaration, repeated `fullNameExact` lookups, per-method source dumps) with identical output.

## Risks and open questions

- The tag-state marker must cover every tagger input; a missed input silently serves stale tags.
  The equivalence test runs on every tagger change, not just this one.
- Excluding `vendor/` changes what PHP data flows can see. Measure reachables on the PHP corpus
  before and after.
