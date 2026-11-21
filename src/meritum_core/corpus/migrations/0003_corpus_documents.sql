-- Catalogue documents, ingestion attempts and snapshot manifests in the shared `corpus` schema
-- (US-KOR-02, US-KOR-05, F-10, F-12, ADR-19, ADR-32). Written only by the
-- worker's catalogue ingestion and snapshot workflows (meritum-worker#17).
-- Backward compatible only: add, never drop or rename; deploys from main run it.

-- One row per fetched URL; its passages in corpus.passages share source_id.
-- full_text is for the system only (search, re-chunking); users see passages.
-- Retention (meritum-worker#24) clears full_text 90 days after fetched_at and
-- keeps the row; a refetch moves fetched_at, so the period starts again.
CREATE TABLE IF NOT EXISTS corpus.documents (
    source_id text PRIMARY KEY,
    url text NOT NULL UNIQUE,
    -- Catalogue domain and the metadata copied from its CatalogEntry.
    domain text NOT NULL,
    publisher_id text NOT NULL,
    license text NOT NULL,
    published_on date,
    fetched_at timestamptz NOT NULL,
    -- sha256 of full_text: an unchanged page keeps its passages.
    checksum text NOT NULL,
    full_text text,
    added_at timestamptz NOT NULL DEFAULT now(),
    retired_at timestamptz
);

CREATE INDEX IF NOT EXISTS documents_fetched_at ON corpus.documents (fetched_at);
CREATE INDEX IF NOT EXISTS documents_domain ON corpus.documents (domain);

-- What one corpus_version saw: each live document with its checksum and fetch
-- time, written in the same transaction as the corpus.snapshots row.
CREATE TABLE IF NOT EXISTS corpus.snapshot_manifest (
    version text NOT NULL REFERENCES corpus.snapshots (version),
    source_id text NOT NULL,
    checksum text NOT NULL,
    fetched_at timestamptz NOT NULL,
    PRIMARY KEY (version, source_id)
);

-- Last catalogue ingestion attempt per catalogue domain, whether or not a page
-- was stored, so a domain whose pages all fail waits its refresh_minutes too.
CREATE TABLE IF NOT EXISTS corpus.ingest_attempts (
    domain text PRIMARY KEY,
    attempted_at timestamptz NOT NULL
);
