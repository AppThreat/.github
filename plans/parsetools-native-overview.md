# Native atom-parsetools (overview)

Status: in progress for v5.0.0. The native type map has landed behind `ASTGEN_TYPES=native`; what has
landed, what is in review and what comes next is in [parsetools-native-status.md](parsetools-native-status.md).
The measurements below come from a spike run on 2026-11-02 by AI agents on a 48 GB Apple silicon
laptop. Every number names its input and tool, so it can be rerun.

atom-parsetools today is a Node.js package with four commands. `astgen` parses JavaScript and
TypeScript (plus Vue, Svelte, Astro, Ember and HTML templates) with `@babel/parser` 8, Flow with
`hermes-parser`, and computes a type map with the TypeScript 6 compiler API
(`@typescript/typescript6`). `phpastgen` runs nikic/php-parser 5.8 inside a PHP runtime the user must
install. `rbastgen` runs the `ruby_ast_gen` gem inside a Ruby 3.4 or 4.0 runtime the user must install.
`scalasem` reads what the Scala compiler wrote (TASTy and SemanticDB) and moves into the binary as
well, keeping its small Java TASTy helper, which runs on the JVM a Scala project already needs.

This plan replaces the first three with one native binary that needs no Node, PHP or Ruby runtime,
keeps their JSON output contracts so chen's frontends do not change, and makes JavaScript and
TypeScript type generation an order of magnitude faster.

## Why

Type generation, not parsing, is where astgen spends its time and memory. Measured with astgen
1.10.6 (`/usr/bin/time -l`), parse only against parse plus types:

| project | files | parse only | with types | peak RSS with types |
|---|---|---|---|---|
| bulletproof-react | 390 | 0.6 s | 1.7 s | 340 MB |
| juice-shop | 648 | 2.3 s | 20.6 s | 2.0 GB |
| outline | 2,011 | 2.4 s | 24.3 s | 2.0 GB |
| cdxgen | 438 | 2.6 s | 67 min | 3.6 GB |

The type checker in TypeScript 7 is a Go port (typescript-go). A probe that applies the same node
rules, format flags and file set through both checkers (`typeprobe` in Go, `typeprobe6.mjs` on
TypeScript 6) gave:

| project | TS 6 probe | tsgo, 1 checker | tsgo, 8 checkers | identical type strings |
|---|---|---|---|---|
| bulletproof-react | 1.1 s | 0.33 s | 0.11 s | 89.5% of 12,755 keys |
| juice-shop | 5.8 s | 3.2 s | 1.8 s | 91.8% of 64,472 keys |
| outline | 14 s | 6 s | 2.2 s | 92.7% of 273,714 keys |

Almost all of the differing strings are the same type written differently. TypeScript 7 orders
union members and object members by a stable key (`"ADMIN" | "USER"` against `"USER" | "ADMIN"`)
and keeps the source's quote style for literal types. The one real gap is that tsgo returns no type
for identifiers inside type annotations (`Promise<T>`, `HTMLDivElement`), which is 4 to 9 percent
of the keys and needs `getTypeFromTypeNode` on the enclosing type reference instead.

Two more results matter. The stable ordering makes parallel type generation deterministic: the
8-checker run matched the single-checker run on 261,600 of 261,635 keys for outline, where astgen's
TypeScript 6 workers reorder unions between runs and the docs advise against them when output is
compared. And no runtime install: a Go or Rust binary removes the PHP and Ruby prerequisites that
users hit first today.

## The plans

| plan | what it covers |
|---|---|
| [parsetools-native-status.md](parsetools-native-status.md) | what has landed, measurements, decisions taken, known gaps, the next round |
| [parsetools-native-testing.md](parsetools-native-testing.md) | corpus, baselines, contract differs, type and callsites scoring, resource caps, determinism |
| [parsetools-native-js.md](parsetools-native-js.md) | type map on typescript-go, Babel-shaped AST from the tsgo parser, Vue, Svelte, Astro, Ember, HTML, Flow |
| [parsetools-native-ruby-php.md](parsetools-native-ruby-php.md) | rbastgen on the Prism C library, phpastgen without a PHP runtime |
| [parsetools-native-ship.md](parsetools-native-ship.md) | binaries, npm packaging, atom and chen integration, upstream reports |
| [parsetools-native.corpus.json](parsetools-native.corpus.json) | the inputs every gate runs on |

## Recommended design

Go hosts the binary. The deciding fact is that exact TypeScript types exist only in typescript-go,
and Go is the only language that can run that checker in the same process. In-process matters
because astgen asks for a type at nearly every node (61,000 to 274,000 queries per project above):
in process each query is a function call, and the checker's own length limit and node builder are
directly reachable when a type has to be cut short.

The binary is one command, `atom-parsetools`, with a subcommand per tool (`astgen`, `phpastgen`,
`rbastgen`, `scalasem`) that takes the flags the tool takes today. The old command names are not kept:
chen, atom and cdxgen are changed to call the subcommands, and the changelog lists every breaking
change (ship plan, S4). The subcommands write the same JSON:

- JavaScript and TypeScript: parse once with the typescript-go parser, check with its checker, and
  write the Babel 8 AST shape and `.typemap` files astgen writes today. One parser for both outputs
  removes today's need to keep Babel offsets and TypeScript offsets in step.
- Ruby: the Prism C library (MIT, no CRuby dependency) linked through cgo, with Prism's parser-gem
  translation ported to Go so the output stays in the `ruby_ast_gen` shape that ruby2atom reads.
