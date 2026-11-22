-- Tables only the API reads and writes, made here because the API role has no
-- DDL in the app schema (meritum-infra db.sh); the worker runs this as owner and
-- the API gets SELECT, INSERT, UPDATE and DELETE through default privileges.
-- The backend used to create them on first use (backend#85).

-- Result cache shared by every channel (backend#25, US-WTY-03, F-05): results by input
-- key, and each check's key with what a hit was served.
CREATE TABLE IF NOT EXISTS result_cache (
    key text PRIMARY KEY,
    entry jsonb NOT NULL,
    expires_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS result_cache_checks (
    check_id text PRIMARY KEY,
    key text NOT NULL,
    served jsonb,
    linked_at timestamptz NOT NULL DEFAULT now()
);

-- Jury links (US-OBS-06, F-28): only token digests and expiry timestamps.
CREATE TABLE IF NOT EXISTS jury_links (
    token_hash bytea PRIMARY KEY,
    expires_at timestamptz NOT NULL
);

-- Rate limit counters shared by every API instance (ADR-18): hits per hashed key
-- and fixed window.
CREATE TABLE IF NOT EXISTS rate_limit_hits (
    key text NOT NULL,
    window_start timestamptz NOT NULL,
    hits integer NOT NULL,
    PRIMARY KEY (key, window_start)
);

CREATE INDEX IF NOT EXISTS rate_limit_hits_window_start
ON rate_limit_hits (window_start);
