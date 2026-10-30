# callsites: syntax coverage across language versions

| | |
| --- | --- |
| Epic | EPIC_URL |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) (synthetic `versions/` fixtures) |

## Why

Projects in the wild mix language versions: CommonJS next to TC39 decorators, Python 2 scripts next
to PEP 695 aliases, PHP 5 code next to 8.4 property hooks, Java 8 lambdas next to record patterns.
A frontend that fails on one construct must not lose a file, and a slice must find external uses
inside every construct. A syntax matrix of 94 one-feature fixtures (JS/TS 27, Python 16, Java 17,
PHP 19, Ruby 15), each using a real package inside the construct and once outside it, measured:

- **Every frontend drops unparseable files silently**: exit 0 and nothing logged at default
  verbosity. astgen rejects the TC39 auto-accessor (`accessor x = …`, "';' expected after class
  property") and the whole file disappears, its other uses included.
- **JS/TS**: everything else, from CommonJS to `using`, import attributes, Flow, Vue `<script setup>`
  and Svelte 5 runes, reaches 1.00 recall and precision in `callsites`; `(await import('uuid')).v4()`
  is missed.
- **Python**: `except X` and `except* X` handler classes produce no node at that line (missed by both
  slices); everything from walrus to t-strings (3.14) and lazy imports (3.15) works. Python 2 files
  parse in atom.
- **Java**: method references (`StringUtils::trim`) are missed although the graph has resolved
  `METHOD_REF` nodes; Lombok `@Slf4j` `log.info` stays unresolved without delombok; records, sealed
  types, patterns, unnamed variables and text blocks all work.
- **PHP**: the 8.5 pipe operator becomes an opaque `Expr_BinaryOp_Pipe` node and loses every call
  on the line; property-hook bodies (8.4) have calls with no enclosing method; attributes leave no
  node; class-constant and enum-case fetches are resolved field accesses that a slice must read.
- **Ruby**: every construct up to 3.4's `it` parses; nothing resolves (see the Ruby plan).

## Scope

The frontends' parsers (astgen in atom-parsetools, the Python parser in pysrc2cpg, JavaParser in
javasrc2cpg, php-parser in php2atom, ruby_ast_gen/Prism in ruby2atom, CDT and EDG for C/C++), the
slices' handling of each construct, and the oracles' own parser limits.

## Deliverables

### D1. Report what was not parsed (chen, atom)

Every frontend records files it could not parse, or parsed only in part, with the parser's message:
a warning at default verbosity and a count in the atom (metadata) that slices and cdxgen can report.
Done when the auto-accessor fixture produces a visible warning and the file appears in a "not
parsed" list.

### D2. astgen: TC39 auto-accessors and the `(await import(x)).m()` shape (atom-parsetools, atom)

Parse `accessor` fields (JS and TS); resolve a member call on an awaited dynamic import.

### D3. Python handler classes (chen)

`except X` / `except* X` produce an identifier or type reference node at the handler's position.

### D4. Java method references and Lombok (atom, chen)

Slices read `METHOD_REF` nodes; Lombok-generated members (`log` from `@Slf4j`, accessors and
constructors) are modelled, or delombok mode is the default when Lombok is on the classpath.

### D5. PHP 8.4/8.5 (chen)

Lower the pipe operator into calls, give property-hook bodies a method, attributes as annotation
nodes (shared with the PHP plan).

### D6. Fixtures as tests (atom, chen)

The matrix fixtures become frontend tests (every file parsed, expected node counts) and slice tests
(expected records), so a parser upgrade that drops a construct fails CI. Extend the matrix to C/C++
standards (C11–C23, C++17–C++26 on CDT and EDG) and bytecode targets (Java 8–25 class files,
Kotlin, Scala 3, D8/R8 output).

## Risks and open questions

- Oracles have parser limits too: Python 3.15's `ast` cannot read Python 2; the Java oracle fails a
  whole tree when `module-info.java` is present (the classpath is not a module path); star imports and
  `importlib` uses are unscored. Fixtures that hit an oracle limit carry hand-written expectations.
- Parser upgrades (TypeScript, JavaParser language level, php-parser, Prism) can change node shapes;
  the fixture tests in D6 are the guard.
