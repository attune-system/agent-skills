# Attune agent skills

Reusable skills for authoring and reviewing Attune packs. Each skill directory is independently installable and includes its own examples and references. Attune is pre-production; verify version-sensitive behavior against the target server and CLI.

## Skills

| Skill | Use when |
| --- | --- |
| [attune-pack-architect](attune-pack-architect/SKILL.md) | Planning pack boundaries, manifests, dependencies, trust, release strategy, and specialist handoffs. |
| [attune-schema-author](attune-schema-author/SKILL.md) | Defining flat schemas, reusable `types/*.yaml`, defaults, secret fields, or schema references. |
| [attune-action-author](attune-action-author/SKILL.md) | Writing action metadata and entrypoints with stdin parameters and structured output. |
| [attune-mcp-agent-action-author](attune-mcp-agent-action-author/SKILL.md) | Running agents with execution-scoped Attune MCP access. |
| [attune-rule-author](attune-rule-author/SKILL.md) | Mapping trigger events to actions, configuring managed sensor placement, or debugging missing enforcements. |
| [attune-workflow-author](attune-workflow-author/SKILL.md) | Writing two-file workflows, transitions, iteration, approvals, and child permissions. |
| [attune-sensor-author](attune-sensor-author/SKILL.md) | Writing trigger contracts and managed sensors with stdin bootstrap, notifier updates, and fenced tokens. |
| [attune-queue-author](attune-queue-author/SKILL.md) | Defining durable queues, dispatch mappings, batching, idempotency, and acknowledgements. |
| [attune-cache-author](attune-cache-author/SKILL.md) | Choosing snapshot/live cache modes and designing namespace, publication, and retention contracts. |
| [attune-dashboard-author](attune-dashboard-author/SKILL.md) | Composing dashboard sources, filters, visualizations, layouts, and permission-aware previews. |
| [attune-runtime-author](attune-runtime-author/SKILL.md) | Defining custom runtime verification, interpreter setup, dependencies, and version entries. |
| [attune-policy-author](attune-policy-author/SKILL.md) | Designing execution scheduling limits and shared-resource concurrency, not RBAC grants. |
| [attune-permission-set-author](attune-permission-set-author/SKILL.md) | Defining scoped RBAC grants and purpose-specific runtime access, not scheduling limits. |
| [attune-cli-guide](attune-cli-guide/SKILL.md) | Using the CLI and MCP, including offline validation and release archives. |
| [attune-pack-test-reviewer](attune-pack-test-reviewer/SKILL.md) | Checking component contracts and release readiness before deployment. |
| [translate-to-attune-pack](translate-to-attune-pack/SKILL.md) | Converting external automation while documenting semantic differences. |

Start with the architect for a new pack or a pack-wide redesign. For an isolated component task, start with its specialist directly. Run the reviewer before publication.

### Organization and loading

The architect owns pack-wide decisions and routes work; it is not a combined metadata manual. Each component skill has a short authoring/review workflow and its own detailed references, loaded only for that task's relevant branches. Release packaging remains with the architect because it spans components.

`attune-schema-author` owns shared schema semantics. `attune-permission-set-author` owns grant/delegation semantics. Component skills explain their specific schema and permission attachments without repeating the full shared rules. Execution policies and permission sets have separate skills because scheduling admission and API authorization are different tasks.

Each skill's file links stay inside its directory so it can be copied independently. Related skills are named rather than linked through sibling filesystem paths. Install the related specialists when a task needs those branches; an isolated skill still carries its own core workflow and component reference.

## Documentation and verification baseline

Reviewed on 2026-10-29 against:

