-- TicketDrop schema.
-- Safe to run on your EXISTING Supabase database: every statement uses
-- IF NOT EXISTS, so it only adds what's missing and never drops data.
--
-- Run it in Supabase → SQL Editor, or with: psql "$DATABASE_URL" -f schema.sql

-- ============================================================
-- 1) MULTI-COMPANY BRANDING  (the new bit)
-- ============================================================
CREATE TABLE IF NOT EXISTS companies (
    id            SERIAL PRIMARY KEY,
    name          TEXT NOT NULL,
    tagline       TEXT DEFAULT 'Dispatch & Field Ticketing',
    primary_color TEXT DEFAULT '#8B5CF6',
    phone         TEXT,
    address       TEXT,
    logo_url      TEXT,
    active        BOOLEAN DEFAULT TRUE,
    created_at    TIMESTAMP DEFAULT NOW()
);

-- Your first company (id 1 matches the data you already have).
INSERT INTO companies (id, name, tagline, primary_color, phone, address)
VALUES (1, 'Rick''s Oilfield Hauling', 'Oilfield Hauling · Digital Field Tickets',
        '#8B5CF6', '(780) 942-2932', '4606 51 Ave, Redwater AB')
ON CONFLICT (id) DO NOTHING;

-- ============================================================
-- 2) SECURE LOGIN  (add hashed-PIN column to users)
-- ============================================================
ALTER TABLE users ADD COLUMN IF NOT EXISTS pin_hash TEXT;

