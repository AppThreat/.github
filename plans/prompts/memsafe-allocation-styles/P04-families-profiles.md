# P04: offset allocator families and declared library profiles

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D6, D7 and the third risk in [memsafe-allocation-styles.md](../../memsafe-allocation-styles.md), and the earlier reports in `~/work/memsafe-alloc-styles/reports/`.

Issues: AppThreat/chen#324 (task A) and AppThreat/chen#325 (task B). Branches: `memsafe/p04-families` in chen and atom, from `origin/feat/memsafe-alloc-styles` (or the branch the prompt that hands you this one names). Write the report to `~/work/memsafe-alloc-styles/reports/P04-report.md`.

## Task A: offset allocator families (D6)

In `MemorySemanticsPass`, body inference today accepts an allocator only when every non-NULL return flows from an allocation, so the probe's `my_xalloc` (`return h + 1;`) gets no summary. Add the offset shape:

1. A method whose every non-NULL value return is a known allocation advanced by one constant amount (`h + 1` with `h` of a struct type, `(char *)p + PREFIX_SIZE`, `p + sizeof(size_t)`) is an allocator of a new family named after the method (for example `offset:zmalloc`). Normalise the amount to bytes where the types allow it, so `h + 1` and `(char *)h + sizeof(*h)` are the same amount. Carry over the size and nullable facts that a plain wrapper gets.
2. A method that releases its parameter moved back by the same amount is that family's free. Pair them through the amount and the underlying family, never through the names.
3. `MemoryApiPass` tags the call sites with the new family, so MS-ALLOC-007 (`RuleMismatchedFree`) reports `free()` on an offset allocation and the offset free on a plain allocation, with no change to the rule unless the family comparison needs one.
4. A wrapper that returns an allocation unchanged stays in its underlying family. `free(xmalloc(n))` is correct C and must not be reported.

Check against the P01 header-prefix fixture, and on the Redis and SQLite arms. Note that Redis builds `zmalloc` differently depending on `HAVE_MALLOC_SIZE`; run the arm once with the macro defined and once without (`--define`), and report both.

## Task B: declared library profiles (D7)

The inventory is `platform/frontends/x2cpg/src/main/resources/memory-apis.json`, read by `MemApiVocab.scala`. The external configuration (`atom memory-safety --memory-api-config`) is merged over it by API name.

1. Add a profiles section to the inventory format, or one resource file per profile, whichever keeps `MemApiVocab`'s validation simplest. Each profile has a name, the header names that select it, and entries in the existing entry format. Add the new roles that later prompts need as fields now, documented but not yet read by any rule: `region` (create, allocate with the region argument index, reset, destroy), `release` and `acquire` (with the parameter index), `steal`, and `cleanup` (a function that frees `*pp`). Stop and ask under "Questions" if the format change cannot be made backward compatible with existing external configuration files.
2. Write the profiles: glib, the Linux kernel, PostgreSQL, APR, nginx, CPython and PHP. Each entry needs a citation in the profile's comment block: the header and line, or the documentation page, that states the function's behaviour. Include at least the functions the survey names for each project (`g_new0`, `g_free`, `g_steal_pointer`; `kmalloc`, `kzalloc`, `kvfree`, `kfree`, `devm_kzalloc`, `kref_put`; `palloc`, `palloc0`, `pfree`, `MemoryContextReset`, `MemoryContextDelete`, `AllocSetContextCreate`; `apr_palloc`, `apr_pool_create`, `apr_pool_clear`, `apr_pool_destroy`; `ngx_alloc`, `ngx_free`, `ngx_palloc`, `ngx_create_pool`, `ngx_destroy_pool`; `PyMem_Malloc`, `PyMem_Free`, `Py_DECREF`, `Py_INCREF`; `emalloc`, `efree`, `zend_string_release`). Families must say which frees are interchangeable: `kvfree` accepts `kmalloc` and `vmalloc` memory, and glib's `g_free` is `free` on every platform glib supports today (cite the glib release note that made it so).
3. Select a profile for a translation unit when the file includes one of its headers. Find how c2cpg and edg2atom record `#include` (an IMPORT or DEPENDENCY node, or a tag), and if neither records it, add the smallest record that works for both front ends. A body inferred in the analysed tree wins over a profile entry with the same name, as the built-in inventory already yields to bodies.
4. In atom, add `--memory-api-profiles <auto|none|name,name>` to `memory-safety` (default `auto`), and print the selected profiles and how many files selected each, in the same place the command prints the `MemorySemanticsPass` summary counts. Add the option to atom's docs for the command.

Tests: for each profile, a file that includes its header gets one allocation, one free and one mismatch reported correctly; a file that includes none gets no profile entry; `none` turns selection off; an external config entry overrides a profile entry.

## Finish

Run the gates at `medium` and `low`. Profiles only add knowledge, so a rise in findings on an arm is expected where a profile now recognises an allocator; read every added finding on the QEMU, Linux, PostgreSQL-backed, nginx and CPython arms. Any false finding added at `medium` must be fixed before you finish.
