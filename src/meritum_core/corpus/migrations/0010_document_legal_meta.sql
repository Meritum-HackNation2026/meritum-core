-- What ELI says about the legal act a corpus document holds (US-KOR-02, US-ZRD-05,
-- F-12, meritum-core#167). Field names are agreed on meritum-worker#162. Written
-- by the worker's ELI ingestion, read by corpus_ready and the evidence steps.
-- A separate 1:1 table, not new columns: corpus.documents, the snapshot manifest
-- and every query on them stay as they are, and a page outside ELI has no row.
-- Numbered 0010 after the app schema's 0008 and 0009; files run in name order.
-- Backward compatible only: add, never drop or rename; deploys from main run it.
CREATE TABLE IF NOT EXISTS corpus.document_legal_meta (
    source_id text PRIMARY KEY
        REFERENCES corpus.documents (source_id) ON DELETE CASCADE,
    eli text NOT NULL,
    document_type text NOT NULL,
    legal_status text NOT NULL,
    in_force boolean NOT NULL,
    in_force_from date,
    in_force_until date,
    journal_publisher text NOT NULL,
    journal_year integer NOT NULL,
    journal_position integer NOT NULL,
    display_address text NOT NULL,
    updated_at timestamptz NOT NULL DEFAULT now()
);

-- corpus_ready looks acts up by ELI and filters on when they stop being in force.
CREATE INDEX IF NOT EXISTS document_legal_meta_eli ON corpus.document_legal_meta (eli);
CREATE INDEX IF NOT EXISTS document_legal_meta_in_force_until
    ON corpus.document_legal_meta (in_force_until);
