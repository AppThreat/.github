# AppThreat project board

The AppThreat organization tracks its work on one GitHub project, described in [schema.json](schema.json). The fields, views, label maps and rules are the same as for the cdxgen organization, and are explained in [cdxgen/.github project/README.md](https://github.com/cdxgen/.github/blob/main/project/README.md). Only this organization's repositories, area options and label maps differ.

The scripts live in [cdxgen/.github](https://github.com/cdxgen/.github/tree/main/project) and take this schema with `--schema`. From a clone of cdxgen/.github, with `gh` authenticated with the `project` scope:

```
node project/setup.mjs --schema <path to this schema.json>
node project/setup.mjs --schema <path to this schema.json> --apply
node project/backfill.mjs --schema <path to this schema.json> --apply
```

The first command only reads from GitHub. The sync runs from each repository through the reusable workflow in cdxgen/.github, which fetches this schema from the `schema-repository` input. See [workflow-templates/project-sync.yml](../workflow-templates/project-sync.yml).
