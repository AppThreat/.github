# 0001. callsites: what counts as a use, attribution, standard libraries, vendored code

| | |
| --- | --- |
| Date | 2026-10-30 |
| Status | Accepted |
| Decided by | @prabhu |
| Plans | [callsites-overview.md](../callsites-overview.md), [callsites-risks.md](../callsites-risks.md) |

## Context

The callsites plans left five questions open (risks P1–P5). They decide which records the slice
emits, how the ground truth is scored, and what cdxgen turns into occurrences.

## Decisions

### P1. Every reference to a dependency is a use

Run-time uses, **declaration types** (parameter, field, local, return and `throws` types),
**TypeScript `implements`**, **C/C++ macro uses**, and **uses in generated code** (Lombok members,
annotation-processor and compiler-generated calls) all count. Each keeps a distinct `kind`
(`decltype`, `implements`, `macro`, …) so consumers can still filter, but none is dropped or neutral.
The ground truth credits and penalises them like any other use.

Unchanged by this decision: import lines are recorded by `kind` but are not uses on their own; test
files stay out of scope by default.

### P2. A typed call belongs to the receiver's static type

`claims.get("k")` on a jjwt `Claims` is a jjwt use even though `java.util.Map` declares `get`: the
dependency the code relies on is the one whose type it holds. The record's `module` is the
receiver's static type; when the declaring class differs, the record also carries it as
`declaringModule`, so a consumer that wants the declaration (for a vulnerable-method match, say) has
it. The ground truth credits a record on the receiver's package; the declaring class's package is
neutral.

### P3. Standard libraries are in the slice and in cdxgen

Node built-ins, the Python standard library, the JDK, PHP and Ruby core, and libc/libc++ uses are
emitted with `builtin: true` and passed to cdxgen, which records them as occurrences where the BOM
has a component for the runtime or standard library. Scoring includes them by default.

### P4. The evaluation harness stays private

The oracles, scorer, corpus checkouts and recorded results are not published. The public plans keep
the corpus manifest (projects by URL, commit and digest, with licences) and the numbers; the
synthetic fixtures that become repository tests (ground-truth D2) are published with the tests.

### P5. Vendored third-party code is external

Code a project carries from someone else (`vendor/`, `third_party/`, `deps/`, bundled minified JS,
copied single-header libraries) is marked external wherever it can be recognised: package-manager
directories by default (`vendor/` for Composer, `node_modules/`), the BOM's component locations when a
BOM is given, and a new command-line option that takes a regular expression of paths to treat as
external, supported by every frontend and needed above all for C/C++, where no package manager says
which directories are vendored. External code is parsed when types or bodies are needed but its
methods and types are `isExternal=true`, and uses of it from project code are callsites records.

## Consequences

- Scorer: `decltype`, `implements` and JS type positions move from neutral to scored; builtins are
  included by default (`--without-builtins` to exclude). The sprint-1 baseline is re-run under these
  rules; numbers in the plans were measured under the previous defaults.
- core-js D3: `implements` records count as evidence in cdxgen.
- c-cpp D2: macro uses are emitted and counted; D7 adds the external-path option.
- jvm-android D1 and language-versions D4: Lombok and other generated members are modelled.
- consumers D2/D5: builtin records are attributed to runtime components when the BOM has them.
- ground-truth D1: no public harness; publish the manifest and the test fixtures only.
