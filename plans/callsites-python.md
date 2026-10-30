# callsites for Python

| | |
| --- | --- |
| Epic | EPIC_URL |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

On nine Python projects `usages` finds a median 0.77 of external use sites at 0.62 precision; most
of its false positives are import lines and constructor positions placed on unrelated lines, plus
uses of a parameter that shadows an import. A measurement prototype of the JS design on the same
atoms reaches a median 0.90 recall at 0.99 precision (DefectDojo: 0.889 / 0.990, vs 0.813 / 0.772),
in about 10 seconds on DefectDojo's atom.

The Python frontend already lowers imports to assignments (`x = import(from, name, alias)`), links
captured module-level names through closure bindings, and names many external calls through type
recovery, so the binding → origin → use design carries over directly.

## Scope

A `PythonCallSiteSource` in atom and fixes to pysrc2cpg type recovery that cause wrong names.

## Deliverables

### D1. Type recovery: shadowing and receiver-less calls (chen)

- A parameter or local that shadows an imported name inside its scope (`def f(requests):
  requests.get()`) must not take the import's names.
- A call with no receiver (`handler(request)`, `f(ctx)`) must never be named as a member of an
  argument's type (today `aiohttp.web_request.Request.handler`, `click.Context.f`).
- A str constant from a dependency module keeps a builtin type: `value.strip()` is not
  `urllib3.util.SKIP_HEADER.strip`. No member-name denylists.

Done with bad and good twins in `TypeRecoveryPassTests` for each.

### D2. Dotted imports bind their first segment (chen)

`import a.b` creates an identifier literally named `a.b`, and a use `a.b.c()` roots at an unassigned
local `a`. Bind `a` to the import so uses resolve through REF edges.

### D3. The Python adapter (atom)

Origins from import assignments (single-assignment rule), closure bindings, the `tmpN = a.b` callee
lowering, duplicated receiver nodes; `via=type` for calls named under a module the file imports,
guarded against shadowing; heritage, `except X`, typed attribute reads (`request.method`). Project
vs external from the import resolver's tags, not path guesses. Done when the fixtures pass and the
corpus subset is at or above the prototype on every project, precision ≥ 0.97.

### D4. Package mapping (atom)

Module → distribution through `top_level.txt` (`PythonDependencyStubs.packageIndex`) or the BOM's
`ImportedModules`, for records that carry `purl`.

## Risks and open questions

- Namespace packages and distributions that share an import name (`yaml` from PyYAML and
  ruamel-yaml) cannot always be mapped; such records keep an empty `purl`.
- Conditional imports (`try: import x except ImportError: x = None`) violate the single-assignment
  rule; decide whether a guarded fallback still counts as one origin.
- `if TYPE_CHECKING:` imports have no run-time uses.
