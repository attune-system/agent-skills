---
name: translate-to-attune-pack
description: Converts StackStorm packs, Ansible/AWX content, Rundeck jobs, Airflow DAGs, n8n workflows, AWS Step Functions, OpenAPI integrations, and similar orchestration resources into working Attune packs. Use when translating external automation to Attune.
license: Apache-2.0
compatibility: An Attune repository and CLI are recommended for final validation
metadata:
  target: attune-pack
  validation: attune-pack-check
---

# Translate To Attune Pack

Translate external orchestration and integration resources into behaviorally equivalent, maintainable Attune packs. Produce working files and tests when the user requests a conversion, not only a migration plan.

Optimize for current Attune behavior rather than mechanical source-syntax conversion. Never claim full equivalence when retry, timeout, cancellation, concurrency, event delivery, credential, or state semantics differ.

## When To Use

Use this skill for source material such as:

- StackStorm packs, actions, runners, sensors, triggers, rules, and Orquesta workflows.
- Ansible collections, modules, roles, playbooks, and AWX job templates.
- Rundeck jobs, plugins, node sources, and webhooks.
- Airflow DAGs, operators, sensors, connections, and variables.
- n8n, Zapier, or similar integration workflows and trigger nodes.
- AWS Step Functions or other state-machine definitions.
- OpenAPI specifications, SDKs, webhook catalogs, and integration manifests.
- Bespoke automation bundles whose operations and events should become an Attune pack.

Do not use this skill for changes to Attune's Rust services unless a real platform gap blocks the pack conversion and the user explicitly asks to change Attune itself.

## Source Of Truth

When working in the Attune repository, retrieve current behavior before making strong claims. Prefer sources in this order:

1. Current Rust implementation and CLI behavior.
2. Working files under `packs/core/`.
3. `AGENTS.md` guardrails.
4. Globally available specialist skills when relevant:
   - `attune-pack-architect`
   - `attune-workflow-author`
   - `attune-pack-test-reviewer`
5. Other documentation, which may contain historical formats.

Inspect only the relevant sections. Do not copy stale examples when they conflict with implementation or the specialist references.

## Required Context

Infer what is safe to infer, state small assumptions, and ask only questions that block a correct implementation. Establish:

1. Source platform and version.
2. Source directories, manifests, exported definitions, schemas, or URLs.
3. Desired Attune pack ref and destination directory.
4. Behaviors and use cases that must be preserved.
5. Authentication methods and credential references, using redacted descriptions only.
6. Runtime, library, binary, and network requirements.
7. Event mode: webhook, polling, stream, schedule, queue, or manual execution.
8. Retry, timeout, cancellation, concurrency, ordering, and compensation requirements.
9. Test constraints, including whether external network calls are permitted.
10. Source license, attribution, and redistribution constraints.

Never request plaintext credentials. If a destination is not supplied, use `packs.dev/<pack_ref>` for local iteration unless repository conventions indicate another location.

## Translation Process

### 1. Inventory Before Editing

Inspect the complete source resource set and build a semantic inventory:

| Source resource | Kind | Inputs | Outputs/events | Dependencies | Side effects |
|---|---|---|---|---|---|

Identify shared clients, configuration, credentials, schedules, event payloads, workflow edges, retries, timeouts, concurrency, state, generated files, tests, and licensing. Do not start by translating files one at a time without understanding cross-resource references.

### 2. Classify Fidelity

Assign every source resource one status:

- `exact`: the target preserves material behavior directly.
- `adapted`: behavior is preserved through a different Attune structure.
- `partial`: useful behavior is generated, but a documented semantic gap remains.
- `manual`: a product or implementation decision is required.
- `unsupported`: no safe Attune representation exists.

Record important differences. A conversion with undisclosed `partial`, `manual`, or `unsupported` resources is not complete.

### 3. Map Semantics To Attune

Use this as a starting point, not a forced one-to-one mapping:

