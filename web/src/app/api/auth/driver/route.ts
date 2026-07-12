// POST { name, pin } → verifies the driver's PIN against the bcrypt
// pin_hash in the existing users table and sets an httpOnly session cookie.
import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { db } from "@/lib/db";
import { createDriverSession } from "@/lib/session";
import { handle, readJson, requireString, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

export const POST = handle("driver_login", async (req, { requestId }) => {
  const body = await readJson(req);
  const name = requireString(body.name, "Name", 100);
  const pin = requireString(body.pin, "PIN", 20);
  if (pin.length < 4) throw new ApiError(400, "PIN must be at least 4 digits");

  // Case-insensitive name match among active drivers. Also accepts a partial
  // first-name match when it's unambiguous ("John" → "John Driver").
  const { rows } = await db().query(
    `SELECT id, name, company_id, role, pin_hash, pin
     FROM users
     WHERE role = 'driver' AND active = TRUE
       AND (LOWER(name) = LOWER($1) OR LOWER(name) LIKE LOWER($1) || ' %')`,
    [name]
  );
  if (rows.length !== 1) {
    // 0 = unknown name; >1 = ambiguous — same response so names can't be probed
    log.warn("driver_login_failed", { requestId, matches: rows.length });
    throw new ApiError(401, "Wrong name or PIN");
  }
  const u = rows[0];
  const ok = u.pin_hash
    ? await bcrypt.compare(pin, u.pin_hash)
    : Boolean(u.pin) && pin === String(u.pin); // legacy plaintext fallback
  if (!ok) {
    log.warn("driver_login_failed", { requestId, user_id: u.id });
    throw new ApiError(401, "Wrong name or PIN");
  }

  await createDriverSession({
    user_id: u.id,
    name: u.name,
    company_id: u.company_id,
    role: u.role,
  });
  log.info("driver_login_success", { requestId, user_id: u.id, company_id: u.company_id });
  return NextResponse.json({ ok: true, name: u.name });
});
