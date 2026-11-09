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

`parsa` ships as one npm package per binary, `@appthreat/parsa-linux-x64`, `-linux-arm64`,
`-darwin-x64`, `-darwin-arm64`, `-win32-x64` and `-win32-arm64`, each declaring its `os` and `cpu`
(the Linux binaries are static, so the Linux packages declare no `libc` and serve musl too).
`@appthreat/atom-parsetools` lists them as optional dependencies at its exact version, so npm
installs the one for the host, as `@typescript/native-preview` and esbuild do (overview, decision 7,
changed 2026-11-09). astgen looks for the binary through `ASTGEN_NATIVE_BIN`, next to `astgen.js`,
in the installed platform package, then on `PATH`, and falls back to TypeScript 6 when it finds
none (`--omit=optional`, linux-arm, riscv64, ppc64). cdxgen, atom, chen and their container images
need no setting: installing atom-parsetools 2.x is enough.

`parsa-release.yml` publishes the six packages with provenance through npm trusted publishing on
each release; `ci.yml` waits for them before it publishes atom-parsetools with the optional
dependencies, which are written at publish time and not kept in git. A maintainer of the
`@appthreat` scope runs `parsa/scripts/setup-npm-trusted-publishing.sh` once before the first such
release (AppThreat/atom-parsetools#94).

This replaces the earlier route through cdxgen-plugins-bin's platform packages and a download in
atom's images (cdxgen/cdxgen-plugins-bin#164, cdxgen/cdxgen#4721's `ASTGEN_NATIVE_BIN`, and the
image half of AppThreat/atom#361), which left anyone installing atom from npm on TypeScript 6.

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
