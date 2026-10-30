# callsites for C and C++ (CDT and EDG)

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/308 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

C and C++ projects use libraries through headers: calls, global variables, enum constants, and
macros. Against a clang-based oracle (JSON AST per translation unit from `compile_commands.json`;
external = declared in a header outside the project, package = the header's install prefix) on
libuv, jq, OpenSSL's TLS demo apps, curl and leveldb, with both frontends:

| project | usages R / P, CDT | usages R / P, EDG | call-based prototype R, either |
| --- | ---: | ---: | ---: |
| libuv (S) | 0.93 / 0.997 | 0.93 / 1.0 | 0.93 |
| jq (M) | 0.72 / 0.96 | 0.72 / 1.0 | 0.34 |
| openssl apps (M) | 0.98 / 0.985 | 0.96 / 1.0 | 0.93 |
| curl (L) | 0.85 / 0.95 | 0.74 / 0.97 | 0.59 |

- Call recall is the same on both frontends (about 95 % on curl).
- References to external globals and enum constants are missed by both (curl 1 of 145, libuv 0 of
  22).
- Object-like macro constants dominate the rest: `usages` finds 383 of curl's 398 on CDT but 244 on
  EDG, which constant-folds `case` labels (`case SSL3_RT_CHANGE_CIPHER_SPEC:`); a call-based slice
  finds 59.
- CDT IMPORT nodes carry `include-resolved-path` and `include-system`; EDG atoms have neither.
- CDT adds false positives on include lines and macro expansion sites; EDG does not.
- EDG is up to 1.8× slower and uses up to 1.8× the memory.
- Parse fidelity on 31 C99–C23 and C++11–C++23 snippets: CDT fails C23 `[[nodiscard]]`, C23 digit
  separators with binary literals and C++23 deducing `this`; EDG parses all 31.
- Function bodies in project headers are not sliced (leveldb `port/port_stdcxx.h`), likely because
  atom builds C graphs with `withFunctionBodies(false)` for headers (to confirm).
- The default C ignore pattern `.*(docs|example|samples|mocks|Documentation|demos).*` drops a whole
  input such as OpenSSL's `demos/` with no warning outside compile-database mode.

## Scope

c2cpg (CDT) and edg2atom (EDG) in chen, edga where EDG output lacks facts, and a `CCallSiteSource`
in atom. Header → package mapping stays in cdxgen (`cppIncludeResolver`), with an optional `purl`
from atom when a BOM is given.

## Deliverables

### D1. External references beyond calls (chen, both frontends)

Identifiers that refer to external globals and enum constants carry the declaring header, like calls
do today (`callee-declared-in`). Done when curl's and libuv's global/enum references are found.

### D2. Macro uses (chen, edga)

Every expansion of an external macro (object-like and function-like) is recorded at its expansion
site with the defining header, on both frontends; EDG keeps the macro identity of constant-folded
`case` labels. Macro uses count as dependency evidence (decision 0001, P1).

### D3. EDG parity for includes (chen, edga)

EDG atoms carry IMPORT nodes with `include-resolved-path` and `include-system` like CDT.

### D4. The C/C++ adapter (atom)

Calls, references and macro uses whose declaration is in a header outside the project; `module` =
header path as included, `path` = symbol; C++ member calls and constructors of external classes.
Done at ≥ 0.95 recall and ≥ 0.97 precision on curl, libuv, jq and the OpenSSL apps, on both
frontends.

### D5. CDT parse gaps (chen)

C23 attributes and digit separators, C++23 deducing `this`; report what CDT could not parse (shared
with the language-versions plan D1).

### D6. Header bodies and the ignore pattern (atom)

Slice function bodies defined in project headers; make the default ignore pattern match path
segments under the input root, never the input root itself, and warn whenever it removes files.

### D7. Mark vendored code external by path (atom, chen)

A command-line option that takes a regular expression of paths (`third_party/`, `deps/`, copied
single-header libraries) whose code every frontend marks `isExternal=true`, with C/C++ first, plus
the BOM's component locations when a BOM is given (decision 0001, P5). Uses of that code from the
project become callsites records with the vendored library as `module`.

## Risks and open questions

- Without a compilation database, include resolution is guesswork; cdxgen must pass one
  (`--compile-commands`) for meaningful records.
- EDG is available only as the `edga` binary; its tests cancel in CI without it (risks B4).
- C++20 modules are untested on both frontends.
