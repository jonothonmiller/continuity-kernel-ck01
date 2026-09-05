# Render production deployment checklist

This checklist deploys the external Continuity Kernel / CK-01 MCP Adapter v0.4. It does not modify, authorize, or deploy the frozen CK-01 specification or identity state.

## Before service creation

- [ ] Use the public repository `jonothonmiller/continuity-kernel-ck01` and the intended deployment commit.
- [ ] In Render, create a Blueprint and set the Blueprint Path to `integrations/ck-mcp-adapter/v0.4/render.yaml`.
- [ ] Review and approve a paid web-service plan that supports a persistent disk.
- [ ] Confirm the temporary `onrender.com` hostname is acceptable; defer any custom domain.
- [ ] Generate a high-entropy bearer secret outside Git and choose a non-sensitive tenant identifier.

## Render resources and secrets

- [ ] Confirm service name `ck01-mcp-adapter`.
- [ ] Confirm service root directory `integrations/ck-mcp-adapter/v0.4`.
- [ ] Attach the `ck01-data` 1 GB persistent disk at `/var/data`.
- [ ] Set secret environment variable `CK01_API_KEYS` as `tenant:high-entropy-secret`. For rotation, temporarily provide old and new tenant/key pairs separated by commas, validate the new key, then remove the old key and redeploy.
- [ ] Confirm `CK01_DATABASE_PATH=/var/data/ck01-adapter.sqlite`.
- [ ] Use Render's runtime `PORT`; do not expose an additional port.
- [ ] Confirm the HTTP health-check path is `/healthz`.

## Deployment verification

- [ ] Confirm the temporary `https://<service>.onrender.com` URL has a valid platform-managed TLS certificate and redirects HTTP to HTTPS.
- [ ] Verify `GET /healthz` returns HTTP 200 and reports `ok: true` and `storage: sqlite`.
- [ ] Verify an unauthenticated `POST /mcp` returns HTTP 401.
- [ ] Authenticate, initialize MCP, and list the four CK-01 adapter tools.
- [ ] Propose a uniquely labelled test candidate; confirm `authorization_granted: false` and `state_changed: false`.
- [ ] Record provenance, retrieve the candidate with `ck01_continuity_brief`, and confirm the provenance count.
- [ ] Use a second tenant key and confirm the first tenant's candidate is absent.
- [ ] Restart or redeploy the service and confirm the first tenant can still retrieve the test candidate.

## Backup and restore

- [ ] Confirm Render automatic disk snapshots are active and record their retention in the operations runbook.
- [ ] Schedule an application-consistent SQLite backup using the SQLite backup API or `VACUUM INTO`; include the database plus any required WAL state and copy the result off the service disk.
- [ ] Encrypt off-platform backups, define retention, and restrict restore access.
- [ ] Test restoration into a non-production service before relying on the procedure.
- [ ] Document recovery-point and recovery-time objectives. Do not restore a live SQLite disk snapshot without first stopping writers and validating consistency.

## Operations and security

- [ ] Route Render deploy/runtime logs to the chosen monitoring destination without logging bearer secrets or full assertion content.
- [ ] Alert on repeated 401 responses, `/healthz` failures, restart loops, disk-capacity thresholds, and backup failures.
- [ ] Document the secret owner, rotation interval, emergency revocation procedure, and tenant offboarding process.
- [ ] Define and implement external provenance authentication before treating recorded provenance as verified evidence.
- [ ] Keep the service at one instance while SQLite uses the attached disk; do not enable autoscaling.
- [ ] Do not connect ChatGPT or other production clients until the remote smoke, isolation, and restart-persistence checks all pass.
