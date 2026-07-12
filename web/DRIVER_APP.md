# Driver App — how it works & how to test it

The driver flow in the Next.js app is now fully working: **Name + PIN login →
list of assigned loads → Accept / Start / Complete → digital field ticket with
the 11-item hazards checklist, backup photo, notes and signature** — writing to
the same database tables as the Streamlit app, so AR review, field-ticket PDFs
and invoicing all keep working unchanged.

---

## How it's built

| Piece | File | Notes |
|-------|------|-------|
| PIN login API | `src/app/api/auth/driver/route.ts` | Verifies the bcrypt `pin_hash` in your existing `users` table; falls back to the legacy plaintext `pin` column during migration. Sets an httpOnly signed cookie (14 h shift). |
| Loads API | `src/app/api/driver/loads/route.ts` | The signed-in driver's open loads + today's completed. Company- and driver-scoped on the server. |
| Accept/Decline/Start | `src/app/api/driver/action/route.ts` | Same status names and transitions as `services/status.py`, with row locking and the `load_status_history` audit trail. |
| Complete | `src/app/api/driver/complete/route.ts` | Creates the ticket (hazards, photo, notes, signature) and marks the load COMPLETED — identical columns to the Streamlit driver form. |
| Driver UI | `src/app/(app)/driver/page.tsx` | Phone-first cards, big glove-friendly buttons, and the offline outbox. |
| Hazards list | `src/lib/hazards.ts` | Must stay in sync with `HAZARD_ITEMS` in `services/field_ticket.py`. |

**Server config (in `.env.local` or your host's variables):**
- `DATABASE_URL` — the same Postgres connection string your Streamlit app uses
  (Supabase → Project Settings → Database → Connection string). The browser never
  sees it; only API routes use it.
- `SESSION_SECRET` — any long random string (signs the login cookie).

## Offline behaviour (for dead zones)

- The last loads list is **cached on the phone**, so the page still shows the
  driver's loads with zero signal.
- Accept / Start / Complete try the network first. **If there's no signal, the
  action — including the ticket and its photo — is saved into an "outbox" on the
  phone**, the screen updates immediately, and a banner says it will send later.
- When the connection returns (or the app is reopened), the outbox **syncs
  automatically** in order, then the list refreshes from the server.
- Photos are downscaled on the phone (max 1280 px, JPEG) so they upload fast on
  one bar of LTE and fit in the outbox.
- Honest limits: the outbox lives in localStorage (~5 MB), which comfortably
  holds a shift's worth of actions and 1–2 queued photo tickets. If a queued
  action is rejected by the server when it syncs (for example dispatch cancelled
  the load meanwhile), the driver sees a clear message and the rest of the queue
  still sends. A full PWA/service-worker setup can come later if needed.

## Test it yourself (10 minutes)

1. **Configure** `web/.env.local` (copy from `.env.local.example`) with your
   `DATABASE_URL` and a `SESSION_SECRET`.
2. **Run** `cd web && npm install && npm run dev` → http://localhost:3000
3. **Assign a load** to a driver: in the Streamlit app's Dispatch page (or in
   Supabase → Table Editor → loads, status `ASSIGNED`, `driver_id` = your driver).
4. On your phone (or a narrow browser window) open **/driver/login**:
   - Name: the driver's name (first name is enough if unique, e.g. `John`)
   - PIN: their PIN (seeded drivers start at `1234` — change in Settings)
5. You should see the load. Tap **Accept** → **Start load** → **Complete load**:
   fill ticket #, volume, tick hazards, add the photo, sign, **Submit ticket**.
6. **Check the results**: the Streamlit AR page shows the ticket under
   "Submitted" — and the 📄 PDF button renders the field ticket with the ticked
   hazards and photo.
7. **Offline test**: turn on airplane mode, tap Accept on another load — you'll
   see "saved on this phone". Turn airplane mode off — it syncs by itself.
