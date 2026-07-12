// POST { name, pin } → sign in office staff (dispatch / admin / AR) with the
// same Name + PIN accounts the Streamlit app uses. Same session cookie
// mechanism as drivers, but scoped to office roles.
import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { db } from "@/lib/db";
import { createDriverSession } from "@/lib/session";
import { handle, readJson, requireString, ApiError } from "@/lib/api";
import { log } from "@/lib/log";

export const POST = handle("office_login", async (req, { requestId }) => {
  const body = await readJson(req);
  const name = requireString(body.name, "Name", 100);
  const pin = requireString(body.pin, "PIN", 20);
  if (pin.length < 4) throw new ApiError(400, "PIN must be at least 4 digits");

  const { rows } = await db().query(
    `SELECT id, name, company_id, role, pin_hash, pin
     FROM users
     WHERE role IN ('dispatch','admin','ar') AND active = TRUE
       AND (LOWER(name) = LOWER($1) OR LOWER(name) LIKE LOWER($1) || ' %')`,
    [name]
  );
  if (rows.length !== 1) {
    log.warn("office_login_failed", { requestId, matches: rows.length });
    throw new ApiError(401, "Wrong name or PIN");
  }
  const u = rows[0];
  const ok = u.pin_hash
    ? await bcrypt.compare(pin, u.pin_hash)
    : Boolean(u.pin) && pin === String(u.pin);
  if (!ok) {
    log.warn("office_login_failed", { requestId, user_id: u.id });
    throw new ApiError(401, "Wrong name or PIN");
  }

  await createDriverSession({
    user_id: u.id,
    name: u.name,
    company_id: u.company_id,
    role: u.role,
  });
  log.info("office_login_success", { requestId, user_id: u.id, role: u.role });
  return NextResponse.json({ ok: true, name: u.name, role: u.role });
});
