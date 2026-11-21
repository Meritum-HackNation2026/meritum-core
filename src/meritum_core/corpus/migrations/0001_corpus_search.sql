-- Corpus search tables in the shared `corpus` schema (ADR-04, ADR-19, ADR-32).
-- Backward compatible only: add, never drop or rename; deploys from main run it.
-- Needs the infra image (pgvector + hunspell-pl with the `public.polish` config).
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS pg_trgm;
CREATE SCHEMA IF NOT EXISTS corpus;

-- A snapshot (corpus_version) sees the passages with added_at <= taken_at and
-- no retired_at at or before taken_at. Passages are append-only: a changed or
-- withdrawn document gets retired_at (and new passage ids for new text), so
-- old snapshots keep the text they saw; only retention deletes rows.
-- The snapshot workflow writes taken_at after the ingestion transactions it
-- covers have committed, so a later commit cannot change a published snapshot.
CREATE TABLE IF NOT EXISTS corpus.snapshots (
    version text PRIMARY KEY,
    taken_at timestamptz NOT NULL
);

CREATE TABLE IF NOT EXISTS corpus.passages (
    passage_id text PRIMARY KEY,
    source_id text NOT NULL,
    text text NOT NULL,
    published_on date,
    fetched_at timestamptz NOT NULL,
    added_at timestamptz NOT NULL DEFAULT now(),
    retired_at timestamptz,
    -- 768 = DEFAULT_DIMENSIONS in meritum_core.shared.embeddings.constants
    embedding vector(768) NOT NULL,
    search_vector tsvector
        GENERATED ALWAYS AS (to_tsvector('public.polish'::regconfig, text)) STORED
);

CREATE INDEX IF NOT EXISTS passages_added_at ON corpus.passages (added_at);
CREATE INDEX IF NOT EXISTS passages_search_vector
    ON corpus.passages USING gin (search_vector);
CREATE INDEX IF NOT EXISTS passages_text_trgm
    ON corpus.passages USING gin (text gin_trgm_ops);
CREATE INDEX IF NOT EXISTS passages_embedding
    ON corpus.passages USING hnsw (embedding vector_cosine_ops);
