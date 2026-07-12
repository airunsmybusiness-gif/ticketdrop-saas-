// Minimal signed-cookie session for drivers (no extra packages).
// The cookie value is base64(payload).hmacSha256(payload, SESSION_SECRET),
// httpOnly so JavaScript on the page can never read or forge it.
import { createHmac, timingSafeEqual } from "crypto";
import { cookies } from "next/headers";

export type DriverSession = {
  user_id: number;
  name: string;
  company_id: number;
  role: string;
  exp: number; // unix seconds
};

const COOKIE = "td_driver";
const MAX_AGE = 60 * 60 * 14; // 14 hours — one shift

function secret(): string {
  const s = process.env.SESSION_SECRET;
  if (!s) throw new Error("SESSION_SECRET is not set (any long random string)");
  return s;
}

function sign(payload: string): string {
  return createHmac("sha256", secret()).update(payload).digest("base64url");
}

export async function createDriverSession(u: Omit<DriverSession, "exp">) {
  const payload = Buffer.from(
    JSON.stringify({ ...u, exp: Math.floor(Date.now() / 1000) + MAX_AGE })
  ).toString("base64url");
  const store = await cookies();
  store.set(COOKIE, `${payload}.${sign(payload)}`, {
    httpOnly: true,
    sameSite: "lax",
    secure: process.env.NODE_ENV === "production",
    maxAge: MAX_AGE,
    path: "/",
  });
}

export async function getDriverSession(): Promise<DriverSession | null> {
  const store = await cookies();
  const raw = store.get(COOKIE)?.value;
  if (!raw) return null;
  const dot = raw.lastIndexOf(".");
  if (dot < 0) return null;
  const payload = raw.slice(0, dot);
  const sig = raw.slice(dot + 1);
  const expected = sign(payload);
  const a = Buffer.from(sig);
  const b = Buffer.from(expected);
  if (a.length !== b.length || !timingSafeEqual(a, b)) return null;
  try {
    const s = JSON.parse(Buffer.from(payload, "base64url").toString()) as DriverSession;
    if (s.exp < Math.floor(Date.now() / 1000)) return null;
    return s;
  } catch {
    return null;
  }
}

export async function clearDriverSession() {
  const store = await cookies();
  store.set(COOKIE, "", { maxAge: 0, path: "/" });
}