| Source concept | Typical Attune target |
|---|---|
| Action, operation, module, operator, or job step | Action |
| DAG, playbook, flow, or state machine | Workflow action |
| Poller, watcher, or long-running event listener | Sensor |
| Event type or webhook event contract | Trigger |
| Event-to-operation binding | Rule |
| Durable business work dispatcher | Work queue |
| Integration settings | Pack `conf_schema` and `config` |
| Credential or secret object | Attune Key requirement |
| Execution API authority | `permission_set_refs` |
| Shared client/runtime code | `lib/` and a root dependency manifest |
| Reconstructable external inventory snapshot | Data Cache when justified |
| Schedule | Core timer trigger plus rule or workflow |

Do not create a sensor merely because the source calls something a sensor. Determine whether it polls, blocks, receives a webhook, waits inside a workflow, or only expresses a condition.

### 4. Design The Target Pack

Use only directories the pack needs. A typical result may include:

```text
<pack-ref>/
|-- pack.yaml
|-- README.md
|-- LICENSE
|-- requirements.txt
|-- package.json
|-- lib/
|-- permission_sets/
|-- runtimes/
|-- triggers/
|-- actions/
|   |-- workflows/
|-- dashboards/
|-- queues/
|-- policies/
|-- rules/
|-- sensors/
|-- caches/
|-- tests/
```

Apply these target invariants:

- Pack refs are stable lowercase refs without dots.
- Use canonical manifest fields `label`, `conf_schema`, `meta`, and `tags`. Legacy aliases are normalized for imported manifests, with canonical values taking precedence and conflicts reported; do not duplicate aliases in new output.
- Component refs use `<pack_ref>.<component_name>`.
- Schema fields use Attune's flat per-field format for `conf_schema`, action `parameters`, action `output`, trigger `parameters` and `output`, and queue `item_schema`.
- Execution config is the flat parameter map, never `{ "parameters": {...} }`.
- Implemented action parameter delivery is `stdin` or `file` with `json`, `yaml`, or `dotenv`. Prefer stdin JSON for new structured actions. Use another mode only when justified and tested; dotenv is a limited scalar transport and environment-variable delivery is unsupported.
- Use core runtimes where possible and compare runtime names through Attune's normal aliases.
- Put Python and Node dependencies in pack-root manifests; runtime setup must not write into the pack directory.
- Use full refs for cross-component links and declare cross-pack dependencies.
- Preserve source attribution and compatible license notices for copied or adapted code.

### 5. Implement Actions

For each action:

- Define a stable input and output contract before adapting implementation code.
- Prefer a shared pack client under `lib/` when several actions use the same API, auth, pagination, error mapping, or retry behavior.
- Read one flat JSON document from stdin.
- Emit exactly the declared structured format on stdout and diagnostics on stderr.
- Treat JSON/YAML/JSONL worker parsing as best-effort: malformed output does not fail a zero-exit process and malformed JSONL lines can disappear. Use a real serializer and make tests parse the complete expected output.
- Exit nonzero for failures and redact sensitive values from every output path.
- Preserve idempotency and side-effect behavior where possible; document differences.
- Do not duplicate retries in the action and workflow unless layered retries are deliberate.
- Avoid shell command construction from untrusted values; use argument arrays in languages that support them.

### 6. Implement Events

Separate event contracts from event producers:

- Triggers define instance configuration and emitted payload schemas.
- Sensors declare the triggers they emit and must produce compatible payloads.
- Rules map `event.payload.*` fields into valid action parameters.
- Rule-specific sensor emission uses `trigger_instance_id: rule_<numeric-id>`; omit it only for an intentional broadcast. Do not use an SDK targeted helper until its emitted request is contract-tested.
- Polling sensors need bounded intervals, pagination, checkpoints or deduplication where required, backoff, graceful shutdown, and redacted logs.
- Webhook resources need a documented Attune ingress path; do not silently replace push delivery with polling.
- Scheduled resources should normally reuse core timer triggers rather than introducing a custom scheduler.

### 7. Implement Workflows

New workflow actions always use two files:

