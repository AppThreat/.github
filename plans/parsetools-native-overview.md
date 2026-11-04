# Native atom-parsetools (overview)

Status: in progress for v5.0.0. The native type map has landed behind `ASTGEN_TYPES=native`; what has
landed and what comes next is in [parsetools-native-status.md](parsetools-native-status.md).
The measurements below come from a spike run on 2026-11-02 by AI agents on a 48 GB Apple silicon
laptop. Every number names its input and tool, so it can be rerun.

atom-parsetools is a Node.js package with four commands. `astgen` parses JavaScript and TypeScript
(plus Vue, Svelte, Astro, Ember and HTML templates) with `@babel/parser` 8, Flow with
`hermes-parser`, and computes a type map with the TypeScript 6 compiler API
(`@typescript/typescript6`). `phpastgen` runs nikic/php-parser 5.8 inside a PHP runtime the user must
install. `rbastgen` runs the `ruby_ast_gen` gem inside a Ruby 3.4 or 4.0 runtime the user must
install. `scalasem` reads what the Scala compiler wrote (TASTy and SemanticDB).

Scope (2026-11-04): only the type map moves to native code. `parsa`, a Go binary built on
typescript-go, writes the `.typemap` and `.typespans` files that astgen asks it for, and makes type
generation an order of magnitude faster. Everything else stays in Node as it is: Babel and
`hermes-parser` write the AST, the template handling stays in JavaScript, and phpastgen, rbastgen
and scalasem do not change. chen's input does not change apart from the types, and Node stays a
requirement. An earlier version of this plan also replaced the AST, the Ruby and PHP wrappers and
scalasem with Go, to remove Node altogether; that was dropped because reproducing Babel's JSON
exactly from the tsgo parse could not be shown to be reliable, while the type map alone already
removes astgen's slow and memory-hungry part.

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
compared.

## The plans

| plan | what it covers |
|---|---|
| [parsetools-native-status.md](parsetools-native-status.md) | what has landed, measurements, decisions taken, known gaps, the next round |
| [parsetools-native-testing.md](parsetools-native-testing.md) | corpus, baselines, the type map differ, callsites scoring, resource caps, determinism |
| [parsetools-native-js.md](parsetools-native-js.md) | the type map on typescript-go; the sections on a native AST are kept as a record and not planned |
| [parsetools-native-ruby-php.md](parsetools-native-ruby-php.md) | not planned; the ruby_ast_gen single-executable spikes |
| [parsetools-native-ship.md](parsetools-native-ship.md) | binaries, how astgen finds `parsa`, the default switch, atom and chen, upstream reports |
| [parsetools-native.corpus.json](parsetools-native.corpus.json) | the inputs every gate runs on |

## Design

Go hosts the binary. The deciding fact is that exact TypeScript types exist only in typescript-go,
and Go is the only language that can run that checker in the same process. In-process matters
because astgen asks for a type at nearly every node (61,000 to 274,000 queries per project above):
in process each query is a function call, and the checker's own length limit and node builder are
directly reachable when a type has to be cut short.

astgen runs as today and starts `parsa js --types-only -i SRC -o OUT` for the type maps, with the
same `ASTGEN_*` discovery variables, then moves its output next to the AST files. When `parsa` is
missing, fails, times out or its output cannot be moved into place, astgen falls back to
TypeScript 6 with one warning. The `astgen`, `phpastgen`, `rbastgen` and `scalasem` commands keep
their names and flags.

## Order of work

1. Testing and baselines for the type map (done).
2. The type map on typescript-go, behind `ASTGEN_TYPES=native` (done).
3. Getting `parsa` to users: release binaries (done), and a way for astgen to find one after a
   normal install (ship plan, S2).
4. Native types as astgen's default, with TypeScript 6 kept as the fallback (ship plan, S3).
5. Releases of atom-parsetools 2.0.0, chen and atom with native types on by default.

## Gates for changing the default

Native type maps become astgen's default only when, on every JavaScript and TypeScript corpus input:

- Type maps agree with the baseline on at least 95 percent of keys after normalizing member order
  and quote style, and every remaining difference class is reviewed.
- callsites recall and precision on the JS/TS scorer are not lower than the baseline.
- Wall time is at most half of today's and peak memory is not higher, both measured under caps.
- No input exceeds the caps (cdxgen included), and output is identical across checker counts and
  across two runs.
- A normal install of atom-parsetools finds a `parsa` binary on Linux glibc and musl (x64, arm64),
  macOS (arm64, x64) and Windows (x64, arm64), and falls back to TypeScript 6 elsewhere.

## Decisions for a maintainer

Decisions 1, 2 and 6 were taken as recommended (Go host, an AppThreat shim over `microsoft/TypeScript`
`tsc/`, TypeScript 7's order kept); see the status page. Decisions 3 to 5 (the PHP parser, Flow and
Svelte in a native AST) no longer arise with the types-only scope. Decision 7 is open.

- Decision 1: Go as the host language, or Rust as the host with types through the TypeScript 7.1 API.
- Decision 2: how to track typescript-go. The `microsoft/typescript-go` repository was archived on 2026-08-31
   and the code now lives in `microsoft/TypeScript` under `tsc/`, all in `internal/` packages.
   Options: reuse the oxc-project/tsgolint shim, or keep an AppThreat shim generated against
   `microsoft/TypeScript` as rslint has done since 2026-09-05.
- Decision 6: whether type strings keep TypeScript 7's member order (chen expectations change once) or are
   reordered to look like TypeScript 6. Keeping TypeScript 7's order is recommended.
- Decision 7: how an npm install of atom-parsetools gets `parsa` (ship plan, S2): per-platform npm packages as
   optional dependencies, as `@typescript/native-preview` and esbuild do (recommended now that Node
   stays), or no npm packages, with users and images installing the binary from the GitHub release
   or cdxgen-plugins-bin.

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
  in a type map is converted so it lands on the node Babel wrote, and the tests include non-ASCII
  and astral characters.
- **Two parses per file.** Babel parses each file for the AST and tsgo parses it again for types.
  tsgo's parse is a small share of its checking time, and `.typespans` matches a type to a Babel
  node by its extent, so the two parsers only have to agree on where a node starts and ends.
