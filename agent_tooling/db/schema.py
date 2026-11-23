"""SQLite schema, idempotent migrations, and safe backup/integrity utilities."""
from __future__ import annotations

import hashlib
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

MIGRATIONS: list[tuple[int, str]] = [
    (
        1,
        """
        CREATE TABLE IF NOT EXISTS resources (
            resource_id TEXT PRIMARY KEY,
            kind TEXT NOT NULL CHECK(kind IN ('mcp','plugin','skill','cli','dependency')),
            display_name TEXT NOT NULL,
            source TEXT NOT NULL,
            owner_client TEXT NOT NULL,
            fingerprint TEXT,
            version TEXT,
            risk TEXT NOT NULL DEFAULT 'unknown',
            managed_by TEXT NOT NULL DEFAULT 'manual'
        );

        CREATE TABLE IF NOT EXISTS installations (
            installation_id TEXT PRIMARY KEY,
            resource_id TEXT NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
            client TEXT NOT NULL,
            scope TEXT NOT NULL,
            path_ref TEXT,
            availability TEXT NOT NULL DEFAULT 'unknown',
            detected_enabled INTEGER CHECK(detected_enabled IN (0,1) OR detected_enabled IS NULL),
            last_seen TEXT,
            UNIQUE(resource_id, client, scope, path_ref)
        );
        CREATE INDEX IF NOT EXISTS idx_installations_res_client ON installations(resource_id, client);

        CREATE TABLE IF NOT EXISTS resource_capabilities (
            resource_id TEXT NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
            capability TEXT NOT NULL,
            confidence TEXT NOT NULL DEFAULT 'declared',
            evidence TEXT,
            PRIMARY KEY(resource_id, capability)
        );

        CREATE TABLE IF NOT EXISTS resource_dependencies (
            resource_id TEXT NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
            depends_on_id TEXT NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
            requirement TEXT NOT NULL DEFAULT 'required',
            optional INTEGER NOT NULL DEFAULT 0 CHECK(optional IN (0,1)),
            PRIMARY KEY(resource_id, depends_on_id)
        );

        CREATE TABLE IF NOT EXISTS profiles (
            profile_id TEXT PRIMARY KEY,
            yaml_path TEXT NOT NULL,
            yaml_hash TEXT NOT NULL,
            schema_version INTEGER NOT NULL DEFAULT 1,
            last_validated TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS projects (
            project_id TEXT PRIMARY KEY,
            repo_remote_hash TEXT,
            root_path TEXT NOT NULL,
            identity_strategy TEXT NOT NULL,
            lifecycle_state TEXT NOT NULL DEFAULT 'DISCOVERY',
            last_seen TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_projects_remote ON projects(repo_remote_hash);

        CREATE TABLE IF NOT EXISTS project_profiles (
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            profile_id TEXT NOT NULL,
            decision TEXT NOT NULL,
            approved_at TEXT,
            reason TEXT,
            PRIMARY KEY(project_id, profile_id)
        );

        CREATE TABLE IF NOT EXISTS snapshots (
            snapshot_id TEXT PRIMARY KEY,
            client TEXT NOT NULL,
            project_id TEXT REFERENCES projects(project_id) ON DELETE SET NULL,
            fingerprint TEXT NOT NULL,
            recorded_at TEXT NOT NULL,
            source TEXT NOT NULL
        );

        CREATE TABLE IF NOT EXISTS client_artifacts (
            client TEXT NOT NULL,
            project_id TEXT NOT NULL REFERENCES projects(project_id) ON DELETE CASCADE,
            artifact_path TEXT NOT NULL,
            last_managed_hash TEXT,
            ownership TEXT NOT NULL DEFAULT 'managed',
            PRIMARY KEY(client, project_id, artifact_path)
        );

        CREATE TABLE IF NOT EXISTS changes (
            change_id TEXT PRIMARY KEY,
            project_id TEXT REFERENCES projects(project_id) ON DELETE SET NULL,
            created_at TEXT NOT NULL,
            status TEXT NOT NULL,
            risk TEXT NOT NULL DEFAULT 'LOW',
            approval_ref TEXT,
            preflight_result TEXT
        );
        CREATE INDEX IF NOT EXISTS idx_changes_status ON changes(status);

        CREATE TABLE IF NOT EXISTS change_items (
            change_id TEXT NOT NULL REFERENCES changes(change_id) ON DELETE CASCADE,
            resource_id TEXT NOT NULL,
            target_client TEXT NOT NULL,
            action TEXT NOT NULL,
            before_fp TEXT,
            after_fp TEXT,
            status TEXT NOT NULL,
            PRIMARY KEY(change_id, resource_id, target_client)
        );

        CREATE TABLE IF NOT EXISTS metrics (
            metric_id TEXT PRIMARY KEY,
            client TEXT NOT NULL,
            project_id TEXT REFERENCES projects(project_id) ON DELETE SET NULL,
            metric_name TEXT NOT NULL,
            value REAL,
            unit TEXT,
            source TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_metrics_lookup ON metrics(client, project_id, metric_name, recorded_at);
        """,
    ),
    (
        2,
        """
        CREATE TABLE IF NOT EXISTS client_targets (
            target_id TEXT PRIMARY KEY,
            family TEXT NOT NULL,
            surface TEXT NOT NULL,
            scope TEXT NOT NULL,
            availability TEXT NOT NULL DEFAULT 'unknown',
            last_verified TEXT,
            evidence TEXT,
            UNIQUE(family, surface, scope)
        );

        CREATE TABLE IF NOT EXISTS resource_targets (
            resource_id TEXT NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
            target_id TEXT NOT NULL REFERENCES client_targets(target_id) ON DELETE CASCADE,
            eligibility TEXT NOT NULL DEFAULT 'unknown',
            observed_state TEXT NOT NULL DEFAULT 'unknown',
            desired_state TEXT NOT NULL DEFAULT 'unknown',
            applied_state TEXT NOT NULL DEFAULT 'unknown',
            verified_state TEXT NOT NULL DEFAULT 'unknown',
            evidence TEXT,
            last_seen TEXT,
            PRIMARY KEY(resource_id, target_id)
        );
        CREATE INDEX IF NOT EXISTS idx_resource_targets_target
            ON resource_targets(target_id, eligibility, observed_state);

        CREATE TABLE IF NOT EXISTS distribution_events (
            event_id INTEGER PRIMARY KEY AUTOINCREMENT,
            resource_id TEXT NOT NULL REFERENCES resources(resource_id) ON DELETE CASCADE,
            target_id TEXT NOT NULL REFERENCES client_targets(target_id) ON DELETE CASCADE,
            channel TEXT NOT NULL,
            event TEXT NOT NULL,
            approval_ref TEXT,
            timestamp TEXT NOT NULL
        );
        """,
    ),
    (
        3,
        """
        CREATE TABLE IF NOT EXISTS token_sessions (
            session_id TEXT PRIMARY KEY,
            harness TEXT NOT NULL,
            mode TEXT NOT NULL DEFAULT 'default',
            title_sanitized TEXT NOT NULL DEFAULT '',
            primary_model TEXT NOT NULL DEFAULT 'unknown',
            profile_active TEXT NOT NULL DEFAULT 'unknown',
            started_at TEXT NOT NULL,
            ended_at TEXT NOT NULL,
            calls_count INTEGER NOT NULL DEFAULT 0,
            input_uncached INTEGER NOT NULL DEFAULT 0,
            cache_read INTEGER NOT NULL DEFAULT 0,
            cache_write INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            reasoning_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            cache_hit_ratio REAL NOT NULL DEFAULT 0.0,
            cost_usd REAL NOT NULL DEFAULT 0.0,
            ai_credits REAL NOT NULL DEFAULT 0.0,
            anomaly_count INTEGER NOT NULL DEFAULT 0,
            source_file TEXT NOT NULL DEFAULT '',
            source_mtime REAL NOT NULL DEFAULT 0.0
        );
        CREATE INDEX IF NOT EXISTS idx_token_sessions_harness_started
            ON token_sessions(harness, started_at DESC);
        CREATE INDEX IF NOT EXISTS idx_token_sessions_model
            ON token_sessions(primary_model, started_at DESC);

        CREATE TABLE IF NOT EXISTS token_traces (
            trace_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES token_sessions(session_id) ON DELETE CASCADE,
            turn_index INTEGER NOT NULL DEFAULT 1,
            call_index INTEGER NOT NULL DEFAULT 1,
            timestamp TEXT NOT NULL,
            model TEXT NOT NULL DEFAULT 'unknown',
            input_uncached INTEGER NOT NULL DEFAULT 0,
            cache_read INTEGER NOT NULL DEFAULT 0,
            cache_write INTEGER NOT NULL DEFAULT 0,
            output_tokens INTEGER NOT NULL DEFAULT 0,
            reasoning_tokens INTEGER NOT NULL DEFAULT 0,
            total_tokens INTEGER NOT NULL DEFAULT 0,
            cost_usd REAL NOT NULL DEFAULT 0.0,
            ai_credits REAL NOT NULL DEFAULT 0.0,
            latency_ms REAL NOT NULL DEFAULT 0.0,
            tools_called_json TEXT NOT NULL DEFAULT '[]',
            anomaly_flags_json TEXT NOT NULL DEFAULT '[]'
        );
        CREATE INDEX IF NOT EXISTS idx_token_traces_session_call
            ON token_traces(session_id, call_index);
        CREATE INDEX IF NOT EXISTS idx_token_traces_ts
            ON token_traces(timestamp DESC);

        CREATE TABLE IF NOT EXISTS token_anomalies (
            anomaly_id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL REFERENCES token_sessions(session_id) ON DELETE CASCADE,
            trace_id TEXT,
            rule_code TEXT NOT NULL,
            severity TEXT NOT NULL CHECK(severity IN ('CRITICAL','HIGH','MEDIUM','LOW')),
            detected_at TEXT NOT NULL,
            metric_value REAL NOT NULL DEFAULT 0.0,
            threshold_value REAL NOT NULL DEFAULT 0.0,
            recommendation TEXT NOT NULL DEFAULT ''
        );
        CREATE INDEX IF NOT EXISTS idx_token_anomalies_sev_time
            ON token_anomalies(severity, detected_at DESC);

        CREATE TABLE IF NOT EXISTS telemetry_watermarks (
            source_key TEXT PRIMARY KEY,
            last_mtime REAL NOT NULL DEFAULT 0.0,
            last_cursor TEXT NOT NULL DEFAULT '',
            last_synced_at TEXT NOT NULL
        );
        """,
    ),
]


