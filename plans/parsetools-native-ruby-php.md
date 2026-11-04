# Native atom-parsetools: Ruby and PHP

Not planned (2026-11-04). With the types-only scope in the [overview](parsetools-native-overview.md),
`rbastgen` and `phpastgen` stay as they are: Node commands that run `ruby_ast_gen` in the user's
Ruby 3.4 or 4.0 and nikic/php-parser in the user's PHP 8, with the gem bundle and the nikic tree in
the npm package's `plugins/` directory. ruby2atom and php2atom in chen read the same JSON as before.

An earlier version of this plan ported `rbastgen.js` and `phpastgen.js` to Go as `parsa rb` and
`parsa php` and embedded the plugins in the binary, to remove Node. The work items
(AppThreat/atom-parsetools#38, #39, #58, #59, #60, #62 and #63) are closed as not planned.

## Single executables of ruby_ast_gen

ruby_ast_gen's release workflow builds tebako single executables that carry CRuby, prism and the
gem. If they can replace the gem, rbastgen can run the executable on the platforms that have one, so
users there need no Ruby, and the npm package can stop carrying the gem bundle for those platforms.
Three spikes asked whether they can (AppThreat/ruby_ast_gen#16, #17 and #18). They were answered
in AppThreat/ruby_ast_gen#19 (merged 2026-11-04), with the numbers in `docs/sea-spike.md` of that
repository, and are closed.

What the spikes found, with tebako v2.8.68 and CRuby 4.0.7:

- Linux glibc and musl (x64, arm64) and macOS (arm64, x64) build in CI. On the syntax fixtures,
  railsgoat, maybe and mastodon the executables write the same AST JSON as the gem with prism 1.9,
  backend included; only `ruby_version` differs, and neither chen nor atom reads it. The glibc
  executables need glibc 2.31 (Ubuntu 20.04, Debian 11, RHEL 9), the macOS ones macOS 14.
- Each executable is 92 to 156 MB, against about 10 MB for the gem bundle, unpacks 86 to 147 MB
  into `~/.tebako` on its first run, and costs about 0.2 s and 100 MB of peak RSS more per run than
  the gem.
- A caller has to set `TEBAKO_HOME` and `TMPDIR` to writable directories that allow executing files,
  remove `RUBYOPT`, `BUNDLE_*`, `GEM_*` and `RUBYLIB` from the child environment, fall back to the
  gem when the bootstrap fails, and check `parser_backend` in the manifest, because a prism that
  fails to load falls back to the Ruby 3.3 grammar with exit status 0.
- Windows x64 builds only with the runtime's prism 1.8.1, because prism 1.9's native extension does
  not compile during a Windows press; it is not published. Windows arm64 cannot be pressed until
  tebako ships its press tools for that platform; the x64 executable runs there under emulation.

Open work in ruby_ast_gen: provenance, an SBOM and a signing decision before the first release with
executables (AppThreat/ruby_ast_gen#20), and the Windows executables (AppThreat/ruby_ast_gen#21).
atom-parsetools still pins ruby_ast_gen at 4ac8432, before the Windows input path fix from #19.

Not decided: whether rbastgen should run the executables. The spikes show that it can on the six
Linux and macOS targets; the cost is the download size and memory above, against removing the Ruby
requirement for users on those platforms. No atom-parsetools work item exists until that is decided.
