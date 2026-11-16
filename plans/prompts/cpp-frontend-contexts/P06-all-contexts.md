# P06: every build context, opt-in

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D10 and the name-stability and graph-growth risks in [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), and the P01 and P05 reports in `~/work/cpp-frontend-contexts/reports/`.

Issue: AppThreat/atom#417. Branches: `cfc/p06-all-contexts` in chen and atom, from `origin/feat/cpp-frontend-contexts`, or from the P05 branches if they are not merged yet.

## Background

Read how a unit's settings flow from `CompileDatabase` through `ProjectSources` into `AstCreationPass` and edg2atom's `EdgAstCreationPass`, how `DuplicateDefinitionPass` decides that two definitions are the same and keeps one, and how calls are linked to METHODs by full name in both front ends and in the later passes. List in the report every place that assumes one METHOD per full name.

## Task: `--c-build-contexts` (D10)

Add the option to atom and the matching setting to chen, with `first` as the default. With `all`, analyse each distinct context of a file, keep identical functions once, and keep differing functions once per context with the suffix and tag D10 specifies. Calls inside a context resolve to that context's copy of a function; a call from a context to a function that does not differ resolves to the single copy.

The equality test for "the same body" decides how many copies there are. Use the same test `DuplicateDefinitionPass` uses if it fits; if it does not, record the test you chose under "Decisions".

The default must give exactly today's graph: compare leveldb and abseil-cpp graphs with the option absent and with `first`, and show they are identical.

Run the P01 duplicated-file and two-target fixtures with `all` under both front ends, and run leveldb with `all` (its CMake database has one context per file, so the graph must equal the default). Report node and METHOD counts.

## Finish

Run the gates at the default and the P01 context fixtures with `all`.