def connect(db_path: Path) -> sqlite3.Connection:
    """Open SQLite connection with foreign_keys=ON, busy_timeout, and WAL mode."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 5000;")
    conn.execute("PRAGMA journal_mode = WAL;")
    return conn


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Run idempotent schema migrations. Returns list of newly applied versions."""
    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS schema_migrations (
            version INTEGER PRIMARY KEY,
            applied_at TEXT NOT NULL,
            checksum TEXT NOT NULL
        );
        """
    )
    applied = {
        row["version"]
        for row in conn.execute("SELECT version FROM schema_migrations").fetchall()
    }
    newly_applied: list[int] = []
    now = datetime.now(timezone.utc).isoformat()
    for version, sql in MIGRATIONS:
        if version in applied:
            continue
        checksum = hashlib.sha256(sql.encode("utf-8")).hexdigest()
        with conn:
            conn.executescript(sql)
            conn.execute(
                "INSERT INTO schema_migrations(version, applied_at, checksum) VALUES (?, ?, ?)",
                (version, now, checksum),
            )
        newly_applied.append(version)
    return newly_applied


def backup_db(src_path: Path, dest_path: Path) -> str:
    """Consistent online backup using sqlite3.Connection.backup() + integrity_check."""
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    src = sqlite3.connect(str(src_path))
    dst = sqlite3.connect(str(dest_path))
    try:
        src.backup(dst)
        res = dst.execute("PRAGMA integrity_check;").fetchone()[0]
        if res != "ok":
            raise RuntimeError(f"Backup integrity_check failed: {res}")
        return res
    finally:
        dst.close()
        src.close()
