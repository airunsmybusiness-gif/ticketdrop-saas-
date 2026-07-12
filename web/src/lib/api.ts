// Shared plumbing for API routes: one wrapper that guarantees
//  (1) every request gets a request id,
//  (2) every failure is logged with that id,
//  (3) the client always gets clean JSON — never a stack trace or silence.
//
// Usage:
//   export const POST = handle("driver_action", async (req, ctx) => { ... });
// Inside, throw ApiError(400, "message") for expected problems; anything
// else becomes a logged 500 with a generic message.
import { NextResponse } from "next/server";
import { randomUUID } from "crypto";
import { log } from "@/lib/log";

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export type Ctx = { requestId: string };

export function handle(
  name: string,
  fn: (req: Request, ctx: Ctx) => Promise<NextResponse>
) {
  return async (req: Request): Promise<NextResponse> => {
    const requestId = randomUUID().slice(0, 8);
    const started = Date.now();
    try {
      const res = await fn(req, { requestId });
      log.info(`${name}_ok`, { requestId, ms: Date.now() - started, status: res.status });
      return res;
    } catch (e) {
      if (e instanceof ApiError) {
        log.warn(`${name}_rejected`, { requestId, status: e.status, reason: e.message });
        return NextResponse.json({ error: e.message, requestId }, { status: e.status });
      }
      log.error(`${name}_failed`, {
        requestId,
        ms: Date.now() - started,
        error: e instanceof Error ? `${e.name}: ${e.message}` : String(e),
      });
      return NextResponse.json(
        { error: "Something went wrong on our side. Please try again.", requestId },
        { status: 500 }
      );
    }
  };
}

// Same wrapper for dynamic routes (e.g. /api/thing/[id]) where Next passes
// route params as a second argument.
export function handleWithParams<P>(
  name: string,
  fn: (req: Request, params: P, ctx: Ctx) => Promise<NextResponse | Response>
) {
  return async (req: Request, segment: { params: Promise<P> }): Promise<NextResponse | Response> => {
    const requestId = randomUUID().slice(0, 8);
    const started = Date.now();
    try {
      const params = await segment.params;
      const res = await fn(req, params, { requestId });
      log.info(`${name}_ok`, { requestId, ms: Date.now() - started, status: res.status });
      return res;
    } catch (e) {
      if (e instanceof ApiError) {
        log.warn(`${name}_rejected`, { requestId, status: e.status, reason: e.message });
        return NextResponse.json({ error: e.message, requestId }, { status: e.status });
      }
      log.error(`${name}_failed`, {
        requestId,
        ms: Date.now() - started,
        error: e instanceof Error ? `${e.name}: ${e.message}` : String(e),
      });
      return NextResponse.json(
        { error: "Something went wrong on our side. Please try again.", requestId },
        { status: 500 }
      );
    }
  };
}

// ---------------------------------------------------------------- validation
// Small, readable validators — throw ApiError(400, ...) with a human message.
export async function readJson<T = Record<string, unknown>>(req: Request): Promise<T> {
  try {
    return (await req.json()) as T;
  } catch {
    throw new ApiError(400, "Request body must be JSON");
  }
}

export function requireString(v: unknown, field: string, maxLen = 500): string {
  if (typeof v !== "string" || !v.trim()) throw new ApiError(400, `${field} is required`);
  if (v.length > maxLen) throw new ApiError(400, `${field} is too long`);
  return v.trim();
}

export function optionalString(v: unknown, field: string, maxLen = 2000): string | null {
  if (v === undefined || v === null || v === "") return null;
  if (typeof v !== "string") throw new ApiError(400, `${field} must be text`);
  if (v.length > maxLen) throw new ApiError(400, `${field} is too long`);
  return v.trim() || null;
}

export function requireNumber(v: unknown, field: string, opts?: { min?: number; max?: number }): number {
  const n = typeof v === "string" ? parseFloat(v) : (v as number);
  if (typeof n !== "number" || !isFinite(n)) throw new ApiError(400, `${field} must be a number`);
  if (opts?.min !== undefined && n < opts.min) throw new ApiError(400, `${field} must be at least ${opts.min}`);
  if (opts?.max !== undefined && n > opts.max) throw new ApiError(400, `${field} is too large`);
  return n;
}

export function requireId(v: unknown, field: string): number {
  const n = Number(v);
  if (!Number.isInteger(n) || n <= 0) throw new ApiError(400, `${field} is missing or invalid`);
  return n;
}
