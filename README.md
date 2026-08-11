# Attune Agent Skills

This repository contains reusable, self-contained agent skills for developing Attune pack contents. Each skill includes its required conventions inline and can be loaded from workspaces that do not contain the Attune repository.

## Verification baseline

Claims were last audited on 2026-08-11 against:

- Attune working tree based on commit `9ab78cf3b9184eaa0b1e2a3c3f48d1d2da5af054`, with the audited remediation changes still uncommitted. Full `cargo test --workspace --all-targets` and `cargo check --all-targets --workspace` pass; ignored database/integration tests are not part of the default test run. The core pack passes `pack check` and all 19 declared pack tests.
- Python SDK working tree based on commit `93814eacffad22207768b2ab9368865a1b1008a1`, plus uncommitted sensor remediation and a regenerated API client. All 91 pytest tests pass, including generated OpenAPI contract coverage in `test_api_client`, and both the sdist and wheel build successfully.
- JavaScript SDK working tree based on commit `15773a5a3767213f5d1ac005219174d5e06f4681`, plus uncommitted sensor remediation and a regenerated API client. All 61 tests pass, including deferred create/enable/update authoritative refetch coverage, as do lint, build, package smoke, generated-client freshness, and `npm audit` with 0 vulnerabilities.
- Java SDK working tree based on commit `02755db2d62683bfff0c5ca19427d4a4f5a596ba`, with uncommitted remediation that uses long rule IDs and targets supplied rules by default; all 31 JUnit tests pass, but notifier WebSocket lifecycle support remains unavailable and the incompatible legacy RabbitMQ consumer is disabled.
- This `agent-skills` repository had no commit at audit start; the skill files were untracked at that point.

See [CLAIM-VERIFICATION.md](CLAIM-VERIFICATION.md) for implementation sources, focused tests, commands, and the scope of each verification. Implementation-backed limitations in the skills describe the recorded revisions; re-check source and installed `--help` output when using another revision.

## Shared authoring rules

- Canonical manifest fields are `label`, `conf_schema`, `meta`, and `tags`. Pack check and registration normalize legacy `name`, `config_schema`, `metadata`, and `keywords` aliases; canonical values win and conflicting pairs are reported, so new manifests should not duplicate aliases.
- Implemented action parameter delivery is `stdin` or `file` with `json`, `yaml`, or `dotenv`. Prefer stdin JSON for new structured actions; dotenv is a limited scalar transport.
- The reserved `standard` execution permission covers scoped key and artifact operations and scoped cache reads. It is not broad API authority.
- Ordinary workflow tasks, `with_items` children, inherited action defaults, and native cache iteration reject named permission refs that were not delegated by the parent execution. The reserved `standard` ref retains its scoped behavior without requiring a named parent ref.
- JSON, YAML, and JSONL stdout parsing is best-effort. Parse failure does not turn an otherwise successful process into a failed execution, and malformed JSONL lines can be omitted.
- `pack check` is the primary read-only structural gate, not a registrar-equivalent simulation. Run `pack test` as well and use a permitted server smoke test when runtime or update behavior must be proven; failed pack tests return nonzero in every output format.
- `attune-mcp` stdio is the default for local and execution-scoped clients. HTTP defaults to `127.0.0.1:8090`, requires a separate inbound token through `ATTUNE_MCP_HTTP_BEARER_TOKEN` or `--http-bearer-token`, and refuses non-loopback listeners unless `--public-listen` is explicit.
- Key API routes admit access and execution tokens, then apply normal RBAC and owner constraints. Refresh, sensor, and worker tokens are rejected for key list/get/decrypt/create/update/delete operations.
- Managed sensors receive a startup snapshot in `ATTUNE_SENSOR_TRIGGERS` and the complete declared trigger list in `ATTUNE_SENSOR_TRIGGER_TYPES`; compatible sensors consume in-process lifecycle updates from `ATTUNE_NOTIFIER_WS_URL`. Ordinary rule changes do not restart an already-running sensor merely to refresh the snapshot.
- The recorded Python and JavaScript working trees support notifier WebSocket lifecycle updates and numeric rule-targeted emission by default. The Java working tree supports the same targeting default but only bootstraps the startup snapshot: it has no notifier WebSocket lifecycle updates, and its incompatible legacy RabbitMQ consumer is disabled. All require an explicit false targeting option for an intentional broadcast.

