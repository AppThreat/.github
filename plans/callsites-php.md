# callsites for PHP

| | |
| --- | --- |
| Epic | https://github.com/AppThreat/chen/issues/239 |
| Owner | @prabhu |
| AI use | Auto |
| Corpus | [callsites-corpus.corpus.json](callsites-corpus.corpus.json) |

## Why

`usages` finds 0–19 % of external use sites on four PHP projects (DVWA, symfony-demo, koel,
bookstack); its PHP names are mostly scalar types and project classes. A measurement prototype on
symfony-demo reaches only 0.15 recall (0.93 precision) because the graph lacks what it would need:

- `vendor/` is parsed as project source (the PHP ignore rule has no `vendor`), so every Composer
  class is `isExternal=false` and a build takes 76–224 s and up to 13 GB;
- attributes (`#[ORM\Column]`, `#[Route]`) are not annotation nodes with resolved names (2 of 103);
- class-constant fetches (`Types::INTEGER`) have no resolved node (0 of 58);
- instance calls are `<unresolvedNamespace>\<code>` although PHP declares parameter, property and
  return types (0 of 111 typed calls);
- a class's TYPE_DECL line is its first attribute's line;
- trait `use` is not lowered, and a free function called inside a class is named `Ns\Class->f`.

## Scope

php2atom (chen) first, then a `PhpCallSiteSource` in atom.

## Deliverables

### D1. vendor is a dependency (chen, atom)

Shared with the performance plan D4: excluded by default, or loaded as external stubs.

### D2. Attributes and class constants (chen)

Attributes become annotation nodes with fully qualified names and their arguments; `X::CONST`,
`X::class` and static properties get nodes that carry the resolved class.

### D3. Declared-type recovery for instance calls (chen)

From parameter, property, promoted-constructor and return types, and single-assignment `$x = new X`,
name `$x->m()` as `Fq\Class->m`. Done with twins per source of type.

### D4. Positions, traits and free functions (chen)

TYPE_DECL at the `class` keyword; trait `use` lowered as inheritance-like edges; free functions keep
their namespace name.

### D5. The PHP adapter (atom)

Static calls, `new`, function calls, attributes, constants, heritage and typed instance calls whose
class is not the project's; `module` = FQN. Done at ≥ 0.85 recall and ≥ 0.95 precision on the PHP
corpus.

## Risks and open questions

- The PHP parser bundled with php2atom must accept PHP 8.4/8.5 syntax (property hooks, pipe
  operator): see [callsites-language-versions.md](callsites-language-versions.md).
- Laravel facades (`\Cache::get`) resolve through runtime aliases; record them as `via=name` or
  leave them out (policy decision).
- D2 and D3 may need new node properties in the cpg2 schema (release chain in the risks file).
