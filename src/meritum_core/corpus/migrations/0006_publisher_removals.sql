-- Ledger of publisher removal requests in the shared `corpus` schema (US-KOR-05,
-- F-10, ADR-13). Written only by the worker's publisher_removal workflow
-- (meritum-worker#77), in the same transaction that deletes the documents and
-- passages, so the 7-day deadline can be shown afterwards.
-- Numbered 0006 after the app schema's 0004 and 0005; files run in name order.
-- Backward compatible only: add, never drop or rename; deploys from main run it.

-- One row per request; documents is how many corpus.documents rows it removed.
CREATE TABLE IF NOT EXISTS corpus.publisher_removals (
    url text NOT NULL,
    publisher_id text NOT NULL,
    requested_at timestamptz NOT NULL,
    removed_at timestamptz NOT NULL,
    documents integer NOT NULL CHECK (documents >= 0),
    PRIMARY KEY (url, publisher_id, requested_at)
);
