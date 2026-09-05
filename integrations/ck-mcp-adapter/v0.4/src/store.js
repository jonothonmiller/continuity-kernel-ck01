// Copyright 2026 Jon Miller. SPDX-License-Identifier: Apache-2.0
import { DatabaseSync } from "node:sqlite";
import { mkdirSync } from "node:fs";
import { dirname } from "node:path";
import { randomUUID } from "node:crypto";

export class Store {
  constructor(path) { mkdirSync(dirname(path), { recursive: true }); this.db=new DatabaseSync(path); this.db.exec(`PRAGMA journal_mode=WAL; CREATE TABLE IF NOT EXISTS candidates(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,claim TEXT NOT NULL,status TEXT NOT NULL DEFAULT 'PROPOSED',created_at TEXT NOT NULL,superseded_by TEXT); CREATE TABLE IF NOT EXISTS provenance(id TEXT PRIMARY KEY,tenant TEXT NOT NULL,candidate_id TEXT NOT NULL,source_id TEXT NOT NULL,statement TEXT NOT NULL,created_at TEXT NOT NULL,FOREIGN KEY(candidate_id) REFERENCES candidates(id)); CREATE INDEX IF NOT EXISTS candidate_tenant ON candidates(tenant,created_at); CREATE INDEX IF NOT EXISTS provenance_tenant ON provenance(tenant,candidate_id);`); }
  propose(tenant,claim){const id=randomUUID(),now=new Date().toISOString();this.db.prepare("INSERT INTO candidates(id,tenant,claim,created_at) VALUES(?,?,?,?)").run(id,tenant,claim,now);return {id,status:"PROPOSED",created_at:now,authorization_granted:false,state_changed:false};}
  provenance(tenant,candidateId,sourceId,statement){const c=this.db.prepare("SELECT id FROM candidates WHERE id=? AND tenant=?").get(candidateId,tenant);if(!c) throw new Error("candidate_not_found");const id=randomUUID(),now=new Date().toISOString();this.db.prepare("INSERT INTO provenance VALUES(?,?,?,?,?,?)").run(id,tenant,candidateId,sourceId,statement,now);return {id,candidate_id:candidateId,created_at:now};}
  supersede(tenant,id,replacement){const r=this.db.prepare("UPDATE candidates SET status='SUPERSEDED',superseded_by=? WHERE id=? AND tenant=? AND status='PROPOSED'").run(replacement,id,tenant);if(!r.changes) throw new Error("candidate_not_found_or_not_active");return {id,status:"SUPERSEDED",superseded_by:replacement,state_changed:false};}
  brief(tenant){return this.db.prepare("SELECT c.*,COUNT(p.id) provenance_count FROM candidates c LEFT JOIN provenance p ON p.candidate_id=c.id AND p.tenant=c.tenant WHERE c.tenant=? GROUP BY c.id ORDER BY c.created_at DESC LIMIT 50").all(tenant);}
  health(){return this.db.prepare("SELECT 1 AS ok").get().ok===1;}
  close(){this.db.close();}
}

