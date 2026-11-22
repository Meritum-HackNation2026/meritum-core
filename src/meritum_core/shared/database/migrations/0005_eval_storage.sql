-- Evaluation runs and the case files staff uploaded (core#124, US-OBS-06, F-28).
-- The worker writes runs and the API reads them, so the API role needs no DDL (the
-- worker's lazy CREATE TABLE and the API's in-memory index are gone). A run is one
-- JSONB document, like the worker stored it; a case file's bytes live in the blob
-- store, here only its id.

CREATE TABLE IF NOT EXISTS eval_runs (
    id text PRIMARY KEY,
    user_id text,
    started_at timestamptz NOT NULL,
    run jsonb NOT NULL
);

CREATE INDEX IF NOT EXISTS eval_runs_started_at ON eval_runs (started_at DESC);

CREATE TABLE IF NOT EXISTS eval_datasets (
    id text PRIMARY KEY,
    name text NOT NULL,
    blob_id text NOT NULL,
    cases integer NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);
