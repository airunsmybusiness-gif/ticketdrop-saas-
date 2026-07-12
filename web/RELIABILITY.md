# TicketDrop Reliability Guide

What makes this app hard to break, what its honest limits are, and what to do
next. Written for the owner, not for engineers.

---

## 1. What's now built in (and proven by tests)

| Protection | What it means in the field |
|------------|---------------------------|
| **No silent failures** | Every API request is wrapped: expected problems return a plain-English message ("Actual volume must be at least 0.01"), unexpected ones return "Something went wrong" + a short **request ID** you can search in the logs. Nothing ever disappears without a trace. |
| **Structured logs** | Every request logs one JSON line with a timestamp, event name, request ID and duration (e.g. `driver_login_failed`, `ticket_submitted`). In Vercel/Railway you can filter by event name in seconds. |
| **Input validation** | Every field is checked server-side (types, ranges, lengths, hazard names against the official list, 5 MB photo cap) — a buggy or malicious client can't write garbage into your database. |
| **Database outage safety** | Connection timeout 8s, query timeout 15s, pool error handler. **Proven in test:** with the database stopped, the app stays up, APIs return clean JSON errors, `/api/health` says 503 — and everything recovers by itself the moment the database is back. Drivers' work lands in their phone outbox meanwhile, so nothing is lost. |
| **Crash screens** | If a page ever crashes, users see a friendly "Try again" screen (with an error code), never a white page. |
| **Dead-zone tolerance** | Requests give up after 15s instead of hanging on one bar of signal — a timeout is treated as "offline" and the action goes to the phone outbox, which auto-syncs later. |
| **Live updates that always recover** | The driver list refreshes every 30s while open, plus instantly when the app regains focus or connectivity. Polling was chosen over websockets deliberately: after any dropped connection it recovers by itself, with nothing to reconnect or debug. |
| **Double-tap / two-dispatcher safety** | Status changes lock the row and check the current status inside a transaction — two conflicting updates can't both win, and the loser gets a clear "Load is already X" message. |
| **TypeScript strict mode** | On since day one; the compiler catches whole classes of mistakes before deploy. |
| **Uptime monitoring hook** | `/api/health` checks the app **and** the database. Point a free UptimeRobot monitor at it and you'll get an email/text within minutes of any outage. |

## 2. Honest answer: is Supabase + Next.js enough for 50–200 loads/day?

**Yes — by a factor of at least 100, and that is not marketing.** Do the math:
200 loads/day ≈ 1,000–2,000 requests/day from all drivers and dispatch combined
≈ **about one request every 30 seconds at peak**. Supabase's free tier and any
$5–20/month Next.js host handle hundreds of requests *per second*. Your scale
risk is effectively zero; you would need thousands of loads per day across many
companies before architecture becomes the conversation.

The real risks at your scale are different, and they're operational:

1. **Photos in the database.** Each ticket photo (~100–300 KB after downscaling)
   lives in Postgres. At 200 loads/day that's roughly 1–2 GB/month. Supabase's
   free tier includes 500 MB of database storage, so this is your first real
   ceiling. Fix when needed: upgrade to Supabase Pro (~$25/mo, 8 GB) or move
   photos to Supabase Storage (cheap object storage). **Flagged, not urgent.**
2. **One shared database password.** The Streamlit app and the Next.js API both
   use `DATABASE_URL`. Keep it only in host environment variables; rotate it if
   it's ever pasted anywhere. (Already the practice — keep it up.)
3. **Backups.** Supabase Pro keeps daily backups; the free tier does not. Once a
   real company depends on this data, the $25/mo Pro plan **is** your disaster
   recovery plan. This is the single best reliability dollar you can spend.

## 3. How to make the whole system hard to break (owner's checklist)

1. **Uptime monitor** (10 min, free): UptimeRobot → monitor `https://your-app/api/health`. You'll know about outages before your customers do.
2. **Supabase Pro** ($25/mo when a paying customer exists): daily backups + storage headroom.
3. **Never edit the production database by hand.** Use the app's Settings pages. Hand edits bypass every validation above.
4. **Deploy via git only.** Vercel/Railway build from GitHub; if a deploy is bad, the dashboards have a one-click **rollback to the previous deploy** — that's your undo button.
5. **Keep the two secrets secret**: `DATABASE_URL`, `SESSION_SECRET`. Host env vars only, never in code or chat.
6. **When something misbehaves**: get the **request ID** from the user's error message, open your host's logs, search for it — the matching log line tells you exactly which step failed and why.

## 4. Prioritized next steps for stability

| # | Action | Effort | Why |
|---|--------|--------|-----|
| 1 | Point UptimeRobot at `/api/health` | 10 min | Know about problems first |
| 2 | Supabase Pro once revenue exists | 1 click | Daily backups = disaster recovery |
| 3 | Add rate limiting on `/api/auth/driver` (e.g. 10 tries/min/IP) | small | Slows down PIN guessing from the public internet |
| 4 | Move photos to Supabase Storage when DB size nears the plan limit | medium | Removes the only real growth ceiling |
| 5 | Row Level Security policies in Supabase | medium | Second fence around company data isolation (API already enforces it) |
| 6 | A staging deploy (Vercel preview deployments give this for free per-PR) | small | Try changes safely before drivers see them |

**Deliberately NOT recommended** (over-engineering at this scale): websockets/
Supabase Realtime (polling is more robust in the field), microservices, Redis,
Kubernetes, load balancers, multi-region databases. Revisit only past ~5,000
loads/day.
