# Continuity Kernel / CK-01 MCP Adapter v0.4

External remote MCP bridge for Continuity Kernel / CK-01. CK-01 and its frozen specification are unchanged: this adapter stores external candidate assertions and provenance, not identity or constitutional state.

## Capabilities

- Streamable HTTP MCP at `POST /mcp`, with bearer keys scoped by configuration to one tenant.
- SQLite persistence for candidate assertions, provenance, supersession, and continuity briefs.
- `ck01_propose_candidate`, `ck01_record_provenance`, `ck01_supersede_candidate`, and `ck01_continuity_brief` tools.
- Docker and Render deployment scaffolding.

Candidates can only be `PROPOSED` or `SUPERSEDED`. No tool authorizes, consolidates, rolls back, or changes CK-01 identity/constitution; responses explicitly report `authorization_granted: false` or `state_changed: false`. Provenance is recorded but not independently authenticated or treated as CK-01 quorum evidence.

## Run

```text
npm ci
copy .env.example .env
npm start
```

Set `CK01_API_KEYS` to comma-separated `tenant:strong-secret` pairs, set a persistent `CK01_DATABASE_PATH`, and send `Authorization: Bearer <strong-secret>` on every MCP request. The server derives tenant scope from the key; callers cannot select a tenant in tool arguments or headers. `GET /health` is unauthenticated. The server is stateless at the MCP transport layer; durable records live in SQLite.

## Validate

```text
npm run check
npm test
```

## Render deployment

Create a Render Blueprint from this repository and set its Blueprint Path to
`integrations/ck-mcp-adapter/v0.4/render.yaml`. The Blueprint scopes the Docker
build to this adapter, mounts a 1 GB persistent disk at `/var/data`, stores the
SQLite database at `/var/data/ck01-adapter.sqlite`, and checks database readiness
at `GET /healthz`. Supply `CK01_API_KEYS` only through Render's secret environment
configuration. See `RENDER_PRODUCTION_CHECKLIST.md` before provisioning or
connecting a production client.

This is a reference integration layer, not the complete CK-01 architecture and not evidence of deployment safety, biological validity, consciousness, or generalization to language-model agents. Production deployments should use a managed secret store, TLS at the platform edge, backups, tenant/key rotation, and external provenance verification.

Licensed under Apache License 2.0. See `LICENSE` and `NOTICE`.

