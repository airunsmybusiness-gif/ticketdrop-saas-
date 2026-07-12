// POST { name, pin } → verifies the driver's PIN against the bcrypt
// pin_hash in the existing users table and sets an httpOnly session cookie.
import { NextResponse } from "next/server";
import bcrypt from "bcryptjs";
import { db } from "@/lib/db";
import { createDriverSession } from "@/lib/session";

export async function POST(req: Request) {
  let body: { name?: string; pin?: string };
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Bad request" }, { status: 400 });
  }
  const name = (body.name || "").trim();
  const pin = (body.pin || "").trim();
  if (!name || pin.length < 4) {
    return NextResponse.json({ error: "Name and a 4+ digit PIN are required" }, { status: 400 });
  }

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
    return NextResponse.json({ error: "Wrong name or PIN" }, { status: 401 });
  }
  const u = rows[0];
  const ok = u.pin_hash
    ? await bcrypt.compare(pin, u.pin_hash)
    : Boolean(u.pin) && pin === String(u.pin); // legacy plaintext fallback
  if (!ok) {
    return NextResponse.json({ error: "Wrong name or PIN" }, { status: 401 });
  }

  await createDriverSession({
    user_id: u.id,
    name: u.name,
    company_id: u.company_id,
    role: u.role,
  });
  return NextResponse.json({ ok: true, name: u.name });
}