-- ============================================================
-- 3) FULL SCHEMA  (for a brand-new database; no-ops if tables exist)
-- ============================================================
CREATE TABLE IF NOT EXISTS users (
    id          SERIAL PRIMARY KEY,
    company_id  INTEGER NOT NULL REFERENCES companies(id),
    name        TEXT NOT NULL,
    email       TEXT,
    role        TEXT NOT NULL DEFAULT 'driver',   -- driver | dispatch | ar | admin
    pin         TEXT,                             -- legacy plaintext (migrate away)
    pin_hash    TEXT,                             -- bcrypt hash (preferred)
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS settings (
    id          SERIAL PRIMARY KEY,
    company_id  INTEGER NOT NULL REFERENCES companies(id),
    category    TEXT NOT NULL,                    -- trucks | trailers | customers
    value       TEXT NOT NULL,
    active      BOOLEAN DEFAULT TRUE,
    created_at  TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS loads (
    id                 SERIAL PRIMARY KEY,
    company_id         INTEGER NOT NULL REFERENCES companies(id),
    customer           TEXT,
    pickup_location    TEXT,
    delivery_location  TEXT,
    driver_id          INTEGER REFERENCES users(id),
    truck              TEXT,
    trailer            TEXT,
    notes              TEXT,
    po_number          TEXT,
    safety_number      TEXT,
    status             TEXT NOT NULL DEFAULT 'ASSIGNED',
    created_by         INTEGER,
    created_at         TIMESTAMP DEFAULT NOW(),
    status_changed_at  TIMESTAMP DEFAULT NOW(),
    status_changed_by  INTEGER,
    updated_at         TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS tickets (
    id                      SERIAL PRIMARY KEY,
    company_id              INTEGER NOT NULL REFERENCES companies(id),
    load_id                 INTEGER REFERENCES loads(id),
    ticket_number           TEXT,
    customer_ticket_number  TEXT,
    ticket_date             DATE,
    operator_name           TEXT,
    truck_number            TEXT,
    trailer_number          TEXT,
    customer_name           TEXT,
    loaded_at               TEXT,
    load_tank               TEXT,
    load_riser              TEXT,
    arrive_load_datetime    TIMESTAMP,
    depart_load_datetime    TIMESTAMP,
    load_start_volume       NUMERIC,
    load_end_volume         NUMERIC,
    offloaded_at            TEXT,
    offload_tank            TEXT,
    offload_riser           TEXT,
    arrive_offload_datetime TIMESTAMP,
    depart_offload_datetime TIMESTAMP,
    product_description     TEXT,
    commodity               TEXT,
    transport_placard       TEXT,
    last_contained          TEXT,
    density                 NUMERIC,
    bsw_cut                 NUMERIC,
    estimated_volume        NUMERIC,
    actual_volume           NUMERIC,
    hours_charged           NUMERIC,
    road_ban                BOOLEAN DEFAULT FALSE,
    driver_signature        TEXT,
    signature_datetime      TIMESTAMP,
    status                  TEXT NOT NULL DEFAULT 'SUBMITTED',
    invoiced_at             TIMESTAMP,
    created_at              TIMESTAMP DEFAULT NOW(),
    status_changed_at       TIMESTAMP DEFAULT NOW(),
    status_changed_by       INTEGER,
    updated_at              TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS load_status_history (
    id              SERIAL PRIMARY KEY,
    load_id         INTEGER NOT NULL REFERENCES loads(id),
    old_status      TEXT,
    new_status      TEXT NOT NULL,
    changed_by      INTEGER,
    changed_by_name TEXT,
    reason          TEXT,
    changed_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS ticket_status_history (
    id              SERIAL PRIMARY KEY,
    ticket_id       INTEGER NOT NULL REFERENCES tickets(id),
    old_status      TEXT,
    new_status      TEXT NOT NULL,
    changed_by      INTEGER,
    changed_by_name TEXT,
    reason          TEXT,
    changed_at      TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS axon_exports (
    id           SERIAL PRIMARY KEY,
    company_id   INTEGER NOT NULL REFERENCES companies(id),
    filename     TEXT,
    ticket_count INTEGER,
    ticket_ids   INTEGER[],
    total_volume NUMERIC,
    checksum     TEXT,
    exported_by  INTEGER,
    exported_at  TIMESTAMP DEFAULT NOW(),
    status       TEXT DEFAULT 'EXPORTED'
);

-- ============================================================
-- 4) INDEXES  (speed as data grows)
-- ============================================================
CREATE INDEX IF NOT EXISTS idx_loads_company_status   ON loads (company_id, status);
CREATE INDEX IF NOT EXISTS idx_tickets_company_status ON tickets (company_id, status);
CREATE INDEX IF NOT EXISTS idx_users_company_role     ON users (company_id, role, active);
CREATE INDEX IF NOT EXISTS idx_settings_company_cat   ON settings (company_id, category, active);

-- ============================================================
-- 5) INVOICING  (PDF invoices + per-company rates)
-- ============================================================
ALTER TABLE companies ADD COLUMN IF NOT EXISTS rate_per_m3    NUMERIC DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS rate_per_hour  NUMERIC DEFAULT 0;
ALTER TABLE companies ADD COLUMN IF NOT EXISTS tax_rate       NUMERIC DEFAULT 5;      -- percent
ALTER TABLE companies ADD COLUMN IF NOT EXISTS tax_label      TEXT DEFAULT 'GST';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS invoice_prefix TEXT DEFAULT 'INV-';
ALTER TABLE companies ADD COLUMN IF NOT EXISTS invoice_terms  TEXT DEFAULT 'Payment due within 30 days.';

CREATE TABLE IF NOT EXISTS invoices (
    id             SERIAL PRIMARY KEY,
    company_id     INTEGER NOT NULL REFERENCES companies(id),
    invoice_number TEXT NOT NULL,
    customer_name  TEXT,
    ticket_ids     INTEGER[],
    subtotal       NUMERIC,
    tax            NUMERIC,
    total          NUMERIC,
    notes          TEXT,
    created_by     INTEGER,
    created_at     TIMESTAMP DEFAULT NOW()
);
CREATE INDEX IF NOT EXISTS idx_invoices_company ON invoices (company_id, created_at);

-- ============================================================
-- 6) FIELD TICKET PDF  (hazards checklist + backup load photo)
-- ============================================================
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS hazards         TEXT[];  -- ticked hazard labels
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS hazard_notes    TEXT;    -- free text for "Other"
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS load_photo      BYTEA;   -- backup photo of the load
ALTER TABLE tickets ADD COLUMN IF NOT EXISTS load_photo_mime TEXT;
