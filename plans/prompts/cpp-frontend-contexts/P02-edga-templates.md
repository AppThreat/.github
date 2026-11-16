# P02: template identity and prototype bodies in edga

Read [00-RULES.md](00-RULES.md) first and follow it throughout. Then read D2, D3 and the first two risks in [cpp-frontend-contexts.md](../../cpp-frontend-contexts.md), and the P01 report in `~/work/cpp-frontend-contexts/reports/`.

Issues: {D2} (task A) and {D3} (task B). Branch: `cfc/p02-edga-templates` in edga, from `origin/feat/cpp-frontend-contexts`, or from the P01 branch if the prompt that hands you this one says it is not merged yet. Write the report to `~/work/cpp-frontend-contexts/reports/P02-report.md`.

## Background

Read in the EDG sources (`third_party/edgcpp`):

- `doc/source/templates.rst`, the section on templates in the IL: how entities generated from templates identify their template arguments, the template IL entry, and prototype instantiations.
- `src/il_def.h`: `a_template_arg`, the fields of routines, types and variables that point to their template and its argument list, and the `is_prototype_instantiation` bits.
- `doc/source/ext_intf.rst`: `--defer_parse_function_templates` and `--dep_name`, and the section "Dependent Name Processing".

Then read `src/edga_back_end.cpp` end to end: where routines, types and variables are collected (the `is_prototype_instantiation` filters near the top), how `templateInstance` is written today, how types get ids, and how unresolved calls are written. Read `docs/json-format.md` and `schema/edga-1.schema.json`.

## Task A: template identity (D2)

Write the `template` object and `templateArgs` for every routine, class, struct, union and variable generated from a template, as D2 describes. The template's id must be stable within a document and the same for every instance of one template; use the IL entry of the template, not a counter over instances. Arguments that are types carry the type id; non-type arguments carry their value as the front end prints it; template template arguments carry the template's qualified name. Explicit specialisations are instances of their primary template, with a flag saying they are explicit.

Update the JSON format reference and the schema, and the P01 template fixture's future expectations become the golden. Regenerate every existing golden, read each diff by hand, and list it under "Recorded expectations". Windows goldens cannot be regenerated on this machine; say so, and give the reviewer the list of Windows goldens that need regenerating in CI.

## Task B: prototype bodies (D3)

Export the prototype instantiation of each function template and class template member function defined under `--edga-root` that has no real instance in the unit, as D3 describes, behind the default-on behaviour and the `--edga-no-prototypes` option. Add a `dependent` type kind that names the template parameter, and write calls whose callee depends on a parameter as unresolved calls with the name as written.

Find out first what turning off deferral does. Run the P01 fixtures and the existing goldens with and without `--no_defer_parse_function_templates`, and run edga with and without it on the units of the abseil-cpp arm through edg2atom (use the P01 baseline run's units). Report how many units change exit status, how many new diagnostics appear and whether any real (non-prototype) routine changes. If real routines change, follow the first risk in the plan instead of turning deferral off, and report how many templates the fallback loses.

## Finish

Run edga's goldens with the schema check, then build chen's edg2atom against the new binary and run `edg2atom/test` and the memory-safety gates with edg2atom only: chen does not read the new fields yet, so nothing in chen's output may change. Any change there is a defect in this prompt.
