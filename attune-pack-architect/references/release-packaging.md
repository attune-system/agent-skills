# Release packaging

Use [pack administration](https://docs.attunedev.org/administration/packs/), [custom indices](https://docs.attunedev.org/administration/custom-pack-indices/), and [testing and release](https://docs.attunedev.org/pack-development/testing-and-release/) for public guidance. Current offline release tooling is newer than parts of those guides. Verify `crates/cli/src/commands/pack_release.rs`, `crates/common/src/pack_format/`, and the [release specification](https://github.com/attune-system/attune/blob/main/docs/packs/pack-release-artifacts-spec.md) against the installed binary. A proposed-spec heading is not proof that every publishing command exists.

## Source versus release

A source directory is an authoring input. A canonical `.attune-pack.tar.gz` is immutable executable content with `.attune/release-manifest.json`, schema `attune.pack.release/v1`. Its media type is `application/vnd.attune.pack.v1+tar+gzip`. Keep the initial format v1; do not invent a v2 or compatibility adapter for pre-production changes.

The builder records payload paths, sizes, SHA-256 digests, explicit modes, logical artifact variants, compatibility requirements, dependencies, and optional provenance/evidence. Use the builder rather than hand-writing its manifest. Verification preserves exact archive bytes rather than repacking publisher artifacts.

```bash
attune pack release build ./example \
  --output dist/example.attune-pack.tar.gz --format json
attune pack release verify dist/example.attune-pack.tar.gz --format json
attune pack release inspect dist/example.attune-pack.tar.gz --format json
```

For `build`, `--output` is the archive destination and `--format` controls result formatting. The destination must not already exist. Do not use global `--output json` as though it were the archive path.

## Native artifacts

```yaml
ref: example.reconcile
label: Reconcile
runner_type: native
launch:
  type: native
  artifact: reconcile
parameter_delivery: stdin
parameter_format: json
output_format: json
```

```bash
attune pack release build ./example \
  --artifact 'reconcile[linux/amd64/static]=dist/amd64/reconcile' \
  --artifact 'reconcile[linux/arm64/static]=dist/arm64/reconcile' \
  --output dist/example.attune-pack.tar.gz
```

Generated `--artifact` inputs are included even if ignored during source collection. Native variants currently target Linux amd64/arm64 static binaries. Do not promise Windows, macOS, glibc variants, or CPU feature selection. Assignment must find a compatible variant before execution.

Use exactly one of `launch`, `entry_point`, or `workflow_file`. `launch: {type: file, path: ...}` uses a pack-root-relative file path; conventional `entry_point` is relative to `actions/` or `sensors/`. Verify path semantics rather than reusing one spelling's path with another.

Executable intent is declared, not inferred solely from local mode bits. Native artifacts receive `0755`; data/interpreted source and JARs receive `0644`. Use builder `--executable PACK_RELATIVE_PATH` for executable helpers that require it. No symlinks, hardlinks, devices, traversal paths, duplicate/case-colliding paths, or undeclared generated artifacts.

## Java

Executable JAR metadata:

```yaml
ref: example.java_reconcile
label: Java reconcile
runner_type: java
launch:
  type: java_jar
  artifact: reconcile_jar
  jvm_args: [-Xmx256m]
parameter_delivery: stdin
parameter_format: json
output_format: json
```

Supply `--artifact reconcile_jar=build/libs/reconcile.jar`. A JAR has one portable variant and requires a compatible Java runtime on the worker; the release does not bundle a JRE. `java_jar` launches with `java -jar`, while `java_class` declares `main_class`, ordered `classpath` entries with `artifact` or `path`, and optional `jvm_args`. Do not assume Java source, executable JAR, and compiled-class launches are interchangeable. Intrinsic handlers are platform-specific, not arbitrary plugin names.

## Registry and deployment

The current source still has registry entries with `install_sources` containing pinned Git or checksum-qualified archive sources. The published guide and proposed canonical-release index format are not interchangeable. Generate entries with the installed CLI and validate its accepted index schema. Do not recommend a proposed `pack index release add` command unless installed `--help` confirms it exists.

For reproducible binary releases, prefer an archive source with the SHA-256 of the exact archive bytes. Git source may omit generated artifacts. A directory checksum is not an archive checksum. Pin Git refs when using development source installation.

Remote sources must pass the API's outbound-host policy. HTTPS, approved public/private hosts, response limits, redirect/proxy rules, and Git egress controls are separate from metadata correctness. Adding an index does not implicitly trust all source hosts.

Candidate tests download version-pinned archives through the API's configured object backend, even with shared-volume workers. A local test run is not proof of candidate distribution. `testing.candidate_api_effects: true` requests bounded isolated effects where supported; it does not authorize tests against active production triggers or Keys.

Release republishing policy is separate from `--force` replacement. Existing release pins remain immutable; inspect the target server's off/on/suffix policy instead of assuming `--force` rewrites historical code. Deployment omission policies and incompatible-trigger rollout consent are also separate controls. Prefer draining live emitters over acknowledging incompatible contracts casually.
