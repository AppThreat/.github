# Rules for every prompt in this plan

These prompts drive an implementation agent through [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md). A second agent reviews, refactors and publishes the work, and a maintainer approves it. Read this file first in every prompt and follow it throughout.

## Where things are

- **Repositories:** chen at `~/work/AppThreat/chen` and atom at `~/work/AppThreat/atom`. Read other checkouts under `~/work` if they help, but do not change them.
- **Corpus:** the memory-safety corpus at `~/sandbox/memsafe-corpus`. Read its `README.md` before the first run. `tools/run.sh` scores the hand-written arm, `tools/run_cve.sh` the FFmpeg arm, and `tools/score.py` any findings file. The precision arms that D1 adds live under `arms/` in the same folder.
- **Working folder:** `~/work/memsafe-alloc-styles`. `refs/` holds the probe the plan's table came from (`allocation-styles-probe.c`) and its findings from c2cpg at `medium` and `low` and from edg2atom at `low`; read them, do not change them. Write each prompt's report to `reports/P<nn>-report.md` and nothing else.
- **EDG front end:** edg2atom runs with `--c-frontend edg --edga-path ~/work/AppThreat/edga/build/bin/edga` on `atom memory-safety`, or `ATOM_ARGS="--c-frontend edg --edga-path ..."` on the corpus scripts. Every scope-cleanup check runs on both front ends.
- **Plan:** the prompt names the deliverables it covers. The plan section is the design and its "Done when" paragraph is the acceptance test. If the prompt and the plan disagree, the prompt wins; say so in the report.
- **Writing and credit rules:** `~/.agents/AGENTS.md`. The commit-msg hook enforces them.

## Git

1. Before starting, run `git fetch origin` in each repository the prompt touches and check that the working tree is clean. If the task branch already exists, inspect it with `git status` and `git log` and continue it; do not start over.
2. Create task branches from `origin/feat/memsafe-alloc-styles` in chen and atom, using the branch names the prompt gives. When a prompt follows another whose branches have not been merged yet, the prompt names the branch to start from instead.
3. Commit in small, reviewable steps. Each commit compiles.
4. **Never push, never create or delete remote branches, never open pull requests, never comment on GitHub.**
5. **Never rewrite `main` or `feat/memsafe-alloc-styles`, never `git reset --hard` a branch you did not create in this prompt, and never run `git stash`.**

## Commit messages, code comments and docs

- **Subject:** a plain sentence in the repository's style, for example "Summarise destroy functions that free members before their argument". No conventional-commit prefixes in chen or atom.
- **Body:** what changed and why, in short paragraphs.
- **No process references** anywhere in commits, code, comments, test names or docs: no deliverable or prompt numbers (D3, P02), no plan file names, no corpus or arm names, no `~/sandbox` or `/Users` paths, no agent or model names. Issue numbers belong in the pull request, which the reviewer writes. Test fixtures describe the C idiom they exercise, not the plan item.
- **Style:** no first person, no em-dashes, no emojis, no words from `~/.agents/credits/jargon.txt`.
- **Code comments** explain the code as it is now, for a reader who has never seen this plan.

## How to work

- **Iterate fast.** Write the C fixture for the case first, then run the single test suite that covers it, for example `sbt "c2cpg/testOnly io.appthreat.c2cpg.passes.AllocationStatePassTests"` in chen, with a timeout. Run `atom memory-safety` on one small directory, not on a whole project, while developing. Do not run benchmarks and do not time anything.
- **Negative control first.** For every new behaviour, write the correct-C look-alike before the detector: the style's own correct idiom, plus a loop, a `goto` error path, static storage and a freep wrapper where they apply. A finding on a correct function is a failure, whatever the recall gain.
- **Evidence, never names.** Summaries come from declared attributes, inferred bodies, the built-in inventory or a declared profile. Do not add any decision based on a function's name; the existing name heuristic in `MemorySemanticsPass` stays limited to `low` findings.
- **End to end.** Every rule change gets a test in atom's `MemorySafetyCommandTests` that runs the command and reads the rendered finding (rule, line, confidence). A tag assertion in chen alone does not count, because earlier work computed facts that the renderer then dropped.
- **chen and atom together.** To test atom against a chen branch, run `sbt publishLocal` in chen (keep its version unchanged) and then atom's tests. Say in the report which chen commit atom was tested against.
- **Formatting.** Run `sbt scalafmtAll` in each repository you changed, as the last commit of the prompt, and only on files you changed.
- **Gates once, at the end.** On the final head, run the gates in the plan's "Gates" section at `medium` and `low`: `tools/run.sh`, `JOBS=5 PROJECT=ffmpeg-all SCOPE=libavformat tools/run_cve.sh`, and the arms with `tools/run_arms.sh` once D1 has added it. Compare every number with the baseline in `~/work/memsafe-alloc-styles/reports/P01-report.md`. Report exit codes and the summary lines. Never hide a failure behind `| tail` or `|| true`.
- **Every new finding on a real arm is read by hand.** For each finding a change adds on an arm, open the source and decide whether it is a real defect. List each one in the report with the decision and a one-line reason.
- **Stay in scope.** Do not reformat files you do not otherwise change, rename unrelated things, or add a dependency.
- **Tests check behaviour.** Do not record your own output as the expected value unless you checked every field by hand; list any such test under "Recorded expectations". Fixtures contain no local paths, usernames or hostnames.
- **No silent clean results.** A front-end failure, a timeout or a skipped file is reported with its reason, never as zero findings.
- **Stop when the prompt's tasks are done.** Do not start the next prompt.

## When something is unclear

If a decision is needed that the plan does not make, choose the option that commits to the least and is easiest to change later, implement it, and record the decision and the alternatives under "Decisions". If the decision would change a tag name, a rule id, a command-line option or the inventory's JSON format in a way that is hard to undo, stop that part and put it under "Questions".

## The report

Write the report with these sections:

1. **Branches:** each branch with its head SHA and base SHA, per repository.
2. **Commits:** one line each.
3. **Done when:** for each condition in each deliverable's "Done when" paragraph, whether it is met, and the exact command and output lines that show it.
4. **Gates:** every gate at `medium` and `low`, baseline next to result.
5. **Arm findings read by hand:** each added finding, its decision and the reason.
6. **Not done:** each part not done, with the reason.
7. **Decisions** and 8. **Questions.**
9. **Recorded expectations.**

Be exact. "All tests pass" needs the command and the count. If you did not run something, say so.