## Skill Set

| Skill | Directory | Use when |
| --- | --- | --- |
| `attune-pack-architect` | [attune-pack-architect](attune-pack-architect/) | Planning a complete pack, directory layout, refs, runtime/config strategy, and delegation to specialist skills. |
| `attune-action-author` | [attune-action-author](attune-action-author/) | Writing conventional action YAML and entrypoint scripts with correct schemas, stdin parameters, runtimes, and outputs. |
| `attune-mcp-agent-action-author` | [attune-mcp-agent-action-author](attune-mcp-agent-action-author/) | Writing AI agent actions that use execution-scoped Attune MCP access through `attune-mcp`. |
| `attune-rule-author` | [attune-rule-author](attune-rule-author/) | Connecting trigger events to action executions with correct rules, conditions, and `action_params` mappings. |
| `attune-workflow-author` | [attune-workflow-author](attune-workflow-author/) | Writing workflow actions and graph-only workflow YAML using current Attune workflow conventions. |
| `attune-sensor-author` | [attune-sensor-author](attune-sensor-author/) | Writing triggers, sensor YAML, and sensor implementations that emit events through the supported sensor interface. |
| `attune-cli-guide` | [attune-cli-guide](attune-cli-guide/) | Using the `attune` CLI and `attune-mcp` for pack upload/register, workflow upload, execution, artifacts, keys, auth, and MCP launch. |
| `attune-pack-test-reviewer` | [attune-pack-test-reviewer](attune-pack-test-reviewer/) | Reviewing and testing pack contents before upload, registration, or publishing. |
| `translate-to-attune-pack` | [translate-to-attune-pack](translate-to-attune-pack/) | Translating external orchestration resources into complete Attune packs. |

## Suggested routing

Start with `attune-pack-architect` for a new pack or large change. Use the more focused skills when the scope is already clear. Run `attune-pack-test-reviewer` before publishing or when several component types changed together.

## Agent portability

The standard `SKILL.md` frontmatter is sufficient for Claude, Codex, OpenCode, and GitHub Copilot; no extra metadata is required for discovery by those hosts. The optional `agents/openai.yaml` files provide OpenAI interface labels and starter prompts. Host-specific frontmatter fields are intentionally avoided, and `allowed-tools` is omitted so each host retains least-privilege control over tool access.

Install the root skill directories, not this containing directory as a single skill. Common user-level discovery paths are:

- Claude Code: `~/.claude/skills`
- Codex, OpenCode, and GitHub Copilot shared discovery: `~/.agents/skills`
- GitHub Copilot dedicated discovery: `~/.copilot/skills`

The equivalent repository-local paths are `.claude/skills`, `.agents/skills`, and `.github/skills`. From this directory, symlink every skill into any user-level or repository-local target with:

```sh
SKILLS_SOURCE=/home/david/Codebase/attune-system/agent-skills
install_attune_skills() {
  target=$1
  mkdir -p "$target"
  for skill in "$SKILLS_SOURCE"/*/SKILL.md; do
    skill_dir=${skill%/SKILL.md}
    ln -sfn "$skill_dir" "$target/${skill_dir##*/}"
  done
}

install_attune_skills "$HOME/.claude/skills"
install_attune_skills "$HOME/.agents/skills"
install_attune_skills "$HOME/.copilot/skills"

# Run from the consuming repository root when project-local discovery is preferred.
install_attune_skills "$PWD/.claude/skills"
install_attune_skills "$PWD/.agents/skills"
install_attune_skills "$PWD/.github/skills"
```

For claude.ai, upload each skill directory using its skill upload interface. OpenAI plugin packaging can wrap these skills later, but no plugin manifest is included now: the source layout is currently a set of root skill directories, and no published package version or repository URL has been established.

## OpenCode

Register this repository globally in `~/.config/opencode/opencode.jsonc`:

```jsonc
{
  "$schema": "https://opencode.ai/config.json",
  "skills": {
    "paths": ["/home/david/Codebase/attune-system/agent-skills"]
  }
}
```

OpenCode scans the path recursively for `SKILL.md`. Restart OpenCode after changing the configuration or any skill files.