- PHP: the choice between mago-syntax (Rust, PHP 7.0 to 8.6) behind a C ABI, a Rust sidecar, or
  keeping nikic in a PHP runtime is a decision below. No Go PHP parser covers PHP 8.3 to 8.5.

The Rust-centric alternative (oxc, swc for Flow, `ruby-prism`, mago in one Rust binary) has better
parsers for everything except types, and that is the problem: its only source of exact types is the
TypeScript 7.1 IPC API, which is a beta (7.1.0-beta, 2026-10-20), sends every query over msgpack,
and has no cancellation and no maximum length for `typeToString`. oxc also writes ESTree, not Babel,
and does not parse Flow. It stays the fallback if the shim risk below turns out too high.

## Order of work

1. Testing and baselines (all gates depend on them).
2. The type map on typescript-go, run next to today's Babel parse, behind `ASTGEN_TYPES=native`.
   This alone removes the slow part of astgen, needs no AST work, and can ship in a 1.x release.
3. The Babel-shaped AST from the tsgo parser, file kinds in order of use: TS/JS, JSX/TSX, Vue,
   HTML, Astro, Ember, Svelte. Flow follows its decision.
4. Ruby on Prism.
5. PHP after its decision.
6. scalasem in Go: build discovery, SemanticDB decoding and the evidence it derives, with the
   same report format; the Java TASTy inspector stays.
7. Packaging, then switching atom, chen and cdxgen to the native binary by default. Once every
   command is native, cdxgen no longer depends on the `@appthreat/atom-parsetools` npm package.

Steps 4, 5 and 6 do not depend on 2 and 3 and can run in parallel with them.

## Gates for changing the default

The native binary becomes the default for a language only when, on every corpus input:

- AST JSON is identical to the baseline after normalization, apart from differences on a reviewed
  allow-list that is part of the test suite.
- Type maps agree with the baseline on at least 95 percent of keys after normalizing member order
  and quote style, and every remaining difference class is reviewed.
- callsites recall and precision on the JS/TS scorer are not lower than the baseline.
- Wall time is at most half of today's and peak memory is not higher, both measured under caps.
- No input exceeds the caps (cdxgen included), and output is identical across checker counts and
  across two runs.
- It runs without Node, PHP or Ruby on Linux glibc and musl (x64, arm64), macOS (arm64, x64) and
  Windows (x64, arm64).

## Decisions for a maintainer

Decisions 1, 2 and 6 were taken as recommended (Go host, an AppThreat shim over `microsoft/TypeScript`
`tsc/`, TypeScript 7's order kept), and decision 5 as a Go port of the Svelte handling with no Node
fallback; see the status page. Decisions 3 and 4 are open.

1. Go as the host language, with Rust only where no Go parser exists (recommended), or Rust as the
   host with types through the TypeScript 7.1 API.
2. How to track typescript-go. The `microsoft/typescript-go` repository was archived on 2026-08-31
   and the code now lives in `microsoft/TypeScript` under `tsc/`, all in `internal/` packages.
   Options: reuse the oxc-project/tsgolint shim (pinned to the 2026-07-07 commit, six patches,
   about 446 KB of generated `//go:linkname` shims), or keep an AppThreat shim generated against
   `microsoft/TypeScript` as rslint has done since 2026-09-05.
3. PHP: mago-syntax through a C ABI, a separate Rust binary, or keep nikic in a PHP runtime.
4. Flow: port to swc's Flow parser (Rust), keep `hermes-parser` in a Node fallback, or drop Flow.
5. Svelte: port the template segmentation to Go, or keep a Node fallback for `.svelte` files.
6. Whether type strings keep TypeScript 7's member order (chen expectations change once) or are
   reordered to look like TypeScript 6 (more code, no precision gain). Keeping TypeScript 7's order
   is recommended.

## Risks

- **Internal API churn.** Every typescript-go upgrade can break the shim. tsgolint bumped about 30
  times between January and July 2026. Mitigation: pin, upgrade on a schedule, and gate each bump
  on the type map tests.
- **Memory.** tsgo used more memory than TypeScript 6 on outline (4.2 GB against 1.7 GB peak RSS).
  On cdxgen it kept every type it printed: the heap reached 11.6 GB after 222 of 784 files with
  printing, 480 MB without. Bounding this (dropping printer caches, recycling checkers) is
  required work, not tuning.
- **Unbounded types.** With `TypeFormatFlagsNoTruncation`, tsgo ignores `MaxTruncationLength`. An
  uncapped probe run froze the test machine for hours. Every type write is bounded and every test
  run is capped (see the testing plan).
- **Inputs that defeat both checkers.** astgen's 67 minutes on cdxgen come from one untyped
  `let components = [];` reassigned with `concat` in 25 sequential `if` blocks. Checking that shape
  grows exponentially with the number of blocks, in time for TypeScript 6 and in time and memory for
  TypeScript 7 (a generated 22-block file passes 3 GB). One JSDoc annotation brings cdxgen's file down
  to 0.3 s, but inputs cannot be relied on to have it, so type collection gets a per-file time
  budget, and the reproducer goes upstream.
- **Offsets.** Babel and chen use UTF-16 code unit offsets; Go strings use UTF-8 bytes. Every offset
  written is converted, and the tests include non-ASCII and astral characters.
- **cgo.** Prism and a Rust PHP parser need cgo, which complicates cross-compiling for musl and
  Windows. The ship plan builds each target natively in CI.
