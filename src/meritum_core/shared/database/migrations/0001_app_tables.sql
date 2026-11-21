-- App tables of one environment (ADR-03, ADR-13). No schema name here: the tables
-- go to the first schema of the connection's search_path (app_dev or app_prd,
-- infra#12). The corpus schema has its own migrations (corpus/migrations).
-- Each table keeps the whole contract model as jsonb, plus the columns that the
-- repositories filter and sort on.

CREATE TABLE IF NOT EXISTS check_records (
    check_id text PRIMARY KEY,
    session_id text NOT NULL,
    user_id text,
    channel_user_hash text,
    received_at timestamptz NOT NULL,
    retention_until timestamptz NOT NULL,
    record jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS check_records_session_id ON check_records (session_id);
CREATE INDEX IF NOT EXISTS check_records_user_id ON check_records (user_id);
CREATE INDEX IF NOT EXISTS check_records_channel_user_hash
    ON check_records (channel_user_hash);
CREATE INDEX IF NOT EXISTS check_records_retention_until
    ON check_records (retention_until);

CREATE TABLE IF NOT EXISTS moderator_cases (
    id text PRIMARY KEY,
    state text NOT NULL,
    last_seen timestamptz NOT NULL,
    body jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS moderator_cases_state_last_seen
    ON moderator_cases (state, last_seen DESC);
CREATE INDEX IF NOT EXISTS moderator_cases_claims
    ON moderator_cases USING gin ((body -> 'claims') jsonb_path_ops);

CREATE TABLE IF NOT EXISTS high_risk_topics (
    name text PRIMARY KEY,
    keywords text[] NOT NULL
);

CREATE TABLE IF NOT EXISTS notifications (
    id text PRIMARY KEY,
    session_id text,
    user_id text,
    created_at timestamptz NOT NULL,
    retention_until timestamptz NOT NULL,
    body jsonb NOT NULL
);
CREATE INDEX IF NOT EXISTS notifications_session_id ON notifications (session_id);
CREATE INDEX IF NOT EXISTS notifications_user_id ON notifications (user_id);
CREATE INDEX IF NOT EXISTS notifications_retention_until
    ON notifications (retention_until);
