# P01: allocation-style fixtures, precision arms and the baseline

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read these sections of [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md): "Why", "Approach", "Gates" and D1. Read `~/work/memsafe-alloc-styles/refs/allocation-styles-probe.c` and the three findings files beside it.

Issue: AppThreat/chen#{{D1}}. This prompt changes no product code. It works only in `~/sandbox/memsafe-corpus` (which is not a git repository, so keep a list of every file you add or change for the report) and reads chen and atom at `origin/main`. Write the report to `~/work/memsafe-alloc-styles/reports/P01-report.md`.

## Task A: fixtures

Add five C fixtures to `c/`, written the way the corpus README asks (realistic code, each `bad_*` paired with a `good_*`, `@expect` and `@nofinding` markers, `clang -fsyntax-only` clean):

1. `cwe415_scope_cleanup.c`: the scope-cleanup attribute through the macro spellings real projects use, each defined in the fixture the way its project defines it: Linux `DEFINE_FREE(kfree, void *, if (_T) kfree(_T))` with `__free(kfree)` and `no_free_ptr`/`return_ptr`; glib `g_autofree`, `g_autoptr(T)` with `G_DEFINE_AUTOPTR_CLEANUP_FUNC` and `g_steal_pointer`; systemd `_cleanup_free_` with `TAKE_PTR`. Bad cases: explicit free then scope exit; returning the variable without a steal; storing it into a struct that outlives the scope. Good cases: plain use; steal on return; `free(p); p = NULL;` before exit; cleanup on an early `return`, on a `goto` out of a nested block and on `break` out of a loop body. Use `kfree` and `kmalloc` declared as externs with `malloc`-family GCC attributes so the fixture does not need kernel headers.
2. `cwe590_region_allocation.c`: a bump pool (the probe's shape), a PostgreSQL-style memory context (`MemoryContextCreate`, `palloc`, `pfree`, `MemoryContextReset`, `MemoryContextDelete`, with the context as a global current context and as an explicit argument), and an nginx-style pool (`ngx_create_pool`, `ngx_palloc`, `ngx_destroy_pool`, cleanup handlers). Bad cases: `free()` of region memory; use after destroy; use after reset. Good cases: region memory never freed individually; `pfree` of `palloc` memory; use before reset.
3. `cwe761_header_prefixed_allocator.c`: the Redis `zmalloc`/`zfree` shape with `PREFIX_SIZE`, the SQLite `mem1.c` shape (`p--` then free), and a plain wrapper that returns `malloc`'s result unchanged. Bad cases: `free()` on a prefixed allocation; the prefixed free on a plain `malloc` result. Good cases: matched pairs; `free()` on the plain wrapper's result; the prefixed free function's own body.
4. `cwe416_destroy_function.c`: destroy functions that free members then the argument, with and without a NULL guard, with a loop over a linked list of members, and calling another destroy function. Bad cases: use after each destroy call. Good cases: destroy then reassignment; a function that frees only when a flag is set (must not be read as a destroy function, so a use after it is not reported).
5. `cwe416_reference_release.c`: a plain `obj_ref`/`obj_unref` pair, a `kref_put(&o->ref, release)` with a release callback written as the kernel writes it, and a `Py_DECREF`-style macro that decrements and calls a dealloc function at zero. Bad cases: use after the release of the only owned reference. Good cases: acquire, release, use, release; use of a borrowed reference passed in as a parameter (not reported at medium).

Also add to `c/` the probe's terminator idiom as a good case (`buf[len] = 0` after `malloc(len + 1)`) with a bad twin (`buf[len + 1] = 0`), in whichever existing bounds fixture fits best.

Mark each defect with the CWE the plan names and the attributes that describe what it needs (`interprocedural`, `error-path`, and so on; add a new attribute only if none fits, and document it in the README's attribute list). Run `python3 tools/manifest.py` and check that the new rows are in `manifests/expected.json`.

## Task B: precision arms

Add `arms/` with one checkout per arm, at the tag the plan names, as a shallow clone of the upstream repository (`git clone --depth 1 --branch <tag>`): SQLite, Redis, nginx, pgvector with PostgreSQL, QEMU, Linux, CPython and Lua. Analyse only the subtree the plan names. For pgvector, pass PostgreSQL's `src/include` as an include directory with `--include-path`. For Linux, a sparse checkout of `drivers/input/`, `include/` and `arch/x86/include/` is enough; do not clone the whole history or the whole tree.

Write `tools/run_arms.sh`, modelled on `tools/run.sh`: for each arm, run `atom memory-safety` on its subtree at `MIN_CONFIDENCE` (default `medium`), with `JOBS=N` concurrency like `run_cve.sh`, and print findings per arm and per rule, and findings per thousand lines of C in the subtree. A failed or timed-out arm prints "not assessed" with the reason and makes the script exit non-zero. Accept `ATOM_ARGS` as the other scripts do. Document it in the README.

Write `arms/memsafe-allocation-styles.corpus.json` following [corpus-manifest.schema.json](../../corpus-manifest.schema.json): one item per arm, `source` naming the repository, tag and commit, `sha256` the digest of `git archive --format=tar <commit> <subtree...>`, `license` the SPDX identifier from the project's own licence file, and `storage` of kind `repository` with the upstream URL as the location. The reviewer moves it into the plans folder.

## Task C: baseline

Build atom from `origin/main` against chen `origin/main` as published (atom's `build.sbt` already pins it). Then record, at `medium` and at `low`:

- `tools/run.sh`: recall, precision, `@nofinding` hits, and the per-file result for each new fixture.
- `JOBS=5 PROJECT=ffmpeg-all SCOPE=libavformat tools/run_cve.sh`: sites reported at both tolerances and fixed-site hits.
- leveldb and abseil-cpp findings per tree, the way the earlier reports in the corpus `NOTES-*.md` files measured them.
- `tools/run_arms.sh`: findings per arm and per rule.
- The new fixtures with edg2atom as well (`ATOM_ARGS` as in the rules), per file.

For the arms at `medium`, open and classify the first 20 findings of each arm (or all of them, if fewer) as true or false, with a one-line reason. These are the precision baseline later prompts are judged against.

The report's "Gates" section is this baseline. Put the numbers in tables that later reports can copy.
