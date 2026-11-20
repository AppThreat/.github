# Rules for the prompt in this plan

This prompt drives an implementation agent through [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md). A second agent reviews, refactors and publishes the work, and a maintainer approves it. Read this file first and follow it throughout.

## Where things are

- **Repositories:** edga at `~/work/AppThreat/edga`, chen at `~/work/AppThreat/chen` and atom at `~/work/AppThreat/atom`. Read other checkouts under `~/work` if they help, but do not change them.
- **edga binary:** build it in the edga checkout with `cmake --build build --target edga` (see edga's README; `tools/fetch-edg.sh` first if `third_party/edgcpp` is empty). After a change to the EDG pin or the build, reconfigure with `cmake -S . -B build` first, or `--version` keeps reporting the old commit. chen and atom run it with `--c-frontend edg --edga-path ~/work/AppThreat/edga/build/bin/edga`. A stale edga build makes edg2atom tests fail for reasons that have nothing to do with the change; check `edga --version` before blaming the code.
- **Corpus:** the memory-safety corpus at `~/sandbox/memsafe-corpus`. Read its `README.md` before the first run. `tools/run_gates.sh` runs every gate at `medium` and `low` (`GATES` and `LEVELS` choose a subset, `OUT=out/gates-<label>` names the output). The baseline is `out/gates-p02-final`.
- **Working folder:** `~/work/cpp-frontend-contexts`. `refs/` holds the probes the plan's "Why" section came from: `templates-probe.cpp` with its edga 0.1.1 output `templates-probe.edga.json`, and `non-self-contained/` (a unit and a header that uses the unit's typedef). Read them, do not change them. Write the plan file and the report there under `reports/`, and nothing else.
- **Plan:** the prompt names the deliverables. The plan section is the design and its "Done when" paragraph is the acceptance test. If the prompt and the plan disagree, the prompt wins; say so in the report.
- **Writing and credit rules:** `~/.agents/AGENTS.md`. The commit-msg hook enforces them.

## Git

1. Before starting, run `git fetch origin` in each repository and check that the working tree is clean. If the task branch already exists, inspect it with `git status` and `git log` and continue it; do not start over.
2. Create the task branch `cfc/frontend-contexts` from `origin/main` in edga, chen and atom.
3. Commit in small, reviewable steps. Each commit compiles.
4. **Never push, never create or delete remote branches, never open pull requests, never comment on GitHub, never create releases or tags.** Developer branches and worktrees (see "Work as a workflow") are local only.
5. **Never rewrite `main`, never `git reset --hard` a branch you did not create in this prompt, and never run `git stash`.**

## Commit messages, code comments and docs

- **Subject:** a plain sentence in the repository's style, for example "Link template instances to the template they came from". No conventional-commit prefixes in chen or atom; follow edga's history for edga.
- **Body:** what changed and why, in short paragraphs.
- **No process references** anywhere in commits, code, comments, test names or docs: no deliverable or prompt numbers (D3, P01), no plan file names, no corpus or arm names, no `~/sandbox`, `~/work` or `/Users` paths, no agent or model names, and no mention of the language server whose write-up motivated the plan. Issue numbers belong in the pull request, which the reviewer writes. Fixtures describe the C or C++ construct they exercise.
- **Style:** no first person, no em-dashes, no emojis, no words from `~/.agents/credits/jargon.txt`.
- **Code comments** explain the code as it is now, for a reader who has never seen this plan.

## How to work

