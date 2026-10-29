---
name: attune-policy-author
description: Authors Attune execution policies for concurrency, resource grouping, rate limits, and quotas. Use when editing policies/*.yaml or reviewing scheduling limits and policy precedence, not RBAC permission sets.
license: Apache-2.0
compatibility: Verify actual scheduler enforcement, not only persisted policy metadata, on the target revision
metadata:
  target: attune-policy
---

# Attune policy author

Define which executions compete for capacity and what happens when capacity is unavailable. Execution policies limit scheduling; they do not grant API access.

## Documentation

- [Policy administration](https://docs.attunedev.org/administration/policies/)
- [Policy implementation and limitations](https://docs.attunedev.org/internal-implementation/data-structures/policies/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)

Before authoring policy YAML, read [policy controls and enforcement](references/metadata.md). For shared limits across actions, read its resource-concurrency branch. Keep persisted metadata and production enforcement evidence separate.

## Workflow

1. Establish the protected resource, action/pack scope, grouping paths, desired limit, enqueue/cancel behavior, and intended precedence. Finish with concrete competing execution examples.
2. Inspect existing matching policies and target scheduler support. Determine whether ordinary concurrency or a shared-resource policy expresses the requirement. Avoid promising unsupported rate/quota enforcement.
3. Author `policies/<name>.yaml` using the loader's nested control shapes, stable refs, positive limits, and deliberate enabled/priority values. Resolve action refs and configuration parameter paths.
4. Test policy selection and boundary behavior: same/different group values, full capacity, release of slots, cancellation, timeout, and competing scopes/priorities. Resource policies also need cross-action contention tests.
5. Run offline pack validation, then permitted scheduling tests using owned synthetic executions. Confirm observed admission/queueing behavior, not merely successful policy persistence.
6. Report supported enforcement, unsupported controls, update effects, and the evidence needed before relying on a limit in production.

## Boundaries and related skills

- Use `attune-permission-set-author` for RBAC, delegated API authority, or secret access. A permission set is not an execution policy.
- Use `attune-queue-author` for durable work items, dispatch concurrency, batching, and acknowledgement. A policy waiting queue is not the same as a work queue.
- Use `attune-action-author` or `attune-workflow-author` when action defaults, task concurrency, retries, or timeout behavior must change.
- Use `attune-pack-architect` for pack-wide limits, ownership, and deployment decisions.

Schema `parameters` and policy grouping `parameters` are different structures. This skill owns the scheduling meaning of the latter; use `attune-schema-author` if the action's input shape needs redesign.

## Completion gate

- Scope, precedence, grouping, positive limits, and admission behavior are explicit.
- Metadata uses the correct nested fields and resolves real action/config paths.
- Controls are supported by the actual scheduler or clearly marked unverified/unsupported.
- Contention, slot release, failure, and timeout behavior have evidence.
- No RBAC or durable-queue guarantee is inferred from a policy definition.
