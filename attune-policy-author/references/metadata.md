# Policy controls and enforcement

See [policy administration](https://docs.attunedev.org/administration/policies/) and [implementation limitations](https://docs.attunedev.org/internal-implementation/data-structures/policies/). Source parsing is in `crates/common/src/policy_control.rs` and the pack loader; scheduling is in `crates/executor/src/policy_enforcer.rs`.

```yaml
ref: example.serialize_deploy
name: Serialize deployments
action_ref: example.deploy
enabled: true
priority: 10
concurrency:
  limit: 1
  method: enqueue
  parameters: [environment]
```

## Ordinary controls and precedence

Pack files create pack-scoped policies, or action scope when `action_ref` is set. Pack files are not a way to create global policy. `name` is the policy display field; the loader also accepts `label`. `concurrency.limit` and `concurrency.method` must appear together, with a positive limit and `enqueue` or `cancel`. Grouping `parameters` are paths in flat execution config, not parameter schema definitions. Do not copy database `threshold` columns into pack YAML.

Additional supported metadata includes `rate_limit: {max_executions: 10, window_seconds: 60}` and quotas such as `{quota_type: running_executions, limit: 10}` or `executions_total`. At least one control must be configured. Scope precedence is action, pack, global; highest priority wins within a scope. Policies are not merged feature-by-feature across scopes and do not grant API authority.

Persisted metadata does not prove enforcement. At the 2026-10-29 source audit, the production constructor resolves database concurrency but does not load persisted rate/quota policies into the in-memory enforcer maps. Recheck the target implementation before relying on that limitation or claiming rate/quota protection. Require a target-version scheduling test.

## Shared resource-concurrency branch

For a shared resource limit across actions, current source accepts a separate policy control:

```yaml
ref: example.organization_limit
name: Organization limit
resource_concurrency:
  namespace: organizations
  limit: 1
  method: enqueue
  participants:
    - action: example.deploy
      resource_parameter: organization_id
    - action: example.reconcile
      resource_parameter: target.organization_id
```

Do not combine resource concurrency with ordinary concurrency/rate/quota controls in one policy. Participant actions must be unique full refs and parameter paths nonempty. Resource IDs must resolve to nonempty strings, integers, or booleans, not fractional numbers, objects, arrays, or null. Test the actual scheduler's shared-resource behavior before claiming isolation.

Group-path tests should include missing/invalid IDs and values of different scalar types. Do not log sensitive resource identifiers or infer ownership from a shared namespace name.
