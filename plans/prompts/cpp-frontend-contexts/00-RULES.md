# Rules for every prompt in this plan

These prompts drive an implementation agent through [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md). A second agent reviews, refactors and publishes the work, and a maintainer approves it. Read this file first in every prompt and follow it throughout.

## Where things are

- **Repositories:** edga at `~/work/AppThreat/edga`, chen at `~/work/AppThreat/chen` and atom at `~/work/AppThreat/atom`. Read other checkouts under `~/work` if they help, but do not change them. Other agents may be working in these checkouts; if a working tree is not clean, or is on a branch this plan did not create, stop and say so in the report instead of touching it.
- **Working folder:** `~/work/cpp-frontend-contexts`. `refs/` holds the probes the plan's "Why" section came from: `templates-probe.cpp` with its edga output `templates-probe.edga.json`, and `non-self-contained/` (a unit and a header that uses the unit's typedef). Read them, do not change them. Write each prompt's report to `reports/P<nn>-report.md` and nothing else there.
- **edga binary:** build it in the edga checkout with `cmake --build build --target edga` (see edga's README; `tools/fetch-edg.sh` first if `third_party/edgcpp` is empty). chen and atom run it with `--c-frontend edg --edga-path ~/work/AppThreat/edga/build/bin/edga`. When a prompt changes edga, chen and atom are tested against the edga built from that prompt's branch, and the report names its commit.
- **Memory-safety corpus:** `~/sandbox/memsafe-corpus`. Read its `README.md` before the first run. `tools/run.sh` scores the hand-written arm; the leveldb and abseil-cpp arms are described there. `ATOM_ARGS="--c-frontend edg --edga-path ..."` runs them with edg2atom.
- **Plan:** the prompt names the deliverables it covers. The plan section is the design and its "Done when" paragraph is the acceptance test. If the prompt and the plan disagree, the prompt wins; say so in the report.
- **Writing and credit rules:** `~/.agents/AGENTS.md`. The commit-msg hook enforces them.

## Git

1. Before starting, run `git fetch origin` in each repository the prompt touches and check that the working tree is clean. If the task branch already exists, inspect it with `git status` and `git log` and continue it; do not start over.
2. Create task branches from `origin/feat/cpp-frontend-contexts` in each repository, using the branch names the prompt gives. When a prompt follows another whose branches have not been merged yet, the prompt that hands you this one names the branch to start from instead.
3. Commit in small, reviewable steps. Each commit compiles.
4. **Never push, never create or delete remote branches, never open pull requests, never comment on GitHub, never create releases or tags.**
5. **Never rewrite `main` or `feat/cpp-frontend-contexts`, never `git reset --hard` a branch you did not create in this prompt, and never run `git stash`.**

## Commit messages, code comments and docs

- **Subject:** a plain sentence in the repository's style, for example "Link template instances to the template they came from". No conventional-commit prefixes in chen or atom; follow edga's history for edga.
- **Body:** what changed and why, in short paragraphs.
- **No process references** anywhere in commits, code, comments, test names or docs: no deliverable or prompt numbers (D3, P02), no plan file names, no `~/sandbox`, `~/work` or `/Users` paths, no agent or model names, and no mention of the language server whose write-up motivated the plan. Issue numbers belong in the pull request, which the reviewer writes. Fixtures describe the C or C++ construct they exercise.
- **Style:** no first person, no em-dashes, no emojis, no words from `~/.agents/credits/jargon.txt`.
- **Code comments** explain the code as it is now, for a reader who has never seen this plan.

## How to work

- **Iterate fast.** Write the fixture for the case first, then run the single test suite that covers it with a timeout, for example `sbt "c2cpg/testOnly io.appthreat.c2cpg.parser.CompileCommandTests"` or `sbt "edg2atom/testOnly io.appthreat.edg2atom.astcreation.CppShapesTests"` in chen, or `python3 tests/run.py --edga build/bin/edga` in edga. Run atom on one fixture directory, not on a whole project, while developing. Do not run benchmarks and do not time anything.
- **Build with a private ivy home.** Publish chen for atom with `sbt -Dsbt.ivy.home=<a folder under ~/work/cpp-frontend-contexts> publishLocal` and point atom's build at the same ivy home, so other sessions' `~/.ivy2` is not overwritten. sbt needs `GITHUB_TOKEN=$(gh auth token)`. Keep chen's version unchanged. Say in the report which chen and edga commits atom was tested against.
- **Both front ends.** Every deliverable that names both c2cpg and edg2atom is checked with both, and the report gives both results side by side.
- **Correct code first.** For every new behaviour, write the correct look-alike before the detector or the change: a template used once, a header that is self-contained, a database with no duplicates, a known compiler. A change that alters the graph of correct, ordinary code is a failure unless the deliverable asks for it.
- **AST format versions.** A change to what a front end writes moves its AST format version (`AstFormatVersion` in c2cpg's `AstCreationPass`, and the matching key in edg2atom). Check that a warm run gives the same graph as a cold one.
- **End to end.** Every change that atom prints gets a test in atom that runs the command and reads the output, not only a tag assertion in chen.
- **Formatting.** Run `sbt scalafmtAll` in chen and atom, and edga's formatter if its repository defines one, as the last commit of the prompt, and only on files you changed.
- **Gates once, at the end.** On the final head, run the plan's "Gates" section. Compare every number with the baseline in `~/work/cpp-frontend-contexts/reports/P01-report.md`. Report exit codes and summary lines. Never hide a failure behind `| tail` or `|| true`.
- **Every new finding on a real arm is read by hand.** For each finding a change adds on leveldb or abseil-cpp, open the source and decide whether it is a real defect. List each one in the report with the decision and a one-line reason.
- **Stay in scope.** Do not reformat files you do not otherwise change, rename unrelated things, or add a dependency.
- **Tests check behaviour.** Do not record your own output as the expected value unless you checked every field by hand; list any such test, and every regenerated edga golden, under "Recorded expectations".
- **No silent clean results.** A front-end failure, a timeout or a skipped file is reported with its reason, never as an empty result.
- **Stop when the prompt's tasks are done.** Do not start the next prompt.

## When something is unclear

If a decision is needed that the plan does not make, choose the option that commits to the least and is easiest to change later, implement it, and record the decision and the alternatives under "Decisions". If the decision would rename an existing METHOD or tag at default options, change edga's document version, add or rename a command-line option beyond those the plan names, or change the format of an existing atom output, stop that part and put it under "Questions".

## The report

Write the report with these sections:

1. **Branches:** each branch with its head SHA and base SHA, per repository.
2. **Commits:** one line each.
3. **Done when:** for each condition in each deliverable's "Done when" paragraph, whether it is met, and the exact command and output lines that show it.
4. **Gates:** every gate, baseline next to result, for each front end.
5. **Graph size:** node and METHOD counts on leveldb and abseil-cpp before and after, when the prompt changes what a front end writes.
6. **Arm findings read by hand:** each added finding, its decision and the reason.
7. **Not done:** each part not done, with the reason.
8. **Decisions** and 9. **Questions.**
10. **Recorded expectations.**

Be exact. "All tests pass" needs the command and the count. If you did not run something, say so.
