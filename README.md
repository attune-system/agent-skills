# Attune Agent Skills

This repository contains reusable, self-contained agent skills for developing Attune pack contents. Each skill includes its required conventions inline and can be loaded from workspaces that do not contain the Attune repository.

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
