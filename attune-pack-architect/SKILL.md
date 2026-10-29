---
name: attune-pack-architect
description: Plans complete Attune packs, component boundaries, manifests, dependencies, trust boundaries, and release strategy. Use when designing or reorganizing a pack and routing component implementation to authoring specialists.
license: Apache-2.0
compatibility: Attune pre-production packs; an Attune CLI and source checkout help verify revision-sensitive contracts
metadata:
  target: attune-pack
---

# Attune pack architect

Plan the pack's component graph and deployment contract before implementing individual components. This skill owns pack-wide decisions and the manifest; component specialists own their metadata and implementation. Return a usable blueprint or scaffold, with unresolved assumptions visible.

## Documentation and branch references

- [Pack development](https://docs.attunedev.org/pack-development/overview/)
- [YAML formats](https://docs.attunedev.org/reference/yaml/)
- [Pack administration](https://docs.attunedev.org/administration/packs/)
- [Permissions](https://docs.attunedev.org/administration/permissions-and-rbac/)
- [Testing and release](https://docs.attunedev.org/pack-development/testing-and-release/)

For native/Java artifacts, indexed distribution, or immutable releases, read [release packaging](references/release-packaging.md). Release strategy crosses component boundaries and stays with this skill; individual runtime launch/setup metadata belongs to the runtime specialist.

## Specialist routing

Use only the specialist needed for the current component. Read that skill's references when its branch conditions apply, not every reference for the whole pack.

| Task | Skill |
| --- | --- |
| Action metadata, entrypoints, stdin and output contracts | `attune-action-author` |
| Agent harnesses with execution-scoped MCP | `attune-mcp-agent-action-author` |
| Event conditions and trigger-to-action mappings | `attune-rule-author` |
| Workflow graphs, iteration, joins, and inquiry waits | `attune-workflow-author` |
| Trigger contracts and managed sensor processes | `attune-sensor-author` |
| Durable work items, queue dispatch, batching, and acknowledgements | `attune-queue-author` |
| Cache namespace modes, publication, and retention | `attune-cache-author` |
| Dashboard sources, filters, visualizations, and preview | `attune-dashboard-author` |
| Custom runtime verification, interpreter setup, and versions | `attune-runtime-author` |
| Execution scheduling limits and shared-resource concurrency | `attune-policy-author` |
| RBAC grants, runtime permission purposes, and external scope | `attune-permission-set-author` |
| Shared schema semantics, named types, defaults, and secret traversal | `attune-schema-author` |
| CLI/MCP commands and target/profile safety | `attune-cli-guide` |
| Cross-component validation and publication readiness | `attune-pack-test-reviewer` |
| External-platform conversion and fidelity assessment | `translate-to-attune-pack` |

Assign work to another agent only when the user or host instructions permit delegation; otherwise follow the specialist guidance yourself. A skill handoff is not authorization to spawn agents or change a live server.

## Planning workflow

1. Establish identity, use cases, external API/event contracts, target Attune revision, runtime/network requirements, distribution method, and license.
2. Inventory each component with its ref, file, owner, inputs/outputs, dependencies, visibility, and side effects. A declared dependency does not grant runtime or secret access.
3. Separate safe release defaults, persisted operator overrides, Keys, runtime API permissions, and human disclosure rights.
4. Choose event-driven rules for reactions, workflows for orchestration, queues for durable dispatch, caches for reconstructable datasets, and artifacts for retained outputs.
5. Draft only the needed directories and metadata. Validate all references, including forward references and foreign visibility, as one candidate graph.
6. Define deterministic tests and the least invasive deployment smoke test. Finish with explicit readiness and unverified behavior.

## Layout and refs

```text
example/
  pack.yaml
  pack-icon.svg                 # optional root icon, not a manifest field
  README.md
  LICENSE
  requirements.txt              # Python dependencies when needed
  package.json                  # Node dependencies when needed
  lib/
  types/                        # reusable single-value schemas
  permission_sets/
  runtimes/
  triggers/
  actions/
    workflows/                  # graph-only workflow files
  dashboards/
  queues/
  policies/
  rules/
  sensors/
  caches/
  tests/
```

Pack refs are stable lowercase names without dots. Most component refs use `<pack>.<name>`. Dashboard definitions can use a short ref which the loader qualifies; cache definition refs are distinct from their owner-scoped namespace names. Prefer explicit full refs for links. Runtime aliases normalize case-insensitively.

Use new workflow actions as `actions/name.yaml` plus `actions/workflows/name.workflow.yaml`, linked with `workflow_file: workflows/name.workflow.yaml`. The wrapper owns action metadata and flat schemas; the graph owns `version`, `vars`, `tasks`, `output_map`, and optional `cancellation_policy`. Do not copy historical standalone workflows into new output.

## Manifest

```yaml
ref: example
label: Example
description: Example Service automation
version: "0.1.0"
author: Example Team
email: team@example.invalid
owner_roles: [automation-maintainers]
conf_schema:
  api_base_url:
    type: string
    default: https://api.example.invalid
  retry_limit:
    type: integer
    default: 3
    minimum: 0
config:
  retry_limit: 3
dependencies: [core]
runtime_deps: [python]
meta:
  repository_url: https://github.com/example/attune-pack-example
  documentation_url: https://example.invalid/docs
tags: [integration]
testing:
  enabled: true
  discovery: {method: directory, path: tests}
  runners:
    contract:
      type: script
      entry_point: tests/run_tests.sh
      timeout: 120
      result_format: simple
```

Use canonical `label`, `conf_schema`, `meta`, and `tags`. Older manifest aliases `name`, `config_schema`, `metadata`, and `keywords` are fallback inputs; canonical values win and conflicts produce diagnostics. Do not mirror them in new manifests. `runtime_deps` is inventory metadata, not proof that install preflight or target workers provide those runtimes.

`owner_roles` is typed ownership metadata, not arbitrary `meta` and not a permission assignment. Names are exact case-sensitive role names. On replacement, omission preserves the existing declaration and `[]` clears it. Role membership can establish human pack-management ownership where the caller's grants permit it; it does not grant executions the human's role membership.

For current configuration support, effective pack/sensor config combines release defaults with persistent operator overrides. Redeployment must validate preserved overrides; omit is not reset. Use explicit config-reset operations. Verify the target release because older upload paths ignored manifest config defaults. Never assume a recursive JSON merge contract. Use Keys for credentials, not plaintext `config` or schema defaults.

Pack-level `sensor_worker_selector`, `sensor_worker_tolerations`, and `sensor_worker_affinity` can constrain managed sensors. Combine them deliberately with sensor-level and enabled-rule placement; mutually incompatible rule constraints can make a shared sensor impossible to place.

## Loading and lifecycle

Current source preflights types and ownership, then loads permission sets, runtimes, triggers, actions/action-linked workflows, dashboards, queues, policies, rules, sensors, and cache definitions. Cache owners must exist before cache namespaces load. Validate the complete candidate graph rather than relying on alphabetical filenames to resolve forward references.

On supported components, omission of `enabled` means enabled on create and preserves operator override state on reload. Explicit values declare the intended state. Queue `accepting_new_items` has the corresponding create/preserve semantics. Do not generalize this to every field or component type.

Omitted metadata is governed by deployment `absent_metadata_policy`: `remove`, `disable`, or `retain`, default `remove` in current CLI. Removal may retire metadata from new admission while retained work keeps pinned snapshots. Validate surviving referencers. Do not promise immediate physical deletion, implicit cancellation, or historical contract rewriting.

Actions, triggers, queues, and named types support reference policy: `public`, `private`, or `restricted` with `reference_allowed_pack_refs`. Same-pack private composition is allowed; foreign private refs remain private. Reference visibility and API authorization are separate checks.

## Trust boundaries

Inventory which components read secrets, call APIs, cross pack ownership, or disclose retained results. Keep deployment authority, human ownership, runtime sponsorship, input delivery, and human plaintext disclosure separate. A deployment right over executable code is a trust boundary for the secrets that code may consume.

Use `attune-permission-set-author` for grant shape, consumer selection, delegation, and recorded-authority readiness. Use `attune-schema-author` for secret classification and reusable schemas. Component specialists own their attachment fields and input/output contracts; the architect records the cross-component trust plan rather than duplicating these rules.

## Runtime and distribution decisions

- Prefer platform-provided core runtimes. Define custom runtimes only for distinct interpreter/setup behavior.
- Install dependencies under `{env_dir}`, never in the read-only pack tree. Use compatible dependency pins and lockfiles for real deployments.
- Environment filtering means proxy, CA, cloud, and package-manager settings are not inherited automatically. Operator passthrough is explicit and applies to setup hooks too.
- Use `pack upload` for a host-local directory. `pack register` sends only an API-visible server path. `pack install` resolves its source server-side.
- Prefer a verified canonical archive for reproducible distribution, especially when generated binaries are absent from Git. Git/archive source development inputs are not equivalent to immutable publisher bytes.
- Platform catalog metadata and an indexed executable `core` release have different ownership. Do not republish or overwrite reserved platform metadata in an integration pack.

## Deliverable and quality gate

Return assumptions/non-goals, a directory tree, manifest, component inventory, config/Key/permission plan, runtime/release plan, specialist handoffs, and test commands. Each handoff should name the component refs/contracts and remaining implementation or validation work. Include source-version limitations.

```bash
attune --output json pack check ./example
attune pack test ./example --detailed
```

`pack check` is read-only structural validation, not registrar or runtime equivalence. Resolve warnings and external-unverified references explicitly. Publish-ready means the selected release bytes, tests, runtime availability, reference policies, input/output/ack contracts, and permitted deployment path have been checked. A forced or skipped-test upload is not release evidence.
