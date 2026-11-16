# P01: fixtures and baseline

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read the whole of [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), with D1 in detail, and the probes in `~/work/cpp-frontend-contexts/refs/`.

Issue: AppThreat/chen#329. Branches: `cfc/p01-fixtures` in chen and edga, from `origin/feat/cpp-frontend-contexts`. Write the report to `~/work/cpp-frontend-contexts/reports/P01-report.md`.

This prompt changes no product code. It adds fixtures and the tests that read them, and records the baseline every later prompt is compared with.

## Background

Read how fixtures and expectations are written today before adding any:

- chen: the C and C++ fixtures under `platform/frontends/c2cpg/src/test` and `platform/frontends/edg2atom/src/test`, and `EdgCodeToCpgSuite` in `edg2atom/testfixtures`, which builds a graph from a snippet with edga. `CompileCommandTests` and `PredefinedMacrosTests` show how compilation databases and compiler identity are tested.
- edga: `tests/fixtures`, `tests/expected` and `tests/run.py`. Fixtures declare what they use instead of including system headers.

Reproduce the plan's findings first and say in the report what you saw: run edga on `refs/templates-probe.cpp` and compare with `refs/templates-probe.edga.json`; build a graph of `refs/non-self-contained/` with c2cpg and with edg2atom and compare the types and members the header's function sees through its parameter (`c->n`, `c->buf`). The plan says the CDT result there is unconfirmed; settle it.

## Task A: template fixtures

Add the template fixtures from D1 to chen (one project for c2cpg and edg2atom) and the single-unit ones to edga's `tests/fixtures`. For each fixture write the expectations the finished work must meet: for edga, the `template` and `templateArgs` fields and prototype routines D2 and D3 describe; for chen, the tags D4 describes and the callee list of the dependent call. Expectations that today's code does not meet are written as tests marked pending (`pendingUntilFixed` or the suite's equivalent) with a comment naming the behaviour, not the plan. For edga, keep today's goldens unchanged and put the future expectations in a separate file the later prompt will compare against; do not change `tests/run.py` behaviour for existing fixtures.

Add one seeded bug that only one instantiation has and one that every instantiation has (an out-of-bounds index that depends on `sizeof(T)`, and a null dereference that does not), with `@expect` markers in the memory-safety corpus format, for D5.

## Task B: toolchain fixtures

For each driver in D1's toolchain list, add a compilation database and one source file that `#error`s unless that compiler's identifying macros are defined (for example `__NVCC__` and `__CUDACC__` for `nvcc`, `__INTEL_LLVM_COMPILER` for `icx`, `__EMSCRIPTEN__` for `emcc`, `__TINYC__` for `tcc`, `__IAR_SYSTEMS_ICC__` for `iccarm`, `__TI_COMPILER_VERSION__` for the TI compilers, `_MSC_VER` for `clang --driver-mode=cl`). The compilers need not be installed; the fixture tests the fallback path. Record for each which family chen chooses today and where its macros came from.

## Task C: context fixtures

Add the context fixtures from D1 to chen, each with expectations: which code is in the graph for each database entry, which unit owns each header, and which types and members a non-self-contained header's code sees. Record today's results for c2cpg and edg2atom.

## Task D: baseline

On chen, atom and edga at `origin/feat/cpp-frontend-contexts` (which equals `main` at this point), record:

- edga goldens: pass count per platform you can run.
- chen `c2cpg/test` and `edg2atom/test`, atom `test`: pass, fail and pending counts.
- The memory-safety hand-written arm, leveldb and abseil-cpp at `medium` and `low`, with c2cpg and with edg2atom: the summary lines of `tools/run.sh` and the arm scripts, and findings per tree.
- Node and METHOD counts of the leveldb and abseil-cpp graphs from each front end.

Put every number in the report, in tables that later reports can copy.
