# P08: documentation and final measurement

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D12 and the whole of [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), and every report in `~/work/cpp-frontend-contexts/reports/`.

Issue: {D12}. Branches: `cfc/p08-docs` in edga, chen and atom, from `origin/feat/cpp-frontend-contexts` after P02 to P07 are merged into it. If any is not merged, stop and say which.

## Task A: documentation

Update the documents D12 lists. Start from what each document says today and change only what the work changed. For each new paragraph, find the code that makes it true and name the file in the report, next to the paragraph. Include, in chen's documentation, a short worked example of adding a toolchain table entry, and in atom's, an example of reading the parse report's `units` section and of a grouped template finding.

## Task B: final measurement

On the head of `feat/cpp-frontend-contexts` in all three repositories, run every gate in the plan against the P01 baseline, with both front ends, and every option the plan added at its non-default value on the P01 fixtures. Write the results into the report as the table the plan's Outcome section will hold. Do not edit the plan; the reviewer copies the table.
