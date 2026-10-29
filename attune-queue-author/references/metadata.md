# Queue metadata and dispatch contracts

See [queue administration](https://docs.attunedev.org/administration/queues/) and [action acknowledgements](https://docs.attunedev.org/pack-development/actions/#queue-item-result-contract). Source contracts live in `crates/common/src/queue_definition.rs` and `crates/executor/src/queue_dispatcher.rs`. Verify the deployed revision before using newer metadata.

```yaml
ref: example.inbox
label: Inbox
dispatch_action: example.process_items
reference_visibility: private
batch_mode: batch
default_priority: 0
allow_pending_update: true
update_strategy: merge_patch
item_schema:
  external_id:
    type: string
    required: true
action_params:
  items: "{{ items }}"
  queue_items: "{{ queue_items }}"
  queue: "{{ queue }}"
config:
  dispatch:
    concurrency: {source: literal, value: 2}
    batch_size: {source: literal, value: 10}
    retry_limit: 2
    separate_requesters: false
  ack_contract:
    version: 1
```

- `enabled` controls dispatch; `accepting_new_items` controls producer admission. Treat them separately. Omission creates enabled/accepting metadata and preserves supported operator overrides on reload; explicit values are intentional declarations.
- `batch_mode` is `single` or `batch`. Single mappings use `item` and `queue_item`; batch mappings use `items` and `queue_items`. `queue` and pack `config` are also available. Whole templates preserve JSON types.
- `update_strategy` is `immutable`, `replace`, or `merge_patch`. `item_key` can provide enqueue idempotency; test pending updates and already-terminal duplicates.
- Tunables can use `source: literal`, `source: pack_config` with `path`/`fallback`, or `source: keystore` with `key_ref`/optional path/fallback. Keep secret handling and attribution explicit.
- Coalescing can group payloads through `config.dispatch.coalescing` with `enabled`, `group_by_path`, and `across_priorities`. Requester grouping is separately controlled by `separate_requesters`; do not claim mixed-requester API/secret authority works merely because grouping metadata exists.
- Dispatch-action visibility must allow the queue's pack. Producer queue visibility uses the queue's `public`/`private`/`restricted` reference policy and restricted allowlist. Definition management uses `queues`; enqueue/item operations use `queue_items`.
- Pass item IDs explicitly. Empty `action_params` does not reliably give the action the IDs needed for `queue_ack`.

## Acknowledgements and failures

The dispatch action uses `output_format: json` and returns `queue_ack` in its semantic result. Include each leased ID exactly once with `completed`, `failed`, `skipped`, or `retry`:

```json
{"queue_ack":{"version":1,"items":[{"id":1001,"status":"completed"},{"id":1002,"status":"retry","error":{"message":"upstream unavailable"}}]}}
```

Invalid/missing ack, unsupported version/status, duplicate/unexpected IDs, or omitted leased IDs cause conservative retry handling up to `retry_limit`, default `0`. A valid acknowledgement can be honored for any terminal execution status. Test timeout, partial failure, retry exhaustion, and duplicate external side effects rather than checking only the process exit code.

## Accepted work and edits

On current managed-admission paths, behavioral queue edits can require queued, leased, and retry work to drain. Already accepted items retain their admission contracts and dispatch bindings. Inspect the target update path before changing schema, templates, dispatch target, permissions, or batch envelope; do not silently reinterpret accepted work. Pack omission and release retention are deployment decisions, not a queue-local cleanup shortcut.
