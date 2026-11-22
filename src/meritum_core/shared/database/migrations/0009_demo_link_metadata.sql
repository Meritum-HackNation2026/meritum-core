-- Metadata for reusable demo links (meritum-backend#126).
-- The digest and deadline stay in jury_links. Legacy links have no metadata.
CREATE TABLE IF NOT EXISTS demo_link_metadata (
    token_hash bytea PRIMARY KEY REFERENCES jury_links(token_hash) ON DELETE CASCADE,
    account text NOT NULL CHECK (account IN ('obywatel', 'admin')),
    issued_at timestamptz NOT NULL
);
