---
name: attune-pack-test-reviewer
description: Reviews and tests Attune pack metadata, component contracts, security, release archives, and deployment readiness. Use before upload, registration, publication, or when pack validation and install tests fail.
license: Apache-2.0
compatibility: The target Attune CLI is recommended; server mutations and external calls require permission
metadata:
  target: attune-pack-review
---

# Attune pack test reviewer

Review the complete component graph, not just YAML parsing. Findings must identify a file, consequence, minimal fix, and validation. Separate static acceptance from runtime evidence and release readiness.

## Documentation

- [Testing and release](https://docs.attunedev.org/pack-development/testing-and-release/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)
- [Pack administration](https://docs.attunedev.org/administration/packs/)
- [Actions](https://docs.attunedev.org/pack-development/actions/)
- [Sensors](https://docs.attunedev.org/pack-development/sensors/)
- [Workflows](https://docs.attunedev.org/pack-development/workflows/)
- [Queues](https://docs.attunedev.org/administration/queues/)
- [Caches](https://docs.attunedev.org/administration/data-caches/)
- [Dashboards](https://docs.attunedev.org/pack-development/dashboards/)
- [Policies](https://docs.attunedev.org/administration/policies/)

Use installed CLI help and the target loader/DTO/runtime consumers to resolve differences. Named schemas, sensor stdin bootstrap, inquiry waits, and immutable release tools are newer than some public examples. A source implementation or paused plan is not a passed runtime acceptance gate.

This skill owns the cross-component release gate. For detailed corrections, use `attune-queue-author`, `attune-cache-author`, `attune-dashboard-author`, `attune-runtime-author`, `attune-policy-author`, or `attune-permission-set-author` for that component. Shared schema semantics belong to `attune-schema-author`. Load only the specialist/reference needed by a finding; do not load all component manuals before starting a review.

## Review process

1. Establish pack path, target revision, deployment source, intended use cases, runtime requirements, safe fixtures, and allowed checks. Never request real credentials.
2. Inventory all component directories and references, including `types`, dashboards, caches, policies, permission sets, and graph files.
3. Run offline structural checks, deterministic tests, packaging checks, and permitted deployment smoke tests in that order.
4. Verify observed behavior against contracts. Do not hide skipped, forced, blocked, or unavailable checks behind historical test totals.
5. Report blockers/warnings, commands and outcomes, remaining evidence gaps, and a publish-readiness verdict.

```bash
attune --version
attune --output json pack check ./example
attune pack test ./example --detailed
```

`pack check` is read-only and needs no server. It is not a registrar-equivalent simulation: it can leave external refs unverified and does not prove runtime availability, permission admission, candidate distribution, or every persistence/test configuration behavior.

## Metadata checks

### Manifest and lifecycle

- `pack.yaml` has a stable lowercase ref, label, description, version, license/setup documentation, and canonical `conf_schema`, `meta`, and `tags`. Legacy aliases are not duplicated.
- Dependencies and runtime requirements are declared and checked independently of `runtime_deps` inventory metadata.
- Release defaults and operator overrides are separate. Redeploy validates preserved overrides; omission is not reset. No secret defaults or plaintext credentials.
- `owner_roles` declares exact role names, not permission assignments. Ownership and runtime sponsorship are distinct.
- Explicit `enabled` values are intentional. Omission preserves existing operator state for supported components. Queue acceptance and dispatch state are separate.
- Deployment omission policy `remove`/`disable`/`retain` is deliberate. Surviving dependencies remain valid; retained historical work is not silently rebound.
- No ignored generated artifacts, secrets, symlinks, dependency caches, `.git`, or unowned large files accidentally enter upload/release bytes.

### Schemas and references

- Outer component schemas remain flat field maps; named type `schema` bodies describe a single JSON Schema value.
- `parameters`/`param_schema` and `output`/`out_schema`/`output_schema` are not declared together. Supported aliases do not justify duplicated fields.
- Named types have correct ownership, dependency versions, visibility, valid local/named refs, no cycles, and supported keywords. Defaults validate without further default insertion.
- Secret markers retain nested text-tree restrictions and prohibit default/const/enum/example literals. Test nested object/array redaction and sanitized errors.
- Authoring-template deferral is not strict runtime validation. Test rendered values and retained bindings across metadata changes/retries.
- Action/trigger/queue/type public/private/restricted policies permit each referencing pack. A dependency or admin grant does not bypass foreign private reference policy.

### Actions and runtime setup

- Conventional entrypoints exist relative to `actions/`; typed launch metadata and workflows use their own path rules. Exactly one launch form.
- Stdin JSON or justified file/alternate format matches implementation. No environment-variable user parameter transport.
- Structured stdout parses completely with the declared serializer/schema; stderr is redacted. Parsing/conformance warnings do not guarantee execution failure.
- Positive action `timeout_seconds`, workflow task overrides, retries, process cleanup, and idempotency are tested separately from CLI watch deadlines.
- Runtime aliases normalize correctly, additional worker runtimes exist, and placement is satisfiable.
- Dependencies install under owned runtime env directories, not read-only pack paths. Explicit dependency pins/lockfiles match the deployed API/SDK.
- Cleared child environments do not accidentally rely on service proxy/CA/cloud credentials. Any operator passthrough is deliberate.
- Artifacts have registered rows/versions and transport finalization, not merely arbitrary local files.

### Rules and sensors

- Trigger parameters configure instances; trigger output describes payload; current `event_config_schema` describes emitted config. Webhook metadata remains separate.
- Rule conditions use expressions or supported payload-relative array operators. Test missing/null payload and fields.
- `action_params` is flat; rule namespaces use `event.payload` and `pack.config`, not workflow syntax.
- Runtime permission refs and input permission refs have separate purpose and admission.
- Secret rule values satisfy the target Key-selector policy, not literal or mixed-text credentials. Recorded origins survive enforcement/execution propagation.
- Managed sensor SDK and manager agree on bounded stdin `config`/`triggers` bootstrap. Old environment snapshots are not substituted.
- Sensor tokens are workload/generation fenced; notifier WebSocket lifecycle updates work without assuming ordinary rule changes restart the process.
- Targeted events use an existing same-trigger numeric rule ID. Broadcast is explicit. Token-type admission is not blanket event authority.
- Pack/sensor/enabled-rule placement is compatible. Shutdown, reconnect, transient backoff, token restart, redacted logs, and declared trigger coverage are tested.

### Workflows and inquiries

- New workflows have wrapper metadata and graph-only files linked by `workflow_file`; no runtime/entrypoint on wrappers.
- Canonical `next` targets exist, complete expressions fail closed, and all-match branches do not accidentally overlap. Numeric joins wait for intended predecessors.
- Task result access is `task.name.data.field` or its alias, not `task.name.result.field`.
- Pure templates preserve types. Terminal output variables exist; handled failures do not accidentally make a required-failure parent succeed.
- `with_items` tests empty, non-array, chunk shape, concurrency, retry, and cancellation. Do not assume implicit aggregate results.
- `iterate_cache` uses snapshot mode, one pinned generation, safe page/batch sizes, correct entry shape, freshness, read authority, and restart behavior. Live mode cannot iterate.
- `core.ask` is not copied from obsolete docs. Action-created inquiries use current `wait_for.inquiry`, retained response contracts, and provider idempotency.
- Wait targets are positive IDs/pure templates, authorized, non-iterating, and outside cycles. Test prerequisite failure/timeout separately from action timeout.
- Dynamic actions have finite literal `allowed_action_refs`; each target is independently referenceable/admitted. Recorded capability gates are not enabled as a test workaround.

### Queues, caches, dashboards, and policies

- Queues pass payload plus item metadata IDs, use deliberate retry/coalescing/requester grouping, and return a complete valid `queue_ack` for every leased item exactly once.
- Queue timeout/malformed-ack behavior and duplicate side effects are tested. Default retry limit `0` is understood.
- Cache definitions use strict supported fields, same-pack owners, valid namespace names, and immutable owner/name/mode. Runtime mutation request fields do not appear in definitions.
- Snapshot generation/retention and live revision/idempotency contracts are distinct. Cache grants use namespace names, not definition refs; `standard` is read-only.
- Dashboards have valid source/filter/card IDs, breakpoint positions, catalog-compatible params, and preview checks. Dashboard visibility does not bypass source RBAC; test forbidden/stale/empty states.
- Policy YAML follows the loader's nested `concurrency` and `rate_limit` shapes, not database columns. Scope/priority and positive limits are valid. Persisted rate/quota metadata is not proof of production enforcement; test the actual enforcer.

## Pack tests

Configure non-empty runners, not merely `testing.enabled: true`:

```yaml
testing:
  enabled: true
  discovery: {method: directory, path: tests}
  runners:
    contract:
      type: script
      entry_point: tests/run_tests.sh
      timeout: 120
      result_format: simple
  min_pass_rate: 1.0
  on_failure: block
```

Implemented runner types are `script`, `unittest`, and `pytest`. `script` uses `/bin/sh` for `.sh` and otherwise `/bin/bash`; Python runners use the prepared interpreter, falling back to `python3`, with `-m unittest ENTRYPOINT` or `-m pytest ENTRYPOINT -v`. Verify entrypoint syntax and installed dependencies. Node/Java suites can be invoked by a supported script runner. Include the required `discovery` object, but do not assume it replaces the explicit runner map.

Reliable runner result format is `simple`, with lines `Total Tests: N`, `Passed: N`, `Failed: N`, `Skipped: N`. Without counts, exit status becomes one suite outcome. Runner `result_format: json` is not the same as global CLI JSON output; its parser is unimplemented on the audited revision. Do not assume Jest, TAP, JUnit XML, or discovery modes are supported.

Current source validates test policy during metadata preflight. `min_pass_rate` must be in `0..1`; `on_failure` is `block`, `warn`, or `ignore`. Worker candidate acceptance applies that policy: `warn`/`ignore` can admit a failed suite, and a reduced pass threshold can admit partial passes. Keep `1.0`/`block` for publication and report the actual test result independently of install acceptance. Runner timeouts must be `1..3600` seconds and combined configured timeouts are bounded. Older guidance saying these fields were parsed but ignored is stale.

Failed tests return nonzero in every supported output format. Test local fixtures, mock external calls, and assert secret absence without echoing values. Always await owned test-process/resource cleanup.

## Release and server smoke gate

For canonical releases, run offline `pack release build`, `verify`, and `inspect`; review declared executable modes, native architecture variants, Java launch requirements, exact archive digest, and included generated artifacts. Index format and source checksums must match the installed publisher/installer, not a proposed spec alone.

Upload local bytes or register an API-visible path only when authorized. Candidate tests use version-pinned object-backed API downloads, including shared-volume workers. Candidate API effects must stay in their isolated context. Local test success does not prove this distribution/activation path.

Do not use `--force` or `--skip-tests` as the default smoke command. If replacement is intended, explain its scope and retain actual test results. Treat component warnings as release blockers, and verify active state after ambiguous failures.

Use owned synthetic resources for the event-to-rule-to-enforcement-to-execution chain, representative workflows, queue ack, and permission-denial tests. Cleanup must target only resources created by this test. Never mutate production metadata to compensate for an unavailable test environment.

End with blockers/warnings/suggestions, exact commands and results, unavailable runtime checks, and whether the chosen release is publish-ready. Parser acceptance or historical pass counts alone cannot satisfy that verdict.
