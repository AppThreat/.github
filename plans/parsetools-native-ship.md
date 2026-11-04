# Native atom-parsetools: packaging, integration and upstream

## S1. Binaries

One Go binary per target, `parsa`, whose `js --types-only` subcommand writes the type maps astgen
asks for: Linux glibc and musl on x64 and arm64, macOS on arm64 and x64, Windows on x64 and arm64.
parsa uses no cgo, so one Linux runner cross-compiles every target and the Linux binaries are static
(one binary for glibc and musl); each binary then runs on its own platform in CI. Builds are
reproducible (`-trimpath`, pinned toolchains) and carry a post-build SBOM and build provenance
(AppThreat/atom-parsetools#72, #73).

## S2. Distribution

Every push to main pushes each target's binary to `ghcr.io/appthreat/parsa` with oras (a tag per
commit and a moving `main` tag), and each release attaches the binaries to the GitHub release with a
`.sha256` file, build provenance and the SBOM.

The `@appthreat/atom-parsetools` npm package keeps all four commands and does not carry `parsa`;
there are no per-platform npm packages for it (overview, decision 7, settled 2026-11-04). `parsa`
reaches users in two ways:

- cdxgen-plugins-bin: its release workflow downloads the binary from a pinned atom-parsetools
  release, checks the `.sha256`, and places it under `plugins/parsa/` in each platform package
  (cdxgen/cdxgen-plugins-bin#164); cdxgen points astgen at it (cdxgen/cdxgen#4721).
- Container images: atom's images download the binary from the GitHub release and check its hash
  (AppThreat/atom#361).

astgen looks for `parsa` through `ASTGEN_NATIVE_BIN`, next to `astgen.js`, on `PATH`, and in an
installed cdxgen-plugins-bin platform package, and falls back to TypeScript 6 when it finds none, as
it will after a plain `npm install` of atom-parsetools.

## S3. Default, atom and chen

astgen's default for `ASTGEN_TYPES` becomes `native` once the gates in the overview are met, with
TypeScript 6 kept as the fallback and `ASTGEN_TYPES=ts6` to choose it. `ASTGEN_VERSION` changes with
the default, so caches keyed on it are rebuilt.

chen and atom v5 work with atom-parsetools 1.x and 2.x. The AST is the same in both; only the types
differ, and chen already reads TypeScript 6 type maps, native type maps and `.typespans` when present
(AppThreat/chen#296, #298), with the engine in its parse cache fingerprint. What remains is to run
jssrc2cpg's tests against both releases in CI (AppThreat/chen#295). atom passes
`--frontend-args astgen-types=native|ts6` through (AppThreat/atom#363), reports the parsetools and
`parsa` versions in `atom --version` and the perf report, and its container images ship the `parsa`
binary with a hash check (AppThreat/atom#361). Node, Ruby and PHP stay in the images as today.

## S4. Documentation and changelog

`CHANGELOG.md` in atom-parsetools lists every breaking change per release with what a consumer has
to change: output names, environment variables, the type string differences of native type maps,
`.typespans`, the per-file budgets and the manifest. The parsetools guides (`ASTGEN.md`, `ENV.md`,
`PERFORMANCE.md`, `PACKAGING.md`, `TROUBLESHOOTING.md`) describe how astgen finds `parsa`, the
default and the fallback.

## S5. Upstream

- A TypeScript issue with the reduced cdxgen reproducer (the call that exhausts memory in both
  TypeScript 6 and 7).
- A TypeScript issue for memory kept per printed type, if D3 in the JS plan confirms it is the
  checker and not the shim.
- Shim fixes and missing exports offered back to tsgolint or rslint where AppThreat's shim adds them.
