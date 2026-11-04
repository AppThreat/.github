# Native atom-parsetools: JavaScript and TypeScript

astgen writes two things per source file: the Babel 8 AST as JSON and a `.typemap` that maps node
start offsets to type strings (and, in native runs, a `.typespans` keyed by `"start:end"`).
jssrc2cpg in chen reads both (it handles 164 Babel node types across about 8,800 lines of Scala).
This plan moves the type map to typescript-go. Babel keeps writing the AST.

Status (2026-11-04): D1 to D5 and D9 have landed in AppThreat/atom-parsetools#68, #69 and #71.
D6 to D8 and D10 described a native AST and are not planned (see the overview's scope); they are
kept below, shortened, as a record of what was found. See [parsetools-native-status.md](parsetools-native-status.md).

## D1. Go module and typescript-go pin

A Go module in atom-parsetools (`parsa/`) that links typescript-go through generated shims over its
`internal/` packages, the way oxc-project/tsgolint and web-infra-dev/rslint do. The source moved:
`microsoft/typescript-go` was archived on 2026-08-31 and the code is now `microsoft/TypeScript`,
directory `tsc/`, module `github.com/microsoft/TypeScript/tsc`, Go 1.27. The pin, the patch stack and
the shim generator are checked in, with a script that upgrades the pin and reruns the type map tests.

## D2. Type map on typescript-go

Port astgen's type collection (`createTsc` and `addType` in `astgen.js`) to Go, rule for rule:
call and new expressions (resolved signature, return type, the fallback to inferring a declaration's
return type), function-like declarations (return and parameter types, async fallbacks), property and
element access (also keyed at the name or argument), variable declarations (declared type, initializer
type, call fallback), binding elements, parameters, object literal properties, dynamic `import()`,
binary, conditional, logical, template, tagged template, yield, spread, delete, typeof and void
expressions, class declarations (construct signature return), enum members, and the default rule
with literal types widened. The scoring between candidate strings (`addTypeAtPosition`) and the
unresolved-type filter move over unchanged.

The spike's probe already shows the API differences to handle:

- `GetTypeAtLocation` returns no type for identifiers in type positions. Use `GetTypeFromTypeNode` on
  the enclosing type reference, which is what TypeScript 6 did internally.
- JavaScript functions print as their signature in tsgo, where TypeScript 6 printed
  `typeof setFromEuler`. chen's type name handling has to accept both during the transition.
- Union and object member order and literal quote style differ (see the overview decision 6).
- TypeScript 7 removed or changed compiler options (for example `baseUrl` handling,
  `moduleResolution: node10` and `classic`, and ES5 targets). Projects whose tsconfig still uses
  them must fall back to astgen's inferred defaults with a warning, not fail.

The first release runs this next to the existing Babel parse: astgen calls the native type map
binary when `ASTGEN_TYPES=native` is set and falls back to TypeScript 6 when the binary is missing.

## D3. Bounded type printing and memory

- Never pass `TypeFormatFlagsNoTruncation`; it disables `VerbosityContext.MaxTruncationLength`.
  Write with a 4,096 character limit, retry once with type aliases by name, then give up on that
  type and count it, the way astgen does today.
- Add a per-type budget on node builder work. tsgo has no cancellation token for printing, so this
  needs a small patch in the shim layer or a check on `approximateLength`.
- Release printing state. On cdxgen the checker's heap grew about 50 MB per file with printing and
  stayed flat without it. Find what holds the printed nodes and drop it per file, or recycle the
  checker every N files; measure both.
- Per-file wall time and memory budgets: a file that exceeds them gets no type map entries for the
  rest of the file and a diagnostic in the manifest.

## D4. Parallel checkers and project configuration

Use tsgo's checker pool, with each file handled by its own checker under the exclusive lock
(`GetTypeCheckerForFileExclusive`; the non-exclusive call races when two goroutines share a checker,
which the spike hit). Port `createTscProgramConfig`: tsconfig discovery, extended configs, project
references, the forced options (`allowJs`, `checkJs`, `noEmit`, `skipLibCheck`,
`resolveJsonModule`), automatic `@types`, and the rule that keeps files discovery left out of the
program. Default checker count follows `ASTGEN_TYPE_WORKERS`, now safe to turn on by default because
output does not depend on it.

## D5. The cdxgen case

The cause is known. `scanOnePathInner` in cdxgen's `lib/cli/index.js` declares `let components = [];`
without a type and reassigns it with `concat` in 25 sequential `if` blocks. Type checking an evolving
array in that shape grows exponentially with the number of blocks: a generated file with 20 blocks
takes 9.6 s to check in TypeScript 6 and 6.0 s and 690 MB in TypeScript 7.1, and 22 blocks pass 3 GB
in 7.1. With `/** @type {any[]} */` on that one declaration, `tsc` checks the whole cdxgen file in
0.3 s and 177 MB. Inputs cannot be expected to carry that annotation, so astgen needs a per-file
time budget on type collection (the existing budget covers only printing), today on TypeScript 6
and later in the native binary. The generated reproducer goes to the upstream report (S5).

## D6 to D8. Native AST, templates and Flow (not planned)

These sections planned a Babel-shaped AST converted from the tsgo parse in Go, the template handling
in Go, and Flow through Hermes's parser run as WebAssembly. They were dropped on 2026-11-04 in favour
of keeping Babel and `hermes-parser` in Node. What was learned, for anyone who reopens them:

- Matching Babel's JSON from tsgo's tree has to rebuild spans without leading trivia, Babel's
  comment attachment, `extra` fields, optional chains, JSX text and Babel's script or module choice,
  and the two parsers recover from syntax errors differently.
- tsgo recovers from Flow syntax instead of failing, so a Flow file gets a wrong tree rather than an
  error, and astgen reaches Flow not only with `-t flow` but through its parser fallback chain for
  any JavaScript file Babel rejects with the TypeScript plugin (`codeToJsAst`).
- `hermes-parser` is Hermes's C++ parser built as WebAssembly; its C++ side writes a flat buffer and
  about 4,200 lines of JavaScript turn that into ESTree and then Babel shape.

The work items were AppThreat/atom-parsetools#37, #53, #54, #55, #56, #57 and #75, closed as not
planned.

## D9. Command line and environment

`parsa js --types-only -i SRC -o OUT` reads the same `ASTGEN_*` discovery variables as astgen
(`docs/ENV.md`), with the same file discovery, ignore rules and test-file exclusion, so the type maps
cover the files astgen writes ASTs for. astgen keeps its own flags and starts `parsa` itself.

## D10. Syntax only Babel parses (not planned)

tsgo at the pinned commit does not parse two proposals astgen enables in Babel, `doExpressions`
(`let x = do { ... }`) and `exportDefaultFrom` (`export v from "mod"`), and recovers from them
instead of failing. With Babel writing the AST this matters only for the type map of such a file,
which tsgo computes on its recovered tree; how many nodes that leaves untyped or mistyped has not
been measured. AppThreat/atom-parsetools#76
is closed as not planned.