```text
actions/<name>.yaml
actions/workflows/<name>.workflow.yaml
```

The action YAML owns `ref`, metadata, flat input/output schemas, and `workflow_file`. It must not define a runner or entry point. The graph file contains graph fields such as `version`, `vars`, `tasks`, and `output_map`.

Use current workflow conventions:

- Tasks invoke actions.
- Transitions use canonical `next` entries with list-valued `do` targets.
- Conditions belong on transitions.
- Use `parameters`, `workflow`, `task`, `config`, `keystore`, `item`, `index`, and `system` namespaces.
- Pure `{{ ... }}` expressions preserve types; do not stringify arrays, objects, numbers, or booleans accidentally.
- Use `with_items` for arrays already in workflow context.
- Use `iterate_cache` for bounded, generation-pinned Data Cache traversal.
- Make retries, timeouts, failure paths, approval timeouts, concurrency, and compensation explicit.
- Use `permission_set_refs` only on tasks that need execution API authority.
- Full transition expressions may combine `succeeded()`, `failed()`, or `timed_out()` with result predicates. Invalid expressions fail closed, and all matching transitions fire independently.
- Define intentional behavior for empty `with_items` arrays, which complete successfully with an empty item result. Non-arrays are wrapped as one item; `batch_size > 1` makes `item` an array chunk and `index` the chunk ordinal.
- Include and preserve `cancellation_policy` when source cancellation semantics matter; visual-builder/API graph generation preserves it on round trip.
- Use normalized task results as `task.<name>.<field>` or `task.<name>.data.<field>`, never `task.<name>.result.<field>`.
- Taking a failure transition handles the source failure. Publish outputs on every terminal path and add a deliberate later failing task when the target parent must remain failed.

Compare source and target behavior for joins, parallel branches, cancellation, retries, catches, finalizers, compensation, and partial fan-out failure. Mark the conversion `partial` if material behavior cannot be represented.

### 8. Handle Config, Keys, And Permissions

- Put safe editable settings in flat `conf_schema` and safe defaults in `config`.
- Represent credentials as documented Attune Key requirements; never write real secrets into pack files.
- Mark any parameter that can carry sensitive material with `secret: true`.
- Use the reserved `standard` permission only for scoped executing action/pack key/artifact operations and cache reads.
- Create narrowly scoped named permission sets only when broader API access is required, and document why.
- Do not migrate broad source-platform roles mechanically into broad Attune execution permissions.
- Ordinary workflow tasks, `with_items` children, inherited action defaults, and native cache iteration reject named refs outside the parent execution snapshot. Ensure the parent is explicitly delegated every named child ref.
- Do not log authorization headers, cookies, execution tokens, decrypted keys, private payloads, or cache values.

### 9. Add Deterministic Tests

Test behavior and cross-component contracts, not only YAML syntax:

- Action success, invalid input, API failure, timeout, and output shape.
- Shared client authentication, pagination, retry, and error mapping with mocks.
- Sensor startup validation, deduplication/checkpoint behavior, backoff, and emitted payload shape.
- Trigger output to rule template to action input compatibility.
- Workflow references, graph targets, success/failure/timeout branches, type preservation, fan-out, and output mapping.
- Queue item-to-action mappings and acknowledgements when queues are used.
- Secret absence from stdout, stderr, fixtures, snapshots, and artifacts.
- File presence, executable bits where required, dependency manifests, and read-only pack assumptions.

Use supported pack test runners (`script`, `unittest`, or `pytest`) and `result_format: simple` unless the current implementation proves otherwise. Tests must not require real credentials. External calls must be mocked unless the user explicitly opts into integration tests.

### 10. Validate With Attune

Use Attune's validator as the primary read-only structural gate, not a generic YAML parser:

```bash
attune --output json pack check <pack-path>
```

`pack check` validates substantial pack structure, flat schemas, refs, duplicates, workflows, referenced files, local cross-component references, and canonical/legacy manifest normalization. It does not validate pack-test runner semantics, prove runtime availability, or cover every enum/update behavior. Read its diagnostics, fix errors and alias conflicts, and rerun. Generic YAML parsing is only a fallback when the Attune CLI cannot be built or run.

