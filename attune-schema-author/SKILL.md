---
name: attune-schema-author
description: Authors and reviews Attune flat schemas and reusable named types, including defaults, references, secret annotations, and immutable runtime contracts. Use when editing types/*.yaml, parameters, output, conf_schema, event_config_schema, or item_schema.
license: Apache-2.0
compatibility: Attune pre-production schema compiler; verify named-type consumer support on the target revision
metadata:
  target: attune-schema
---

# Attune schema author

Define the schema context before writing a schema. Attune distinguishes a flat parameter document from a single value. Confusing them can silently change the intended contract in older versions and is rejected by the current compiler.

## Documentation and version check

- [YAML reference](https://docs.attunedev.org/reference/yaml/)
- [Actions](https://docs.attunedev.org/pack-development/actions/)
- [Sensors and triggers](https://docs.attunedev.org/pack-development/sensors/)
- [Keys and secrets](https://docs.attunedev.org/administration/keys-and-secrets/)
- [API reference](https://docs.attunedev.org/reference/api/)

The published YAML guide does not yet describe the full named-type compiler. For named types, verify the target source against [the compiler contract](https://github.com/attune-system/attune/blob/main/docs/plans/named-type-schema-compiler.md), `crates/common/src/schema_type.rs`, and `crates/common/src/value_schema/`. The contract's status section records remaining consumer validation; do not present every integration as release-certified. Authoring previews are not runtime release bindings.

## Workflow

1. Identify the consumer, declaring pack, schema context, and target Attune revision.
2. Inspect existing values and downstream mappings. Record required fields, missing/null behavior, defaults, and sensitive paths.
3. Write inline schemas for small local values. Use a named type for a reusable domain value, not merely to move a few lines.
4. Check references, visibility, dependencies, default validity, and secret traversal together.
5. Run `attune --output json pack check PACK_PATH`. Resolve every error and distinguish unresolved external references from verified ones.
6. Test fully rendered values at their real acceptance boundary, including nested arrays, missing fields, explicit nulls, invalid defaults, and secret redaction.

## Flat documents

Action/trigger/sensor `parameters`, action/trigger `output`, pack `conf_schema`, trigger `event_config_schema`, queue `item_schema`, and inquiry response field maps use flat field definitions:

```yaml
parameters:
  destination:
    type: example.address
    required: true
    description: Shipping destination
  retries:
    type: integer
    default: 3
    minimum: 0
    maximum: 10
```

At a flat field occurrence, boolean `required: true` requires that outer field. Inside an object value, JSON Schema's `required: [street, city]` requires child properties. To require both the outer object and its children, reference a named object type with `required: true` at the occurrence.

Do not wrap the outer document in `type: object` / `properties`. Flat documents allow extra input fields; an object's `additionalProperties: false` constrains that value, not the outer parameter map.

Current pack loaders accept `parameters` or `param_schema`, and `output`, `out_schema`, or `output_schema`. Use `parameters` and `output` for new pack files. Declare exactly one spelling per schema: the reader rejects multiple aliases even when their values match. API DTO field names are a separate contract; inspect OpenAPI instead of renaming them mechanically.

## Named types

One definition per `types/*.yaml` or `types/*.yml`:

```yaml
ref: example.address
label: Address
description: Postal destination accepted by the shipping API
reference_visibility: restricted
reference_allowed_pack_refs: [shipping]
schema:
  type: object
  properties:
    street:
      type: string
      minLength: 1
    city:
      type: string
      minLength: 1
  required: [street, city]
  additionalProperties: false
```

The `schema` body describes one ordinary JSON Schema value and can be an object or boolean schema. Definition fields are strict: unknown metadata fields fail. The ref must belong to the installing pack. Short type names are rejected; use `type: example.address`. Named refs inside arrays use `items: {type: example.address}`, not an array of named type strings.

`reference_visibility` is `public`, `private`, or `restricted`. The allowlist is valid only for `restricted`. External consumers must declare the pack dependency, optionally with a version constraint such as `example@^1.0.0`. Visibility controls pack references, not authenticated schema inspection or permission to read/decrypt a Key.

Same-pack types bind to the executable's selected release. External types bind to eligible active releases satisfying recorded dependency and visibility constraints. Runtime records retain self-contained immutable contracts; editing a type does not rewrite historical inputs, outputs, queue items, inquiries, or Key bindings. Ordinary Key updates retain their binding; explicit rebinding is a separate operation.

## References and supported vocabulary

The compiler uses a bounded subset of JSON Schema draft 2020-12:

- Primitive types: `string`, `number`, `integer`, `boolean`, `object`, `array`, `null`. Primitive type arrays express unions.
- Schema children: `properties`, `$defs`, `items`, `additionalProperties`, `not`, `contains`, `allOf`, `anyOf`, `oneOf`, `prefixItems`.
- Assertions: `enum`, `const`, `required`, numeric bounds and `multipleOf`, string length/pattern, array size/uniqueness/contains counts, and object size.
- Annotations: `title`, `description`, `default`, `examples`, `position`, `secret`. `format` is an annotation, not a validation assertion.

Local `$ref` supports `#` and plain JSON Pointer fragments such as `#/$defs/address`, including `~0` and `~1` escapes. In a flat document, pointers address the authored field map, for example `#/destination/$defs/country`; `#` cannot use the entire flat map as a single value schema. Each named type keeps its own local reference scope.

Remote URLs, filesystem refs, anchors, `$id`, dynamic references, percent-escaped fragments, unknown keywords, and recursive graphs are rejected. This includes cycles in unused definitions. Do not assume conditional/dependent/unevaluated schema keywords or `patternProperties` work.

Reference occurrences may override annotations, not structural constraints. They cannot replace bounds, properties, items, or enums. An inherited `secret: true` cannot be removed with `secret: false`.

## Defaults and templates

- Defaults must validate without inserting more defaults to make them valid.
- Defaults fill missing properties. They do not replace explicit `null`, `false`, `0`, or `""`.
- An absent optional object stays absent unless its occurrence has an explicit object default. Defaults do not append array elements.
- Defaults beneath composition branches, `not`, or `contains` are rejected. An explicit enclosing default is allowed when valid.
- Authoring validation defers whole-value templates but still validates known literal siblings and shape. It does not prove the eventual rendered value is valid.
- Queue payloads and inquiry responses use strict value validation. Template-looking strings do not bypass it.

## Secrets

Use `secret: true` on credential-bearing inputs and outputs. Current secret values are text trees: strings or nested arrays/objects with string leaves. Numeric, boolean, null, and unconstrained non-text values beneath secret marking are rejected. `const`, `enum`, `default`, and `examples` are prohibited beneath a secret marker, including empty examples and Key-template defaults.

```yaml
parameters:
  api_token:
    type: string
    secret: true
    required: true
output:
  access_token:
    type: string
    secret: true
```

Schema marking classifies values; it does not authorize delivery or disclosure. Key-derived inputs require authorized resolution into secret destinations. Decrypting a destination requires its own read/decrypt rights and access to recorded source origins. Tests should prove absence of secret fixtures from diagnostics, results, logs, and artifacts without printing those fixtures.

## Completion check

- Every schema has an explicit flat-document or single-value context.
- Every named ref resolves or is reported as externally unverified.
- Defaults, requiredness, nested constraints, and secret paths have boundary tests.
- Alias duplication, unsupported keywords, inaccessible refs, and cycles fail safely.
- Generated examples target the installed compiler, not a proposed future dialect.
