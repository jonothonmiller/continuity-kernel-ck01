import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createApp } from "../src/server.js";

async function listen(app) {
  const listener = app.listen(0, "127.0.0.1");
  await new Promise((resolve) => listener.once("listening", resolve));
  return listener;
}

test("unauthenticated MCP requests are rejected", async () => {
  const { app, store } = createApp({
    databasePath: join(mkdtempSync(join(tmpdir(), "ck01-auth-")), "db.sqlite"),
    apiKeys: { secret: "tenant-a" },
  });
  const listener = await listen(app);
  try {
    const response = await fetch(`http://127.0.0.1:${listener.address().port}/mcp`, {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ jsonrpc: "2.0", id: 1, method: "tools/list", params: {} }),
    });
    assert.equal(response.status, 401);
    assert.deepEqual(await response.json(), { error: "authenticated tenant context required" });
  } finally {
    await new Promise((resolve) => listener.close(resolve));
    store.close();
  }
});

test("SQLite records survive an application restart", () => {
  const databasePath = join(mkdtempSync(join(tmpdir(), "ck01-restart-")), "db.sqlite");
  const first = createApp({ databasePath, apiKeys: {} });
  const candidate = first.store.propose("tenant-a", "restart-persistence-probe");
  first.store.close();

  const second = createApp({ databasePath, apiKeys: {} });
  try {
    const restored = second.store.brief("tenant-a");
    assert.equal(restored.length, 1);
    assert.equal(restored[0].id, candidate.id);
    assert.equal(second.store.brief("tenant-b").length, 0);
  } finally {
    second.store.close();
  }
});
