# callsites: ground truth, corpus and gates

| | |
| --- | --- |
| Epic | EPIC_URL |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

Earlier slice work was judged against the previous release's output, so a regression that both
releases shared was invisible, and an agent tuning to the corpus could hide new false positives
behind a better total. Every other plan in the [callsites overview](callsites-overview.md) needs a
fixed answer key: for each project, every place its own code uses a third-party symbol, produced by
the language's own compiler or parser rather than by atom.

## Scope

In scope: oracles for every language atom reads, a pinned corpus, a language-neutral scorer, run and
profiling scripts, synthetic fixtures with hand-written answers, and the subset of fixtures that runs
in atom's CI.

Out of scope: redistributing third-party code. Projects are pinned by repository URL and commit
(APKs by URL and digest); the corpus manifest records licences.

## Approach

### Oracles

| language | oracle | typed uses | limits |
| --- | --- | --- | --- |
| JS/TS | TypeScript binder; `--typed` with `node_modules` uses the checker | yes, with dependencies installed | typed rows name the declaring package (`@types/express-serve-static-core`); the scorer maps lib and Node typings to builtins and neutralises undeclared packages |
| Python | `ast` binder with LEGB scoping, `global`/`nonlocal`, comprehension and class scopes | single-assignment `x = B(...)` and annotated parameters | no inference beyond that; Python 2 files are skipped |
| Java | javac attribution (`JavacTask.analyze`) with the Maven classpath | yes (receiver's static type) | multi-module projects need sibling modules installed; files javac cannot attribute are excluded |
| PHP | nikic/php-parser name resolution with Composer autoload maps | declared parameter/property types, single-assignment `new` | global aliases (`\Cache`) and extension functions not loaded |
| Ruby | Prism, with a constant index built from the gem sources in `Gemfile.lock` | single-assignment `X.new` | dynamically defined constants, ERB/HAML |
| C/C++ | clang JSON AST per translation unit from `compile_commands.json` | member calls on external classes | needs a compilation database; header→package by install prefix |
| JVM/Dalvik bytecode | `javap` / `dexdump` instruction owners with line tables | virtual/interface calls | app vs library boundary by package prefix; R8 obfuscation and inlining |

Every oracle writes the same row schema (file, line, col, module, package, builtin, member, kind, via,
certain). Declaration types, TypeScript type positions and uncertain rows are neutral: neither
credited nor counted as false positives.

### Scoring

The key is (file, line, package). A slice's module string is mapped to a package through the truth's
own module→package table (longest prefix), so the scorer has no per-language package tables.
Builtins are excluded on both sides by default. Reported per project: recall, precision, precision
without `via=type` records, recall by truth kind, precision by slice `via`, false-positive classes
(import line, other line of the same package, package not used in the file, beyond end of file),
samples of misses and false positives with source lines.

### Corpus

43 projects across JS/TS, Python, Java, PHP, Ruby, C/C++, Android APK and JVM bytecode, small,
medium and large per language, plus synthetic fixtures per language and a per-version syntax matrix
([callsites-language-versions.md](callsites-language-versions.md)).

## Deliverables

### D1. Publish the harness

The oracles, scorer and scripts live in a reviewed repository (decision needed: `atom/contrib/` or a
new `AppThreat/callsites-eval` repository), with the corpus manifest and a `fetch` script that
reproduces every pinned project. Done when a clean machine reproduces the baseline table.

### D2. CI fixtures in atom

Synthetic fixtures with hand-written expected records for every language become atom tests
(`<Lang>CallSitesTests`), so a pull request is gated without the corpus. Done when each language
adapter's shapes are covered by bad and good twins.

### D3. Typed oracles

JS: typed truth on every JS project with dependencies installed. Python: pyright or jedi inference
for typed uses beyond single assignment. Done when `via=type` precision can be measured on every
JS and Python project.

### D4. Complete Java and C/C++ truth

Multi-module Maven builds installed (or a classpath resolver that does not need it), Gradle
classpath export, and compilation databases for the C/C++ corpus. Done when no corpus project has
more than 5 % of its files in `errorFiles`.

### D5. Dynamic recall floor (optional)

Run test suites under tracing (Python `sys.monitoring`, a Java agent, Node's inspector) and require
every executed external call site to be in `callsites`. Needs no oracle.

## Risks and open questions

- Oracle mistakes become "slice bugs". Every oracle has a fixture with hand-written answers and is
  spot-checked against source; disagreements are triaged by reading code, not by trusting either.
- Agents may tune to the oracle. The gates are tests in the repositories; corpus numbers are a
  profile, not a target to iterate against.
- Where the harness lives (D1) and whether corpus project licences allow publishing recorded outputs.
