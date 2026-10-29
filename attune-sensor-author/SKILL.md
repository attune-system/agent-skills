---
name: attune-sensor-author
description: Authors and troubleshoots Attune managed sensors and trigger contracts, including stdin bootstrap, event emission, notifier lifecycle, fenced permissions, placement, logs, SDKs, and native packaging. Use when adding or reviewing sensors or triggers.
license: Apache-2.0
compatibility: Match the sensor SDK bootstrap protocol to the deployed Attune revision
metadata:
  target: attune-sensor
---

# Attune sensor author

Write the trigger contract, sensor metadata, process implementation, and tests together. A trigger is an event/configuration contract; a sensor is its managed producer; a rule subscribes to the trigger, not the sensor ref. Stdout is logging, not an event channel.

Use `attune-runtime-author` for custom runtime definitions, `attune-cache-author` for datasets this sensor publishes, and `attune-permission-set-author` for scoped grants. This skill owns sensor lifecycle and purpose-specific attachment fields.

## Documentation and version check

- [Writing sensors](https://docs.attunedev.org/pack-development/sensors/)
- [Rules and sensor placement](https://docs.attunedev.org/pack-development/rules/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)
- [Runtime authoring](https://docs.attunedev.org/pack-development/runtime-authoring/)
- [Permissions](https://docs.attunedev.org/administration/permissions-and-rbac/)
- [Operational visibility](https://docs.attunedev.org/operations/visibility/)

The published sensor guide still describes an older environment startup snapshot and non-delivered config. Current source delivers both through stdin. Inspect `crates/sensor/src/sensor_manager.rs`, `crates/common/src/repositories/sensor_schema.rs`, and the selected SDK's bootstrap reader. Do not mix an old SDK with a new manager or add silent protocol fallbacks.

## Authoring workflow

1. Establish source API, credentials, event/config schemas, per-rule versus shared settings, polling/subscription model, deduplication, and shutdown behavior.
2. Choose a supported runtime and placement. Resolve all trigger refs before writing the process.
3. Implement the startup bootstrap and notifier lifecycle, then event creation and transient-error backoff.
4. Test bootstrap validation, emitted payloads, targeting, create/update/disable/delete, token expiry/fencing, restart, and secret-safe logs.
5. Run offline pack validation and tests, then a permitted managed-process smoke test. Report any missing service-level evidence.

## Trigger metadata

`triggers/item_seen.yaml`:

```yaml
ref: example.item_seen
label: Item seen
description: An external item matched a configured query
reference_visibility: private
parameters:
  query:
    type: string
    required: true
  interval_seconds:
    type: integer
    default: 30
    minimum: 5
output:
  item_id:
    type: string
    required: true
  observed_at:
    type: string
    format: date-time
event_config_schema:
  query:
    type: string
```

The three schemas have different consumers: `parameters` validates rule trigger-instance settings, `output` classifies/validates emitted payload, and `event_config_schema` describes emitted sensor event config in current source. Webhook transport metadata has a separate server-owned contract. Do not use trigger parameters to classify payload/header secrets.

Schemas are flat field maps. Prefer `parameters`/`output`; current aliases `param_schema`, `out_schema`, and `output_schema` must not be duplicated. Use the schema-author skill for named types and secret trees. `format` is descriptive, not asserted by the current validator.

Trigger `reference_visibility` controls rule subscriptions: public by default, private same-pack, restricted with `reference_allowed_pack_refs`. It is separate from event ingress authority.

## Sensor metadata

`sensors/poller.yaml`:

```yaml
ref: example.poller
label: Poller
description: Poll Example Service and emit item events
runner_type: python
entry_point: poller.py
trigger_types: [example.item_seen]
parameters:
  page_size:
    type: integer
    default: 100
    minimum: 1
config:
  page_size: 100
log_retention_policy: versions
log_retention_limit: 4
worker_selector:
  network: external
```

Use `trigger_type` for one trigger or `trigger_types` for a list. Full refs are clearest. The entrypoint is relative to `sensors/`. Explicit `runner_type` avoids the sensor default of native. Python/Node/shell use configured runtimes; native binaries need the correct architecture and executable intent. For release-built variants, use verified typed `launch` metadata instead of also setting `entry_point`.

Omitted `enabled` creates enabled metadata and preserves an existing operator override on reload. Explicit state is deliberate. Descriptive `type`, `tags`, `examples`, `meta`, and `poll_interval` may remain source-only in the loader. Implement polling in the process, not through `poll_interval` metadata.

### Current stdin bootstrap

The manager writes one bounded JSON document, then closes stdin:

```json
{"config":{"page_size":100},"triggers":[{"id":123,"ref":"example.on_item","config":{"query":"status:open","interval_seconds":30}}]}
```

Read at most the manager/SDK limit, currently 32 MiB. Validate `config` as an object and `triggers` as an array. These values can contain secrets; never log the bootstrap. Read it once before starting the long-lived loop. Stdin is not null and is not an ongoing lifecycle stream.

The current manager explicitly removes `ATTUNE_SENSOR_TRIGGERS` and `ATTUNE_SENSOR_CONFIG_JSON`. Do not reconstruct bootstrap values from `ATTUNE_SENSOR_CONFIG_*`. Shared sensor config now arrives in bootstrap `config`; per-rule values arrive in trigger instances and subsequent notifier updates.

Environment supplies `ATTUNE_API_URL`, sensor `ATTUNE_API_TOKEN`, `ATTUNE_SENSOR_ID`, `ATTUNE_SENSOR_REF`, `ATTUNE_PACK_REF`, `ATTUNE_SENSOR_WORKLOAD_ID`, `ATTUNE_SENSOR_ASSIGNMENT_GENERATION`, `ATTUNE_SENSOR_TRIGGER_TYPES`, `ATTUNE_NOTIFIER_WS_URL`, `ATTUNE_ALLOW_INSECURE_NOTIFIER_WS`, artifact staging, and log settings. It does not supply broker credentials. Processes start with a cleared environment; additional exact names require operator `sensor.passthrough_env`.

### SDKs

Use compatible pinned SDK revisions/releases. Source repositories are [Python](https://github.com/attune-system/python-attune-sdk), [JavaScript](https://github.com/attune-system/js-attune-sdk), and [Java](https://github.com/attune-system/java-attune-sdk). Python installs as `attune-sdk[sensor]`, Node as `attune-sdk`, and Java uses `org.attunedev:attune-sdk` with `io.attune` imports. Check Java artifact publication rather than assuming Maven availability.

All three current SDK source trees have stdin bootstrap and notifier WebSocket lifecycle support. Supplying a rule targets `rule_<numeric-id>` by default. Explicit broadcast switches are Python `target_rule=False`, JavaScript `targetRule: false`, and Java `.targetRule(false)`. Publication and API-environment E2E are separate checks; old unit-test totals are not evidence for the chosen release.

```python
#!/usr/bin/env python3
import attune


class ItemSensor(attune.PollingSensor):
    def setup(self):
        self.interval = 30.0

    def poll(self, rule):
        # Implement this adapter with bounded requests, pagination, and deduplication.
        for item in fetch_items(rule.trigger_params["query"]):
            self.emit({"item_id": item["id"]}, rule=rule)


attune.run_sensor(ItemSensor)
```

`fetch_items` is a pack-specific adapter, not an SDK function. Async sensors should close clients during cleanup and preserve base lifecycle behavior when overriding hooks.

## API authority and event emission

Managed tokens are fenced to the sensor's declared triggers, workload, assignment generation, and eligibility. They do not inherit interactive user roles or action permission defaults. Keep these purpose-specific config fields separate:

- `config.cache_permission_set_refs` selects cache authority. `standard` permits sensor/pack cache reads only; writes and cross-owner reads need admitted named sets.
- `config.input_permission_set_refs` selects explicit named Key/Pack read/decrypt authority for server-rendered inputs. It is not execution API permission.
- `config.signing_permission_set_refs` selects admitted Key `use` authority for approved signing; it does not authorize raw plaintext delivery. Signing also requires the operator profile and current workload fence.

Current source captures sensor purpose grants in release/generation admission. Do not describe runtime authority as a live lookup of the human installer's grants. Direct SDK Key reads and their log-provenance rules are separate from input/signing selections; inspect the target version's contract before retrieving credentials.

For shared private signing material, prefer the [approved JWT signing operation](https://github.com/attune-system/attune/blob/main/docs/guides/shared-jwt-signing.md) over raw Key delivery. The operation fixes the signing contract and checks approved profile, subject, lifetime, pack, and sensor. `keys:use` does not return plaintext private material; keep use-only signing Keys outside any implicit pack-readable Key scope.

Provider inquiry callbacks can declare `config.inquiry_callback_adapters` with provider/subject metadata, bounded JSON Pointer extraction rules, and request constraints. Follow [the current callback contract](https://github.com/attune-system/attune/blob/main/docs/workflows/inquiry-handling.md) before authoring this metadata. A response handle is correlation/integrity material, not authority to approve. The fenced sensor, exact provider identity mapping, assigned identity, and inquiry state still require validation. Never log handles or raw provider envelopes.

Create events with the authenticated SDK or `POST /api/v1/events`, not SQL or stdout:

```json
{"trigger_ref":"example.item_seen","payload":{"item_id":"item-42"},"config":{"query":"status:open"},"trigger_instance_id":"rule_123"}
```

Only sensor/execution tokens enter direct event creation; token type alone is not blanket authority. The target trigger must be enabled and the payload/config must satisfy admitted contracts. A rule target must be an existing same-trigger `rule_<positive numeric id>`; malformed or mismatched targets fail closed. Omit it only for an intentional broadcast. Never broadcast once per active rule unless duplicate matching is intended.

## Lifecycle, placement, and logs

The manager starts eligible sensors when enabled rules need them, stops them when none do, and reconciles placement/runtime eligibility. A still-needed process consumes `rule.created`, `rule.enabled`, `rule.updated`, `rule.disabled`, and `rule.deleted` via authenticated notifier WebSocket, not direct AMQP. Subscribe to every declared trigger in `ATTUNE_SENSOR_TRIGGER_TYPES`, including those without startup rules. Reconnect with backoff and process duplicate deltas idempotently.

Pack, sensor, and enabled-rule placement constraints combine. Rule fields use `sensor_worker_*`; sensor fields use `worker_*`. Selectors/required affinity constrain eligibility; tolerations permit taints. Preferred affinity is stored but does not score sensor placement on the audited revision.

The manager rotates tokens through controlled restart, not environment mutation in a running child. On persistent unauthorized responses, exit safely rather than continue indefinitely. Handle SIGTERM/SIGINT, close clients, and release owned resources. Unexpected exits with active demand are persisted and restarted with capped exponential backoff; repeated failures can emit `core.alert`.

Stdout/stderr are private artifact-backed runtime logs, not event data. Streams can have additional sensor/decrypt/source-origin disclosure checks. Sensitive generations suppress mirroring/excerpts; ordinary mirroring is operator-configurable. Never rely on schema redaction to make arbitrary sensor logging safe. Registered sensor-owned file artifacts are required for durable output, especially with standalone/API transport.

Completion requires valid metadata, compatible bootstrap/SDK, observed lifecycle updates, bounded polling/backoff, valid targeted events, graceful shutdown, satisfiable placement, and redacted logs. Report which managed-service tests actually ran.
