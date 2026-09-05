import test from "node:test";
import assert from "node:assert/strict";
import { mkdtempSync } from "node:fs";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { createApp } from "../src/server.js";

test("healthz checks SQLite availability", async () => {
  const { app, store } = createApp({
    databasePath: join(mkdtempSync(join(tmpdir(), "ck01-health-")), "db.sqlite"),
    apiKeys: {},
  });
  const listener = app.listen(0, "127.0.0.1");
  await new Promise((resolve) => listener.once("listening", resolve));
  try {
    const response = await fetch(`http://127.0.0.1:${listener.address().port}/healthz`);
    assert.equal(response.status, 200);
    assert.deepEqual(await response.json(), {
      ok: true,
      name: "Continuity Kernel / CK-01",
      version: "0.4.0",
      storage: "sqlite",
    });
  } finally {
    await new Promise((resolve) => listener.close(resolve));
    store.close();
  }
});
