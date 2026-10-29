---
name: attune-rule-author
description: Authors and debugs Attune rules, conditions, event-to-action mappings, input permissions, and managed sensor placement. Use when editing rules/*.yaml, trigger_params, action_params, or investigating missing enforcements.
license: Apache-2.0
compatibility: Verify rule admission, secret selectors, and runtime ownership on the target Attune revision
metadata:
  target: attune-rule
---

# Attune rule author

A rule watches one trigger, checks an event, renders flat action parameters, and creates an enforcement when it matches. An enforcement records a match, not successful action completion.

Use `attune-permission-set-author` when defining input/runtime grants and `attune-schema-author` for shared schema semantics. This skill owns rule mappings, conditions, and permission attachment behavior.

## Documentation

- [Writing and managing rules](https://docs.attunedev.org/pack-development/rules/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)
- [Sensors](https://docs.attunedev.org/pack-development/sensors/)
- [Actions](https://docs.attunedev.org/pack-development/actions/)
- [Keys and secrets](https://docs.attunedev.org/administration/keys-and-secrets/)
- [Permissions](https://docs.attunedev.org/administration/permissions-and-rbac/)

Source checks: `crates/common/src/pack_registry/loader.rs`, `template_resolver.rs`, `crates/executor/src/event_processor.rs`, `crates/api/src/routes/rules.rs`, and [delegation and secret disclosure](https://github.com/attune-system/attune/blob/main/docs/permissions/delegation-and-secret-disclosure.md). Public docs lag current pack runtime ownership and some secret-input rules.

## Workflow

1. Inspect the trigger's configuration and payload contracts, a safe sample event, and the target action's required/secret parameters.
2. Establish owning pack, enabled behavior, event filtering, action mapping, sensor placement, and permission needs.
3. Draft the rule with explicit full refs and test resolved parameter values, including missing/type-sensitive paths.
4. Run `pack check` and mapping tests before deployment. For a permitted smoke test, inspect event, enforcement, and execution separately.

## Metadata

```yaml
ref: example.on_critical_item
pack_ref: example
label: Handle critical item
trigger_ref: example.item_seen
action_ref: example.handle_item
conditions:
  expression: 'event.payload.severity == "critical"'
trigger_params:
  query: status:open
action_params:
  item_id: "{{ event.payload.item_id }}"
  event_id: "{{ event.id }}"
trace_tag_template: "item.{{ event.id }}"
permission_set_refs: []
```

`action_params` keys are action parameter names, not a wrapper such as `parameters`, `inputs`, or `config`. The containing pack supplies `pack_ref` during pack loading; inspect API DTO requirements separately.

`trigger_params` configure the trigger instance according to the trigger/sensor contract. They are not a general event filter. Use `{}` unless that contract declares configuration fields. Event filtering belongs in `conditions`.

Omitted `enabled` creates enabled metadata and preserves an existing operator override on reload. Explicit `true`/`false` declares state. Pack-loaded rules are non-ad-hoc managed metadata; API-created rules are ad-hoc and preserved separately. Current pack rules receive an explicit runtime identity and captured input authority. Ownerless rules do not fall back to a privileged system identity.

Both target policies matter: action visibility must allow invocation by the rule's pack, and trigger visibility must allow subscription. Foreign private components remain inaccessible regardless of a deployer's broad admin role. A dependency declaration alone is not authorization.

## Conditions

Empty `{}`, `[]`, or null means always match. Prefer an `expression` string for non-trivial logic; bare and `{{ ... }}`-wrapped expressions are supported. Context exposes `event.id`, `event.trigger`, `event.trigger_ref`, `event.created`, and `event.payload`.

```yaml
conditions:
  expression: 'event.payload.severity in ["error", "critical"] and not event.payload.silenced'
```

Use the workflow expression engine's supported operators/functions, but not task-status helpers such as `result()` or `succeeded()` in event conditions. Missing-field/type/evaluation errors fail closed. Do not write JSON Logic or Jinja control blocks.

Simple arrays combine checks with AND:

```yaml
conditions:
  - field: metadata.environment
    operator: equals
    value: production
```

Fields are payload-relative. Supported operators are `equals`, `not_equals`, and string-only `contains`; unknown operators evaluate false. An event with no payload can match before conditions are evaluated on the audited executor, so condition-dependent triggers should always emit object payloads and test null/missing payload explicitly.

## Templates

Rule templates use `event.payload.*`, `event.id`, `event.trigger`, `event.created`, `pack.config.*`, `system.timestamp`, `system.rule.id`, and `system.rule.ref`. Current authorized Key input selectors also use `keystore`, subject to separate input admission. Do not substitute workflow `config.*` syntax for rule `pack.config.*`.

Whole-string templates preserve JSON types, including arrays/objects. Mixed text becomes a string. Missing whole templates yield null; missing fragments in mixed text yield empty text. Rule templates do not provide arbitrary Jinja filters or `{% ... %}` statements.

```yaml
action_params:
  item: "{{ event.payload }}"
  retry_count: "{{ event.payload.retry_count }}"
  message: "Item {{ event.payload.item_id }} observed"
```

Authoring validation may defer template values but still checks literal siblings and required shape. Strict validation of rendered values remains necessary. Do not treat accepted authoring YAML as proof that every event can satisfy the action schema.

## Secrets and permission purposes

`permission_set_refs` selects API authority for the resulting execution. Omission/null inherits action defaults; `[]` explicitly selects none. Prefer a plural literal list in new rule YAML. Existing worker delegation requires effective grant coverage; newer recorded pack policy remains gated, not an automatic exemption.

`input_permission_set_refs` is a separate explicit named list for server-rendered Key/Pack read/decrypt inputs. It does not grant the child API authority, and reserved `standard` is not a named input set. Current deployed rules capture input authority rather than depending on the human installer's live access.

Current rule authoring permits secret-marked `trigger_params` and `action_params` only as whole Key selectors, such as `"{{ keystore['pack.example.api_token'] }}"`. Secret objects/lists can have Key selectors at text leaves or one selector for the whole value. Literal credentials, mixed text, and non-Key templates at secret destinations are rejected. Defaults under secret schema fields are also rejected. Verify the compiled target schema and actual canonical Key ref.

Do not promise that secret event fields can be authored directly into secret rule destinations on every revision. Published docs describe secret event propagation, but the current rule selector policy is stricter. Validate that exact mapping against target admission and runtime contracts rather than broadening it in a skill.

Runtime values retain original Key/event provenance. Normal reads show redaction markers. Plaintext needs explicit `include_secret_values=true`, destination read/decrypt authority, and rights on recorded origins. A marker is neither a usable credential nor evidence of template failure.

## Managed sensor placement

```yaml
sensor_worker_selector:
  network: internal
sensor_worker_tolerations:
  - key: dedicated
    operator: equal
    value: sensors
    effect: no_schedule
sensor_worker_affinity:
  required:
    - match_labels:
        region: us-east
```

These fields place the managed sensor supplying the trigger, not the resulting action. Pack, sensor, and every enabled rule's constraints combine. Keep shared rules compatible. Placement on an unmanaged/webhook trigger is invalid. Preferred affinity is stored but does not score sensor selection on the audited revision.

## Debugging and completion

1. Confirm trigger/action existence, enabled state, and both reference policies.
2. Confirm the event exists and its target association is correct. Only sensor/execution token flows can create events; MCP intentionally has no emit tool.
3. For targeted events, require an existing same-trigger `rule_<positive numeric id>`. Invalid targets must fail, not broadcast.
4. Inspect conditions and resolved enforcement config using safe values. Check current input authority and required action fields.
5. Follow the enforcement into execution status/result. A missing match is not an action failure; a successful enforcement is not an action success.
6. Record commands/tests, remaining unknown mappings, and any unverified runtime behavior. Remove only test resources owned by this run.