- The [published documentation](https://docs.attunedev.org/), particularly the [YAML reference](https://docs.attunedev.org/reference/yaml/).
- Attune source at `1949b92a635055070b2adc0d60ed10be6ab25be5`, platform `0.10.1`. The source checkout was clean apart from an unrelated untracked release note. Its tracked remote was one commit ahead with an unrelated crypto fix.
- Current local Python, JavaScript, and Java SDK source for managed sensor bootstrap and notifier support. Package publication and server/SDK compatibility must be checked separately.

This is a source and documentation audit, not a new platform test certification. The installed CLI was `0.8.0`, older than the audited source, so its availability was not treated as validation of newer contracts. Previous August test counts and references to uncommitted SDK remediations have been removed. They did not describe the current revision. The former link to a nonexistent `CLAIM-VERIFICATION.md` has also been removed.

The published docs lag some source contracts. In particular, the source supports reusable named types, stdin sensor bootstrap, immutable release tooling, and additional deployment metadata. Skills identify those differences and link to implementation sources where a public guide is missing. Source availability does not mean a gated feature is enabled: recorded runtime authority and some named-schema consumer paths still have deferred validation. Do not enable gates or claim production support from a YAML example alone.

### Maintenance

When updating these skills:

1. Record the Attune revision and inspect the relevant loader, DTO, validator, and runtime consumer. Use installed `--help` for CLI syntax.
2. Compare the corresponding docs.attunedev.org pages. Keep links to canonical guides; distinguish published guidance from newer source behavior.
3. Update examples, checklists, and conflicting statements together. Keep branch-specific detail in the skill's `references/` directory.
4. Install development dependencies with `python3 -m pip install -r requirements-dev.txt`, then run `python3 -m unittest discover -s scripts -p 'test_*.py'` and `python3 scripts/check_skills.py`. The checker validates the skill index, metadata/examples, and that local file links stay inside each independently installable skill. Use `--check-urls` to verify documentation pages and fragments over the network. CI runs the offline checks; network availability is not a pull-request gate.
5. Run `attune pack check` and declared tests for any generated pack fixtures. Report unavailable runtime or integration checks rather than copying historical pass counts.

## Shared conventions

- Use canonical manifest fields `label`, `conf_schema`, `meta`, and `tags`. Legacy aliases are fallback inputs, not fields to duplicate.
- Component input/output documents remain flat field maps. Reusable named type bodies describe one JSON Schema value, not another flat document.
- Prefer stdin JSON for actions. File delivery and YAML/dotenv remain implemented alternatives; dotenv is unsuitable for arbitrary structured or untrusted text.
- Execution API access is opt-in. `standard` covers scoped key/artifact operations and cache reads, not event creation, queue writes, signing, or broad API access.
- Configuration defaults, persisted operator overrides, executable releases, runtime permission selection, and human secret disclosure have different lifetimes. Preserve their boundaries.
- Explicit `enabled` values control declared state. Omission preserves operator enabled overrides on reload for supported components; it is not equivalent to writing `true`.
- `pack check` is offline structural validation. It does not prove deployment admission, worker availability, secret disclosure, or runtime behavior.

## Installation

Install each root skill directory, including its `references/` and optional `agents/` contents. Do not install this repository as one containing skill. Discovery locations depend on the agent host; common locations include `~/.claude/skills`, `~/.agents/skills`, and repository-local `.github/skills`.

From this repository root, link the skills into a chosen host's discovery directory:

```sh
SKILLS_SOURCE="$PWD"
target="$HOME/.agents/skills"
mkdir -p "$target"
for skill in "$SKILLS_SOURCE"/*/SKILL.md; do
  skill_dir=${skill%/SKILL.md}
  destination="$target/${skill_dir##*/}"
  if [ ! -e "$destination" ] && [ ! -L "$destination" ]; then
    ln -s "$skill_dir" "$destination"
  fi
done
```

Existing installations are left untouched. The optional `agents/openai.yaml` files provide labels and starter prompts; host permissions still control tool access.

OpenCode can also discover this repository through `skills.paths` in its configuration:

```jsonc
{
  "skills": {
    "paths": ["/absolute/path/to/agent-skills"]
  }
}
```
