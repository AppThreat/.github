# P04: toolchain table and the settings each unit was given

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D6, D7 and the vendor-table risk in [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), and the P01 report in `~/work/cpp-frontend-contexts/reports/`. This prompt does not depend on P02 or P03.

Issues: AppThreat/chen#331 (task A) and AppThreat/atom#416 (task B). Branches: `cfc/p04-toolchains` in chen and atom, from `origin/feat/cpp-frontend-contexts`, or from the P01 branches if they are not merged yet.

## Background

Read in chen's c2cpg `parser/`: `CompileCommands.scala` (`familyOf`, `isCppDriver`, the wrapper list, how dialect options are read, and the list of options that do not change the program), `PredefinedMacros.scala` (the probe command, the process and disk caches, the fallback tables and their format), `ProjectSources.scala` (how a unit's settings are assembled) and `utils/IncludeAutoDiscovery.scala`. Read the tables in `c2cpg/src/main/resources/predefined-macros/`. In edg2atom read `parser/EdgaRunner.scala`, which maps the same settings to EDG's dialect options. In atom read how `--parse-report` is written (`Atom.scala`, around `ParseReporter.records`) and `ParseReportTests`; in chen read `x2cpg/parse/ParseReporter.scala`.

## Task A: the table (D6)

Move compiler identity into a table resource as D6 describes, and make `familyOf`, `isCppDriver`, `PredefinedMacros` and `EdgaRunner` read it. Keep the table's format plain and documented at the top of the file; each entry cites where its macros and option mapping come from. Add `tools/predefined-macros/generate.sh` (the script `PredefinedMacros` already names) and show in the report that it reproduces the existing GCC and Clang tables on this machine, with any differences explained.

Today's behaviour for GCC, Clang and MSVC must not change: the existing `CompileCommandTests` and `PredefinedMacrosTests` pass unchanged, and the gates' graphs are identical. For `nvcc`, preprocess `.cu` units as C++ with the host compiler's macros (from `-ccbin`, or the host compiler) plus nvcc's own, and record that device code is not parsed.

A driver the table does not know is recorded through `ParseReporter`; decide the record's fields together with Task B so the two agree.

## Task B: the `units` section (D7)

Add the `units` section to the parse report as D7 describes. chen collects the settings (through `ParseReporter` or a sibling object, whichever keeps the cost zero when the report is off, as `ParseReporter` does today), and atom writes them. The existing failure records keep their exact format; `ParseReportTests` passes unchanged. Add tests that read the section for the P01 toolchain and context fixtures, with each front end.

## Finish

Run every P01 toolchain fixture with both front ends and show, per fixture, the entry chosen, the macro source and that the `#error` was not reached. Run the gates.
