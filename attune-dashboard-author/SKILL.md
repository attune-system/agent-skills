---
name: attune-dashboard-author
description: Authors and reviews Attune dashboards, typed data sources, filters, visualizations, and layouts. Use when editing dashboards/*.yaml or debugging preview, source visibility, freshness, or card mappings.
license: Apache-2.0
compatibility: Use the target server's dashboard source catalog and preview contract
metadata:
  target: attune-dashboard
---

# Attune dashboard author

Build an operational view from the server's source contracts and the intended reader's permissions. A visible dashboard does not imply access to all of its data.

## Documentation

- [Writing dashboards](https://docs.attunedev.org/pack-development/dashboards/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)
- [Operational visibility](https://docs.attunedev.org/operations/visibility/)

Before drafting dashboard metadata, read [dashboard format and preview](references/metadata.md) for the complete layout example, source/filter rules, and source-level status handling.

## Workflow

1. Establish the operational questions, owning pack/scope, intended readers, time window, refresh cadence, and pack-managed versus ad-hoc lifecycle. Finish with a card inventory tied to those questions.
2. Inspect `GET /api/v1/dashboards/source-catalog` on the target server when available. Select known source types and verify their params, ordering, and result shape rather than inventing query fields.
3. Define stable filter/source/card IDs, explicit source scope, visualization mappings, and positions for supported breakpoints. Check every filter and source reference.
4. Author `dashboards/<name>.yaml` for pack-managed content. Use ad-hoc CRUD only for an ad-hoc dashboard, not to bypass managed ownership.
5. Validate with offline pack checks and, when authorized, dashboard preview under representative reader permissions. Exercise `empty`, `partial`, `stale`, `forbidden`, `invalid`, and `error` states as well as `ok`.
6. Report invalid mappings, unavailable source contracts, permission-dependent gaps, and the preview/check results. Do not describe an offline-only layout review as a verified live dashboard.

## Boundaries and related skills

- `attune-permission-set-author` owns dashboard/source grant design; this skill verifies visible-source behavior without broadening grants automatically.
- `attune-action-author` owns the structured outputs consumed by action-result sources.
- `attune-schema-author` owns schema semantics when the underlying action contract needs changes. Dashboard layout/source metadata is not an action parameter schema.
- `attune-pack-architect` owns which operational views belong in the pack and their deployment lifecycle.

Dashboard `visibility` and action/trigger `reference_visibility` are different contracts. Keep preview data synthetic and avoid secret-bearing values in cards, fixtures, or screenshots.

## Completion gate

- Dashboard ownership/lifecycle, stable IDs, filters, and source params are valid.
- Visualization fields match actual source types and ordering.
- Required breakpoints and non-success data states render deliberately.
- Representative reader permissions have been tested or explicitly remain unverified.
- Pack checks and permitted preview results are recorded.
