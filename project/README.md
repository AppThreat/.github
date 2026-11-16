# AppThreat project board

The AppThreat organization tracks its work on one GitHub project, described in [schema.json](schema.json). The fields, views and rules are the same as for the cdxgen organization and are explained in [cdxgen/.github project/README.md](https://github.com/cdxgen/.github/blob/main/project/README.md). Only this organization's repositories, area options and label maps differ.

## Built-in workflows

Status is kept current by the project's built-in workflows, which need no token. They cannot be enabled through the API, so an organization member with access to the project turns them on once, in the project menu under Workflows: Item added to project with Status set to Triage, Pull request linked to issue with Status set to In progress, and Item reopened, if offered, with Status set to Backlog. Item closed and Pull request merged are already on and set Done.

This organization is on the GitHub Free plan, which allows one Auto-add to project workflow, and a workflow targets a single repository. Configure it for `AppThreat/atom` with the filter `is:issue is:open`. That is one of the five linked repositories, so the other four are added by the backfill or by hand. Existing issues are added by the backfill, because auto-add skips items that already exist, see [Adding items automatically](https://docs.github.com/en/issues/planning-and-tracking-with-projects/automating-your-project/adding-items-automatically).

## Setup and backfill

The scripts live in [cdxgen/.github](https://github.com/cdxgen/.github/tree/main/project) and take this schema with `--schema`. From a clone of cdxgen/.github, with `gh` authenticated with the `project` scope:

```
node project/setup.mjs --schema <path to this schema.json>
node project/setup.mjs --schema <path to this schema.json> --apply
node project/backfill.mjs --schema <path to this schema.json> --apply
```

The first command only reads from GitHub.

## Optional sync

A sync workflow handles what the built-ins cannot: the `blocked` label, Area from labels, and pull requests to non-default branches. It needs the organization secrets `PROJECT_TOKEN` and `PROJECT_NUMBER` (the number is passed as a secret because a reusable workflow input cannot read secrets), because the workflow's automatic token cannot write to an organization project. It runs from each repository through the reusable workflow in cdxgen/.github, which fetches this schema through the `schema-repository` input. See [workflow-templates/project-sync.yml](../workflow-templates/project-sync.yml).

Because the workflow triggers on `pull_request_target`, a public repository also needs an Actions event policy that allows the event. GitHub now attaches a default policy to public repositories that blocks `pull_request_target` unless an Actions event policy that applies to the repository allows it, and a run the default blocks ends as a startup failure before any job starts. Create one policy per repository, scoped so that it covers only the sync workflow:

```
{
  "name": "Allow project-sync on pull_request_target",
  "enforcement": "active",
  "conditions": {
    "workflow_path": {
      "include": [".github/workflows/project-sync.yml"],
      "exclude": []
    }
  },
  "rules": [
    {
      "type": "restrict_action_events",
      "parameters": {
        "allowed_events": ["issues", "pull_request_target", "workflow_call"]
      }
    }
  ]
}
```

```
gh api repos/OWNER/REPO/actions/policies -X POST -H "X-GitHub-Api-Version: 2026-03-10" --input policy.json
```

The `workflow_path` condition limits the rule to the sync workflow, and it is what keeps the rest of the repository working: `allowed_events` is an allowlist for every workflow the policy covers, so a policy aimed at all workflows would block `push`, `pull_request` and every other trigger. The event list names each trigger the sync workflow uses: `issues` for the label events, `pull_request_target` for the pull request events, and `workflow_call` for the reusable workflow the starter calls. An organization owner can apply one policy to every repository at once by adding `"repository_name": {"include": ["~ALL"]}` to the conditions and calling `/orgs/OWNER/actions/policies` instead, which also covers repositories that adopt the starter later; creating it needs the `admin:org` scope. The API is described under [Actions policies](https://docs.github.com/en/rest/actions/policies).
