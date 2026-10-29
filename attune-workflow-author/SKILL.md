---
name: attune-workflow-author
description: Authors and reviews Attune two-file workflows, canonical transitions, joins, typed templates, iteration, inquiry waits, dynamic action ceilings, permissions, and placement. Use when creating or migrating workflow graphs.
license: Apache-2.0
compatibility: Verify inquiry, named-schema, and recorded-authority support against the target Attune revision
metadata:
  target: attune-workflow
---

# Attune workflow author

Produce action metadata plus a separate graph. Preserve execution semantics, not just YAML syntax. Establish inputs/outputs, action contracts, success/failure/timeout behavior, concurrency, cancellation, permissions, and deployment revision before writing the graph.

Use `attune-cache-author` for namespace mode/publication design and `attune-permission-set-author` for grants/delegation. This skill owns how workflow tasks consume their contracts, not the full cache or RBAC metadata manuals.

## Documentation

- [Writing workflows](https://docs.attunedev.org/pack-development/workflows/)
- [Composing actions](https://docs.attunedev.org/pack-development/composing-actions/)
- [Cache iteration](https://docs.attunedev.org/pack-development/cache-iteration/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)
- [Permissions](https://docs.attunedev.org/administration/permissions-and-rbac/)

Public workflow examples can lag current inquiry and managed-admission behavior. Check `crates/common/src/workflow/parser.rs`, `crates/executor/src/scheduler.rs`, `crates/executor/src/workflow/context.rs`, and [inquiry handling](https://github.com/attune-system/attune/blob/main/docs/workflows/inquiry-handling.md). `core.ask` and its intrinsic launch were removed in current source; use action-owned inquiries and `wait_for.inquiry`, not the old scheduler-intercept example.

## Two-file layout

`actions/process_items.yaml`:

```yaml
ref: example.process_items
label: Process items
description: Process a bounded list and report completion
workflow_file: workflows/process_items.workflow.yaml
timeout_seconds: 900
reference_visibility: private
parameters:
  items:
    type: array
    items: {type: string}
    required: true
output:
  processed:
    type: integer
```

`actions/workflows/process_items.workflow.yaml`:

```yaml
version: "1.0"
cancellation_policy: cancel_running
vars:
  processed: 0
tasks:
  - name: process
    action: example.process_one
    with_items: "{{ parameters.items }}"
    concurrency: 2
    input:
      item_id: "{{ item }}"
    timeout: 120
    retry:
      count: 2
      delay: 5
      backoff: exponential
      max_delay: 30
    next:
      - when: "{{ succeeded() }}"
        publish:
          - processed: "{{ length(parameters.items) }}"
output_map:
  processed: "{{ workflow.processed }}"
```

`example.process_one` must exist and accept `item_id`. This example leaves failures unhandled so they remain failures. Do not add a successful error-report task and assume the parent stays failed.

`workflow_file` is relative to `actions/`. The wrapper owns metadata and flat `parameters`/`output`; omit `runner_type`, `entry_point`, and worker parameter/output transport fields. Graph-only files should not repeat the wrapper. If maintaining duplicated graph schemas, current loader reconciliation requires matching bodies. Prefer one source.

Use `parameters`/`output` for new pack schemas. Current schema aliases are accepted but duplicate spellings are rejected. Named types remain single-value schemas inside flat field maps; use the schema-author skill when needed.

Omitted `enabled` preserves operator state on reload. Reference policy is public/private/restricted with an allowlist only for restricted. Cross-pack tasks must satisfy the target action's reference policy independently of execution grants. Workflow upload API updates preserve omitted reference-policy fields; explicit `reference_allowed_pack_refs: []` clears that allowlist. Pack reload is not the same update path.

## Tasks, transitions, and joins

New tasks invoke actions and use `input` as a flat parameter map. Prefer canonical `next` entries:

```yaml
next:
  - when: "{{ succeeded() and result().data.approved == true }}"
    publish:
      - approved: true
    do: [deploy]
  - when: "{{ succeeded() and result().data.approved != true }}"
    do: [report_rejection]
  - when: "{{ failed() }}"
    do: [handle_failure]
  - when: "{{ timed_out() }}"
    do: [handle_timeout]
```

- All matching transitions fire independently. Ordering is not first-match. Use mutually exclusive predicates unless fan-out is intended.
- Omitted `when` is unconditional. Invalid expressions fail closed.
- `publish` is a list of variable/value mappings into `workflow`; pure templates preserve their JSON types.
- `do` should be a list of existing task names, including a one-element list for one successor.
- No successor means a terminal task. A failure transition can mark its source failure handled. If the parent must fail after cleanup/reporting, route to a deliberate nonzero-exit terminal action.
- `join: N` is a numeric inbound-completion barrier; without it, a task can become ready after any predecessor. Do not copy unsupported string `join: all` or assume a merge waits for every branch. Test branch overlap and joins.
- Cycles need a terminating condition. Wait-guarded tasks cannot be in cyclic regions.
- Legacy transition names can be normalized by some parser paths, but new output and direct API payloads should use `next`, not task-level branching or legacy parallel containers.

Common task fields include `delay`, `retry`, `timeout`, `trace_tag_template`, permission selection, and worker placement. `timeout` is a child-execution override in seconds and can be a positive integer or a pure expression resolving to one in current source. It takes precedence over the child action default; it is not the CLI watch timeout. Timeouts are terminal status `timeout`, match `timed_out()`, and may retry when attempts remain.

`cancellation_policy: allow_finish` suppresses new work and lets running children finish. `cancel_running` cancels running children too. Preserve the field across visual-builder/API round trips; neither choice rolls back external side effects.

## Template context

| Namespace | Use |
| --- | --- |
| `parameters` | Immutable workflow inputs |
| `workflow` | Variables initialized by `vars` or written by transitions |
| `task` | Named completed result views |
| `config` | Owning pack configuration, not rule-style `pack.config` |
| `keystore` | Authorized Key values, with secret-origin tracking |
| `item`, `index` | Current iteration value and zero-based ordinal |
| `system` | System-provided workflow context |
| `inquiry` | Inquiry wait state keyed by guarded task name |

For a regular action, use immediate `{{ result().data.field }}` or later `{{ task.fetch.data.field }}`. Parsed data fields also have flattened aliases. Do not add `.result` under `task.fetch` or assume native prerequisite state has the same shape as worker output.

Whole-value `{{ ... }}` expressions preserve objects, arrays, booleans, numbers, and null. Mixed text is a string. Rendered values must satisfy the retained contract. Authoring previews and current mutable schemas do not replace the contracts captured by existing executions/retries. Avoid legacy `vars`, `tasks`, and bare-variable aliases in new templates.

## Array and cache iteration

`with_items` normally resolves to an array. The implementation wraps non-arrays as one item, so validate inputs rather than relying on that coercion. Empty arrays complete successfully with an empty item result. Default concurrency and batch size are `1`.

With `batch_size: 1`, `item` is one element and `index` its ordinal. Larger batches make `item` an array chunk and `index` the chunk ordinal. Use bounded concurrency and idempotent children. Do not assume `result()` after iteration is a stable aggregate of every child result; use an explicit collection/output mechanism when needed.

Use native cache iteration only for snapshot namespaces:

```yaml
- name: cached_users
  action: example.process_user_batch
  iterate_cache:
    owner_type: pack
    owner_ref: example
    namespace: users
    generation: active
    require_fresh: false
    page_size: 100
  batch_size: 25
  concurrency: 4
  permission_set_refs: [standard]
  input:
    users: "{{ item }}"
    batch_index: "{{ index }}"
```

`generation` defaults to `active`; `require_fresh` to false; page size to `100`; task batch size/concurrency to `1`. Use page/batch sizes in `1..1000`. A literal generation selector is a string in graph metadata, for example `generation: "42"`; pure templates may resolve an ID. Owner defaults to the workflow pack; action/sensor owners require their refs. Cross-owner reads need admitted named grants.

One cache entry has `external_id`, `value`, `source_updated_at`, `source_checksum`, and `size_bytes`. At batch size one, `item` is that object; at larger sizes it is an array of entry objects. There is no `item.entries` or `item.generation_id` wrapper.

The iterator pins one generation and persists scan/child progress. Resume retains the generation; retries reuse persisted inputs. Errors stop further discovery and settle in-flight children before the failure transition. Live namespaces cannot scan or use `iterate_cache`. It is mutually exclusive with `with_items`; keep concurrency outside `iterate_cache`. Do not log/publish cache values or external IDs unintentionally.

## Inquiries and durable waits

An action creates an inquiry through the API, delivers its provider message, and returns the inquiry ID. A successor can wait without creating its child execution first:

```yaml
- name: deploy
  action: example.deploy_if_approved
  wait_for:
    inquiry: "{{ task.request_approval.data.inquiry_id }}"
  input:
    approved: "{{ inquiry.deploy.response.approved }}"
```

The producer `request_approval` must run first and return `inquiry_id`. The guarded action must explicitly reject non-approval; answered does not necessarily mean approved. Use the target wait lifecycle to handle timeout/cancellation/failure rather than pretending the prerequisite is an action result.

`wait_for` accepts exactly one `inquiry`, `execution`, or `work_queue_item` positive numeric ID or pure expression. It cannot be combined with iteration or parallel containers, and cannot be in a cyclic graph region. It does not create the inquiry or grant access to the waited resource. Verify executor/consumer readiness for execution and queue waits on the target release.

Inquiry creation needs named `inquiries:create`, not `standard`. `assigned_to` is a numeric identity ID. The API derives creator/workflow/task attribution from the token. Responses validate under the retained response contract; option handles are opaque provider-control material, never logs or action output. Test equivalent creation retries, provider-delivery idempotency, assignment/self-approval rules, late/duplicate responses, and secret-safe inquiry disclosure.

## Dynamic targets, permissions, and placement

Current canonical source supports a finite dynamic action ceiling:

```yaml
- name: choose
  action: "{{ parameters.target }}"
  allowed_action_refs: [example.first, shared.second]
  permission_set_refs: []
  input: {}
```

Use 1 to 256 literal full refs, not wildcards, prefixes, or templated ceilings. Every possible target needs reference/admission checks. A literal `action` with a ceiling must belong to it. Dynamic selection cannot borrow another target's grants. See [managed component edits](https://github.com/attune-system/attune/blob/main/docs/permissions/managed-component-readmission.md); recorded capability execution remains gated at the audited revision.

Omitting task `permission_set_refs` inherits pinned target defaults; an explicit empty selection disables token issuance. A string, list, or supported rendered selection must be validated after rendering. Prefer `[]` for explicit opt-out; null handling can differ by parser path. `standard` is scoped key/artifact/cache-read access, not general API authority. Existing delegated children must stay within the parent's named snapshot; recorded invocation ceilings are a separate gated contract, not implicit inheritance.

Task placement overrides `worker_selector`, `worker_tolerations`, and `worker_affinity`. Omit to inherit action defaults; empty objects/lists intentionally clear inherited values where supported. Keep API tokens and secrets out of runtime env, arguments, trace tags, and logs.

## Validation gate

Check two-file paths, refs, finite targets, flat input/output schemas, transitions, joins, status predicates, terminal outputs, iteration shape/empty behavior, permission admission, placement, retry/timeout/cancellation, inquiry waits, and historical binding preservation. Run offline `pack check`, deterministic graph tests, and permitted service-level tests. Report unverified consumers or gates instead of calling parser acceptance a successful workflow run.
