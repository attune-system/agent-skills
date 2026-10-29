# Runtime metadata and environment setup

See [runtime authoring](https://docs.attunedev.org/pack-development/runtime-authoring/) and [runtime environments](https://docs.attunedev.org/pack-development/runtime-environments/).

```yaml
ref: example.python_custom
pack_ref: example
name: Python custom
aliases: [example_python]
distributions:
  verification:
    commands:
      - binary: python3
        args: ["--version"]
        exit_code: 0
        pattern: "Python 3\\."
        priority: 1
execution_config:
  interpreter:
    binary: python3
    args: [-u]
    file_extension: .py
  environment:
    env_type: virtualenv
    create_command: [python3, -m, venv, --copies, "{env_dir}"]
    interpreter_path: "{env_dir}/bin/python3"
  dependencies:
    manifest_file: requirements.txt
    install_command: ["{interpreter}", -m, pip, install, -r, "{manifest_path}"]
```

## Runtime identity and verification

Runtimes are shared by actions and sensors; omit legacy `runtime_type`. Runtime aliases normalize case-insensitively. Native/direct execution uses empty `execution_config`. Interpreter runtimes need interpreter/setup details.

Verification commands run by ascending priority. `always_available: true` or `check_required: false` bypasses checks intentionally, not as a repair for a missing interpreter. Validate the target command, pattern, and exit status; a declared alias is not proof that a binary is installed.

`auto_detected` and `detection_config` are system-managed fields, not authored pack YAML.

## Environments and placeholders

Runtime placeholders are `{pack_dir}`, `{env_dir}`, `{interpreter}`, `{action_file}`, and `{manifest_path}`. Generated environments belong outside the pack. Prefer Python `venv --copies` on shared volumes. Install Python/Node dependencies from the pack-root manifests into the runtime environment, with compatible pins and lockfiles for real deployments.

`env_vars` supports strings or set/prepend/append operation objects. These operate on selected/explicit values, not excluded service variables. Use environment configuration for non-sensitive runtime needs, never as a user-parameter or credential transport. Operator passthrough selects exact names; proxy, CA, package-manager, and cloud settings are not inherited automatically. Setup and verification do not receive action or sensor API tokens.

When inline execution is needed, inspect the target runtime contract for `inline_execution.strategy`, such as `direct` or `temp_file`, plus its supported extension/helper fields. File and typed artifact launches remain separate component contracts.

## Version-specific branch

Optional `versions[]` entries contain `version`, `is_default`, `distributions`, `execution_config`, and `meta`. Do not assume nested version config inherits every base field; provide the required effective launch/setup config. Worker selection chooses available matching versions, not merely the preferred version string in the YAML.

Test the prepared interpreter after setup, repeat setup to verify supported reuse/repair, and exercise missing-dependency/version mismatch behavior. Clean up only the temporary environments owned by the test.
