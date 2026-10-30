# callsites: gotchas, blockers and decisions

Cross-cutting risks for every plan in the [callsites overview](callsites-overview.md). Each item
says what can go wrong, how we will notice, and what we do about it. Items marked **decision** need a
maintainer before the work they block.

## Blockers

| # | blocker | blocks | mitigation |
| --- | --- | --- | --- |
| B1 | Ground truth for multi-module Java and for C/C++ needs the projects' own builds (`mvn install`, `cmake` configure). Sandboxed agent runs may not be allowed to run third-party build scripts. | ground-truth D4, jvm D1 gates on mall/shiro, c-cpp gates | Run those builds once, by a person or in a disposable container, and keep the classpath and `compile_commands.json` with the corpus manifest. Until then, files the compiler cannot attribute are excluded from scoring. |
| B2 | cdxgen adopts atom v4 (Scala 3.10, chen 4) at the end of 2026. | consumers D1–D5 | Land cdxgen changes on the branch that tracks atom v4; **decision**: which branch. |
| B3 | New graph nodes (Ruby constant references, PHP attributes and constants, possibly C macro uses) may need cpg2 schema changes, which release in order: overflowdb2 → cpg2 → chen → atom → cdxgen. A schema change also invalidates saved atoms and AST caches. | ruby D1, php D2, c-cpp | Prefer existing node kinds and properties (`TYPE_REF`, `ANNOTATION`, `FIELD_IDENTIFIER`, tags). If a schema change is unavoidable, batch all of them into one cpg2 release early in sprint 3. |
| B4 | EDG is proprietary: `edga` comes as a binary from `ghcr.io/appthreat/edga`, its tests cancel in CI without it, and the macOS build defines different predefined macros than Linux. | c-cpp EDG deliverables | Run EDG gates locally with `EDGA_PATH` and in the Linux containers; never accept "cancelled" as passing. |
| B5 | The board is on GitHub Free: one auto-add workflow (for atom), so issues in chen, edga, atom-parsetools, cdxgen and dep-scan are added by the backfill or by hand; sub-issues across organizations may not link. | tracking | Keep cdxgen and dep-scan tasks linked from the consumers epic body if they cannot be sub-issues. |

## Gotchas

1. **Shared checkouts.** Other agents work in the main chen and atom checkouts. Every change happens
   in a `git worktree`; chen is published locally under a distinct version (`4.0.0-csN`), never
   `4.0.0`. After `sbt stage`, check that the atom stage holds the new chen jars (stale jars have
   measured the wrong branch before).
2. **sbt 2.** `test` is incremental and skips unchanged suites: use `<project>/testFull` or
   `testOnly`. chen needs `GITHUB_TOKEN`. The sbt server keeps the environment it started with
   (`EDGA_PATH`).
3. **Determinism.** Streaming AST passes commit nodes in completion order, so node ids vary between
   runs. Never order output, iterate fixpoints or break ties by node id.
4. **Tagging rule versus speed.** Skipping re-tagging is only allowed when the tags are provably the
   same (performance D2). A tag-state marker that misses one input serves stale tags silently.
5. **Oracles are tools too.** Each has limits (typed uses, parser versions: Python 3.15's `ast`
   cannot read Python 2; the PHP and Ruby parsers have their own grammar versions; javac rejects
   preview features without flags). A slice "false positive" is triaged by reading the code before
   anything is changed.
6. **Benchmark gaming.** Agents tune to whatever is measured. Gates are repository tests; reviews
   grep for corpus names, package names and method names in rules, and for source-text regexes.
7. **Package mapping is ambiguous in every ecosystem.** Python import names vs distributions;
   Java split packages (`javax.servlet` from tomcat-embed), shaded and relocated classes; Android
   apps have no package boundary and R8 renames classes; Kotlin inline functions disappear from
   bytecode; C headers map to packages only through install prefixes, and vendored copies
   (`third_party/`) are project code by path but dependencies by meaning; PHP polyfills duplicate
   builtins; Ruby gems define constants dynamically and apps reopen gem classes.
8. **Typed truth depends on installed dependencies.** Installing `node_modules` or a venv changes
   what atom itself sees (types), so a baseline and a branch must run on the same tree state.
9. **Resources.** PHP projects with `vendor/` need 11–13 GB per atom process; large JS projects 8–9
   GB. Run at most two lanes on a 48 GB machine. Saved atoms, `node_modules` and gem caches need
   disk; clean them after each sprint run.
10. **astgen type generation can stall** on large, branchy JS files (40+ minutes on cdxgen's
    repository). Corpus lanes need a timeout and a `--ts-types false` fallback, and cdxgen's own
    20-minute budget is at risk on such projects.
11. **Agent reports are claims.** Reproduce every number on the branch head, diff every record
    added and removed, and attribute each to a commit before a pull request.
12. **Frontends drop files silently.** Every frontend exits 0 and logs nothing when a file does not
    parse (astgen on a TC39 `accessor` field loses the whole file). Until the language-versions plan
    D1 lands, compare the atom's file list with the input before trusting a low recall.
13. **Nodes without an enclosing method exist in every frontend we checked**: JS identifiers from
    destructured arrow parameters (7,296 in outline), calls in PHP property-hook bodies. Slice code
    must never assume `.method`.
14. **The C ignore pattern** `.*(docs|example|samples|mocks|Documentation|demos).*` can drop an
    entire input (`openssl/demos`) without a warning; corpus directories named like that look empty.
15. **Android and bytecode specifics.** `--android-sdk` takes the `android.jar` file; large APKs need
    12+ GB and write slices of hundreds of MB; R8 can make line tables synthetic, so line-level
    comparison degrades to file level.
16. **Concurrent harness edits.** Several agents extending `score.py` at once can break each other's
    languages; rescore every language after a scorer change.
17. **Plans are public.** Corpus manifests list projects by URL, commit and digest; vendor or
    proprietary inputs (some APKs) are never committed, and recorded outputs that quote third-party
    code stay out of public repositories.

## Decisions

Decided on 2026-10-30, recorded in [decisions/0001-callsites-what-counts.md](decisions/0001-callsites-what-counts.md):

| # | question | decision |
| --- | --- | --- |
| P1 | What counts as a use: declaration types, TypeScript `implements`, C macros, generated code. | All of them, each with its own `kind`; all scored. Import lines are not uses on their own; tests stay out of scope by default. |
| P2 | Attribution of a typed call: the receiver's static type or the declaring class. | The receiver's static type; the declaring class is kept as `declaringModule`. |
| P3 | Standard libraries in the slice and in cdxgen occurrences. | Yes, both, flagged `builtin`; scored by default. |
| P4 | Where the harness lives. | Not published; the manifest and the test fixtures are. |
| P5 | Vendored third-party code. | External wherever recognisable, plus a path-regex option on every frontend (C/C++ first). |
