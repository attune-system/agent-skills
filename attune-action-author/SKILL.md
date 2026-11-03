---
name: attune-action-author
description: Creates, reviews, and tests Attune action metadata and entrypoints with flat schemas, stdin parameters, structured outputs, timeouts, runtimes, and scoped API access. Use when authoring or reviewing conventional pack actions.
license: Apache-2.0
compatibility: Attune pack development; verify version-sensitive fields against the target CLI and server
metadata:
  target: attune-action
---

# Attune action author

Produce small actions with explicit input/output contracts, safe parameter transport, predictable exit behavior, and local tests. For workflows, sensors, or MCP agent harnesses, use the corresponding specialist skill.

For custom interpreter/setup definitions use `attune-runtime-author`; for reusable grant/delegation design use `attune-permission-set-author`; for queue metadata and dispatch contracts use `attune-queue-author`. Keep this skill focused on the action side of those contracts.

## Documentation

- [Writing actions](https://docs.attunedev.org/pack-development/actions/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)
- [Runtime authoring](https://docs.attunedev.org/pack-development/runtime-authoring/)
- [Runtime environments](https://docs.attunedev.org/pack-development/runtime-environments/)
- [Keys and secrets](https://docs.attunedev.org/administration/keys-and-secrets/)
- [Artifacts](https://docs.attunedev.org/administration/artifacts/)
- [Permissions](https://docs.attunedev.org/administration/permissions-and-rbac/)
- [Pack testing](https://docs.attunedev.org/pack-development/testing-and-release/)

When source is available, inspect `crates/common/src/pack_registry/loader.rs`, `schema_type.rs`, `value_schema/`, `crates/worker/src/runtime/`, and `crates/worker/src/executor.rs`. Docs can lag the source. In particular, current schema aliases and immutable contracts are newer than some public examples.

## Authoring workflow

1. Establish the pack/action ref, external API contract, input/output fields, runtime, dependencies, timeout, and intended side effects.
2. Define the metadata before implementation. Decide which fields may contain secrets and whether API access is actually needed.
3. Choose the implementation structure below, then implement parsing, boundary validation, serialization, failure handling, and cleanup. Make retried side effects idempotent where possible.
4. Test process decisions independently of Attune, plus the entrypoint's input/output and integration behavior: success, empty input, missing/invalid fields, API failure, timeout, output shape, and secret absence.
5. Run offline `pack check`, then declared pack tests. Run a server smoke test only when permitted; inspect the actual execution outcome.

## Implementation structure

Apply this structure to actions in every language, using the language's normal module, dependency, and resource-management conventions. Keep simple actions relatively self-contained in a single implementation file where practical. Split an action when its process rules, branching, or multi-step decisions become substantial enough to benefit from independent reasoning and testing; complexity, rather than a fixed line count, should drive the choice.

For complex actions, use the module named by `entry_point` as a thin Attune adapter. It reads action parameters and permitted process environment, resolves required Attune Keys and secrets with the declared authority, and performs the bulk of Attune API calls. It translates those inputs into explicit function arguments, calls functions imported from other modules, applies their results through Attune where needed, and handles action output and exit behavior. Keep substantive process decisions in the imported modules.

Keep that adapter orchestration directly in the declared entrypoint module so a reader can see which inputs, environment settings, credentials, connections, and process functions the action uses, and how cleanup and output happen. Do not make it a forwarding stub that calls a shared library's `main`, `run_pipeline`, or bootstrap helper which performs the real entrypoint work. In particular, do not move credential loading or environment discovery into a helper merely to shorten the entrypoint. SDK calls and focused utilities are appropriate, but keep the choice and sequence of configuration reads, credential resolution, resource construction, and process invocation explicit at the entrypoint. A shared pipeline should receive prepared inputs and dependencies rather than become the action's hidden entrypoint.

The adapter also owns authenticated resource setup and teardown: use the resolved configuration and credentials to open database connections, configure authenticated API sessions, or construct other service clients. Pass ready-to-use connections, clients, or narrowly scoped operations into the process functions rather than requiring those functions to retrieve credentials or assemble connections. Manage resource lifetimes around those calls with the language's context/resource scopes, `try`/`finally`, deferred cleanup, or equivalent mechanisms, including cleanup on failure. Keep process decisions such as when a transaction should commit or roll back in the process layer, while the adapter owns connection lifecycle mechanics.

Those modules should accept ordinary data values or explicit dependencies and return results or decisions. Avoid having them discover execution context through process environment, read Attune Keys, or use a global Attune SDK client. Keep decision logic pure where practical. When a process must interleave decisions and I/O, pass ready-to-use clients or narrowly scoped callbacks/interfaces so the process code can request operations without owning authentication, connection setup/teardown, or Attune API details. Do not introduce an abstraction framework for a small action.

Keep supporting modules available in the materialized pack or packaged executable using the language's existing layout, build, and runtime conventions. Importing, loading, or initializing a process module should not start an action or perform API calls; keep execution in the language's explicit entrypoint mechanism. Test complex process logic directly with ordinary inputs and explicit fakes, then test the adapter's context resolution, authenticated resource setup, cleanup on success and failure, API interactions, and output separately. Simple actions can retain their tests around the single module.

## Normal action metadata

```yaml
ref: example.fetch
label: Fetch
description: Fetch one resource and return its HTTP status
runner_type: python
entry_point: fetch.py
parameter_delivery: stdin
parameter_format: json
output_format: json
timeout_seconds: 120
reference_visibility: private
log_retention_policy: versions
log_retention_limit: 4
parameters:
  url:
    type: string
    required: true
  request_timeout:
    type: integer
    default: 30
    minimum: 1
    maximum: 60
  api_token:
    type: string
    secret: true
output:
  status_code:
    type: integer
  success:
    type: boolean
tags: [http]
```

Place this at `actions/fetch.yaml` and the implementation at `actions/fetch.py`. `entry_point` is relative to `actions/`, not the pack root. The working directory is normally the materialized pack directory. Treat it as read-only; put generated dependencies in runtime environments and durable outputs in registered artifacts.

New actions should set `runner_type` explicitly. Common normalized names are `shell`/`sh`/`bash`, `python`/`python3`, `node`/`nodejs`/`node.js`, and `native`/`builtin`/`standalone`. Runtime matching is case-insensitive. `bash` is an alias, not proof that a Bash interpreter is installed.

`runtime_version` constrains the main runtime. `required_worker_runtimes` declares additional runtimes needed on the same worker. Use `worker_selector`, `worker_tolerations`, and `worker_affinity` only for known placement requirements.

For release-packaged native or Java artifacts, current source supports typed `launch` metadata. Use exactly one of `entry_point`, `launch`, or `workflow_file`; verify the release builder and worker support together. A regular native `entry_point` must be an executable file of the correct architecture. Symbolic platform handlers are not portable pack entrypoints.

### State and reference policy

- Omitting `enabled` creates enabled metadata and preserves an existing operator enabled override on reload. Explicit values update the declared state. Disabled actions cannot be newly dispatched.
- `reference_visibility` is `public` by default, `private` for same-pack callers, or `restricted` for the owning pack plus `reference_allowed_pack_refs`. An allowlist belongs only with `restricted`.
- Action reference policy applies to rules, workflow tasks, and queues. It is separate from permission to execute the action. Ad-hoc metadata without pack context can reference only public actions.
- Do not assume omission has the same meaning across pack reload and API updates. In particular, workflow-upload APIs preserve omitted reference-policy fields on update, while pack declarations are desired metadata.

### Timeouts and retention

`timeout_seconds` must be positive. An execution snapshots its timeout from an explicit execution override, workflow task `timeout`, action default, then platform default. Changing defaults does not rewrite existing executions. Worker timeouts terminate the process group and finish with status `timeout`.

`log_retention_policy`/`log_retention_limit` govern runtime logs. Current source also reads `artifact_retention_policy`/`artifact_retention_limit` for action artifact defaults. Policies are `versions`, `days`, `hours`, or `minutes`; verify limits and effective platform defaults on the target revision.

## Parameters and schemas

Execution config is the parameter map itself, never `{"parameters": {...}}`.

- Prefer `stdin` with `json`; the worker writes one document and closes stdin. Read all stdin, not just its first line.
- `file` delivery exposes `ATTUNE_PARAMETER_FILE`. JSON and YAML preserve structured types.
- `dotenv` is scalar-oriented: objects flatten into dotted names, arrays stringify, null becomes an empty string, and empty objects emit no field. Shell quoting and multiline strings make arbitrary input fragile. Use JSON plus a real parser instead of `eval` or sourcing dotenv.
- Environment-variable parameter delivery is unsupported. Environment variables carry execution context and explicitly allowed runtime configuration, not general user parameters.

Use flat per-field `parameters` and `output`. Current loaders also accept `param_schema`, `out_schema`, and `output_schema` aliases, but reject duplicate spellings. Prefer `parameters`/`output` in pack files. Use the schema-author skill for named types, nested requiredness, defaults, or secret traversal. Do not put a generic JSON Schema wrapper around the flat document.

Mark secret inputs and outputs with `secret: true`. Secret annotations do not authorize reading Keys. The worker restores explicitly resolved secret values, not every system/pack/action Key. Encrypted Key input needs read and decrypt authority and a secret-marked destination. Secret fields cannot contain defaults, consts, enums, or examples in the current compiler.

## Output and failures

Supported `output_format` values are `text`, `json`, `yaml`, and `jsonl`. Keep structured stdout limited to semantic output; send diagnostics to stderr. Use a real serializer. Parsing remains best-effort: malformed JSON/YAML does not necessarily fail a zero-exit process, and malformed JSONL lines can be omitted. Current bound output conformance produces sanitized warnings rather than changing process success; JSONL validates each record separately. Tests must parse and validate output independently.

Parsed regular action output is under execution `result.data`. Workflow result views keep `data` and expose its fields as aliases. Immediate transitions can use `{{ result().data.field }}`; later tasks use `{{ task.fetch.data.field }}`. There is no extra `.result` below `task.fetch`.

Exit zero for successful work and nonzero for execution failure. If downstream logic must inspect an expected business outcome, return a stable field such as `success: false` deliberately rather than hiding infrastructure failure as success.

### Queue-dispatched actions

Use JSON output and pass queue item metadata explicitly through queue `action_params`, including `queue_item` or `queue_items`. Return one `queue_ack.items` entry for each leased numeric item ID, exactly once:

```json
{"queue_ack":{"version":1,"items":[{"id":1001,"status":"completed"},{"id":1002,"status":"retry","error":{"message":"upstream unavailable"}}]}}
```

Statuses are `completed`, `failed`, `skipped`, or `retry`. Missing, malformed, duplicate, unexpected, or omitted acknowledgements cause conservative retry handling subject to the queue's retry limit, default `0`. A valid acknowledgement can be honored for any terminal execution status. Test partial batches and duplicate side effects. See the [ack contract](https://docs.attunedev.org/administration/queues/#ack-contract).

## Execution context and API access

The worker supplies `ATTUNE_EXEC_ID`, `ATTUNE_ACTION`, `ATTUNE_PACK_REF`, `ATTUNE_API_URL`, `ATTUNE_ARTIFACTS_DIR`, `ATTUNE_RUNTIME_ENVS_DIR`, and parameter-delivery context. `ATTUNE_RULE`/`ATTUNE_TRIGGER` are conditional. `ATTUNE_API_TOKEN` exists only for non-empty execution permission refs.

Pack processes start with a cleared environment. Operator-controlled `worker.passthrough_env` selects exact extra names. Proxy, CA, package-manager, and cloud credentials do not automatically pass through. Setup and verification commands do not receive execution API tokens. Environment filtering is not filesystem or network isolation.

Use `default_execution_permission_set_refs` only when the action needs API access. `standard` permits scoped key/artifact operations and cache reads in the signed action/pack scope, including containing workflow scope for children. It does not grant event creation, queue writes, signing, or general action execution. For those operations, define and select narrow named grants. Do not infer authority from a token's presence or `accesses_mcp: true`.

Current worker-issued named delegation and newer recorded pack-runtime authority have different readiness. Verify the target admission path; do not assume a published set gives the caller or child authority. Recorded local/external policy bindings and approvals are source-backed but still have production gates. Never enable those gates to make a pack example pass.

The older delegated event-ingress branch admits execution tokens without the newer recorded per-trigger grant check. Do not treat that permissive branch as a scoped security guarantee or rely on it for portable behavior. Declare the intended Events/Create capability and verify the target consumer path.

Human plaintext disclosure is separate from execution input delivery. Reading sensitive results or logs requires destination read/decrypt rights plus rights on every recorded source origin. Changing a Key ref later does not authorize old values.

## SDK pattern

Use an SDK release compatible with the deployed API and pin it in the pack's dependency manifest. Avoid hardcoded versions in reusable guidance, but do pin real deployment dependencies.

| Runtime | Package | Helpers |
| --- | --- | --- |
| Python | `attune-sdk`, import `attune` | `attune.run_action`, `attune.context.client` |
| Node.js | `attune-sdk` | `runAction`, `context`; generated API functions in `attune-sdk/api_client` |
| Java | `org.attunedev:attune-sdk`, imports `io.attune` | `Attune.runAction`, `Attune.context().client()`; verify repository/release availability |

```python
#!/usr/bin/env python3
import attune


def main(name: str, count: int = 1):
    if count < 1 or count > 10:
        raise ValueError("count must be between 1 and 10")
    return {"greeting": f"Hello, {name}!" * count}


attune.run_action(main)
```

Declare Python dependencies in root `requirements.txt` and Node dependencies in root `package.json`, with compatible pins/lockfiles. SDK tests and package publication are separate from an action smoke test against Attune.

## Artifacts and completion

Create an artifact/version row before writing durable files to its allocated path. `ATTUNE_ARTIFACTS_DIR` is shared-volume storage or worker-local staging depending on transport; execution-linked files are finalized through the supported transport. An arbitrary file under that directory is only scratch output until registered.

Before finishing, verify refs/files, transport, flat schemas, timeout, placement, permission selection, parseable output, exit behavior, dependency installation outside the pack, and secret-safe logs. Report commands run and any runtime behavior not verified.
