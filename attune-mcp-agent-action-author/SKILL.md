---
name: attune-mcp-agent-action-author
description: Authors and reviews AI agent actions using execution-scoped Attune MCP over stdio. Use when launching agent harnesses inside executions or designing their permission sets, token handling, and output contracts.
license: Apache-2.0
compatibility: A compatible attune-mcp binary and agent harness must exist on the selected worker
metadata:
  target: attune-mcp-agent-action
---

# Attune MCP agent action author

Design the agent as delegated executable code. Use structured stdin, execution-scoped API authority, local stdio MCP, explicit tool capabilities, and secret-safe output. A token is an API boundary, not an operating-system sandbox.

Use `attune-permission-set-author` for reusable grant and admission design. This skill owns the harness's selection, token handling, tool-call behavior, and process boundary.

## Documentation

- [Actions and execution access](https://docs.attunedev.org/pack-development/actions/)
- [MCP setup](https://docs.attunedev.org/reference/mcp/)
- [Permissions](https://docs.attunedev.org/administration/permissions-and-rbac/)
- [Artifacts](https://docs.attunedev.org/administration/artifacts/)
- [Runtime environments](https://docs.attunedev.org/pack-development/runtime-environments/)

Inspect the target `crates/cli/src/bin/attune-mcp.rs`, worker token issuance, API authorization, and runtime-authority readiness. The MCP catalog and installed action inventory are revision-sensitive; discover them rather than copying a historical list.

## Workflow

1. Establish the fixed harness command/runtime, action refs, required operations, external/model credentials, input/output schemas, state paths, and worker isolation.
2. Map every API operation to the minimum permission set and target constraints. Keep local scoped access separate from external capabilities.
3. Implement the pack-local wrapper, token/binary preflight, stdin transport, cancellation, and output serialization.
4. Test allowed and denied tool calls with the intended execution token, not an admin profile. Verify malformed input, missing token/binary, timeout, and secret absence from transcripts/artifacts.

## Metadata

```yaml
ref: ops.triage
label: Triage
description: Run a fixed triage harness with scoped MCP access
runner_type: python
entry_point: triage.py
parameter_delivery: stdin
parameter_format: json
output_format: json
timeout_seconds: 900
reference_visibility: private
accesses_mcp: true
default_execution_permission_set_refs:
  - standard
  - ops.enqueue_follow_up
parameters:
  incident_id:
    type: string
    required: true
output:
  summary:
    type: string
```

Define `ops.enqueue_follow_up` rather than treating it as an installed set:

```yaml
ref: ops.enqueue_follow_up
label: Enqueue follow-up
scope: pack
grants:
  - resource: queue_items
    actions: [create]
    constraints:
      refs: [ops.follow_up]
```

The queue must exist, accept new items, and permit the producer under its reference policy. Pack-local scope is based on actual managing ownership, not a name prefix. External targets require explicit scope and admission/approval. Recorded runtime capability support remains gated in current source; publishing YAML does not bypass the existing delegated path.

`accesses_mcp` is a metadata marker, not authorization. Non-empty permission selection causes API-token issuance. Omission inherits action defaults where supported; explicit `[]` selects none. `standard` covers scoped key/artifact operations and cache reads only. Action execution, queue writes, inquiry operations, cancellation, event creation, and signing need appropriate named access. MCP itself intentionally has no direct event-emission tool.

Workflow tasks select their own refs. Existing delegated child creation checks the parent's named ceiling, including target defaults and iteration. Newer recorded invocation policy uses separately admitted target ceilings; do not assume this gated model is production-enabled or that foreign children inherit parent capability. Dynamic action targets require literal `allowed_action_refs` bounds.

## Process and token handling

The worker supplies `ATTUNE_API_URL`, conditional `ATTUNE_API_TOKEN`, `ATTUNE_EXEC_ID`, `ATTUNE_ACTION`, `ATTUNE_PACK_REF`, artifact/runtime directories, and conditional rule/trigger context. Processes start with a cleared environment. Runtime/model tooling credentials need an explicit approved source; they do not appear merely because the worker service has them.

Fail clearly if MCP is required but token, URL, or executable is missing. Common injected deployments provide `/opt/attune/agent/attune-mcp`; verify the actual worker mount/PATH. The Attune binary bundle does not install the agent harness or all language dependencies.

```sh
#!/bin/sh
set -eu
: "${ATTUNE_API_TOKEN:?Execution permission refs are required}"
: "${ATTUNE_API_URL:?Attune API URL is required}"
export ATTUNE_MCP_COMMAND="${ATTUNE_MCP_COMMAND:-/opt/attune/agent/attune-mcp}"
export ATTUNE_MCP_TRANSPORT=stdio
test -x "$ATTUNE_MCP_COMMAND" || {
  echo "attune-mcp executable is unavailable" >&2
  exit 1
}
# Replace this with the fixed installed harness. It must read the action's stdin.
exec my-agent-harness --mcp-command "$ATTUNE_MCP_COMMAND" --mcp-transport stdio
```

This is a wrapper pattern, not a complete harness. Keep the token in inherited execution context, never arguments, prompts, transcripts, MCP configuration files, or logs. CLI/MCP execution auth prefers `ATTUNE_API_TOKEN`; do not add saved user profiles, refresh tokens, or passwords inside an action.

Prefer stdin JSON and read the entire document before parsing. Stdout must contain the declared semantic result, not harness progress or raw JSON-RPC traffic. Use stderr for redacted diagnostics. Worker parsing/conformance warnings do not guarantee malformed output fails the execution; test it yourself.

## MCP protocol and transport

`attune-mcp` is a server, not an `event emit` or `queue enqueue` CLI. A client performs `initialize`, sends `notifications/initialized`, discovers `tools/list`, then uses `tools/call`. Inspect JSON-RPC errors and `result.isError`, not just the MCP process exit code. API mutations are not one transaction merely because the agent calls them in sequence.

Use stdio for execution-local clients. Shared HTTP is an explicit deployment choice: loopback by default, a distinct inbound bearer token, explicit public-listen opt-in for non-loopback, restricted networking, and TLS/proxy protection. Do not reuse the outbound execution token as inbound HTTP server auth.

MCP cache access is bounded. Discover support for namespace modes and operations; live caches do not support scans/iteration. Local pack checking in HTTP mode needs configured check roots. Tool discovery does not grant permission to call every tool.

## Arbitrary command bridges

If the installed core pack includes `core.run_agent_command`, inspect its current schema and implementation. Its `command` executes through `/bin/sh -c`, so execute permission is worker shell access. Use only fixed reviewed code. Never interpolate prompts, model output, event/queue/cache values, inquiry responses, or user parameters into that command string.

A pack-local fixed wrapper that reads structured stdin is safer. Action reference visibility and narrow execute grants should prevent general users or agents from selecting arbitrary shell-command actions. Execution tokens do not constrain shell/file/network access of the harness itself.

## State, secrets, and completion

Use execution-specific writable state, for example a private scratch directory under artifact staging keyed by `ATTUNE_EXEC_ID`. Set restrictive permissions and avoid cross-execution shared state. Registered artifact/version rows are required for durable files; arbitrary files under `ATTUNE_ARTIFACTS_DIR` are not automatically published.

Mark sensitive input/output fields, redact transcripts before persistence, and retain source-origin protections. Human read/decrypt of the destination does not bypass Key/event/queue source disclosure. Never log full tool payloads containing secrets.

Finish only after checking fixed command safety, compatible installed binaries, explicit input/output contracts, scoped grants, denied-call behavior, cancellation/timeout, state isolation, and secret-safe logs. Report unavailable runtime checks separately from successful static validation.
