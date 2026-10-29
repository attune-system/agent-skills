---
name: attune-cache-author
description: Authors Attune cache namespaces and producer contracts. Use when editing caches/*.yaml, choosing snapshot versus live mode, designing refresh or revision-guarded writes, or debugging cache ownership and retention.
license: Apache-2.0
compatibility: Verify namespace modes and producer APIs against the deployed Attune revision
metadata:
  target: attune-cache
---

# Attune cache author

Choose the dataset's consistency and publication model before writing its namespace definition. Pack metadata creates a namespace, not its records.

## Documentation

- [Data caches](https://docs.attunedev.org/administration/data-caches/)
- [Workflow cache iteration](https://docs.attunedev.org/pack-development/cache-iteration/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)

For namespace YAML, mode selection, ownership, retention limits, and producer permissions, read [cache metadata and publication](references/metadata.md). The snapshot/live contract is newer than parts of the public YAML guide; verify source and target API support together.

## Workflow

1. Establish dataset source, reconstructability, record identifiers, expected size, freshness requirement, owner, readers, and writers. Finish with a sample record and an explicit snapshot or live consistency requirement.
2. Choose snapshot mode for immutable publication, scans, and generation-pinned workflow traversal. Choose live mode for one revision-guarded current collection with ID lookups. Record why the chosen readers can use that mode.
3. Draft `caches/<name>.yaml` with a stable declaration ref, owner-scoped namespace, and bounded policy. Keep runtime write-request fields out of metadata.
4. Define the producer protocol: full/delta snapshot refresh or atomic live batches. Specify concurrent writers, retry/idempotency, freshness, and failure cleanup before implementation.
5. Test owner/name/mode immutability, invalid limits, writer conflicts, failed publication, stale reads, duplicate retries, and retention/removal. Snapshot consumers must not accidentally switch generation on resume.
6. Run offline pack validation and producer tests. When authorized, exercise one owned namespace through the target API and report publication/read outcomes, not merely metadata acceptance.

## Boundaries and related skills

- `attune-action-author` or `attune-sensor-author` owns the producer process and its purpose-specific permission selection.
- `attune-permission-set-author` owns scoped cache grants. Cache grant refs name namespaces, not declaration refs.
- `attune-workflow-author` owns `iterate_cache` task behavior and batch inputs. Live caches cannot use that source.
- `attune-schema-author` owns any schemas in producer/consumer action contracts. Cache namespace policy is not itself a flat value schema.
- `attune-pack-architect` owns the choice between caches, durable queue work, and retained artifacts across the pack.

Load a related skill only for that part of the task. Keep record values and external IDs out of diagnostics and shared references.

## Completion gate

- Mode, owner, namespace, publication protocol, and consumer requirements agree.
- Policy limits and freshness are bounded and deliberate; immutable fields do not change on reload.
- Producer grants and concurrency/retry behavior are verified against the target API.
- Retention and removal preserve supported active/pinned work, with owned cleanup only.
- Tests and unverified service behavior are reported explicitly.
