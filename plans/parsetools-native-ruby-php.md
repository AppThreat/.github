# Native atom-parsetools: Ruby and PHP

Decision (2026-11-03): the Ruby and PHP parsers are not rewritten. `ruby_ast_gen` (Prism through the
parser gem translation) and nikic/php-parser stay, running in the user's Ruby and PHP runtimes as
they do today. What moves to Go is the Node code around them, `rbastgen.js` (166 lines) and
`phpastgen.js` (2,114 lines), which become `parsa rb` and `parsa php`. Users still need Ruby 3.4 or
4.0 for Ruby projects and PHP 8 for PHP projects; they no longer need Node for either. ruby2atom and
php2atom in chen read the same JSON as before.

Ruby and PHP add no C or Rust code to parsa (no Prism C library, no Rust PHP parser), and their
output stays byte for byte what rbastgen and phpastgen write today.

## Ruby

### R1. parsa rb

Port `rbastgen.js` to Go: the command line, the Ruby version check (`RUBY_VERSIONS_NEEDED`), how the
vendored bundle is exposed through `GEM_PATH` (one gem repository per ABI directory, with prism and
racc taken from the runtime's default gems), how the `ruby_ast_gen` script is found inside the
bundle's git gems, the timeout, and the exit codes and messages. `ruby_ast_gen` itself and its
output, including the provenance fields (`parser_backend`, `generator_version`, `ruby_version`,
`magic_comments`, `encoding_scrubbed`, `truncated_nodes`), do not change.

### R2. Ruby parity

`test-fixtures/rbastgen-regression.js` runs against `parsa rb` unchanged, and the output is
byte-identical to rbastgen 1.10.6 on mastodon, maybe, railsgoat and the Ruby synthetic fixtures with
the same Ruby. Because the generator does not change, any difference is a bug in the port.

## PHP

### P1. parsa php

Port `phpastgen.js` to Go: file discovery and the exclusion rules (`DEFAULT_EXCLUDE`,
`--include-vendor`, the dependency directories, the PHP extensions), `--target-version` against
`SUPPORTED_TARGET_VERSIONS`, the PHP worker processes running `phpbatch.php` with the bundled
`php.ini`, chunking and concurrency, failure isolation, the manifest and diagnostics files, stale
diagnostics, and the provenance that reads the vendored nikic version from `installed.php`. The
parts that run inside PHP (`phpbatch.php`, nikic, `framework_facts`, `--max-depth` truncation,
encoding scrubbing) do not change.

### P2. PHP parity

The `test-fixtures/phpastgen-*` contract, snapshot and property-based tests run against `parsa php`
unchanged, and the output is byte-identical to phpastgen 1.10.6 on symfony-demo, bookstack, koel,
DVWA and the PHP synthetic fixtures with the same PHP.

## Shipping the Ruby and PHP sources

Today `build.sh` fills `plugins/` and the npm package ships it: `rubyastgen/` (the vendored pure-Ruby
gem bundle with `ruby_ast_gen`, about 10 MB) and the PHP parts (`nikic/`, `composer/`, `autoload.php`,
`bin/php-parse`, about 2 MB), with `phpbatch.php` next to `phpastgen.js`. Once the npm package is
deprecated these have to come with `parsa`, which embeds them:

- The release build packs exactly those Ruby and PHP files into one compressed tarball and embeds it
  with `go:embed` (about 1.2 MB compressed). Nothing else goes in: `plugins/log4j2.xml` is unused
  (atom has its own) and is deleted, and `php.ini` is not shipped today either. The tree is pure Ruby
  and PHP source, so every target embeds the same tarball; prism and racc come from the user's Ruby.
- A tarball rather than embedded files, because it is smaller in the binary and keeps what
  `go:embed` would drop: dotfiles such as `rubyastgen/.bundle/config`, and the executable bit on
  `bin/php-parse` and the gem executables.
- On the first `parsa rb` or `parsa php` run the tarball is unpacked into the user cache directory
  under a name that includes its hash (`<cache>/parsa/plugins-<sha256>`), into a temporary directory
  that is then renamed into place, so concurrent runs do not collide and a new `parsa` gets a fresh
  copy.
- `PARSA_PLUGINS_HOME` points at an unpacked copy instead, and `parsa plugins extract DIR` writes one,
  for read-only file systems, container images (unpack at image build time) and offline use.
- The tarball and its hash are listed in the post-build SBOM, with the gems and nikic as components.

### Single executables of ruby_ast_gen

ruby_ast_gen's release workflow builds tebako single executables that carry CRuby 4.0.6, prism and
the gem (AppThreat/ruby_ast_gen#13): Linux glibc and musl on x64 and arm64, and macOS on arm64 and
x64. Windows x64 is an experimental leg, Windows arm64 is not attempted, and no release with the
executables has been published yet. If they can replace the gem, `parsa rb` runs the executable on
the platforms that have one, users there need no Ruby, and parsa embeds the gem bundle only for the
platforms without one (or not at all once all six targets are covered). Three spikes decide this:
AppThreat/ruby_ast_gen#16 (parity, grammar coverage, size and start-up cost on Linux and macOS),
AppThreat/ruby_ast_gen#17 (Windows x64, retried on a current tebako) and AppThreat/ruby_ast_gen#18
(Windows arm64).
