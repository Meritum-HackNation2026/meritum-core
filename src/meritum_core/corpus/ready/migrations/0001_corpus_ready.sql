-- Agent-ready corpus layer (US-KOR-02, US-ZRD-05, F-12, meritum-core#168).
-- Additive only: new tables in the new `corpus_ready` schema; nothing in
-- `corpus` or `app_*` changes. The platform creates the schema (infra db.sh),
-- because the migrating role has no CREATE on the database. Applied only by
-- the worker's corpus_ready build when MERITUM_CORPUS_READY is on, never by the
-- deploy's `meritum-worker-migrate`. Undo: rollback/0001_corpus_ready.sql.
-- No foreign keys to corpus.*: retention and removals there must never be
-- blocked by this layer; the search joins live documents instead.

-- One row per gold build run.
CREATE TABLE IF NOT EXISTS corpus_ready.builds (
    build_id text PRIMARY KEY,
    started_at timestamptz NOT NULL DEFAULT now(),
    finished_at timestamptz,
    documents integer NOT NULL DEFAULT 0,
    chunks integer NOT NULL DEFAULT 0
);

-- Silver: the bronze text cleaned deterministically (no LLM), per document version.
CREATE TABLE IF NOT EXISTS corpus_ready.silver_documents (
    source_id text PRIMARY KEY,
    checksum text NOT NULL,
    text text NOT NULL,
    dropped_chars integer NOT NULL,
    build_id text NOT NULL,
    built_at timestamptz NOT NULL DEFAULT now()
);

-- Gold: retrieval-ready chunks. text = bronze full_text[start_offset:end_offset]
-- of the document version with `checksum`; header is search context, not citable.
CREATE TABLE IF NOT EXISTS corpus_ready.gold_chunks (
    chunk_id text PRIMARY KEY,
    source_id text NOT NULL,
    checksum text NOT NULL,
    start_offset integer NOT NULL CHECK (start_offset >= 0),
    end_offset integer NOT NULL CHECK (end_offset > start_offset),
    text text NOT NULL,
    header text NOT NULL,
    kind text NOT NULL,
    published_on date,
    valid_from date,
    valid_to date,
    eli text,
    subject text,
    topic text,
    numbers jsonb NOT NULL DEFAULT '[]',
    summary text,
    weight real NOT NULL CHECK (weight > 0 AND weight <= 1),
    -- 768 = DEFAULT_DIMENSIONS in meritum_core.shared.embeddings.constants
    embedding vector(768) NOT NULL,
    search_vector tsvector GENERATED ALWAYS AS (
        to_tsvector('public.polish'::regconfig, header || ' ' || text)
    ) STORED,
    build_id text NOT NULL,
    built_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS gold_chunks_source ON corpus_ready.gold_chunks (source_id, checksum);
CREATE INDEX IF NOT EXISTS gold_chunks_search_vector
    ON corpus_ready.gold_chunks USING gin (search_vector);
CREATE INDEX IF NOT EXISTS gold_chunks_embedding
    ON corpus_ready.gold_chunks USING hnsw (embedding vector_cosine_ops);
