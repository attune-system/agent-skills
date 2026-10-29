---
name: attune-permission-set-author
description: Authors Attune permission sets and scoped grants. Use when editing permission_sets/*.yaml or designing execution, input, cache, signing, or external access; distinguishes runtime admission from human IAM and scheduling policy.
license: Apache-2.0
compatibility: Verify delegated versus recorded authority and production readiness on the target Attune revision
metadata:
  target: attune-permission-set
---

# Attune permission-set author

Translate required operations into scoped grants and explicit consumers. Publication, human assignment, runtime selection, and secret disclosure are different authorization steps.

## Documentation

- [Permissions and RBAC](https://docs.attunedev.org/administration/permissions-and-rbac/)
- [YAML permission-set examples](https://docs.attunedev.org/reference/yaml/#permission-set)
- [Keys and secrets](https://docs.attunedev.org/administration/keys-and-secrets/)

Before writing a set, read [grant scope and admission](references/grants-and-admission.md) for the canonical shape, permission purposes, reserved access, and recorded-authority limits. Follow its secret/signing branch only when those operations are required.

## Workflow

1. Inventory each required API operation, actual target owner/ref, consuming component, caller/token type, and permission purpose. Finish with an operation-to-grant table, including operations that must remain denied.
2. Establish whether the set is for human IAM, execution API calls, server-rendered inputs, sensor cache access, or signing. Identify the target admission path and readiness; a local set name or published grant is not proof of authority.
3. Author `permission_sets/<name>.yaml` with the narrowest resource/action/scope constraints. Use explicit external scope and required approval for foreign/global access. Keep human-relative constraints out of runtime selections unless the target admission contract supports them.
4. Connect the set only to consumers that require it. Preserve omission/inheritance versus explicit empty selection, and distinguish runtime API refs from purpose-specific input/cache/signing refs.
5. Test positive and negative boundaries: allowed target, unrelated owner/ref, missing grant, broader selection, and inherited child authority. For secrets, test delivery and historical disclosure separately without printing values.
6. Run offline pack checks and permitted authorization tests using the intended identity/token, not an admin substitute. Report denied operations, unsupported scope relationships, and gated paths explicitly.

## Boundaries and related skills

- `attune-schema-author` owns secret classification and schema constraints; a grant does not make an invalid secret destination valid.
- Action, workflow, rule, sensor, queue, and cache specialists own their attachment fields and resource-specific contracts. This skill owns what the selected grants authorize.
- `attune-policy-author` owns execution concurrency/rate/quota controls, not RBAC.
- `attune-pack-architect` owns pack trust boundaries, ownership, dependencies, and deployment authority. A dependency declaration is not a grant.

Keep permission semantics here. Other component skills can show a minimal operation-specific set without duplicating the full delegation/disclosure rules.

## Completion gate

- Every selected grant has a documented consumer, purpose, and actual target scope.
- Local ownership, external approval, human assignment, and runtime selection are not conflated.
- Positive and negative tests use the target token/admission path and preserve child ceilings.
- Secret delivery, signing, and human disclosure use their distinct authority checks.
- Static validity, allowed runtime effects, and production readiness are reported separately.
