-- Panel roles granted by an administrator (US-MOD-05, F-25). The backend's staff
-- gate reads them; addresses are stored lower-cased (StaffAccount.email).

CREATE TABLE IF NOT EXISTS staff_accounts (
    email text PRIMARY KEY CHECK (email = lower(email)),
    role text NOT NULL CHECK (role IN ('moderator', 'analyst', 'admin'))
);
