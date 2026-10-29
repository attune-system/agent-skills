# Cache metadata and publication

See [data caches](https://docs.attunedev.org/administration/data-caches/) and [workflow cache iteration](https://docs.attunedev.org/pack-development/cache-iteration/). Check `crates/common/src/pack_cache_definition.rs` and `docs/KEY_CACHE.md` in the target source when the published guide lags namespace modes or request semantics.

```yaml
ref: example.inventory_snapshot
namespace: inventory
owner_type: pack
owner_ref: example
mode: snapshot
refresh_concurrency: reuse
freshness_target_seconds: 3600
max_records_per_generation: 200000
max_generation_bytes: 536870912
max_retained_bytes: 2147483648
max_retained_generations: 5
max_staging_generations: 2
```

Each `caches/*.yaml` declares metadata, not records. Fields are strict: no `enabled`, `label`, or nested `policy`. `ref`, `namespace`, `owner_type`, and `owner_ref` are required. Pack definitions can own only same-pack `pack`, `action`, or `sensor` namespaces, not system or identity namespaces. Namespace names match `[a-z0-9][a-z0-9._-]{0,127}`.

## Snapshot and live modes

`mode` defaults to `snapshot` and is immutable, as are owner and namespace. Snapshot publishers begin, upload, seal, and promote immutable generations. Delta refreshes clone an observed baseline and apply changes through runtime requests. `source_generation_id`, `expected_active_generation_id`, and `deleted_external_ids` are request fields, not definition fields.

Use `mode: live` for one durable current collection updated by atomic ID-based batches with request IDs and expected revisions. Live namespaces support point/multi-ID lookups, not scans, generation selectors, or `iterate_cache`. `request_id`, `expected_revision`, `entries`, `deleted_external_ids`, and `source_revision` belong to runtime requests.

## Policy and lifecycle

Default `refresh_concurrency` is `parallel`; supported values are `reuse`, `conflict`, and `parallel`. Default numeric limits are shown in the example. Retained generation count must be at least `2`, staging count at least `1`, and other numeric limits nonnegative. Zero record/byte limits permit only an empty dataset; freshness `0` disables stale classification. Live mode retains validated snapshot-policy defaults without creating additional generations.

Removal tombstones a managed namespace and schedules bounded cleanup; it does not delete API-created namespaces absent from YAML. Changing owner/name/mode requires a new definition. Test retention against active and pinned generations rather than assuming metadata removal immediately deletes all bytes.

## Producer authority

```yaml
ref: example.cache_writer
label: Inventory writer
scope: pack
grants:
  - resource: caches
    actions: [read, create, update]
    constraints:
      owner_types: [pack]
      owner_refs: [example]
      refs: [inventory]
```

Cache grant `refs` are namespace names, not declaration refs. `standard` grants reads only in signed owner scopes. Snapshot cloning needs read/create; upload/seal/promote need update. Existing live mutation needs update, usually read for the current revision. Select the named set in the action or sensor's purpose-specific permissions. Use `attune-permission-set-author` for local/external admission and grant semantics; a published set does not establish runtime readiness.

Do not store credentials in cache records or log iteration values. Child batch inputs deliberately disclose records to the called action, so choose that action and its output/logging contract accordingly.
