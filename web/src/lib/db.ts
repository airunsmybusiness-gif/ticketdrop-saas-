// Server-only Postgres pool. Uses the SAME DATABASE_URL your Streamlit app
// uses (Supabase is Postgres) — set it in .env.local / your host's env vars.
// Never import this from a "use client" component.
import { Pool } from "pg";

let pool: Pool | null = null;

export function db(): Pool {
  if (!pool) {
    const url = process.env.DATABASE_URL;
    if (!url) throw new Error("DATABASE_URL is not set");
    pool = new Pool({
      connectionString: url,
      max: 5,
      // Supabase requires SSL from most hosts; local dev Postgres doesn't.
      ssl: url.includes("supabase.co") ? { rejectUnauthorized: false } : undefined,
    });
  }
  return pool;
}
