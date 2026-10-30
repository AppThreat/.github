# callsites for Ruby

| | |
| --- | --- |
| Epic | EPIC_URL |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

`usages` attributes none of the 4,265 external use sites in railsgoat, maybe and mastodon to a gem:
its Ruby names are file paths, `<empty>` and locals. No adapter can do better on today's graph:
constant receivers are lowered to `(<tmp-1> = Faraday::Utils).escape(i)` with
`methodFullName = <unknownFullName>`, `Faraday::Connection.new(url)` becomes an `initialize` call
with no name, and only project classes are resolved (with hints in `POSSIBLE_TYPES`). There is no
node for a constant reference.

## Scope

ruby2atom (chen), possibly ruby_ast_gen, then a `RubyCallSiteSource` in atom. Gem mapping stays in
cdxgen, which already knows gem namespaces.

## Deliverables

### D1. Constant references in the graph (chen)

A node (or `TYPE_REF`) for every constant read and constant path, lexically resolved against the
project's modules and classes (`Foo` inside `module Bar` is `Bar::Foo` when the project defines it).
Unresolved constants keep their written path.

### D2. Names for calls on constants (chen)

`Faraday::Utils.escape(i)` → `Faraday.Utils.escape`, `Faraday::Connection.new` →
`Faraday.Connection.new`; single-assignment locals from `X.new` carry the type for `x.get`.

### D3. Heritage and mixins (chen)

`class A < Faraday::Middleware`, `include Rack::Utils`, `extend Forwardable` as resolved inheritance
or mixin edges.

### D4. The Ruby adapter (atom)

Constant references and calls on constants not defined by the project, mixins and heritage;
`module` = constant path. Done at ≥ 0.80 recall and ≥ 0.95 precision on the Ruby corpus.

## Risks and open questions

- Rails autoloading (Zeitwerk) means most files have no `require`: project constants come from the
  file layout, which `ImplicitRequirePass` already models; verify it covers engines and `lib/`.
- Monkeypatched core and gem classes (`class String`, `module ActiveSupport`) make a constant both
  project and dependency.
- D1/D2 may need cpg2 schema changes (risks file) and a matching ruby_ast_gen release
  (AppThreat/atom-parsetools#29 tracks Ruby 4.1 syntax).
