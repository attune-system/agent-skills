---
name: attune-queue-author
description: Authors and reviews Attune durable work queues, dispatch mappings, batching, idempotency, and acknowledgements. Use when editing queues/*.yaml or debugging queue admission, dispatch, or queue_ack behavior.
license: Apache-2.0
compatibility: Verify queue and dispatch-action contracts against the target Attune revision
metadata:
  target: attune-queue
---

# Attune queue author

Design the durable work-item contract and dispatch acknowledgement together. A successful action execution alone is not proof that every leased queue item completed.

## Documentation

- [Queue administration](https://docs.attunedev.org/administration/queues/)
- [Action acknowledgements](https://docs.attunedev.org/pack-development/actions/#queue-item-result-contract)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)

Before writing or reviewing queue YAML, read [queue metadata and dispatch contracts](references/metadata.md). It contains the batch example, tunable sources, update strategies, reference policies, and acknowledgement requirements.

## Workflow

1. Establish pack/queue refs, producer identities, item shape, natural idempotency key, dispatch action, and single-item versus batch processing. Finish with a sample payload and its expected item lifecycle.
2. Inspect the dispatch action's input/output contracts and reference visibility. Define which payload and item-metadata fields the action receives; it must have every leased numeric ID needed for acknowledgement.
3. Choose acceptance/dispatch state, pending-update strategy, priorities, concurrency, batch size, retries, coalescing, and requester grouping. Record external side-effect and attribution constraints.
4. Author `queues/<name>.yaml` and fixtures for its resolved `action_params`. Use whole-value templates for structured values and a flat `item_schema`.
5. Test enqueue duplicates, pending updates, single/batch mappings, partial outcomes, malformed/missing acknowledgements, timeout, and retry exhaustion. Assert every leased ID appears exactly once in valid `queue_ack` output.
6. Run offline pack checks and declared tests. When authorized, smoke-test one owned queue and dispatch action, then inspect both execution and item outcomes. Report unverified admission or runtime behavior.

## Boundaries and related skills

- `attune-action-author` owns dispatch-action implementation and JSON output behavior.
- `attune-schema-author` owns schema semantics, named types, defaults, and secret traversal. This skill owns the queue's item and mapping contract.
- `attune-permission-set-author` owns grants for queue definitions versus item operations. Reference visibility is a separate queue check.
- `attune-policy-author` owns execution admission limits; queue dispatch concurrency is not a substitute for an execution policy.
- `attune-pack-architect` owns pack dependencies and deployment-wide changes.

Use these skills only when that branch of the task is involved. Keep queue-specific metadata in this skill rather than loading the complete pack architecture for an isolated queue edit.

## Completion gate

- Queue and dispatch refs resolve under their actual owning packs and reference policies.
- Item schema, idempotency/update behavior, dispatch inputs, and JSON acknowledgements agree.
- Retry, timeout, batch/requester grouping, and duplicate-side-effect behavior are intentional and tested.
- Producer authority, accepted-work update restrictions, and remaining runtime limitations are documented.
- Commands and observed item/execution outcomes are reported separately from static validation.
