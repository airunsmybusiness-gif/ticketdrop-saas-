// Server-only Postgres pool. Uses the SAME DATABASE_URL your Streamlit app
// uses (Supabase is Postgres) — set it in .env.local / your host's env vars.
// Never import this from a "use client" component.
import { Pool } from "pg";
import { log } from "@/lib/log";

let pool: Pool | null = null;

export function db(): Pool {
  if (!pool) {
    const url = process.env.DATABASE_URL;
    if (!url) throw new Error("DATABASE_URL is not set");
    pool = new Pool({
      connectionString: url,
      max: 5,
      // Fail fast instead of hanging forever on a bad connection:
      connectionTimeoutMillis: 8_000, // give up connecting after 8s
      idleTimeoutMillis: 30_000,
      // Kill any query that runs longer than 15s (nothing in this app should)
      statement_timeout: 15_000,
      // Supabase requires SSL from most hosts; local dev Postgres doesn't.
      ssl: url.includes("supabase.co") ? { rejectUnauthorized: false } : undefined,
    });
    // A dropped idle connection must never crash the server process.
    pool.on("error", (e) => log.error("db_pool_error", { error: e.message }));
  }
  return pool;
}

// Quick connectivity probe used by /api/health.
export async function dbPing(): Promise<{ ok: boolean; ms: number; error?: string }> {
  const started = Date.now();
  try {
    await db().query("SELECT 1");
    return { ok: true, ms: Date.now() - started };
  } catch (e) {
    return { ok: false, ms: Date.now() - started, error: e instanceof Error ? e.message : String(e) };
  }
}
