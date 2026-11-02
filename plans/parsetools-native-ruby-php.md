# Native atom-parsetools: Ruby and PHP

For Ruby and PHP, the gain from going native is less about speed and more about install: users
need a Ruby 3.4 or 4.0 runtime for rbastgen and a PHP runtime for phpastgen today, and both fail in
ways that are hard to diagnose from atom's side. Both commands keep their JSON output, because
ruby2atom and php2atom in chen read it.

## Ruby

rbastgen runs the `ruby_ast_gen` gem (about 1,500 lines of Ruby), which parses with Prism through
Prism's translation to the `parser` gem AST and writes that AST as JSON, plus provenance fields
(`parser_backend`, `generator_version`, `ruby_version`, `magic_comments`, `encoding_scrubbed`,
`truncated_nodes`).

### R1. Prism through cgo

Vendor the Prism C library (ruby/prism, MIT; 2.1.0 released 2026-10-28) and call it through cgo.
Prism needs no Ruby runtime. Grammar versions are chosen per parse (`3.3`, `3.4`, `4.0`, `4.1`), which
replaces `--parser-target` and the closest-grammar fallback in `ruby_ast_gen.rb`. Prism 2.0 made
"nearest" the default version and changed several APIs, so pin 2.1 and test the version switch.

### R2. parser-gem translation in Go

Port Prism's `Prism::Translation::Parser` (the Ruby code that turns Prism nodes into `parser` gem
nodes) and `ruby_ast_gen`'s own JSON writer to Go, so the output stays byte-compatible. This is the
bulk of the Ruby work; the translation is a few thousand lines of Ruby. The alternative, teaching
ruby2atom to read Prism nodes directly, is a larger change in chen and is not planned for v5.

### R3. Ruby parity

Diff against rbastgen baselines on mastodon, maybe, railsgoat and the Ruby synthetic fixtures, then
score ruby2atom's slices with the Prism oracle. DSL files matched by basename (Gemfile, Rakefile,
Podfile and friends), magic comments and encoding scrubbing need their own fixtures.

## PHP

phpastgen (`phpastgen.js`, 2,114 lines, plus `phpbatch.php`) runs nikic/php-parser 5.8 (grammars 8.0
to 8.5) in PHP worker processes and adds its own data: `framework_facts` on nodes (superglobal reads,
declared attributes), depth truncation markers, encoding scrubbing, and the manifest and diagnostics
files.

### P1. Decision: parser

| option | PHP coverage | AST | cost |
|---|---|---|---|
| mago-syntax (Rust, MIT or Apache-2.0, 1.59.0 on 2026-10-25) linked through a C ABI | 7.0 to 8.6, property hooks, asymmetric visibility, pipe operator | mago's own | a Rust build in the Go binary's toolchain; a nikic-shaped writer |
| mago-syntax in a separate Rust binary | same | same | two binaries to ship |
| keep nikic in a PHP runtime | 8.0 to 8.5 | nikic | no change in install |
| a Go PHP parser | VKCOM/php-parser stops at 8.2 (last push 2023), z7zmey is dead since 2021 | | not viable |

The recommendation is to spike mago-syntax first: measure how far its AST is from nikic's on the PHP
corpus before committing, because the writer has to reproduce nikic's node names, attribute names
(`startLine`, `startFilePos`, ...) and child property names exactly.

### P2. nikic-shaped writer and phpastgen extras

Write mago's AST as nikic JSON, then port `framework_facts`, truncation at `--max-depth`, encoding
scrubbing, the exclusion rules, `--target-version`, and the manifest and diagnostics files. Name
resolution stays in php2atom, as today.

### P3. PHP parity

Diff against phpastgen baselines on symfony-demo, bookstack, koel, DVWA and the PHP synthetic
fixtures, and score php2atom's slices with the nikic oracle. The existing contract and
property-based tests in `test-fixtures/phpastgen-*` run against the native binary unchanged.
