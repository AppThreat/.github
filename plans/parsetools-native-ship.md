# Native atom-parsetools: packaging, integration and upstream

## S1. Binaries

One Go binary per target with the commands `astgen`, `phpastgen` and `rbastgen` (subcommands, plus
the old names as links or small wrappers): Linux glibc and musl on x64 and arm64, macOS on arm64 and
x64, Windows on x64 and arm64. cgo (Prism, and Rust if mago is chosen) rules out simple
cross-compiling, so each target builds natively in CI, the Windows ARM64 build on the existing
Windows test VM until a hosted runner exists. Builds are reproducible (`-trimpath`, pinned
toolchains) and signed the way atom's other release files are.

## S2. npm packaging

`@appthreat/atom-parsetools` keeps its name and commands. The native binaries ship as per-platform
optional dependencies, the pattern esbuild and oxlint use, and the JavaScript entry points run the
binary when present and the Node implementation otherwise. `scalasem` stays in JavaScript. The Node
implementation stays for one minor release after the default switches, then is removed.

## S3. atom and chen

chen's `AstGenRunner` calls `astgen` from the path and reads the output directory, so the binary
works without code changes once installed. atom gets an option and an environment variable to force
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
