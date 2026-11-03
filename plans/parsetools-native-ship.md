# Native atom-parsetools: packaging, integration and upstream

## S1. Binaries

One Go binary per target, `parsa`, with the subcommands `js`, `php`, `rb` and `scala` and no links
or wrappers under the old command names: Linux glibc and musl on x64 and arm64, macOS on arm64 and
x64, Windows on x64 and arm64. parsa uses no cgo, so one Linux runner cross-compiles every target
and the Linux binaries are static (one binary for glibc and musl); each binary then runs on its own
platform in CI. Builds are reproducible (`-trimpath`, pinned toolchains) and carry a post-build SBOM
and build provenance. The binary embeds the vendored `ruby_ast_gen` bundle and the nikic vendor tree
that `parsa rb` and `parsa php` run, and the Hermes parser built as WebAssembly that `parsa js` runs
for Flow files; the SBOM lists each with its version or commit.

## S2. Distribution

Every push to main pushes each target's binary to `ghcr.io` with oras (a tag per commit and a
moving `main` tag), so atom, chen and cdxgen-plugins-bin can test a build before it is released.
Each release attaches the binaries to the GitHub release with a `.sha256` file and build provenance.

cdxgen users get the binary through `@cdxgen/cdxgen-plugins-bin`, whose release workflow downloads
it from a pinned atom-parsetools release, checks the hash and bakes it into the platform packages, the
way it ships kosi (cdxgen/cdxgen-plugins-bin#164, used by cdxgen/cdxgen#4721). There are no separate
per-platform npm packages for atom-parsetools. Until a subcommand is native, the
`@appthreat/atom-parsetools` npm package keeps the Node implementation of that tool (today astgen
calls `parsa js --types-only` for its type maps). Once every subcommand is native, the npm package is deprecated
and consumers use `parsa` alone; cdxgen keeps the Svelte parsing it does in process by copying it
from `svelteAst.js` (cdxgen/cdxgen#4722).

## S3. atom and chen

chen and atom v5 work with both atom-parsetools 1.x (the Node commands `astgen`, `phpastgen`,
`rbastgen` and `scalasem` from `@appthreat/atom-parsetools` 1.10.6 or a later 1.x) and 2.x (`parsa`).
A user who installed 1.x from npm keeps a working setup after upgrading atom, and a 2.x release
that regresses on some project can be swapped for 1.x without downgrading atom.

- **Which one runs.** For each language, chen's `AstGenRunner` and its PHP, Ruby and Scala runners
  look for `parsa` (a configured path, then next to atom, then `PATH`) and call `parsa <language>`
  when the binary has that subcommand; otherwise they call the 1.x command. A setting
  (`--frontend-args parsetools=parsa|node`, with an environment variable of the same meaning) forces
  one or the other, and an error names what was looked for when neither is found.
- **Output differences.** chen reads both outputs: 1.x file names with `-i .` (the first path
  segment dropped, see the 2.0.0 changelog), with or without `.typespans` and
  `astgen_manifest.jsonl`, and type strings in either TypeScript's member order through
  `TypeStringNormalizer`. Anything 2.x adds stays optional.
- **Caches.** The parse cache fingerprint names the tool (`parsa` or the Node command) and its
  version, so switching between them never restores the other's output.
- **Tests.** The jssrc2cpg, php2atom and ruby2atom suites run against both in CI, with 1.x pinned
  to its last release.

`atom --version` and the perf report name the tool and version that ran. The container images ship
`parsa`, downloaded from the GitHub release with a hash check, and drop Node where nothing else
needs it; Ruby and PHP stay in the images that analyse Ruby and PHP projects. cdxgen's
`lib/inventory/atomUtils.js` and `lib/ecosystems/scalasem.js` are planned in the cdxgen
organisation.

## S4. Documentation and changelog

`CHANGELOG.md` in atom-parsetools lists every breaking change per release with what a consumer has to
change: the removed commands and their replacements (`astgen` to `parsa js`, `phpastgen` to
`parsa php`, `rbastgen` to `parsa rb`, `scalasem` to `parsa scala`), flags and environment variables
added, renamed or removed, output differences (type string spelling and ordering, newly typed nodes,
`.typespans`, AST differences on the reviewed allow-lists), platforms without a binary, and that Node is no longer needed (Ruby
and PHP still are for those languages). Each pull request that breaks something adds its entry.

Update the parsetools guides (`ASTGEN.md`, `PHPASTGEN.md`, `RBASTGEN.md`, `ENV.md`, `PERFORMANCE.md`,
`PACKAGING.md`, `TROUBLESHOOTING.md`) and atom's install docs: no Node to install, the new type
ordering, the per-file budgets and the diagnostics they write.

## S5. Upstream

- A TypeScript issue with the reduced cdxgen reproducer (the call that exhausts memory in both
  TypeScript 6 and 7).
- A TypeScript issue for memory kept per printed type, if D3 in the JS plan confirms it is the
  checker and not the shim.
- Shim fixes and missing exports offered back to tsgolint or rslint where AppThreat's shim adds them.