Then execute declared pack tests:

```bash
attune pack test <pack-path> --detailed
```

Failed pack tests return nonzero in table, JSON, and YAML output modes. Retain `status` and `failed` from machine-readable output for diagnostics.

If the CLI binary is not installed but this Attune repository is available, prefer the repository's normal CLI execution method or build the CLI. Do not substitute upload/register as the first validation step.

Only when an Attune environment is available and the user permits server changes, perform an upload or registration smoke test. Use `pack upload` for a local path when the API cannot see the host filesystem. Never describe a forced or skipped-test upload as proof that the pack is publish-ready.

Treat loader warnings as installation failures. A bad `workflow_file` can leave an unlinked runtime-less action, and removed standalone workflow definitions may require explicit cleanup because they are outside the recorded stale-component cleanup set. `runtime_deps` is persisted metadata but is not consumed by the recorded install preflight, so verify runtime availability separately.

## Deliverables

For a completed conversion, provide or create:

1. Source inventory and explicit assumptions.
2. Conversion matrix with source resource, Attune target, fidelity, differences, and follow-up.
3. Pack directory and component files.
4. Config, Key, permission, runtime, and dependency requirements.
5. Tests and safe synthetic fixtures.
6. README setup and representative usage.
7. Commands run and their pass, fail, skipped, or unavailable status.
8. Remaining manual or unsupported work.
9. A publish-readiness verdict.

Use this matrix format:

| Source | Attune target | Fidelity | Important differences | Follow-up |
|---|---|---|---|---|

Do not create a separate migration report file unless the user requests one; summarize it in the final response or the pack README where enduring operator guidance belongs.

## Completion Gate

A conversion is complete only when:

- Every inventoried source resource has a fidelity classification.
- Generated refs and referenced files are coherent.
- Action implementations match their declared stdin and output contracts.
- Sensor payloads match triggers, and rule mappings match action inputs.
- Workflow graphs preserve or explicitly document source behavior.
- Config, Keys, permissions, and dependencies are documented and minimal.
- Deterministic tests cover material success and failure paths.
- `attune pack check` passes, or inability to run it is explicitly reported.
- Pack tests pass, or unavailable runtime/environment requirements are explicitly reported.
- No secret or proprietary data was copied into generated content.
- All lossy, manual, and unsupported mappings remain visible to the user.

## Failure Modes

- Do not perform blind field-for-field translation.
- Do not confuse matching YAML shape with matching execution semantics.
- Do not invent Attune fields or copy old schema wrappers from stale documentation.
- Do not embed a new workflow graph in its action metadata file.
- Do not emit legacy workflow transitions when canonical `next` can represent the behavior.
- Do not wrap action parameters under a `parameters` object at execution time.
- Do not deliver action parameters or secrets through environment variables.
- Do not copy source credentials, connection exports, tokens, customer payloads, generated environments, or dependency caches.
- Do not create one action per source file when shared behavior belongs in a client library or workflow.
- Do not replace webhook or streaming semantics with polling without marking the conversion as adapted or partial.
- Do not assume retries, cancellation, concurrency, joins, or compensation are equivalent across engines.
- Do not use broad permission sets merely because the source platform used a broad service account.
- Do not declare success when `pack check` or tests failed, were skipped, or could not run.
- Do not copy upstream implementation code without checking license and attribution obligations.

## Example Invocations

```text
Translate this StackStorm pack into `packs.dev/github`. Preserve its actions, polling sensor, triggers, rules, and Orquesta workflows. Use mocked API tests and run attune pack check.
```

```text
Convert this OpenAPI specification and webhook catalog into an Attune integration pack. Generate a shared client, representative actions, trigger schemas, Key requirements, tests, and a fidelity report.
```

```text
Port this Step Functions state machine to an Attune workflow action. Identify service integrations that need new actions and report any differences in retry, catch, parallel, and cancellation behavior.
```
