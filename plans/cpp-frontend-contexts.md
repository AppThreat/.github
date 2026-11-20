# C and C++ front ends: template identity, toolchains and build contexts

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/chen/issues/335 |
| Owner | @prabhu |
| AI use | Auto: an implementation agent writes each deliverable from the prompts in [prompts/cpp-frontend-contexts](prompts/cpp-frontend-contexts/00-RULES.md), a reviewing agent verifies, refactors and opens the pull requests, a maintainer approves |
| Schedule | After the C memory safety across allocation styles plan ([AppThreat/chen#328](https://github.com/AppThreat/chen/issues/328)), released in chen 4.0.2, atom 4.0.3 and edga 0.3.0 |
| Corpus | Fixtures added by D1; the gates reuse the memory-safety corpus and its `tools/run_gates.sh` |

## Why

[clice](https://github.com/clice-io/clice) is a C and C++ language server built on Clang. Its author's [v1.0 write-up](https://ykiko.me/en/articles/2105384023094834022/) lists the design choices that set it apart from clangd. Four of them carry over to a static analyser that builds code property graphs, because they are about how faithfully a front end sees the program the build compiles, not about editors:

1. A template is treated as an interface and each instantiation as one implementation, so a question asked at a line of template code is answered across every instantiation.
2. The compile command is reconciled with the real compiler for more than 50 toolchains, instead of assuming GCC or Clang.
3. The compilation context is explicit: a source file compiled by several commands, and a header included from several places, are each seen in a chosen context, and the context is visible.
4. The compiler runs in worker processes, so a crash or a runaway parse costs one file, not the session.

chen, edga and atom already do several things clice does. chen asks the real compiler for its predefined macros and system include directories and caches the answer on disk, rewrites C++20 module syntax for CDT, and decides which unit each header belongs to; edga runs once per translation unit with a timeout; both front ends keep a persistent AST cache. A review at chen 47e74f13, atom a504584 and edga 04481ad1 found five gaps, and all five are still present at chen 21c7857c (4.0.2), atom b3f3a75 (4.0.3) and edga ec70847b (0.3.0). The allocation-styles work added `IncludeRecordPass`, which tags each unit's FILE node with the headers it includes, and memory API profiles selected by those includes; both make the build context a file was analysed in matter more, since a header owned by a different unit can select different profiles.

**Templates in edga.** A probe with one class template, one function template used with two types and one function template that nothing instantiates gave three routines for the used templates and none for the unused one. The two instances of `twice<T>` are exported with the same `name`, the same `qualifiedName` and the same position; only their `type` ids differ, and nothing links either to the template it came from. In header-only code, a template the analysed units never instantiate has no body in the graph at all. EDG has what is needed: every entity generated from a template records its template arguments, and with `PROTOTYPE_INSTANTIATIONS_IN_IL` (already 1 in edga's configuration) the front end builds a *prototype instantiation*, the template's own body with its dependent types, which edga skips on purpose (`is_prototype_instantiation` in `src/edga_back_end.cpp`). That prototype is what clice approximates with its pseudo-instantiator, except that here the real front end produces it.

**The two front ends model templates differently.** c2cpg writes one METHOD per template (the generic definition) and tags each call with the signature of the instance it uses (`template-instance`, defined in `x2cpg/Defines.scala`). edg2atom writes one METHOD per instance and nothing for the template. A query or a finding at a template line therefore means different things depending on `--c-frontend`.

**Compiler identity.** `CompileCommands.familyOf` recognises MSVC, Clang and GCC by the driver's name. `nvcc`, Intel `icx` and `icpx`, `emcc`, `zig cc`, `tcc`, IAR `iccarm` and the TI compilers (`armcl`, `cl430`, `cl2000`) all come back as `Unknown`, so the unit is preprocessed with macros that are not the build's.

**Build contexts are silent.** When `compile_commands.json` lists the same file twice (for example once with `-DUSE_OPENSSL` and once with `-DUSE_MBEDTLS`), the first entry wins (`CompileDatabase.byFile`) and nothing says so. Each header belongs to the first unit, in path order, that includes it. The CDT front end parses that header as a unit of its own with its owner's flags but not with the code before the `#include`, so a header that depends on its includer (an X-macro `.def` or `.inc` file, a header that uses a typedef the includer declared first) may lose types. Which build context a FILE node was analysed in is not recorded anywhere a user can see it.

**CDT runs in the analyser's JVM.** `AstCreationPass` gives each parse a thread with a timeout and catches `Throwable`. That survives an exception, but not an out-of-memory error or a CDT loop that ignores interruption, both of which have been seen on large trees. edga already gets process isolation; the default front end does not.

## Scope

In scope: edga's export of templates; c2cpg and edg2atom, their compile-command handling and their AST passes; atom's C and C++ options, its `--parse-report` output and the commands that print findings and slices for C and C++.

Out of scope:

- Editor features and the language-server protocol.
- Building C++20 modules into binary module interfaces. chen's textual rewrite stays.
- A CUDA, HIP or SYCL language mode. D6 makes those units preprocess with the right macros; parsing device code is separate work.
- Changing which front end is the default.

## Approach

The two front ends converge on one template model, so that atom and the memory-safety passes need no front-end checks:

- An instance METHOD carries a `template` tag whose value is the full name of its template's METHOD, and a `template-args` tag with the arguments as written by the front end.
- A template METHOD (c2cpg's generic definition; edg2atom's prototype instantiation) carries a `template-pattern` tag.
- A call written in template code whose callee depends on a template parameter keeps today's `METHOD_FULL_NAME` and lists the callees it reaches across the instances in the unit in `DYNAMIC_TYPE_HINT_FULL_NAME`, the field chen's Java front end already uses for more than one possible callee.

edg2atom keeps one METHOD per instance, because each instance has its own types and its own data flow. c2cpg keeps its one generic METHOD, because CDT does not give instance bodies. atom groups by the `template` tag when it prints, so a finding or a slice entry at a template line appears once and lists the instantiations.

Build contexts become data instead of a silent choice. Every FILE node records the context it was analysed in; the parse report prints the settings each unit was given; duplicates in the compilation database are reported; and an opt-in mode analyses every distinct context. The CDT front end takes a header that is not self-contained from its owner's parse, as edg2atom already does.

Compiler identity moves from code to a table with provenance, next to the fallback macro tables `PredefinedMacros` already reads and generates with `tools/predefined-macros/generate.sh`.

CDT isolation reuses the AST cache. A worker JVM writes the same `.ast` fragments `AstCacheStore` writes today, and the parent reads them as it reads a warm cache, so isolation adds a process boundary and no new serialisation format.

## Prompts

The work runs as one prompt, [P01-frontend-contexts.md](prompts/cpp-frontend-contexts/P01-frontend-contexts.md), run as a workflow of developer and reviewer subagents under one lead (see [00-RULES.md](prompts/cpp-frontend-contexts/00-RULES.md)). It ends in one pull request per repository, from `cfc/frontend-contexts` to `main` in edga, chen and atom. edga merges first, because chen's and atom's CI test against the edga that `main` publishes.

## Gates

The baseline is the memory-safety corpus run `out/gates-p02-final` in `~/sandbox/memsafe-corpus`, taken on the code that is now `main` (chen 4.0.2, atom 4.0.3, edga 0.3.0). The lead confirms it at the start (D1). On the final head, `tools/run_gates.sh` runs every gate at `medium` and `low`:

- `corpus` and `corpus-edg`: the hand-written C and C++ arms with c2cpg and with edg2atom. Recall and precision no lower than the baseline, and no finding on a `@nofinding` line.
- `projects`: leveldb and abseil-cpp. Findings per tree at `medium` no higher than the baseline.
- `arms`: the C precision arms (SQLite, Redis, nginx, pgvector, QEMU, Linux, CPython, Lua). Findings at `medium` no higher than the baseline unless every added finding has been read by hand and is a real defect, listed in the pull request.
- `cve`: the FFmpeg libavformat arm. No fewer CVE sites than the baseline, and no finding at the fixed-commit sites.

Also on the final head: edga's golden tests with the schema check on every platform its CI covers, chen's `c2cpg` and `edg2atom` suites, atom's tests, the D1 fixtures with both front ends, and, for every change that moves an AST format version, a warm run that gives the same graph as a cold one.

## Deliverables

### D1. Fixtures and baseline

Fixtures, each a small project with expectations in a form the tests read, written by the piece that needs them and before its code change:

- **Templates:** a class template with members used with two argument types; a function template used with two types; a function template and a class template member that nothing instantiates; a dependent call (`x.get()` on a parameter of type `T`) whose callee differs per instance; a partial and an explicit specialisation; a variadic template; a lambda with an `auto` parameter passed to a standard algorithm; a template defined in a project header and used from two units; and two seeded memory-safety bugs, one that every instantiation has (a null dereference) and one that only one has (an index that depends on `sizeof(T)`).
- **Toolchains:** compilation databases whose drivers are `nvcc`, `icx`, `icpx`, `emcc`, `em++`, `zig cc`, `zig c++`, `tcc`, `armclang`, `iccarm`, `armcl`, `cl430`, `clang --driver-mode=cl`, a GCC cross compiler (`arm-none-eabi-gcc`) and a compiler behind `ccache`, each with one source file that `#error`s unless that compiler's identifying macros are defined. The compilers need not be installed.
- **Contexts:** a file listed twice in the compilation database with different `-D` options that select different code; a header included by two units with different macros; a header that uses a typedef its includer declared before the `#include`; an X-macro `.def` file included inside an `enum` and inside a `switch`; and a database that compiles the same file for two targets.

The baseline is confirmed before any change: `LEVELS=medium GATES="corpus corpus-edg projects" tools/run_gates.sh` on `main` must reproduce `out/gates-p02-final` exactly. If it does not, the whole baseline is run again on `main` and used instead. Node and METHOD counts of the leveldb and abseil-cpp graphs from each front end are recorded with it.

Done when every fixture is in chen (and in edga where it is a single unit), its tests fail on `main` for the reason the fixture exists, and the baseline is recorded.

### D2. Templates, one model from edga to atom

**edga, identity.** Each routine, class, struct, union and variable generated from a template gets a `template` object (an id shared by every instance of one template in the unit, taken from the template's IL entry; the template's name and qualified name; the position of its declaration) and `templateArgs` (the arguments in order, with a type id for a type argument, the value as the front end prints it for a non-type argument, and the qualified name for a template template argument). Explicit specialisations are instances of their primary template, flagged as explicit.

**edga, prototype bodies.** Each function template, and each member function of a class template, that is defined under `--edga-root` and has no real instance in the unit is exported as its prototype instantiation: a routine with `prototype: true`, its `template` object and its body. Types that depend on a template parameter get a `dependent` kind naming the parameter; a call whose callee depends on a parameter is an unresolved call with the name as written. `--edga-no-prototypes` turns this off. EDG defers prototype instantiation of function templates in GNU mode (`--defer_parse_function_templates`, the default when `gnu_version` is at least 30400), so edga turns deferral off and records, as diagnostics, any errors this exposes in unusable templates, without failing the unit. The document stays `edga/1`: the fields are additions described in `docs/json-format.md` and `schema/edga-1.schema.json`.

**chen.** edg2atom tags each instance METHOD `template` (the full name of its template's METHOD) and `template-args`, and each prototype METHOD `template-pattern`; `DuplicateDefinitionPass` keeps one copy of a prototype across units, as it does for instances. c2cpg tags the METHOD of each template definition `template-pattern` and writes `template-args` on calls to an instance (the existing `template-instance` tag keeps its value). In both front ends a call whose callee depends on a template parameter lists, in `DYNAMIC_TYPE_HINT_FULL_NAME`, the METHODs it reaches in the unit's instances.

**atom.** `memory-safety` findings and the usages and reachables slice entries whose METHODs share a `template` tag and a position are printed once, with an `instances` list naming each instance's `template-args`; a finding present in only some instances lists only those. The field is added; nothing is removed or renamed.

Done when the two instances of `twice<T>` in the probe share a `template` id and differ by `templateArgs`; the unused templates in the probe and the fixture have routines with bodies and a template with real instances gets no prototype; every existing edga golden keeps its exit status, with each regenerated golden checked by hand; both front ends give the tags and the dependent call's callee list for the fixture; the bug every instantiation has is printed once with both instantiations and the other lists one, under each front end, in an atom end-to-end test; and a warm run matches a cold run.

### D3. Compiler identity and the settings each unit was given

**Table.** Compiler identity comes from a table in c2cpg's resources instead of code. Each entry names the driver (a name or a pattern, with wrappers such as `ccache` and two-word drivers such as `zig cc`), the family, whether it compiles every file as C++, how to ask it for its macros and include directories when it can be run (for example `nvcc -E -Xcompiler -dM` and the host compiler named by `-ccbin`), the fallback macro table when it cannot, and how its dialect options map to CDT and EDG settings. `familyOf`, `isCppDriver`, `PredefinedMacros` and edg2atom's `EdgaRunner` read the table. New fallback tables sit next to the existing ones in `resources/predefined-macros`; they are generated with `platform/frontends/c2cpg/tools/predefined-macros/generate.sh` where the compiler can be installed, and otherwise taken from the vendor's documentation, with the source cited in the table. For `nvcc`, a `.cu` unit is preprocessed as C++ with the host compiler's macros plus nvcc's own; device code is not parsed. GCC, Clang and MSVC behave exactly as today.

**Settings.** atom's `--parse-report` gains a `units` section: per translation unit, the front end, the driver, the table entry chosen, where the macros came from (`probed`, `table`, `host` or `unknown`), the language and standard, a fingerprint of the macros, the include directories in search order, forced includes, the headers the unit owns, and for edg2atom the exact edga command line. A driver the table does not know is recorded there instead of being treated silently as the host compiler. The existing failure records keep their format, and nothing is collected when `--parse-report` is not given.

Done when every toolchain fixture preprocesses without reaching its `#error` with both front ends, a test reads the entry chosen and the macro source for each, an unknown driver produces a record, `CompileCommandTests`, `PredefinedMacrosTests` and `ParseReportTests` pass unchanged, and the gates' graphs for GCC and Clang projects are identical to the baseline.

### D4. Build contexts

**Context on every file.** Every FILE node from either front end carries a `build-context` tag: for a unit, a fingerprint of its compile command after the options that do not change the program are removed (the list `CompileCommands` already keeps); for a header, the owner unit's relative path and that fingerprint. Duplicate entries for one file in a compilation database are reported in the parse report's `units` section with every command and the one used. The tag rides the AST cache like the `includes` tags `IncludeRecordPass` writes.

**Headers that are not self-contained (c2cpg).** c2cpg parses each header as its own unit with its owner's flags. A header that cannot be parsed that way (no include guard and included somewhere other than file scope, or names left unresolved that the owner declares before its `#include`) is instead taken from the owner unit's parse, with its own file and line numbers, the way edg2atom writes headers as part of their owner. Detection uses the parse that already happens. A header that parses on its own keeps exactly today's graph.

**Every context, opt-in.** atom gains `--c-build-contexts <first|all>`, `first` by default. With `all`, a file that the database compiles with more than one distinct context is analysed once per context. A function whose body is the same in every context is kept once, as `DuplicateDefinitionPass` keeps template instances; a function whose body differs is kept once per context, the first context's copy keeping today's full name and each other copy's full name gaining `@ctx:<first 8 hex digits of the context fingerprint>`, with a `build-context` tag on the METHOD. Calls inside a context resolve to that context's copy.

Done when the context fixtures show the right tag on each FILE, warm and cold; the duplicated file is reported with both commands; the typedef and X-macro fixtures give the same types and members from c2cpg as from edg2atom; no leveldb or abseil-cpp header that parses on its own changes; with `all` the duplicated-file fixture yields both variants, an unchanged function is present once and calls resolve inside their context; and without the option the graph is exactly today's.

### D5. CDT workers

c2cpg gains an opt-in worker mode (`--c-isolate` in atom, with a matching chen option). The parent starts a small pool of long-lived worker JVMs that parse units and write their AST fragments to the AST cache directory, and loads them through `AstCacheStore` as it loads a warm cache, so the process boundary adds no serialisation format. A worker reads its configuration from a file or standard input, has its own heap size, and is replaced when it exits, runs out of memory or exceeds the parse timeout; the unit it held is recorded in the parse report with the reason and retried once in a fresh worker. Without the option nothing changes.

Done when a test that makes a worker exit, loop without checking for interruption, or run out of memory on one named file (through a test-only system property) still produces the graph for every other file, a report record for that one and exactly one retry; and the graph from worker mode equals the graph from today's mode, FILE by FILE, on the fixtures and on leveldb.

### D6. Documentation and final measurement

edga's JSON format reference and how-it-works document, chen's C and C++ front-end documentation and atom's documentation describe the template tags and grouping, the toolchain table with a worked example of adding an entry, the parse report's `units` section, the `build-context` tag, `--c-build-contexts`, `--c-isolate` and `--edga-no-prototypes`. The Outcome section of this plan records every gate against the baseline.

Done when every sentence of the new documentation has been checked against the code and the Outcome table is filled in.

## Risks and open questions

- **Prototype instantiation errors.** Turning off deferral makes EDG check every function template body even where the code relies on deferral (templates that can never be instantiated with any argument). D2 keeps the unit's export and records the errors; if a real project gains errors that change the exported real code, edga keeps deferral on in GNU mode and exports prototypes only where the front end built them anyway, and the pull request says how many templates that loses on abseil-cpp.
- **Graph growth.** Prototype METHODs and per-context copies add nodes. Each pull request reports node and method counts on leveldb and abseil-cpp before and after; a growth above 20 percent at default options needs a maintainer's approval.
- **Name stability.** The `@ctx:` suffix in D4 changes full names only under the opt-in option, and D2's tags add data without renaming anything. Any change that would rename an existing METHOD at default options is a question for the maintainer, not a decision for the implementation.
- **Vendor macro tables.** Some toolchains (IAR, TI) cannot be installed in CI. Their tables come from documentation and may be incomplete; the table records that, and the parse report says `table` so a user can see where the macros came from.
- **Worker overhead.** JVM start-up costs seconds per worker; the pool is long-lived to pay it once. The mode stays opt-in.

## Outcome

Filled in when the work ends.
