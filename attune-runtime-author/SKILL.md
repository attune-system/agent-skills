---
name: attune-runtime-author
description: Authors Attune custom runtimes, interpreter setup, dependency installation, verification, and version entries. Use when editing runtimes/*.yaml or debugging runtime detection and isolated environment setup.
license: Apache-2.0
compatibility: Verify runtime metadata and worker capabilities against the target Attune revision
metadata:
  target: attune-runtime
---

# Attune runtime author

Define how a worker verifies and launches a runtime and prepares its isolated dependencies. Prefer an existing core runtime when its behavior already fits.

## Documentation

- [Runtime authoring](https://docs.attunedev.org/pack-development/runtime-authoring/)
- [Runtime environments](https://docs.attunedev.org/pack-development/runtime-environments/)
- [YAML reference](https://docs.attunedev.org/reference/yaml/)

For runtime YAML, verification bypasses, placeholders, and version entries, read [runtime metadata and environment setup](references/metadata.md). Read only the version-specific branch when explicit version selection is needed.

## Workflow

1. Inspect core runtime availability and the action/sensor launch requirement. State the missing behavior that justifies a custom runtime before creating one.
2. Establish the runtime ref, normalized aliases, interpreter, version constraints, dependency manifest, target architectures, and worker/sensor environments.
3. Define verification commands and expected output/exit status. Use native/direct empty execution config only for direct launch; do not bypass verification to hide a missing interpreter.
4. Define environment creation and dependency installation under `{env_dir}`. Validate placeholder expansion, prepared interpreter paths, and declared non-secret env configuration. Setup must work with the cleared child environment and a read-only pack tree.
5. Add `versions[]` only when needed, with the effective verification and launch/setup config for each supported version. Check the worker can actually detect/select the intended version.
6. Run offline pack checks and owned setup/verification tests. When permitted, run a representative action or sensor on the target worker. Record dependency installation, runtime selection, and failure cleanup separately.

## Boundaries and related skills

- `attune-action-author` and `attune-sensor-author` own component parameters, lifecycle, placement, and runtime constraints.
- `attune-pack-architect` owns deployment images, release packaging, native/Java artifacts, and cross-component dependency decisions. A runtime definition does not install an entire worker image or build a release artifact.
- `attune-permission-set-author` owns API grants. Dependency setup must not receive action/sensor API tokens.
- `attune-schema-author` owns action/config schema semantics, not the runtime's interpreter/environment structure.

Use the architect's release-packaging guidance only for bundled native/Java variants or immutable distribution. Keep ordinary interpreter authoring independent of the complete pack-design task.

## Completion gate

- Existing runtimes were considered; custom behavior and normalized aliases are justified.
- Verification and interpreter/version selection match available target workers.
- Setup writes only to owned runtime locations and works without ambient service credentials.
- Dependency manifests, interpreter paths, and placeholder expansions are tested.
- Static checks, actual launches, and unverified platform/architecture assumptions are distinguished.
