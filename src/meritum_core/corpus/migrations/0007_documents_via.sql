-- How each document reached the corpus (US-KOR-03, F-13): the same values as
-- SourceVia in meritum_core.checks.contracts. Written by the worker's ingestion
-- (meritum-worker#22 writes rss). Rows from before this migration came from the
-- catalogue ingestion and get the contract's default, corpus.
-- Backward compatible only: add, never drop or rename; deploys from main run it.
-- The inline CHECK is added together with the column, so a second run is a no-op.
ALTER TABLE corpus.documents
    ADD COLUMN IF NOT EXISTS via text NOT NULL DEFAULT 'corpus'
        CONSTRAINT documents_via_known CHECK (via IN ('corpus', 'rss', 'web_search', 'mcp'));
