-- Copies of public pages archived on a citizen's request (core#144, US-KOR-07, F-38).
-- The worker writes a row per copy, the API reads and deletes it; the text itself
-- lives in the blob store under blob_id. Numbered 0008 because 0006 and 0007 are
-- taken by the corpus schema.

CREATE TABLE IF NOT EXISTS page_archives (
    archive_id text PRIMARY KEY,
    blob_id text NOT NULL,
    url text NOT NULL,
    owner_id text NOT NULL,
    sha256 text NOT NULL,
    archived_at timestamptz NOT NULL,
    expires_at timestamptz NOT NULL,
    legal_basis text NOT NULL,
    access_rule text NOT NULL,
    deletion_procedure text NOT NULL
);

-- The rate limit counts one person's copies in the last hour.
CREATE INDEX IF NOT EXISTS page_archives_owner_archived_at
    ON page_archives (owner_id, archived_at);
