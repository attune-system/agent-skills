---
name: attune-cli-guide
description: Guides safe Attune CLI and MCP use for profiles, authentication, pack validation/deployment/releases, workflow upload, execution observation, config, artifacts, and secrets. Use when running attune or attune-mcp commands.
license: Apache-2.0
compatibility: Installed attune or attune-mcp; use version and installed --help before version-sensitive operations
metadata:
  target: attune-cli
---

# Attune CLI guide

Choose commands by where the bytes live, which identity is active, and what effects are permitted. Start with read-only discovery. Do not mutate a live server just to check a local metadata claim.

## Documentation and preflight

- [CLI reference](https://docs.attunedev.org/reference/cli/)
- [MCP setup](https://docs.attunedev.org/reference/mcp/)
- [Pack administration](https://docs.attunedev.org/administration/packs/)
- [Testing and release](https://docs.attunedev.org/pack-development/testing-and-release/)
- [Keys](https://docs.attunedev.org/administration/keys-and-secrets/)
- [Caches](https://docs.attunedev.org/administration/data-caches/)
- [Artifacts](https://docs.attunedev.org/administration/artifacts/)

Check `attune --version` and relevant installed `--help`. Source checks live under `crates/cli/src/commands/`, with transport/auth in `crates/cli/src/bin/attune-mcp.rs` and `client.rs`. An older installed binary is not proof that newer source fields or commands work.

Establish profile/API URL, authentication method, pack source/ref, intended replacement, allowed network/server effects, parameters, and secret disclosure authorization. For production/destructive operations, show the selected target and proposed mutation first. Do not dump saved profile/token content.

Global structured output is `attune --output json ...` or `attune -j ...`; YAML is also supported. NDJSON is restricted to supported streaming commands such as cache entry scan, not a universal output mode.

## Profiles and auth

```bash
attune config add-profile local --api-url http://localhost:8080 --description "Local Attune"
attune --profile local auth login --username test@attune.local
attune --profile local auth whoami
```

Login prompts for the password. For SSO, use `auth sso-login`, or `--no-browser` for headless URL delivery. For integration tokens, `auth token-login` can prompt when `--token` is omitted. Prefer the prompt/protected runtime auth over placing credentials in arguments or shell history.

Use `--profile NAME` or `ATTUNE_PROFILE=NAME` in automation rather than changing global selection. `config current`/`config get api_url` describe selected configuration, not necessarily a one-off profile. Inspect only the non-secret target fields when verifying a profile.

CLI auth precedence is `ATTUNE_API_TOKEN`, then `ATTUNE_AUTH_TOKEN`, then saved profile credentials. Environment tokens can override a profile identity, so `auth whoami` is essential. In executions, retain only the execution-scoped token, not user/refresh credentials.

Integration-token creation reveals the token once. Store it securely and rotate with `auth token list|revoke|delete`; verify installed flags and numeric IDs. Never request a user to paste credentials into chat.

## Validate and deploy packs

```bash
attune --output json pack check ./example
attune pack test ./example --detailed
```

`pack check` is read-only/offline. Current source validates test configuration as well as structure/contracts, but does not execute tests or prove runtime availability, server admission, or every persistence behavior. Failed pack tests exit nonzero in table/JSON/YAML; retain their result diagnostics. Candidate install acceptance can be weakened by `testing.on_failure` or `min_pass_rate`, so successful activation alone is not proof of all tests passing.

| Bytes available at | Command |
| --- | --- |
| Local workstation directory | `attune --profile local pack upload ./example` |
| API-visible server directory | `attune --profile local pack register /opt/attune/packs/example` |
| Server-resolved URL, archive, or registry ref | `attune --profile local pack install SOURCE` |

Upload archives local bytes. Register sends only a server path. Install resolves its source on the server, not the workstation. Approved HTTPS Git sources can select a branch/tag/commit with `--ref-spec`; older `--ref` examples are stale. SSH, `git://`, `file://`, and credential-bearing Git URLs are not general supported alternatives.

Use `--force` only for an intentional replacement. It can also bypass failed-test blocking on supported paths, so it is not a harmless default. `--skip-tests` skips evidence; `--skip-deps` can also skip tests in affected install paths. Do not mark forced/skipped validation publish-ready.

Current deployment commands support `--absent-metadata-policy remove|disable|retain`, default `remove`. Choose deliberately; omitted components can retire from new admission while historical work retains pins. `--acknowledge-incompatible-rollout` is separate consent for incompatible trigger rollout, not implied by `--force`. Prefer draining emitters and verify this flag on the installed version.

After ambiguous transport failure, inspect `pack show REF` and installation state before retrying. Do not blindly repeat side-effectful install requests.

### Offline immutable releases

```bash
attune pack release build ./example \
  --output dist/example.attune-pack.tar.gz --format json
attune pack release verify dist/example.attune-pack.tar.gz --format json
attune pack release inspect dist/example.attune-pack.tar.gz --format json
```

For build, `--output` is an archive destination that must not exist; `--format` controls diagnostic output. Native artifacts use mappings such as `--artifact 'tool[linux/amd64/static]=dist/tool'`; JARs use `--artifact tool_jar=build/tool.jar`. Explicit generated inputs bypass source ignore filtering. Use the architect's release reference for typed launch metadata, modes, variants, and checksums.

Do not assume a proposed publisher/index command exists. Verify installed `pack index --help` and the actual index schema. Exact archive checksums and directory checksums are not interchangeable. `--force` replacement does not rewrite immutable release pins or override the server's republishing policy.

## Workflow upload and execution

`workflow upload` takes action metadata with a `workflow_file` pointer, not the graph alone:

```bash
attune workflow upload ./example/actions/deploy.yaml
attune workflow show example.deploy
```

Graph paths are relative to `actions/`. Use `--force` only when replacing intentionally. API workflow updates preserve omitted reference-visibility fields; explicit empty allowed-pack lists clear that field. Pack reload desired-state semantics are different.

Action parameters are flat:

```bash
attune action execute example.deploy \
  --params-json '{"environment":"dev","dry_run":true}' \
  --watch --timeout 600
```

`--param key=value` parses JSON where possible and otherwise strings. `attune run REF` is the execution shortcut. Use current `--watch`, not stale `--wait`. The CLI watch `--timeout` limits waiting; it is not the action's snapshotted runtime timeout. Inspect installed execute/rerun support before proposing a runtime override.

```bash
attune execution list --action example.deploy --limit 10
attune execution show 123
attune execution watch 123 --timeout 600
attune execution logs 123
attune execution result 123
```

Watch failure/cancellation/timeout/abandonment returns nonzero on the single-execution path. List watch behavior differs. `execution cancel ID --yes` and reruns are mutations, not diagnostic defaults. Reruns reject retained secret redaction markers; supply fresh authorized inputs through a protected mechanism instead of reusing markers or printing plaintext.

## Configuration, schema, queue, and cache tools

Current source has separate `pack config` and `sensor config` set/reset commands. Use `set --help`/`reset --help`; preserve omitted operator overrides and use explicit reset to release defaults. Example non-secret change: `attune pack config set example --set-json retries=3`. Preview supported reset operations with `--dry-run` before confirming.

Inspect `attune schema --help` for authenticated type discovery/preview and `attune key --help` for schema assignment/rebinding. Authoring previews do not choose runtime bindings or grant plaintext access.

Queue definition management and queue item writes need different grants. For caches, distinguish immutable snapshot generations from revision-guarded live mutations. Live namespaces do not support scans, generation selection, or workflow iteration. Confirm the installed cache subcommand/flags rather than inventing commands from API names.

## Artifacts and Keys

Artifact metadata and file bytes have separate operations. Capture returned IDs and create/version/upload/download only the requested owned resource. Examples for safe inspection:

```bash
attune artifact list --execution 123
attune artifact show 42
attune artifact version list 42
attune artifact download 42 -o ./report.txt
attune key list --owner-type pack --owner example
```

Inspect returned metadata privately before downloading sensitive content. Files staged under artifact directories do not appear in the UI without registered rows. Standalone/API transport can use worker-local staging followed by finalization.

`key show REF` redacts encrypted values unless `--decrypt` is explicit and authorized. Plaintext disclosure needs read/decrypt plus applicable recorded-origin rights for derived data. Use canonical owner-qualified refs when constraining access. Key schema updates retain bindings unless explicitly rebound.

Current Key routes have token-specific exceptions, including fenced sensor SDK reads and approved signing. Do not copy the old blanket claim that every sensor Key operation is rejected. Check the exact operation in OpenAPI/source. Read does not imply decrypt, and approved signing does not return private material.

Some CLI Key writes accept only a value argument. For real secrets, use an authorized SDK/API with protected input rather than putting `--value "$SECRET"` in process arguments. Do not invent a `--value-file` flag. Never log decrypted values or issue broad grants merely to make a command pass.

## MCP transport

```bash
attune-mcp --profile local
```

Default stdio is appropriate for local and execution-scoped clients. Discover the installed tools through the MCP handshake/catalog. There is no direct event-create tool. Tool calls can return `isError: true` even if the process exits successfully.

HTTP defaults to loopback port `8090`, with `POST /mcp` and unauthenticated `GET /health`. It requires a separate non-empty inbound token via `ATTUNE_MCP_HTTP_BEARER_TOKEN` or the installed token flag. Prefer secret runtime injection over token arguments. Non-loopback requires explicit `--public-listen`, restricted networking, and TLS/proxy protection. Never reuse the outbound API credential as the inbound server secret.

HTTP local pack checking requires `--packs-check-root` or `ATTUNE_MCP_PACKS_CHECK_ROOTS`; paths outside canonical allowed roots fail. Stdio local checking follows its host filesystem permissions. MCP access still enforces API authorization, scope, and runtime readiness.

Finish with the selected target, commands actually run, observed status, and unverified or version-blocked operations. Do not treat command availability as a successful deployment test.
