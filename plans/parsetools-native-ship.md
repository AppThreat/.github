# Native atom-parsetools: packaging, integration and upstream

## S1. Binaries

One Go binary per target with the commands `astgen`, `phpastgen` and `rbastgen` (subcommands, plus
the old names as links or small wrappers): Linux glibc and musl on x64 and arm64, macOS on arm64 and
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
per-platform npm packages for atom-parsetools. `@appthreat/atom-parsetools` keeps its name and
commands; its entry points run the binary when they find it (`ASTGEN_NATIVE_BIN`, next to the script,
on `PATH`, or in an installed plugins-bin package) and the Node implementation otherwise. `scalasem`
stays in JavaScript, so the npm package stays for it. The Node implementation of the other commands
stays for one minor release after the default switches, then is removed.

## S3. atom and chen

chen's `AstGenRunner` calls `astgen` from the path and reads the output directory, so the binary
works without code changes once installed. atom's and chen's container images download the binary
from the GitHub release and check its hash. atom gets an option and an environment variable to force
the native or the Node implementation for one release, the container images drop Node, PHP and Ruby
where nothing else needs them, and `atom --version` reports which implementation and versions ran.

## S4. Documentation

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
