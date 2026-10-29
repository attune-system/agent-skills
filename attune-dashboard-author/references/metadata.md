# Dashboard format and preview

See [writing dashboards](https://docs.attunedev.org/pack-development/dashboards/). Pack-managed dashboards are edited in `dashboards/*.yaml`; ad-hoc CRUD is a different lifecycle.

```yaml
version: 1
kind: dashboard
ref: operations
label: Operations
scope_type: pack
scope_ref: example
visibility: public
enabled: true
is_default_home: false
spec_version: 1
defaults:
  timezone: UTC
  refresh_seconds: 15
  time_window: 24h
layout:
  columns: 12
  row_height: 44
  gap: 12
  breakpoints:
    lg: {min_width: 1280, columns: 12}
    sm: {min_width: 0, columns: 4}
filters:
  - id: pack_ref
    type: pack_ref
    label: Pack
    default: example
data_sources:
  statuses:
    type: execution_status_breakdown
    params:
      pack_ref: "{{ filters.pack_ref }}"
cards:
  - id: statuses
    title: Execution status
    source: statuses
    visualization: {type: table}
    position:
      lg: {x: 0, y: 0, w: 6, h: 6}
      sm: {x: 0, y: 0, w: 4, h: 6}
```

The pack loader qualifies a short dashboard ref in its owning pack. Keep stable filter/source/card IDs and define positions for required breakpoints. Filter references must exist; array params do not support mixed template entries.

## Source discovery and visualization

Discover current source contracts through `GET /api/v1/dashboards/source-catalog`, then preview through `/api/v1/dashboards/preview` with safe data. Verify required/optional params, result shape, ordering, limits, and suitable visualization fields. Do not invent a source parameter because a similarly named API filter exists elsewhere.

Choose visualizations supported by the target contract. A table is the example's deliberate baseline; richer value/time/series mappings must match numeric and ordering semantics. Use stable positions for the declared responsive breakpoints.

## Visibility and states

Dashboard visibility does not bypass source RBAC. A dashboard reader may receive forbidden or empty sources when related events, executions, rules, Keys, or other source data are outside their scope. Test `empty`, `partial`, `stale`, `forbidden`, `invalid`, and `error` states, not only `ok`.

Check freshness, truncation, and ordering metadata before claiming a count or chart is complete/current. Keep dashboard `visibility` separate from action/trigger `reference_visibility`; they govern different kinds of access.
