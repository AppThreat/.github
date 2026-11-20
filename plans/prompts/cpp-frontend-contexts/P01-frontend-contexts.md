# P01: every deliverable, D1 to D6, in one session

Load the "skill: dynamic workflow" skill (zcode's `dynamic-workflows`) before anything else and run this prompt with its `CreateWorkflow` tool, as `00-RULES.md` "Work as a workflow" describes. Every piece below gets a developer subagent and a separate reviewer subagent, both on GLM-5.3-Flash. Do not use the `Agent` tool for the pieces.

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read the whole of [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), the probes in `~/work/cpp-frontend-contexts/refs/`, and `~/sandbox/memsafe-corpus/README.md`.

This prompt is long: the lead keeps its state in the plan file, not in its context (see "Resuming").

| | |
| --- | --- |
| Issues | D1 AppThreat/chen#329; D2 AppThreat/edga#14, AppThreat/chen#330, AppThreat/atom#415; D3 AppThreat/chen#331, AppThreat/atom#416; D4 AppThreat/chen#332, AppThreat/atom#417; D5 AppThreat/chen#334; D6 AppThreat/atom#418 |
| Branches | `cfc/frontend-contexts` in edga, chen and atom, from `origin/main` |
| Plan file | `~/work/cpp-frontend-contexts/reports/P01-plan.md` |
| Report | `~/work/cpp-frontend-contexts/reports/P01-report.md` |

## Before any piece (lead)

1. **Baseline.** Build edga from `main` and check `edga --version` reports 0.3.0 with EDG commit 123522f. Publish chen and stage atom from `main`. In the corpus, run `LEVELS=medium GATES="corpus corpus-edg projects" OUT=out/gates-cfc-base tools/run_gates.sh` and compare with `out/gates-p02-final`. If any number differs, run the full `OUT=out/gates-cfc-base tools/run_gates.sh` and use it as the baseline instead, and say why in the report. Record node and METHOD counts of the leveldb and abseil-cpp graphs from each front end.
2. **Probes.** Run edga on `refs/templates-probe.cpp` and compare with `refs/templates-probe.edga.json`. Build a graph of `refs/non-self-contained/` with each front end and compare what the header's function sees through its parameter (the types of `c->n` and `c->buf`). The plan says the CDT result is unconfirmed; settle it, and if c2cpg does not lose the types, narrow piece H to the X-macro case and to keeping today's behaviour under test.
3. **Split.** Write `P01-plan.md`: the piece table below as you confirm or change it after reading the code, every decision the pieces need, and the fixture each piece owns.

## Pieces and order

| Piece | Work | Owns | Starts after |
| --- | --- | --- | --- |
| A | D2 edga: template identity, then prototype bodies; golden and schema updates | edga `src/edga_back_end.cpp`, `schema/edga-1.schema.json`, `docs/json-format.md`, `tests/` | |
| B | D2 c2cpg: `template-pattern` on template definitions, `template-args` on instance calls, dependent-call callee lists; the three tag constants | c2cpg `astcreation/CppCallResolution.scala` and the files it needs for call creation, `x2cpg/Defines.scala`, c2cpg template tests and the chen template fixture | |
| E | D3 toolchain table | c2cpg `parser/CompileCommands.scala`, `parser/PredefinedMacros.scala`, `resources/predefined-macros/`, `tools/predefined-macros/`, edg2atom `parser/EdgaRunner.scala`, their tests and the toolchain fixtures | |
| H | D4 headers that are not self-contained (c2cpg) | c2cpg `parser/ProjectSources.scala`, `parser/IncludeGraph.scala`, `parser/CdtParser.scala`, `parser/CustomFileContentProvider.scala`, `passes/AstCreationPass.scala` apart from `AstFormatVersion`, the typedef and X-macro fixtures | |
| C | D2 edg2atom: read `template`, `templateArgs`, `prototype` and `dependent`; tags; prototype deduplication | edg2atom `astcreation/`, `passes/DuplicateDefinitionPass.scala`, edg2atom template tests | A, B |
| F | D3 and D4 reporting: the parse report's `units` section, unknown drivers, duplicate database entries | chen `x2cpg/parse/` (a sibling of `ParseReporter`), the hooks it needs in `ProjectSources` and `EdgaRunner`, atom's parse-report writer and `ParseReportTests` | E, H |
| G | D4 `build-context` tag on every FILE, both front ends | a new pass in each front end (or one in x2cpg) and its registration in `C2Cpg.scala` and `Edg2Atom.scala`, its tests and the two-includer fixture | E, H |
| D | D2 atom: group findings and slice entries by `template` | atom's memory-safety output and slice writers, their tests, the two seeded-bug fixtures | C |
| I | D4 `--c-build-contexts` | atom `Atom.scala` options, chen's settings for it, `CompileDatabase`, `ProjectSources`, `DuplicateDefinitionPass`, call linking by full name, the duplicated-file and two-target fixtures | C, F, G |
| J | D5 CDT workers | a worker entry point in c2cpg, `passes/AstCreationPass.scala`, the chen option; the atom option goes into `Atom.scala` after I merges | H, I |
| T | atom end-to-end tests | atom test files the batch needs | each checkpoint |
| K | D6 documentation | the documents D6 lists | every other piece |

Batches: A, B, E and H; then C, F and G; then D, I and J; then K. A piece starts when every piece it follows is merged and no running piece owns any of its files. A is a CMake build, not sbt, so batch one has three sbt-heavy developers. The lead may split a piece into two that run one after the other on the same branch, and records it.

## Decisions that are already made

- **Template model.** As the plan's Approach section says: instance METHODs (edg2atom only) carry `template` (the template METHOD's full name) and `template-args`; template METHODs (c2cpg's generic definition, edg2atom's prototype) carry `template-pattern`; a dependent call keeps its `METHOD_FULL_NAME` and lists its callees in `DYNAMIC_TYPE_HINT_FULL_NAME`. Before B and C write that field, the lead lists every chen and atom pass that reads it (chen's Java front end fills it today) and records in the plan file why C++ calls filling it changes no call resolution or data flow that should not change.
- **Prototype deferral (A).** A measures before implementing prototype bodies: edga with and without `--no_defer_parse_function_templates` on the template fixture, every existing golden and the abseil-cpp units the lead lists from the baseline run. The lead reads the counts (units whose exit status changes, new diagnostics, real routines that change) and decides, in the plan file, between turning deferral off and the fallback in the plan's first risk. This is a hole in A's workflow.
- **Windows goldens.** They cannot be regenerated on this machine. A regenerates every other platform's goldens, reads each diff, and lists the Windows goldens that need regenerating, for the reviewer to do in CI.
- **Unchanged by default.** GCC, Clang and MSVC compile commands give exactly today's settings (E); a header that parses on its own gives exactly today's graph (H); without `--c-build-contexts all` and `--c-isolate` the graph is exactly today's (I, J). Each piece proves its case with a test that compares graphs, and the lead compares the leveldb and abseil-cpp graphs FILE by FILE at the checkpoint after the piece merges.
- **Parse report.** The `units` section and the unknown-driver and duplicate records are additions. `ParseReportTests` passes unchanged, and nothing is collected when `--parse-report` is not given.
- **Graph growth.** Prototype METHODs grow edg2atom's graphs. Above 20 percent on leveldb or abseil-cpp at default options, stop that part and put it under "Questions" with the counts.

## Checkpoints

After merging each batch, the lead:

1. moves the AST format versions of the front ends the batch changed;
2. rebuilds edga if the batch changed it, runs `sbt publishLocal` in chen and `sbt stage` in atom, each in its own call, and checks the staged chen jar's date;
3. hands piece T the merged batch: a developer writes the atom end-to-end tests for every change atom prints, a reviewer checks them, and the lead runs them;
4. runs `LEVELS=medium GATES="corpus corpus-edg projects" OUT=out/gates-cfc-<batch> tools/run_gates.sh`. If recall or precision falls below the baseline, a `@nofinding` line gains a finding, or a project gains a finding nobody has read, the batch is fixed before the next starts;
5. checks a warm run against a cold run on the fixtures the batch touched;
6. records the batch's merge SHAs, test counts, gate numbers and graph sizes in `P01-plan.md`.

## Finish

1. Merge piece K, run `sbt scalafmtAll` on the changed files in chen and atom as the last commit, rebuild edga, then `sbt publishLocal`, `sbt stage` and the atom end-to-end tests once more.
2. Run the whole-branch review from `00-RULES.md` in each repository and fix what it finds.
3. Run edga's goldens with the schema check, chen's `c2cpg/test` and `edg2atom/test`, atom's `test`, each in its own call, and `OUT=out/gates-cfc-final tools/run_gates.sh` (every gate, `medium` and `low`). Read every finding any arm or project gains.
4. Write the report as `00-RULES.md` describes. Section 3 has one subsection per deliverable, D1 to D6, with every fixture and its result under each front end.

## Resuming

The session may stop before the end. `P01-plan.md` is the record a new session resumes from, so the lead keeps in it, as it goes: the piece table with each piece's state (planned, developing, in review, merged), its branch and merge SHA, the decisions, the measurements and the checkpoint results. A new session reads `00-RULES.md`, this prompt and `P01-plan.md`, checks `git status` and `git log` in all three repositories and in any developer worktree still present, and continues from the first piece not merged. It does not start a merged piece again.