- **Iterate fast.** Write the fixture for the case first, then run the single test suite that covers it with a timeout, for example `sbt "c2cpg/testOnly io.appthreat.c2cpg.parser.CompileCommandTests"` or `sbt "edg2atom/testOnly io.appthreat.edg2atom.astcreation.CppShapesTests"` in chen, or `python3 tests/run.py --edga build/bin/edga` in edga. Run atom on one fixture directory, not on a whole project, while developing; in a workflow only the lead does that, because it needs `publishLocal`. Do not run benchmarks and do not time anything.
- **Both front ends.** Every deliverable that names c2cpg and edg2atom is checked with both, and the report gives both results side by side.
- **Correct code first.** For every new behaviour, write the correct look-alike before the change: a template used once, a header that is self-contained, a database with no duplicates, a known compiler. A change that alters the graph of correct, ordinary code is a failure unless the deliverable asks for it.
- **AST format versions.** A change to what a front end writes moves its AST format version (`AstFormatVersion` in c2cpg's `AstCreationPass`, and the matching key in edg2atom). Developers do not edit those lines; the lead moves each once per batch when merging. Check that a warm run gives the same graph as a cold one.
- **End to end.** Every change that atom prints gets a test in atom that runs the command and reads the output, not only a tag assertion in chen.
- **chen and atom together.** To test atom against chen, run `sbt publishLocal` in chen (keep its version unchanged), then `sbt stage` in atom, then atom's tests. Grep the `publishLocal` output for `[error]`: a failed build can still exit quietly. Check that the staged jar in `target/universal/stage/lib/` has the date of your publish. Say in the report which chen and edga commits atom was tested against.
- **One sbt command per call.** sbt 2's client joins all arguments of one `sbt -batch` call into a single command line, so `sbt -batch "a/test" "b/publishLocal"` runs only the first. Run each command in its own call and check the output says it ran. A hung sbt test worker blocks the server; find and kill the worker process, not the shell.
- **Formatting.** Run `sbt scalafmtAll` in chen and atom, and edga's formatter if its repository defines one, as the last commit, only on files you changed.
- **Gates at checkpoints and at the end.** The checkpoint gate is `LEVELS=medium GATES="corpus corpus-edg projects" tools/run_gates.sh`, because it takes minutes. The full `tools/run_gates.sh` runs once, on the final head. Report exit codes and summary lines. Never hide a failure behind `| tail` or `|| true`.
- **Every new finding on a real arm is read by hand.** For each finding a change adds on any arm or project, open the source and decide whether it is a real defect. List each one in the report with the decision and a one-line reason.
- **Stay in scope.** Do not reformat files you do not otherwise change, rename unrelated things, or add a dependency.
- **Tests check behaviour.** Do not record your own output as the expected value unless you checked every field by hand; list any such test, and every regenerated edga golden, under "Recorded expectations". Fixtures contain no local paths, usernames or hostnames.
- **No silent clean results.** A front-end failure, a timeout or a skipped file is reported with its reason, never as an empty result.

## Work as a workflow

Run the prompt as a zcode workflow. You, the GLM-5.3 lead, read, plan, decide, merge and run the shared steps. Every piece of code is written by a developer subagent and checked by a separate reviewer subagent, both on GLM-5.3-Flash. The reviewer on the other side should receive work that has already been through that loop.

**Use the "skill: dynamic workflow" skill.** Load zcode's bundled `dynamic-workflows` skill (listed as "skill: dynamic workflow") before anything else, and run the developers and reviewers through scripts submitted with its `CreateWorkflow` tool. Do not use the `Agent` tool, the legacy `Workflow` tool or `/expert` for the pieces. Pass `subagent_model: "GLM-5.3-Flash"` (or `agent(name, { model: "GLM-5.3-Flash" })` per subagent). Follow the skill's rules: one named developer per piece and one named reviewer per piece, typed results, `world.run` for the checks a command decides (the piece's `sbt testOnly` suite, edga's golden run), and holes where a later phase depends on what an earlier one finds. The prompt runs as several workflows, one per batch, so the lead can merge and check between them. If `CreateWorkflow` refuses or is not available, stop and put that under "Questions" instead of falling back to `Agent`.

**Developer and reviewer are different agents.** A developer never reviews its own piece, and a reviewer never sees the developer's summary, only the diff, the plan file's decisions for the piece and the checklist below. When the reviewer finds a problem, the same developer fixes it and the same reviewer checks the fix. If a piece still fails review after two rounds, the lead may run its developer on GLM-5.3 instead, and records that under "Workflow" in the report; the reviewer stays on Flash.

**The lead keeps the judgment.** Before starting any developer, read the prompt, the plan's deliverables and the code the prompt names, and write the split into `~/work/cpp-frontend-contexts/reports/P01-plan.md`: each piece, the files it owns, the decisions it must follow, its fixtures and correct look-alikes, and the test that shows it is done. Settle every decision the prompt leaves open yourself, in that file, before a developer sees it. Developers implement decisions; they do not make them. Quote the decisions that matter most word for word in every developer's brief, in particular "correct code first", "GCC, Clang and MSVC behave exactly as today" and "without the option the graph is exactly today's".

**Pieces follow file ownership.** Each developer gets its own git worktree of the repository it changes on a local branch cut from the task branch (`cfc/frontend-contexts-<piece>`), and owns the files listed for it; two developers never edit the same file. A developer commits on its own branch and runs only its piece's tests, in its own worktree. Run at most three sbt-heavy developers at a time: each sbt server takes several GB.

**Shared state belongs to the lead.** Only the lead touches `~/.ivy2/local` (`sbt publishLocal`) and therefore atom's `sbt stage` and every atom test that needs new chen code; the edga binary at `~/work/AppThreat/edga/build/bin/edga` that chen and atom use; the corpus at `~/sandbox/memsafe-corpus`; and the gates. A developer that needs an atom end-to-end test or an edg2atom test against a new edga writes it; the lead builds what it needs and runs it after merging.

**Review before merging.** The reviewer of each piece works through this checklist:

- Does the code do what each decision says, including the edge cases the decision names?
- Is every new behaviour backed by a correct look-alike that a wrong implementation would fail?
- Does every new test fail on the code before the change? The reviewer checks this by running the test against the parent commit.
- Does correct, ordinary code keep exactly its old graph where the deliverable says so? Is there a test that shows it?
- Does any test record the author's own output as the expected value without the fields being checked by hand?
- Do comments, commit messages and test names follow the writing rules above (no process references, no first person)?
- Is every claim in the piece's notes true? Look for the test or command it names.

The developer fixes what the reviewer finds; if they disagree, the lead decides and records it under "Decisions".

**The lead finishes.** The lead merges the pieces into the task branch and resolves anything between them, moves the AST format versions, then runs the checkpoint steps the prompt names. Before writing the report, the lead runs one more fresh Flash reviewer over each repository's whole branch diff against `origin/main` with the same checklist, and fixes what it finds. The lead reads every finding the change adds on the arms and projects, writes the report, and checks every sentence in it; a developer's claim goes in only after the lead has seen the evidence. Delete the developers' worktrees and their branches when the pieces are merged.

## When something is unclear

If a decision is needed that the plan does not make, choose the option that commits to the least and is easiest to change later, implement it, and record the decision and the alternatives under "Decisions". If the decision would rename an existing METHOD or tag at default options, change edga's document version, add or rename a command-line option beyond those the plan names, or change the format of an existing atom output, stop that part and put it under "Questions".

## The report

Write the report with these sections:

1. **Branches:** each branch with its head SHA and base SHA, per repository.
2. **Commits:** one line each.
3. **Done when:** one subsection per deliverable, each condition with whether it is met and the exact command and output lines that show it.
4. **Gates:** every gate at `medium` and `low`, baseline next to result, for each front end.
5. **Graph size:** node and METHOD counts on leveldb and abseil-cpp, baseline and result, per front end.
6. **Arm findings read by hand:** each added finding, its decision and the reason.
7. **Not done:** each part not done, with the reason.
8. **Decisions** and 9. **Questions.**
10. **Recorded expectations.**
11. **Workflow:** the workflow run names and the script files under `.zcode/workflow-drafts/`, the model each subagent ran on, the pieces, the developer and reviewer of each, what each review found and what was fixed.
12. **Outcome:** one table per gate with the baseline, the result and the difference, ready to paste into the plan's Outcome section.

Be exact. "All tests pass" needs the command and the count. If you did not run something, say so.
