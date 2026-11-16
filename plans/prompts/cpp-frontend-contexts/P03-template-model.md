# P03: one template model in chen, and atom grouping

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read the Approach section, D4, D5 and the risks in [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), and the P01 and P02 reports in `~/work/cpp-frontend-contexts/reports/`.

Issues: AppThreat/chen#330 (task A) and AppThreat/atom#415 (task B). Branches: `cfc/p03-template-model` in chen and atom, from `origin/feat/cpp-frontend-contexts`, or from the P01 branches if the prompt that hands you this one says P01 is not merged yet. Build edga from the P02 branch (or `feat/cpp-frontend-contexts` once it is merged) and name its commit in the report.

## Background

Read how each front end handles templates today:

- c2cpg: `astcreation/CppCallResolution.scala` (`templateInstanceSignature`, the call that links to the generic definition, and the `template-instance` tag) and `X2CpgDefines.TemplateInstanceTag` in `x2cpg/Defines.scala`.
- edg2atom: `astcreation/AstCreator.scala` (where `templateInstance` routines and types are selected), `astcreation/AstForCpp.scala`, `astcreation/TypeNames.scala` and `passes/DuplicateDefinitionPass.scala`.
- How chen's Java front end fills `DYNAMIC_TYPE_HINT_FULL_NAME`, and which chen and atom passes read it, so that filling it for C++ calls does not change call resolution or data flow somewhere you did not intend. List every reader in the report.

## Task A: tags and callee lists in both front ends (D4)

Implement the tags and callee lists of D4 and the plan's Approach section in edg2atom (reading the fields P02 added) and in c2cpg. Add the tag names to `X2CpgDefines` with comments that say what each value is. Prototype METHODs from edg2atom have their dependent types as written by edga; check that the memory-safety passes treat a METHOD tagged `template-pattern` with dependent types without new findings (the passes already see c2cpg's generic METHODs, which is the model to follow).

Move both AST format versions and check warm against cold.

## Task B: atom groups template code (D5)

In atom, group `memory-safety` findings and the usages and reachables slice entries as D5 describes. Find where each output is built, add the `instances` field without removing or renaming anything, and add end-to-end tests in `MemorySafetyCommandTests` and in the slice tests for the P01 seeded bugs: the bug in every instantiation is printed once with both listed, the bug in one instantiation lists one, under each front end.

## Finish

Run the gates with both front ends and report graph sizes. Prototype METHODs are expected to grow edg2atom's graphs on abseil-cpp; give the counts and check them against the growth limit in the plan's risks.
