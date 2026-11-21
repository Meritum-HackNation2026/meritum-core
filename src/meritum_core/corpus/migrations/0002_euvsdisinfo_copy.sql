-- Local copy of EUvsDisinfo in the shared `corpus` schema (US-KOR-08, F-11, ADR-26).
-- Written only by the worker's euvsdisinfo_sync workflow (meritum-worker#59).
-- Backward compatible only: add, never drop or rename; deploys from main run it.

-- One row per case or article; deleted entries stay with deleted_at set.
CREATE TABLE IF NOT EXISTS corpus.euvsdisinfo_entries (
    key text PRIMARY KEY,
    kind text NOT NULL CHECK (kind IN ('case', 'article')),
    -- The worker's corpus.Entry as JSON (title, url, dates, texts, domains): the
    -- worker alone reads and writes it, so its fields change without a migration.
    entry jsonb NOT NULL,
    -- 768 = DEFAULT_DIMENSIONS in meritum_core.shared.embeddings.constants
    description_embedding vector(768) NOT NULL,
    fact_embedding vector(768),
    -- meritum_core.checks.contracts.Source of the fact text; NULL for articles.
    source jsonb,
    deleted_at timestamptz
);

-- Domains the domain warning reads, rebuilt by every sync.
CREATE TABLE IF NOT EXISTS corpus.euvsdisinfo_flagged_domains (
    domain text PRIMARY KEY,
    case_keys text[] NOT NULL
);
