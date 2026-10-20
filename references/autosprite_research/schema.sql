-- SQLite Database Schema extracted from autosprite.app (Sloth Studio)
-- Managed internally via Go / uptrace/bun migrations

PRAGMA foreign_keys = ON;

-- 1. Tasks / Jobs Queue
CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  type TEXT NOT NULL CHECK (type IN ('spritegen', 'sprite-sheet', 'text-file')),
  payload TEXT NOT NULL,
  status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'blocked', 'done', 'failed', 'cancelled')),
  progress INTEGER NOT NULL DEFAULT 0,
  attempts INTEGER NOT NULL DEFAULT 0,
  run_after TEXT NOT NULL,
  result TEXT NOT NULL DEFAULT '',
  error TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL
);

-- 2. Assets Storage Management
CREATE TABLE IF NOT EXISTS spritegen_assets (
  kind TEXT NOT NULL,                  -- 'still', 'walkVideo', 'walkChroma', 'loopFrames'
  direction TEXT NOT NULL DEFAULT '',  -- 'front', 'front-right', 'right', 'back-right', 'back', 'back-left', 'left', 'front-left'
  path TEXT NOT NULL,
  job_id TEXT,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (kind, direction),
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);

-- 3. Application Settings (OpenRouter Key, etc.)
CREATE TABLE IF NOT EXISTS settings (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);

-- 4. License State Management
CREATE TABLE IF NOT EXISTS local_license_state (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  machine_id TEXT NOT NULL,
  state TEXT NOT NULL,
  usage_count INTEGER NOT NULL CHECK (usage_count >= 0),
  issued_at INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  signed_receipt TEXT NOT NULL,
  checked_at TEXT NOT NULL
);

-- 5. Execution Receipts
CREATE TABLE IF NOT EXISTS local_receipts (
  job_id TEXT PRIMARY KEY,
  receipt TEXT NOT NULL,
  authorized_at TEXT NOT NULL,
  FOREIGN KEY (job_id) REFERENCES jobs(id)
);
