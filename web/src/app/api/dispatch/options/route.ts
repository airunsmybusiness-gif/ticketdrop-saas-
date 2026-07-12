// GET → everything the dispatch form needs: drivers, customers, trucks,
// trailers (from the same settings table the Streamlit app manages).
import { NextResponse } from "next/server";
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handle, ApiError } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handle("dispatch_options", async () => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const cid = s.company_id;
  const [drivers, settings] = await Promise.all([
    db().query(
      `SELECT id, name FROM users
       WHERE company_id = $1 AND role = 'driver' AND active = TRUE ORDER BY name`,
      [cid]
    ),
    db().query(
      `SELECT category, value FROM settings
       WHERE company_id = $1 AND active = TRUE ORDER BY value`,
      [cid]
    ),
  ]);

  const byCat = (cat: string) =>
    settings.rows.filter((r) => r.category === cat).map((r) => r.value as string);

  return NextResponse.json({
    drivers: drivers.rows,
    customers: byCat("customers"),
    trucks: byCat("trucks"),
    trailers: byCat("trailers"),
  });
});
