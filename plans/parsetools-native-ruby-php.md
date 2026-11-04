# Native atom-parsetools: Ruby and PHP

Not planned (2026-11-04). With the types-only scope in the [overview](parsetools-native-overview.md),
`rbastgen` and `phpastgen` stay as they are: Node commands that run `ruby_ast_gen` in the user's
Ruby 3.4 or 4.0 and nikic/php-parser in the user's PHP 8, with the gem bundle and the nikic tree in
the npm package's `plugins/` directory. ruby2atom and php2atom in chen read the same JSON as before.

An earlier version of this plan ported `rbastgen.js` and `phpastgen.js` to Go as `parsa rb` and
`parsa php` and embedded the plugins in the binary, to remove Node. The work items
(AppThreat/atom-parsetools#38, #39, #58, #59, #60, #62 and #63) are closed as not planned.

## Single executables of ruby_ast_gen

ruby_ast_gen's release workflow builds tebako single executables that carry CRuby 4.0.6, prism and
the gem (AppThreat/ruby_ast_gen#13): Linux glibc and musl on x64 and arm64, and macOS on arm64 and
x64. Windows x64 is an experimental leg, Windows arm64 is not attempted, and no release with the
executables has been published yet. If they can replace the gem, rbastgen can run the executable on
the platforms that have one, so users there need no Ruby, and the npm package can stop carrying the
gem bundle for those platforms. Three spikes decide this: AppThreat/ruby_ast_gen#16 (parity, grammar
coverage, size and start-up cost on Linux and macOS), AppThreat/ruby_ast_gen#17 (Windows x64,
retried on a current tebako) and AppThreat/ruby_ast_gen#18 (Windows arm64).
