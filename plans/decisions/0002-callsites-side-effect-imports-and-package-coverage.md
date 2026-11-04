# 0002. callsites: side-effect imports, configuration references and package coverage

| | |
| --- | --- |
| Date | 2026-11-04 |
| Status | Accepted |
| Decided by | @prabhu |
| Plans | [callsites-ground-truth.md](../callsites-ground-truth.md), [callsites-core-js.md](../callsites-core-js.md) |
| Amends | [0001](0001-callsites-what-counts.md), the sentence on import lines |

## Context

A user ran evinse on akveo/ngx-admin (Angular with Nebular) and found that the callsites slice adds
occurrences but no new package: the components with occurrences were the same set with and without
it (cdxgen/cdxgen#4693, comment 6628861885). An AI agent repeated the run on ngx-admin and on the
13 apps in the frontend corpus (Angular, React, React Router, Vue, Nuxt, Svelte, Solid, Ember, Lit
and Astro) with atom-parsetools 1.10.6 and 2.0.0 (parsa). On every app callsites added no package
to the BOM's evidence. Both parsetools versions gave the same packages.

The packages the slice missed fall into three groups:

- side-effect imports such as `import 'zone.js'`, `import 'core-js/es6/reflect'` and
  `import 'classlist.js'` in `polyfills.ts`, which 0001 left out ("import lines are recorded by
  `kind` but are not uses on their own");
- test files and test configuration (`karma.conf.js`, `@testing-library/*`, `vitest`), out of scope
  by default under 0001;
- references from styles and framework configuration (`angular.json` styles and scripts, SCSS
  `@import '~bootstrap/...'`, Nuxt modules), which no slice reads.

cdxgen's own heuristics already give occurrences to most packages in the first and third groups,
which is why the package sets matched. The corpus did not show any of this, because it scores
records against TypeScript imports and holds four small frontend apps.

## Decisions

### Q1. A side-effect import is a use

An import that binds nothing (`import 'x'`, `import 'x/sub'`, a bare `require('x')` statement whose
value is not used) runs the module, so it is a use: one record at the import, with kind `import` and
the imported module. Imports that bind names stay as 0001 says. A record for a binding import exists
only where the bound name is used. Test files stay out of scope by default.

### Q2. Configuration and style references stay with cdxgen

callsites reads code only. References from styles, HTML and framework configuration stay with
cdxgen's heuristics. The package-coverage metric (Q3) counts them in their own column, so they
cannot hide a gap in what the code slice covers.

### Q3. Package coverage is a gate beside record scores

For every JavaScript and TypeScript corpus project, the harness lists the declared packages the
sources reference, split by channel: code imports (binding and side-effect), styles, framework
configuration and HTML. It reports three numbers for them: the share the callsites slice names, the
share with occurrences in the BOM after evinse without callsites, and the share with occurrences
with callsites. The code-channel share of callsites is a gate. The other two are reported. The JS
corpus gains the frontend apps listed in the ground-truth plan (D6).
