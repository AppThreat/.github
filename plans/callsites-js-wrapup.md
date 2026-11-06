# callsites: closing the JavaScript work for the November release

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/atom/issues/305 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

Nine tranches of callsites work have merged (see [callsites-status.md](callsites-status.md)). Five
open issues remain on the JavaScript side and in the frontends it shares with Java, and they should
close together so that the end-of-November release ships them as one set:

- AppThreat/atom#320: records in Vue, Svelte and Astro components must carry the file's lines. The
  astgen cause is fixed (AppThreat/atom-parsetools#83 on main, #84 on `release/1.x`), but atom
  installs atom-parsetools 1.10.6, which still has the bug.
- AppThreat/atom#322: typed-call recall for JavaScript and TypeScript is 0.67 to 1.0 against the
  typed oracle (angular 0.715, juice-shop 0.816, vue3-realworld 0.673, nestjs 1.0, express 0.968),
  measured without `node_modules`. The cause of the gap has not been measured.
- AppThreat/atom-parsetools#33: `astgen -t ts` stalls on cdxgen's repository. The cause is known: an
  untyped array reassigned in many `if` blocks makes the TypeScript checker's flow analysis grow
  exponentially. The type budgets on main (AppThreat/atom-parsetools#81) bound it, and the native
  type maps avoid it, but neither is on `release/1.x`, which is what atom uses.
- AppThreat/atom-parsetools#34: a class with a TC39 auto-accessor (`accessor x = 1`) does not parse,
  because astgen's Babel plugin list lacks `decoratorAutoAccessors`. chen's jssrc2cpg declares
  `ClassAccessorProperty` but handles only `ClassProperty`.
- AppThreat/atom#334: Java method references (`Foo::bar`) are missing from `usages` and `callsites`,
  though javasrc2cpg emits `METHOD_REF` nodes, and members Lombok generates (`log` from `@Slf4j`)
  may not resolve under atom's default delombok mode, `types-only`.

## Scope

atom-parsetools on `release/1.x` and `main`, chen's jssrc2cpg and javasrc2cpg where a frontend
causes a defect, and atom's callsites and usages slices. The native type maps as astgen's default
(AppThreat/atom-parsetools#40, AppThreat/atom#361) belong to the v5 work and are not part of this
plan; #322 measures them only to inform that decision.

## Approach

Releases happen once, at the end of the month. Every change lands on its branch during the month,
and a fix that atom must see before the release is tested in atom's `js-parsetools-main` CI job,
which runs atom-parsetools main. The release then publishes atom-parsetools 1.x, bumps atom's pins
and runs the full corpus once.

Each deliverable follows the rules of the earlier tranches: tests with bad and good twins that fail
on main, a mutation table, equivalence for changes that should keep output, and a corpus subset per
iteration.

## Deliverables

### D0. atom-parsetools CI is green again

The `parsa` jobs fail on main since the hostile-input cases of #81 first ran in CI. On the 10 MB
minified bundle, Babel's AST takes 1.3 GB of heap and its JSON would be about 80 times the source,
past V8's largest string. On the macOS runner's heap the process runs out of memory before it can
record the file as failed. The native case also runs past the test's 110 s: the native program has
no build budget (47 s on the runner) before its 60 s per-file budget starts. A related defect: when
the TypeScript 6 program budget stops the type worker, astgen starts writing ASTs before the worker
has exited. How astgen should treat a file it cannot write needs a decision (a size limit, or
writing the JSON as a stream); this lands first, on main and `release/1.x`.

### D1. Vue, Svelte and Astro positions (atom#320)

Svelte and Astro already keep positions; their regression tests check `loc` against the source.
atom gets a fixture with an unclosed `<input>`, an `<hr>` and a `<template #fallback>` slot that
expects every record on a script line or a template binding, passing in `js-parsetools-main` first.
At the release, atom's six `ci/` Dockerfiles and the workflows that install the bare package name
pin the new 1.x version, and vue3-realworld is scored again (47 template-line records on main, none
expected). `ASTGEN_VERSION` on 1.x is bumped in the same release so parse caches rebuild.

### D2. TC39 auto-accessors (atom-parsetools#34)

Add `decoratorAutoAccessors` to astgen's Babel plugins on both branches, with a fixture that holds a
decorated accessor beside legacy decorators in other files (the plugin must not change their
output). chen's jssrc2cpg handles `ClassAccessorProperty` as a property with its initializer and
decorators, and atom gets a callsites test where an accessor's initializer calls a dependency.

### D3. Type budgets on release/1.x (atom-parsetools#33)

Backport the per-file and per-program budgets of #81, with D0's fixes, to `release/1.x`. Done when
`astgen -t ts` on cdxgen's repository finishes within five minutes on 1.x, every file that already
finished has the same json and typemap, and the budget records name the files that lost their
types.

### D4. Typed-call recall (atom#322)

Measure first: the typed oracle projects with `node_modules` installed, on 1.x with TypeScript 6
types and on main with native types. Classify every miss as type unavailable (no type for the
receiver), chen typing (a type exists but `methodFullName` does not carry it) or slice logic, and fix
the last two, starting with the confirmed `(await import('uuid')).v4()` shape. Done when typed
recall is at least 0.85 on every typed-oracle project, or the remaining misses are all in the first
class and recorded as such. vue3-realworld is read after D1.

### D5. Java method references and Lombok (atom#334)

Independent of D1 to D4 and can run beside D4. First check whether `log.info` from `@Slf4j`
resolves under `types-only`. Then read `METHOD_REF` nodes in Java callsites and usages, with an
oracle check that the javac oracle emits method-reference rows. The Java corpus (petclinic,
sec-code, webgoat, mall, shiro) needs equivalence tables, because every Java project's slices may
change.

## Order and dates

D0 first, because CI must be green for anything else to merge. D1's atom fixture and D2 next, then
D3. D4 starts once D1's fixture is in and runs through the month; D5 runs beside it. Every pull
request merges when ready. The release at the end of November publishes the 1.x line with D0 to D3,
bumps atom's pins (D1), and runs the full corpus once with the measurements going to
[callsites-status.md](callsites-status.md).

## Risks and open questions

- D0 needs a decision on files whose AST cannot be written (the maintainer).
- If 1.x is not published as npm `latest`, anything that installs the bare package name keeps the
  old version; atom must pin the version explicitly.
- D4's gap may be mostly type availability, which no slice change fixes; the measurement says so
  before any fix is written.
- Budgets turn a stall into files without types, which costs recall on exactly those files.
- D5 changes Java slices on every project; the equivalence tables must show each change.

## Outcome

All deliverables merged on 2026-11-06; the release at the end of November ships them.

- **D0.** AppThreat/atom-parsetools#85 (main) and #86 (`release/1.x`) write the AST JSON as a
  stream and parse a file whose AST does not fit the remaining heap in a child process with more
  heap (`ASTGEN_LARGE_FILE_HEAP_MB`); a file that still does not fit is recorded as failed. CI is
  green on both branches.
- **D1.** The Vue, Svelte and Astro position fix is on both astgen branches (#83, #84), and
  AppThreat/atom#378 adds the `sfc-positions` fixture, which fails with atom-parsetools 1.10.6
  and passes with main. It gates in `js-parsetools-main`; #320 closes when the release pins the
  new 1.x version.
- **D2.** AppThreat/atom-parsetools#87 (main) and #88 (`release/1.x`) parse auto-accessors, with
  every other file's AST unchanged; AppThreat/chen#307 makes `ClassAccessorProperty` a class
  property (private ones included); atom#378 records calls in an accessor's initialiser.
- **D3.** #88 also brings the type budgets to `release/1.x`. On cdxgen at 90baa955
  `astgen -t ts` finishes in 95 s (it ran for more than 40 minutes) with one `type_budget` record,
  for `lib/cli/index.js`; the JSON and type maps of eight corpus projects (2,517 files) are
  byte-identical. The worker-stop race of D0 had no deterministic test.
- **D4.** Most typed misses were uses atom could see but did not record. chen#307 types the
  receiver of a member call on a field or a call result from the TypeScript 6 type map, keeps
  that type through type recovery, and tags every type reference; atom#378 records type
  positions as `decltype`, attributes members a project class inherits from a package class to
  that package, and follows `(await import('m')).f()`. The oracle now counts type-only imports,
  and juice-shop's `frontend/` dependencies are installed for the measurement. On the five
  typed-oracle projects recall moved from between 0.33 and 0.85 to between 0.56 and 0.91 (table
  in [callsites-status.md](callsites-status.md)), with precision equal or higher. The bar of 0.85 is met on angular-realworld and nestjs-realworld;
  on the other three the misses left are runtime built-ins (atom#379) and, on juice-shop, the
  untyped nested app (AppThreat/atom-parsetools#89, fixed afterwards by #90 and #91, which took
  juice-shop to 0.591), so the done condition's second branch holds.
- **D5.** chen#307 names the declaring type of an unresolved constructor reference, and atom#378
  puts method references to external methods in `usages` and `callsites`. Lombok's `@Slf4j`
  `log.info` already resolved under `types-only`. On the Java corpus the slices only gain
  method-reference records (webgoat 6, shiro 5).

The work was first implemented by one agent and then reviewed and largely redone by another,
which found an unformatted chen change, a committed local chen version, a path-duplication bug,
and a measurement that had skipped juice-shop's frontend dependencies and type-only imports. The
new suites pass on the Windows 11 test VM; the JavaScript fixtures used to cancel there, because
the suite looked for a bare `astgen`.
