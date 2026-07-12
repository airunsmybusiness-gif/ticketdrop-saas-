// GET → the driver's backup photo for a ticket, served as an image.
// Office session required; company-scoped so no cross-company access.
import { db } from "@/lib/db";
import { getDriverSession } from "@/lib/session";
import { handleWithParams, requireId, ApiError } from "@/lib/api";

export const dynamic = "force-dynamic";

export const GET = handleWithParams<{ id: string }>("billing_photo", async (_req, params) => {
  const s = await getDriverSession();
  if (!s) throw new ApiError(401, "Not signed in");
  if (s.role === "driver") throw new ApiError(403, "Office access only");

  const ticketId = requireId(params.id, "Ticket");
  const { rows } = await db().query(
    `SELECT load_photo, load_photo_mime FROM tickets
     WHERE id = $1 AND company_id = $2`,
    [ticketId, s.company_id]
  );
  if (rows.length === 0 || !rows[0].load_photo)
    throw new ApiError(404, "No photo for this ticket");

  return new Response(new Uint8Array(rows[0].load_photo), {
    headers: {
      "Content-Type": rows[0].load_photo_mime || "image/jpeg",
      "Cache-Control": "private, max-age=3600",
    },
  });
});
