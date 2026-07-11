-- TicketDrop starter accounts (run AFTER schema.sql, in Supabase SQL Editor).
-- Each PIN is stored as a secure bcrypt hash. Change these PINs in Settings after first login.
--
--   Admin     PIN 246810
--   Dispatch  PIN 135790
--   Billing   PIN 112233
--
-- Safe to re-run: it won't create duplicates.

INSERT INTO users (company_id, name, role, pin_hash, active)
SELECT 1, v.name, v.role, v.pin_hash, TRUE
FROM (VALUES
  ('Admin', 'admin', '$2b$12$pn0xl.IGGe.PhWC5wqaKGuLpLQTggWJLDLQcNG3PiOlo0.xnSvP4q'),
  ('Dispatch', 'dispatch', '$2b$12$PQjWcvG3HhMLRIO7FHsM1OEG/l6IO.OGV.zlMWByazqlyYONx1T.K'),
  ('Billing', 'ar', '$2b$12$QnpS75bBXDzogD/PZ6riE.f.4O/ABDGwuOL.tXOh.RK5SbTuuMTJm')
) AS v(name, role, pin_hash)
WHERE NOT EXISTS (
    SELECT 1 FROM users u
    WHERE u.company_id = 1 AND u.name = v.name AND u.role = v.role
);

-- Give any EXISTING drivers a starting PIN of 1234 (only if they have none yet).
UPDATE users
SET pin_hash = '$2b$12$xBD6cFT7Lc/AaZgJGu7G7uLvTY2KSMc84eYlSSQ99ClQdXY5fJO.2'
WHERE company_id = 1 AND role = 'driver' AND pin_hash IS NULL;
