# Native atom-parsetools: packaging, integration and upstream

## S1. Binaries

One Go binary per target, `atom-parsetools`, with the subcommands `astgen`, `phpastgen`, `rbastgen`
and `scalasem` and no links or wrappers under the old names: Linux glibc and musl on x64 and arm64, macOS on arm64 and
x64, Windows on x64 and arm64. cgo (Prism, and Rust if mago is chosen) rules out simple
cross-compiling, so each target builds natively in CI, the Windows ARM64 build on the existing
Windows test VM until a hosted runner exists. Builds are reproducible (`-trimpath`, pinned
toolchains) and signed the way atom's other release files are.

## S2. Distribution

Every push to main pushes each target's binary to `ghcr.io` with oras (a tag per commit and a
moving `main` tag), so atom, chen and cdxgen-plugins-bin can test a build before it is released.
Each release attaches the binaries to the GitHub release with a `.sha256` file and build provenance.

cdxgen users get the binary through `@cdxgen/cdxgen-plugins-bin`, whose release workflow downloads
it from a pinned atom-parsetools release, checks the hash and bakes it into the platform packages, the
way it ships kosi (cdxgen/cdxgen-plugins-bin#164, used by cdxgen/cdxgen#4721). There are no separate
per-platform npm packages for atom-parsetools. Until a subcommand is native, the
`@appthreat/atom-parsetools` npm package keeps the Node implementation of that tool (today astgen
calls the binary only for type maps). Once every subcommand is native, the npm package is deprecated
and consumers use the binary alone; cdxgen keeps the Svelte parsing it does in process by copying it
from `svelteAst.js` (cdxgen/cdxgen#4722).

## S3. atom and chen

Every consumer is changed to call `atom-parsetools <subcommand>`: chen's `AstGenRunner` and the
PHP, Ruby and Scala runners, atom's frontend wiring and container images, and cdxgen's
`lib/inventory/atomUtils.js` and `lib/ecosystems/scalasem.js`. The container images download the
binary from the GitHub release and check its hash, and drop Node, PHP and Ruby where nothing else
needs them. `atom --version` reports the atom-parsetools version that ran.

## S4. Documentation and changelog

`CHANGELOG.md` in atom-parsetools lists every breaking change per release with what a consumer has to
change: removed command names and their subcommand replacements, flags and environment variables
added, renamed or removed, output differences (type string spelling and ordering, newly typed nodes,
`.typespans`, AST differences on the reviewed allow-lists), platforms without a binary, and the
runtimes no longer needed. Each pull request that breaks something adds its entry.

Update the parsetools guides (`ASTGEN.md`, `PHPASTGEN.md`, `RBASTGEN.md`, `ENV.md`, `PERFORMANCE.md`,
`PACKAGING.md`, `TROUBLESHOOTING.md`) and atom's install docs: no runtimes to install, the new type
ordering, the per-file budgets and the diagnostics they write.

## S5. Upstream

- A TypeScript issue with the reduced cdxgen reproducer (the call that exhausts memory in both
  TypeScript 6 and 7).
- A TypeScript issue for memory kept per printed type, if D3 in the JS plan confirms it is the
  checker and not the shim.
- Shim fixes and missing exports offered back to tsgolint or rslint where AppThreat's shim adds them.
- Prism or mago issues for any parse difference found by the parity tests.
