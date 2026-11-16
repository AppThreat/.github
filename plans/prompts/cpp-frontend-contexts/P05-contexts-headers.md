# P05: build context on every file, and headers that are not self-contained

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D8, D9 and the risks in [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), and the P01 and P04 reports in `~/work/cpp-frontend-contexts/reports/`.

Issues: {D8} (task A) and {D9} (task B). Branches: `cfc/p05-contexts` in chen and atom, from `origin/feat/cpp-frontend-contexts`, or from the P04 branches if they are not merged yet (D8 writes its duplicate records into the report section P04 added).

## Background

Read in c2cpg: `parser/IncludeGraph.scala` (`includers`, `readsAsCpp`), `parser/ProjectSources.scala` (`headerOwners`, `headerContext`, `settingsFor` and the unit order), `parser/CompileCommands.scala` (`CompileDatabase.byFile` and `files`), `parser/CdtParser.scala`, `parser/CustomFileContentProvider.scala` and `passes/AstCreationPass.scala`. Find out how the AST of a unit relates to the nodes CDT gives for the headers it includes, and where c2cpg decides which file's nodes it writes. In edg2atom, read how a header is written as part of its owner unit (`passes/EdgAstCreationPass.scala`, and "Headers, caching and failure" in edga's `docs/how-edga-works.md`).

The P01 report says whether c2cpg actually loses types on the non-self-contained fixtures. If it does not, Task B shrinks to keeping that behaviour under test and covering the X-macro case; say so and do only that.

## Task A: the `build-context` tag and duplicates (D8)

Write the `build-context` tag on every FILE node from both front ends, as D8 describes. The fingerprint is computed from the compile command after removing the options `CompileCommands` already treats as not changing the program; reuse that list, do not write a second one. Report duplicate database entries in the parse report section from P04, with every command and the one used.

## Task B: headers that are not self-contained in c2cpg (D9)

Detect the headers D9 describes and take their nodes from the owner unit's parse instead of parsing them separately. Keep positions in the header's own file. A header that parses on its own must keep exactly today's graph: compare the leveldb and abseil-cpp graphs before and after, FILE by FILE, and list every header whose graph changed, with the reason.

The detection must be cheap: it runs on every header. If the second detection rule (unresolved names that the owner declares first) needs a parse of the header on its own, use the parse that already happens, not an extra one.

Move c2cpg's AST format version, and check that the AST cache key still covers everything the header's graph now depends on (the owner unit and its settings).

## Finish

Run the gates with both front ends. Report which leveldb and abseil-cpp headers, if any, the detection selected.
