# Grant scope and admission

Start with [permissions and RBAC](https://docs.attunedev.org/administration/permissions-and-rbac/) and the [YAML reference](https://docs.attunedev.org/reference/yaml/#permission-set). The published docs lag some scope/admission contracts. Inspect `crates/common/src/runtime_authority.rs`, `crates/common/src/pack_registry/permissions.rs`, and [delegation and secret disclosure](https://github.com/attune-system/attune/blob/main/docs/permissions/delegation-and-secret-disclosure.md) on the target revision.

## Canonical authoring

```yaml
ref: example.emit_events
label: Emit Example events
scope: pack
grants:
  - resource: events
    actions: [create]
    constraints:
      refs: [example.item_seen]
```

The permission-set ref belongs to its declaring pack. `grants` contains resource, actions, optional constraints, and optional per-grant scope. Current source defaults set scope to `pack`; grants may override it. Local envelopes depend on actual structural ownership, not ref prefixes. External/global authority requires explicit `scope: external` and the target admission/approval contract. An unconstrained local grant does not become platform-wide merely because it omits refs.

Use resource-specific selectors: event-create refs name target triggers, queue-item create refs name target queues, cache refs name namespaces, and Key refs use canonical owner-qualified refs. Resolve actual ownership rather than guessing it from text. Verify resource/action names and supported constraint containment in current source/OpenAPI; unknown scope relationships must fail closed.

Publishing a set does not assign it to a human or automatically select it for every action. Human IAM may use relative ownership constraints where supported, but runtime capability admission rejects unsupported human-relative authority. Do not copy human roles into execution grants mechanically.

## Consumer purposes

| Consumer | Selection | Purpose |
| --- | --- | --- |
| Action | `default_execution_permission_set_refs` | Default execution API access |
| Workflow task or rule invocation | `permission_set_refs` | Invocation-specific execution API selection |
| Rule | `input_permission_set_refs` | Explicit server-rendered Key/Pack input authority |
| Sensor config | `input_permission_set_refs` | Server-rendered sensor inputs |
| Sensor config | `cache_permission_set_refs` | Sensor cache access |
| Sensor config | `signing_permission_set_refs` | Approved signing operations |

These fields are not interchangeable. Use the relevant component skill for attachment syntax and omission/null behavior. Prefer explicit `[]` for a deliberate API-token opt-out where supported. Non-empty action API selection can cause token issuance; token presence does not authorize every API operation.

## Reserved access and runtime readiness

`standard` is a reserved scoped permission ref, not a database permission set to redefine. It covers key/artifact operations and cache reads in signed action/pack scopes, including containing workflow scope for children. It does not grant event creation, queue writes, signing, or broad action execution. Sensor `standard` cache access is read-only for the sensor and pack.

Recorded pack-owned runtime authority is not fully production-enabled at the 2026-10-29 source audit. The existing delegated path still has active-owner and parent-subset checks. Recorded invocation policies retain admitted local/external grant bodies and approvals separately; their source presence is not an automatic delegation exemption. Verify production gates and consumer support rather than enabling a gate to make an example pass.

A foreign child does not acquire all parent capability. Validate selected/inherited refs against the applicable delegated or recorded invocation ceiling. External/global authority and explicit input-purpose consent have separate approval requirements. A deployer cannot claim these are satisfied merely by declaring a dependency or a broader set.

The older delegated event-ingress branch can admit execution tokens without the newer recorded per-trigger grant check. Treat this as a version-sensitive limitation, not a portable security guarantee. Declare intended Events/Create scope and test the actual consumer path.

## Secrets and signing branch

Key selectors, authorized input delivery, and human plaintext disclosure are separate contracts. Encrypted Key delivery requires the applicable read/decrypt authority and a valid secret-marked destination. Runtime secret values retain recorded origins; destination decrypt rights alone do not bypass access checks on those origins. Changing a configured ref does not change the origins of historical values.

For assertions, prefer the [approved JWT signing operation](https://github.com/attune-system/attune/blob/main/docs/guides/shared-jwt-signing.md) over private-key delivery. Signing requires the admitted operation and operator profile/subject/lifetime constraints; `keys:use` does not grant raw plaintext reads. Sensor signing also requires the admitted generation and workload fence. Keep use-only private material outside any implicit pack-readable Key scope.

A deployment right over executable code is a trust boundary for secrets that code may consume. Denying a human direct decrypt does not prevent extraction through code they are authorized to replace. Use separate packs and explicit external capabilities when that separation is required.
