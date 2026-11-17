# C memory safety across allocation styles

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/chen/issues/328 |
| Owner | @prabhu |
| AI use | Auto: an implementation agent writes each deliverable from the prompts in [prompts/memsafe-allocation-styles](prompts/memsafe-allocation-styles/00-RULES.md), a reviewing agent verifies, refactors and opens the pull request, a maintainer approves |
| Corpus | `memsafe-allocation-styles.corpus.json`, added by D1 |

## Why

chen's memory-safety overlay (the `MemorySemantics`, `MemoryApi`, `AllocationState` and `MemorySafetyFinding` passes behind `atom memory-safety`) was built and measured against FFmpeg, leveldb, abseil-cpp and a hand-written corpus. All of them allocate with `malloc` and `free` or thin wrappers over them. Most large C projects do not.

[Memory management in 40 major C projects](https://theconsensus.dev/p/2026/11/08/c-memory-management-survey.html) (The Consensus, 2026-11-08) counts allocation call sites in 40 C projects. Only 8 allocate solely with `malloc` and `free`. Regions (pools freed all at once) are the main allocator in 7 projects, including PostgreSQL, nginx and httpd, and appear in 15. Reference counting is the main allocator in CPython, PHP and Perl and is used for some objects in Redis, curl, QEMU and Linux. Linux and QEMU have started to free memory at scope exit through the GCC `cleanup` attribute, for example `u8 *tx_buf __free(kfree) = kmalloc(len + 1, GFP_KERNEL);` in Linux's [raydium_i2c_ts.c](https://github.com/torvalds/linux/blob/v7.2/drivers/input/touchscreen/raydium_i2c_ts.c#L174) and `g_autofree char *filename = NULL;` in QEMU's [block.c](https://github.com/qemu/qemu/blob/v11.1.2/block.c#L855).

A probe file with one function per allocation style was run through `atom memory-safety` at chen 47e74f13 and atom a504584. It contains six bugs and five correct functions:

| Function | Expected | Result |
| --- | --- | --- |
| `free()` of a variable that is also freed at scope exit | double free | missed |
| returning a scope-cleanup variable | use after free in the caller | missed; the function is summarised as an allocator, so callers treat the freed pointer as fresh |
| `free()` of memory taken from a pool | wrong deallocation | missed |
| use after the pool is destroyed | use after free | missed; a destroy function that frees a member and then its argument gets no free summary |
| `free()` of a header-prefixed allocation | wrong deallocation | missed; an allocator that returns `h + 1` is not recognised |
| use after the last `unref` | use after free | missed; a conditional free gets no summary, by design |
| `free((hdr_t *)p - 1)` inside the matching free function | nothing | MS-ALLOC-006 at high confidence |
| `buf[len] = 0` after `malloc(len + 1)` | nothing | MS-BOUND-004 at medium confidence |
| scope-cleanup variable, and a pointer handed out through a steal helper | nothing | MS-ALLOC-003 (leak) at low confidence |

The header-prefix shape is how Redis `zfree` and SQLite's `mem1.c` free their blocks when the C library cannot report allocation sizes, and the terminator shape is in nearly every string-copy helper, so both false positives appear at the default level on real code.

The table is for c2cpg, the default C front end, which drops `__attribute__((cleanup))` altogether: no call to the cleanup function appears anywhere in the graph. The front-end probe for the first memory-safety release found this and left it out of scope. edg2atom, the optional EDG front end, already emits a compiler-generated `fn(&var)` call tagged `lifetime-end` at every exit from the variable's scope. With `--c-frontend edg` the two cleanup leak reports disappear, but the double free is reported as a use after free (MS-ALLOC-002, high) on the explicit `free` line instead of as a double free where the scope ends, and the dangling return is still missed. So the graph shape is settled by edg2atom, and the remaining work is c2cpg parity and correct handling in the allocation-state pass. The survey shows scope cleanup is now how new Linux and QEMU code is written.

## Scope

In scope: C (and C as compiled by a C++ compiler) through both C front ends, c2cpg and edg2atom; the passes and rules of the memory-safety overlay; the memory API inventory and its external configuration; `atom memory-safety`; the hand-written corpus and new real-project precision arms.

Out of scope:

- Garbage-collected heaps (Ruby, Lua, Emacs, OCaml, Julia, Erlang). The only change for them is that their projects join the precision arms, where a leak report is always wrong.
- Lock guards built on the same attribute (Linux `guard(mutex)`, `scoped_guard`). They are lifetimes of locks, not memory, and belong with the concurrency rules.
- Missing reference releases (reference leaks). This plan detects use after the last release, not a release that never happens.
- C++ destructors and smart pointers, which have their own plan items in the original memory-safety plan.
- Points-to analysis for allocators reached through function pointers (zlib `ZALLOC`, xz `lzma_alloc`). Those projects are served by declared entries in the external configuration.

## Approach

The overlay already has the right structure: facts are computed once as tags, rules are conjunctions of tags, and function behaviour comes from evidence (declared GCC attributes, inferred bodies, the built-in inventory), never from a function's name. This plan keeps that rule. Each allocation style gets the smallest addition that lets the existing allocation-state lattice and rules reason about it:

1. **Fix the two default-level false positives first** (D2), because they cost precision on every project regardless of style.
2. **Teach the summaries the destructor shape** (D3). A function that frees members of its argument and then the argument itself is the most common destroy function in the survey, and regions and reference counting both reduce to it once their release function is summarised.
3. **Scope cleanup** (D4, D5). c2cpg emits the same compiler-generated `fn(&var)` calls at scope exits that edg2atom already emits, so both front ends give the passes one graph shape. The allocation-state pass then reads each call through `fn`'s existing summary, so Linux's `__free_kfree`, glib's `g_autoptr_cleanup_generic_gfree` and systemd's `freep` need no special case. A helper that reads `*pp`, stores NULL and returns the old value is summarised as a steal, which moves ownership out of the variable.
4. **Allocator identity** (D6, D7). A wrapper that returns exactly what `malloc` returned is correctly a `heap` allocator, because `free()` on its result is legal. A wrapper that returns an offset into its allocation is not, and gets a family of its own paired with the free function that subtracts the same offset. Libraries whose bodies are not in the analysed tree (glib, the kernel, PostgreSQL, APR, nginx, CPython, PHP) are described by declared profiles in the memory API inventory, selected by the headers a translation unit includes.
5. **Regions** (D8). A region allocation is owned by its region: never a leak, wrong to `free()`, and dead once the region is destroyed or reset. Inference covers the bump-allocator shape (a pointer returned from arithmetic on a field of the region argument); profiles cover `palloc`, `ngx_palloc`, `apr_palloc` and `devm_kzalloc`.
6. **Reference release** (D9). A function that decrements a field of its argument and frees the argument when the count reaches zero is summarised as a release. A use of an object after the release of the only reference the method owns is reported.

Every deliverable follows the rules the first memory-safety release learned the hard way. Each new behaviour ships with a correct-C negative control written first (loops, `goto` error paths, static storage, freep wrappers, and the style's own correct idiom). A summary claims "always" only on control-dependence evidence. Each rule change has an end-to-end test in atom that reads the rendered finding, not only a tag assertion in chen, because several earlier defects computed a fact and then dropped it in the renderer.

## Prompts

The work runs as seven prompts, each covering one or two deliverables and ending in one pull request per repository into `feat/memsafe-alloc-styles` in chen and atom. One pull request per repository then takes the branch to `main`. Each prompt runs as a zcode workflow: a GLM-5.3 lead plans and decides, GLM-5.3-Flash workers implement bounded pieces, and fresh Flash reviewers check each piece before the lead merges it (`00-RULES.md`, "Work as a workflow").

| Prompt | Deliverables |
| --- | --- |
| [P01](prompts/memsafe-allocation-styles/P01-fixtures-arms-baseline.md) | D1 |
| [P02](prompts/memsafe-allocation-styles/P02-false-positives-destroy-summaries.md) | D2, D3 |
| [P03](prompts/memsafe-allocation-styles/P03-scope-cleanup.md) | D4, D5 |
| [P04](prompts/memsafe-allocation-styles/P04-families-profiles.md) | D6, D7 |
| [P05](prompts/memsafe-allocation-styles/P05-regions.md) | D8 |
| [P06](prompts/memsafe-allocation-styles/P06-reference-release.md) | D9 |
| [P07](prompts/memsafe-allocation-styles/P07-docs-final-measurement.md) | D10 |

## Gates

Measured on the head of each pull request, at `medium` and at `low`, with `tools/run_gates.sh` in the corpus:

- The hand-written corpus: recall and precision no lower than the D1 baseline, and no finding on a `@nofinding` line.
- The FFmpeg arm: no fewer CVE sites reported than the baseline, and no finding at the fixed-commit sites.
- leveldb and abseil-cpp: findings per tree at `medium` no higher than the baseline.
- The new precision arms (D1): findings per tree at `medium` no higher than the baseline unless every added finding has been checked by hand and is a real defect, listed in the pull request.
- The allocation-style fixtures (D1): the deliverable's bad functions are reported and its good functions are not.

## Deliverables

### D1. Allocation-style fixtures, precision arms and baseline

Add one corpus fixture per style, each a set of `bad_*` and `good_*` functions with `@expect` and `@nofinding` markers: scope cleanup (Linux `__free`, glib `g_autofree` and `g_autoptr`, systemd `_cleanup_free_`, written as the macros those projects define), regions (a bump pool, a PostgreSQL-style memory context, an nginx-style pool), header-prefixed allocators, destroy functions, and reference counting (a `kref`-style put with a release callback, a `Py_DECREF`-style macro, and a plain `unref`). Each fixture builds with `clang -fsyntax-only`.

Add real-project precision arms at the tags the survey links to, one subtree per style: SQLite `src/` (version-3.53.4), Redis `src/` (8.10.1), nginx `src/` (release-1.31.6), pgvector `src/` against PostgreSQL `src/include` (v0.8.6, REL_18_6), QEMU `block/` and `util/` (v11.1.2), Linux `drivers/input/` (v7.2), CPython `Objects/` (v3.14.7) and Lua (v5.5.1). Record each in `memsafe-allocation-styles.corpus.json` with its repository, tag, subtree and the SHA-256 of a `git archive` of that subtree.

Done when the fixtures are in the manifest the scorer reads, and the baseline for every gate above is recorded at `medium` and `low` on the base of `feat/memsafe-alloc-styles`, with no memory-safety code change. That base is chen `main` plus the flow-summary fix in AppThreat/chen#336, without which `--with-data-deps` does not finish on the FFmpeg worktrees, and atom `main`.

### D2. Default-level false positives

MS-ALLOC-006 no longer fires on a release of a pointer moved back from a parameter or from a value derived only from a parameter (`free((hdr_t *)p - 1)`, `p--; free(p)`, `free((char *)ptr - PREFIX_SIZE)`). It still fires on a release of a pointer advanced from an allocation in the same method or walked forward through it. MS-BOUND-004 treats an index `n` into a buffer allocated with `n + k`, where `k` is a positive constant, as in bounds, including when the allocation and the index are written through different but equal expressions of the same variable.

`close()` releases every file descriptor, from `open` or `socket` alike, and `fclose` releases a `FILE *`; a mismatch between the two is still MS-ALLOC-007.

Done when the probe's two correct functions are silent at every level, the descriptor mismatches are reported and the matched pairs are not, the matching bad variants (`free(p + 1)` on a fresh allocation, `buf[len + 1]` after `malloc(len + 1)`) are still reported, and SQLite's and Redis's free functions produce no MS-ALLOC-006 finding.

### D3. Destructor free summaries

`MemorySemanticsPass` summarises a method as freeing parameter `i` when, after an optional NULL guard on that parameter, every path to the method's exit frees it, whatever else the method does first (freeing members, looping over a list, calling other destroy functions). A NULL guard on the parameter itself is not a condition on the free. Any other condition on the free (a reference count, a flag) still blocks the summary.

Done when `pool_destroy`, `obj_free` with a NULL guard, and a destroy function that frees a linked list of members are summarised as `frees-param`, use after a call to each is reported, and a function that frees only when a counter reaches zero is not summarised.

### D4. Scope cleanup in c2cpg

c2cpg emits, for each local declared with `__attribute__((cleanup(fn)))` or `__attribute__((__cleanup__(fn)))`, a compiler-generated call `fn(&var)` at every exit from the variable's scope: each `return` inside the scope (after the return value is evaluated), each `goto`, `break` or `continue` that leaves it, and the end of the block. The calls carry the same tags and the same argument shape as edg2atom's (`compiler-generated`, `lifetime-end` valued with the variable name, argument 1 the address of the variable), so a pass cannot tell the front ends apart. This works when the attribute comes from a macro (`__free(kfree)`, which pastes `__free_kfree`; `g_autofree`; `g_autoptr(GString)`; `_cleanup_free_`). The AST cache version moves so cached graphs without the calls are rebuilt.

Done when the D1 cleanup fixture gives the same cleanup calls, at the same lines and in the same CFG positions, from c2cpg and from edg2atom, and a test covers each macro spelling and each kind of scope exit.

### D5. Scope cleanup in allocation state and rules

`AllocationStatePass` and the rules read the compiler-generated cleanup calls correctly in both front ends. A method summary marks a parameter as stolen when the method reads `*pp`, stores NULL into `*pp` and returns the old value (`g_steal_pointer`, `TAKE_PTR`; Linux `no_free_ptr` and `return_ptr` reduce to this or to an assignment of NULL).

The rules then: report no leak for a cleanup variable; report a double free (MS-ALLOC-001) at the cleanup call when the variable was freed and not reset to NULL before that exit, instead of today's use after free on the explicit free; report a use after free when a cleanup variable is returned or stored somewhere that outlives the scope without being stolen; and never summarise such a method as an allocator. The early-return path in the double-free fixture is checked on its own, because the misplaced report seen with edg2atom suggests that a cleanup call on one exit path reaches code on another.

Done when the cleanup fixture's bad functions are reported with the right rule at the right line, its good functions (including the steal and the reset-after-free forms) are not, the results are the same from both front ends, and the QEMU `block/` arm has no new leak finding at `low`.

### D6. Offset allocator families

A method that returns an allocation advanced by a constant (`return h + 1`, `return (char *)p + PREFIX_SIZE`) is summarised as an allocator of its own family, named after the method, with nullable and size facts carried over. A method that releases its parameter moved back by the same constant is summarised as that family's free. MS-ALLOC-007 reports a release of one family's pointer with another family's free, which includes `free()` on a header-prefixed allocation and the family's free on a plain `malloc` result.

Done when the header-prefix fixture's mismatches are reported, the matched pairs are not, a plain wrapper that returns `malloc`'s result stays in the `heap` family, and the Redis and SQLite arms do not gain findings.

### D7. Declared library profiles

The memory API inventory gains named profiles for the libraries whose bodies are usually outside the analysed tree: glib, the Linux kernel, PostgreSQL, APR, nginx, CPython and PHP. A profile declares allocation and free families (`g_malloc`/`g_free`, `kmalloc`/`kfree`/`kvfree`, `emalloc`/`efree`, `PyMem_Malloc`/`PyMem_Free`), cleanup functions, steal helpers, and the region and release roles that D8 and D9 consume. Each entry cites the header or documentation that defines its behaviour. A profile is used when a translation unit includes one of its headers, and `atom memory-safety` gains an option to list the profiles in use and to turn selection off. The external configuration keeps its precedence over both.

Done when each profile has a test that selects it from an include and checks one allocation, one free and one mismatch, and a file that includes none of the headers sees no profile entry.

### D8. Region semantics

A region allocation (declared by a profile, or inferred from a method that returns arithmetic on a field of its region parameter without allocating) carries its region as provenance. Such a pointer is never reported as a leak. A heap free of it is a wrong deallocation (CWE-590 or CWE-762, by the existing rules). A use after the region is destroyed, through D3's summary of the destroy function or a declared destroy entry, is a use after free. A use after a declared reset (`MemoryContextReset`, `apr_pool_clear`) is a use after free at medium confidence. Device-managed allocations (`devm_kzalloc`) are region allocations owned by the device.

Done when the region fixture's bad functions are reported and its good functions are not, and the nginx and pgvector arms have no leak finding on a region allocation at any level.

### D9. Reference release semantics

`MemorySemanticsPass` summarises a release (a method that decrements a field of parameter `i` and frees `i` or calls a release callback when the field reaches zero, including `kref_put(&o->ref, release)`) and an acquire (a method that increments a field of parameter `i`, which the pass already records as `grow`). After a release of an object that the method obtained as a new reference (an allocation or a declared constructor) and has not acquired again, a use of the object is reported as a use after free at medium confidence. Any other use after a release is reported at low confidence.

Done when the reference-counting fixture's use after the last release is reported at medium, the balanced acquire and release is not reported, and the CPython `Objects/` arm gains no medium finding.

### D10. Documentation and final measurement

The memory-safety documentation in chen and atom describes each allocation style, what is inferred, what a profile declares, the new option, and how to declare an in-house region or reference-counting API in the external configuration. The Outcome section of this plan records every gate at `medium` and `low` against the D1 baseline.

Done when every sentence of the new documentation has been checked against the code and the Outcome table is filled in.

## Risks and open questions

- **Scope exits in c2cpg.** D4 must find every exit from a block, including `goto` out of nested blocks, and CDT gives scopes differently from EDG. edg2atom's `ExitScope` bookkeeping is the model. If an exit kind cannot be found reliably, D4 emits no call for that exit rather than one in the wrong place, and the pull request lists the kind.
- **Macro spellings.** Linux's `__free(name)` pastes the name into `__free_##name`, which the front end must expand to find the cleanup function. If a macro is not expanded (for example a header that is not on the include path), no cleanup call is emitted and the variable is treated as an ordinary local, which can only produce a leak at `low`, never a double free.
- **Profiles from includes.** A project can define its own `g_malloc`. A profile entry therefore yields to any summary inferred from a body in the analysed tree, the same way the built-in inventory does today.
- **Reference counting through macros.** CPython's `Py_DECREF` and PHP's `zend_string_release` are inline functions or macros whose bodies reach the graph only when the headers are analysed. D9 measures how often they do on the CPython arm before relying on inference, and adds profile entries where it does not.

## Outcome

Filled in when the work ends.
