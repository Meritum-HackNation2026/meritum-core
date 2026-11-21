-- core#74. Checks removed from moderator cases (deleted person or retention): a case
-- read before the removal and saved after it must not bring them back. Holds only
-- random check ids, never personal data.
CREATE TABLE IF NOT EXISTS removed_case_checks (
    check_id text PRIMARY KEY,
    removed_at timestamptz NOT NULL DEFAULT now()
);

-- Erasing a person deletes the notifications about their checks by check_id.
CREATE INDEX IF NOT EXISTS notifications_check_id
    ON notifications ((body ->> 'check_id'));
