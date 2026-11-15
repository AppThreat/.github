# P07: documentation and final measurement

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D10 and the "Gates" section of [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md), and every earlier report in `~/work/memsafe-alloc-styles/reports/`.

Issue: AppThreat/atom#{{D10}}. Branches: `memsafe/p07-docs` in chen and atom, from `origin/feat/memsafe-alloc-styles` after all earlier prompts are merged. Write the report to `~/work/memsafe-alloc-styles/reports/P07-report.md`.

## Task A: documentation

1. Find the existing memory-safety documentation in both repositories (atom's docs for the `memory-safety` command and its rules, and chen's docs for the overlay passes and `memory-apis.json`). Extend them; do not start new documents unless no existing one fits.
2. Describe each allocation style: what the passes infer from bodies and attributes, what a profile declares, how scope cleanup is read from both front ends, how a region owns its allocations, and how reference counts are tracked. Give one short C example per style with the finding it produces and the correct version that produces none.
3. Document `--memory-api-profiles`, the profile list with the headers that select each, and how to declare an in-house region, release, acquire, steal or cleanup function in `--memory-api-config`, with a complete example file that `MemApiVocab` accepts (add a test that loads the example from the docs).
4. Check every sentence against the code. Remove any that describes behaviour the code lacks.

## Task B: final measurement

Run every gate at `medium` and `low`, on c2cpg, and the hand-written arm and the allocation-style fixtures on edg2atom too. Build one table per gate with three columns: the P01 baseline, the result now, and the difference. For each arm, list the findings at `medium` that were classified in P01 and say which ones changed and why.

Write the table into the report in a form the reviewer can paste into the plan's Outcome section, and list every part of D1 to D9 that any earlier report put under "Not done" with its current state.
