# C and C++ front ends: template identity, toolchains and build contexts

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/chen/issues/335 |
| Owner | @prabhu |
| AI use | Auto: an implementation agent writes each deliverable from the prompts in [prompts/cpp-frontend-contexts](prompts/cpp-frontend-contexts/00-RULES.md), a reviewing agent verifies, refactors and opens the pull requests, a maintainer approves |
| Schedule | After the C memory safety across allocation styles plan ([AppThreat/chen#328](https://github.com/AppThreat/chen/issues/328), plan in [AppThreat/.github#40](https://github.com/AppThreat/.github/pull/40)) is merged |
| Corpus | Fixtures added by D1; real-code arms reuse leveldb and abseil-cpp from the memory-safety corpus |

## Why

[clice](https://github.com/clice-io/clice) is a C and C++ language server built on Clang. Its author's [v1.0 write-up](https://ykiko.me/en/articles/2105384023094834022/) lists the design choices that set it apart from clangd. Four of them carry over to a static analyser that builds code property graphs, because they are about how faithfully a front end sees the program the build compiles, not about editors:

1. A template is treated as an interface and each instantiation as one implementation, so a question asked at a line of template code is answered across every instantiation.
2. The compile command is reconciled with the real compiler for more than 50 toolchains, instead of assuming GCC or Clang.
3. The compilation context is explicit: a source file compiled by several commands, and a header included from several places, are each seen in a chosen context, and the context is visible.
4. The compiler runs in worker processes, so a crash or a runaway parse costs one file, not the session.

chen, edga and atom already do several things clice does. chen asks the real compiler for its predefined macros and system include directories and caches the answer on disk, rewrites C++20 module syntax for CDT, and decides which unit each header belongs to; edga runs once per translation unit with a timeout; both front ends keep a persistent AST cache. A review at chen 47e74f13, atom a504584 and edga 04481ad1 found five gaps.

**Templates in edga.** A probe with one class template, one function template used with two types and one function template that nothing instantiates gave three routines for the used templates and none for the unused one. The two instances of `twice<T>` are exported with the same `name`, the same `qualifiedName` and the same position; only their `type` ids differ, and nothing links either to the template it came from. In header-only code, a template the analysed units never instantiate has no body in the graph at all. EDG has what is needed: every entity generated from a template records its template arguments, and with `PROTOTYPE_INSTANTIATIONS_IN_IL` (already 1 in edga's configuration) the front end builds a *prototype instantiation*, the template's own body with its dependent types, which edga skips on purpose (`is_prototype_instantiation` in `src/edga_back_end.cpp`). That prototype is what clice approximates with its pseudo-instantiator, except that here the real front end produces it.

**The two front ends model templates differently.** c2cpg writes one METHOD per template (the generic definition) and tags each call with the signature of the instance it uses (`template-instance`, defined in `x2cpg/Defines.scala`). edg2atom writes one METHOD per instance and nothing for the template. A query or a finding at a template line therefore means different things depending on `--c-frontend`.

**Compiler identity.** `CompileCommands.familyOf` recognises MSVC, Clang and GCC by the driver's name. `nvcc`, Intel `icx` and `icpx`, `emcc`, `zig cc`, `tcc`, IAR `iccarm` and the TI compilers (`armcl`, `cl430`, `cl2000`) all come back as `Unknown`, so the unit is preprocessed with macros that are not the build's.

**Build contexts are silent.** When `compile_commands.json` lists the same file twice (for example once with `-DUSE_OPENSSL` and once with `-DUSE_MBEDTLS`), the first entry wins (`CompileDatabase.byFile`) and nothing says so. Each header belongs to the first unit, in path order, that includes it. In the CDT front end that header is parsed separately with its owner's flags but not with the code before the `#include`, so a header that depends on its includer (an X-macro `.def` or `.inc` file, a header that uses a typedef the includer declared first) may lose types. Which build context a FILE node was analysed in is not recorded anywhere a user can see it.

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

Compiler identity moves from code to a table with provenance, in the format `PredefinedMacros` already reads for its fallback macro tables.

CDT isolation reuses the AST cache. A worker JVM writes the same `.ast` fragments `AstCacheStore` writes today, and the parent reads them as it reads a warm cache, so isolation adds a process boundary and no new serialisation format.

## Prompts

The work runs as eight prompts. Each ends in one pull request per repository it touches, into `feat/cpp-frontend-contexts` in edga, chen and atom. One pull request per repository then takes the branch to `main`.

| Prompt | Deliverables |
| --- | --- |
| [P01](prompts/cpp-frontend-contexts/P01-fixtures-baseline.md) | D1 |
| [P02](prompts/cpp-frontend-contexts/P02-edga-templates.md) | D2, D3 |
| [P03](prompts/cpp-frontend-contexts/P03-template-model.md) | D4, D5 |
| [P04](prompts/cpp-frontend-contexts/P04-toolchains-settings.md) | D6, D7 |
| [P05](prompts/cpp-frontend-contexts/P05-contexts-headers.md) | D8, D9 |
| [P06](prompts/cpp-frontend-contexts/P06-all-contexts.md) | D10 |
| [P07](prompts/cpp-frontend-contexts/P07-cdt-workers.md) | D11 |
| [P08](prompts/cpp-frontend-contexts/P08-docs-final-measurement.md) | D12 |

## Gates

Measured on the head of each pull request:

- The fixtures from D1: each deliverable's expectations hold with c2cpg and with edg2atom where the deliverable names both.
- edga's golden tests on every platform its CI covers, with the schema check on.
- chen's `c2cpg` and `edg2atom` test suites and atom's C and C++ tests pass.
- The memory-safety hand-written corpus, leveldb and abseil-cpp at `medium` and `low`, with both front ends: recall no lower and findings per tree no higher than the D1 baseline, unless every added finding has been read by hand and is a real defect, listed in the pull request.
- A run with the AST cache warm gives the same graph as a cold run, for every change that moves the AST format version.

## Deliverables

### D1. Fixtures and baseline

Add fixtures, each a small project with expectations in a form the tests read:

- **Templates:** a class template with members used with two argument types; a function template used with two types; a function template and a class template member that nothing instantiates; a dependent call (`x.get()` on a parameter of type `T`) whose callee differs per instance; a partial and an explicit specialisation; a variadic template; a lambda with an `auto` parameter passed to a standard algorithm; and a template defined in a project header and used from two units.
- **Toolchains:** compilation databases whose drivers are `nvcc`, `icx`, `icpx`, `emcc`, `em++`, `zig cc`, `zig c++`, `tcc`, `armclang`, `iccarm`, `armcl`, `cl430`, `clang --driver-mode=cl`, a GCC cross compiler (`arm-none-eabi-gcc`) and a compiler behind `ccache`, each with one source file that `#error`s unless the macros of that compiler are defined.
- **Contexts:** a file listed twice in the compilation database with different `-D` options that select different code; a header included by two units with different macros; a header that uses a typedef its includer declared before the `#include`; an X-macro `.def` file included inside an `enum` and inside a `switch`; and a database that compiles the same file for two targets.

Done when the fixtures are in chen (and in edga where the fixture is a single unit) with expectations that describe the correct result, the tests that read them are written and marked as expected to fail where today's code fails, and the baseline for every gate is recorded at chen, atom and edga `main` with no code change.

### D2. edga: template identity

Each routine, class, struct, union and variable generated from a template gets a `template` object (an id that is the same for every instance of one template in the unit, the template's name and qualified name, and the position of its declaration) and `templateArgs`, the arguments as the front end prints them, in order, with a type id where an argument is a type. The document stays `edga/1`; the fields are additions, the JSON format reference and `schema/edga-1.schema.json` describe them, and the goldens on every platform are regenerated and checked by hand.

Done when the two instances of `twice<T>` in the probe differ by `templateArgs` and share a `template` id, every instance in the D1 template fixture has both fields, and no non-template entity has either.

### D3. edga: prototype bodies for templates without instances

For each function template, and each member function of a class template, that is defined under `--edga-root` and has no real instance in the unit, edga exports the prototype instantiation as a routine with `prototype: true`, its `template` object, and its body. Types that depend on a template parameter are exported with a `dependent` kind that names the parameter, and an expression whose callee depends on a parameter is exported as an unresolved call with the name as written. `--edga-no-prototypes` turns this off. The front end defers prototype instantiation of function templates in GNU mode (`--defer_parse_function_templates`, the default when `gnu_version` is at least 30400), so edga passes the option that turns deferral off and reports, as diagnostics, any errors that this exposes in unusable templates instead of failing the unit.

Done when the unused template in the probe and in the D1 fixture has a routine with a body, a template that has real instances gets no prototype routine, the exit status of every existing golden is unchanged, and the goldens record any new diagnostics.

### D4. One template model in chen

edg2atom writes the `template` and `template-args` tags on instance METHODs and the `template-pattern` tag on prototype METHODs, with prototypes deduplicated across units by `DuplicateDefinitionPass` the same way instances are. c2cpg writes `template-pattern` on the METHOD of each template definition and, for each instance a unit uses, the instance's signature in `template-args` form on the call (the existing `template-instance` tag keeps its value). In both front ends a call whose callee depends on a template parameter lists, in `DYNAMIC_TYPE_HINT_FULL_NAME`, the METHODs it reaches in the unit's instances. The AST format version moves in both front ends.

Done when the D1 template fixture gives, from each front end, the tags the plan's Approach section describes, a test reads the dependent call's callee list from both front ends, and a warm run matches a cold run.

### D5. atom groups template code

atom's `memory-safety` output and its usages and reachables slices group entries whose METHODs share a `template` tag and whose position is the same: one entry, with an `instances` list naming each instance's `template-args`. A finding present in only some instances lists only those. The grouping is a field added to the existing output; nothing is removed.

Done when a seeded bug in the D1 template fixture is printed once with both instantiations listed under edg2atom and once under c2cpg, a bug that only one instantiation has lists one, and an end-to-end test in atom reads the printed output.

### D6. Toolchain table

Compiler identity comes from a table in chen's resources instead of code. Each entry names the driver (a name or a pattern, with wrappers such as `ccache` and `zig cc` handled), the family, whether it compiles every file as C++, how to ask it for its macros and include directories when it can be run (for example `nvcc -E -Xcompiler -dM` and the host compiler named by `-ccbin`), the fallback macro table when it cannot, and how to map its dialect options to the CDT and EDG settings. Entries cover the D1 toolchain fixtures. Fallback macro tables sit next to the existing ones in c2cpg's `resources/predefined-macros`. They are generated from real compilers where the compiler can be installed in CI, and otherwise copied from the vendor's documentation, with the source cited in the table. `PredefinedMacros` says its tables come from `tools/predefined-macros/generate.sh`, which is not in the repository; D6 adds that script and regenerates the existing tables with it to show it reproduces them. A driver the table does not know is reported in the parse report (D7) instead of being treated silently as the host compiler. `familyOf` and `PredefinedMacros` read the table, and edg2atom's `EdgaRunner` chooses the EDG dialect from the same entry.

Done when every D1 toolchain fixture preprocesses without reaching its `#error` with both front ends, the test reads which entry was chosen and where its macros came from, and an unknown driver produces a parse-report record.

### D7. The settings each unit was given

atom's `--parse-report` gains a `units` section: for each translation unit, the front end, the driver, the table entry chosen, where the macros came from (`probed`, `table`, `host` or `unknown`), the language and standard, a fingerprint of the macros, the include directories in search order, forced includes, the headers the unit owns, and for edg2atom the exact edga command line. The existing failure records keep their format. The section is written only when `--parse-report` is given.

Done when the report for each D1 fixture names the settings the fixture expects, and a test parses the report.

### D8. Build context on every file

Every FILE node from either front end carries a `build-context` tag: for a unit, a fingerprint of the compile command after the options that do not change the program are removed (chen already lists such options in `CompileCommands`); for a header, the owner unit's relative path and that fingerprint. Duplicate entries for one file in a compilation database are reported in the parse report with every command, and the one used is named.

Done when the D1 context fixtures show the right tag on each FILE, the duplicated file is reported with both commands, and the tag is the same with a warm cache.

### D9. Headers that are not self-contained (CDT)

c2cpg finds headers that cannot be parsed on their own: a header with no include guard that is included somewhere other than file scope, or one whose separate parse leaves names unresolved that the owner unit declares before its `#include`. Such a header is not parsed separately. Its declarations and function bodies are taken from the owner unit's parse, with their own file and line numbers, the way edg2atom writes headers as part of their owner. Headers that parse on their own keep today's path.

Done when the D1 typedef and X-macro fixtures give the same types and members from c2cpg as from edg2atom, a self-contained header's graph is unchanged, and the leveldb and abseil-cpp gates hold.

### D10. Every build context, opt-in

atom gains `--c-build-contexts <first|all>`, `first` by default. With `all`, a file that the compilation database compiles with more than one distinct context (after D8's removal of options that do not change the program) is analysed once per context. A function whose body is the same in every context is kept once, as `DuplicateDefinitionPass` keeps template instances. A function whose body differs is kept once per context: the copy from the first context keeps today's full name, and each other copy's full name gains the suffix `@ctx:<first 8 hex digits of the context fingerprint>`, with a `build-context` tag on the METHOD. Calls inside a context resolve to that context's copy.

Done when the duplicated-file fixture yields both variants of the selected code with `all` and only the first with `first`, a function that does not differ is present once, calls resolve inside their context, and the run without the option gives exactly today's graph.

### D11. CDT workers

c2cpg gains an opt-in worker mode (`--c-isolate` in atom, a matching chen option). The parent starts a small pool of worker JVMs that parse units and write their AST fragments to the AST cache directory; the parent loads them through `AstCacheStore` as it loads a warm cache. A worker that exits, runs out of memory or exceeds the parse timeout is replaced, and the unit it held is recorded in the parse report with the reason and retried once in a fresh worker. The pool size and each worker's heap are options with defaults derived from the machine. Without the option nothing changes.

Done when a test that makes a worker exit, loop or run out of memory on one named file (through a test-only system property) still produces the graph for every other file and a report record for that one, and the graph from worker mode equals the graph from today's mode on the D1 fixtures and on leveldb.

### D12. Documentation and final measurement

edga's JSON format reference and how-it-works document, chen's C and C++ front-end documentation and atom's documentation describe the template tags and grouping, the toolchain table and how to add an entry, the parse report's `units` section, the `build-context` tag, `--c-build-contexts` and `--c-isolate`. The Outcome section of this plan records every gate against the D1 baseline.

Done when every sentence of the new documentation has been checked against the code and the Outcome table is filled in.

## Risks and open questions

- **Prototype instantiation errors.** Turning off deferral makes EDG check every function template body even where the code relies on deferral (templates that can never be instantiated with any argument). D3 keeps the unit's export and records the errors; if a real project gains errors that change the exported real code, D3 keeps deferral on in GNU mode and exports prototypes only where the front end built them anyway, and the pull request says how many templates that loses on abseil-cpp.
- **Graph growth.** Prototype METHODs and per-context copies add nodes. Each pull request reports node and method counts on leveldb and abseil-cpp before and after; a growth above 20 percent at default options needs a maintainer's approval.
- **Name stability.** D10's suffix changes full names only under the opt-in option, and D4's tags add data without renaming anything. Any change that would rename an existing METHOD at default options is a question for the maintainer, not a decision for the implementation.
- **Vendor macro tables.** Some toolchains (IAR, TI) cannot be installed in CI. Their tables come from documentation and may be incomplete; the table records that, and the parse report says `table` so a user can see where the macros came from.
- **Worker overhead.** JVM start-up costs seconds per worker; the pool is long-lived to pay it once. The mode stays opt-in.

## Outcome

Filled in when the work ends.
