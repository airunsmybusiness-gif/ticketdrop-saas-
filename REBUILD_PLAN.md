# TicketDrop — Next.js Rebuild Plan

The modern web version of TicketDrop lives in the **`web/`** folder of this repo:
**Next.js 15 (App Router) + TypeScript + Tailwind CSS v4 + Supabase**, styled as a
premium dark SaaS. This document is the map: what's built, how to run it, and how to
migrate from the Streamlit app without breaking your working system.

> **Golden rule: the Streamlit app keeps running in production until the new app does
> the same job end-to-end.** Both share the same Supabase database, so nothing needs
> to be migrated twice.

---

## 1. Architecture & project structure

```
web/
├── src/
│   ├── app/                       ← pages (App Router: folder = URL)
│   │   ├── page.tsx               ← landing page  (/)
│   │   ├── login/page.tsx         ← office login  (/login)
│   │   ├── driver/login/page.tsx  ← driver PIN pad login (/driver/login)
│   │   ├── (app)/                 ← signed-in area (shared sidebar layout)
│   │   │   ├── layout.tsx         ← sidebar + top bar shell
│   │   │   ├── dashboard/page.tsx ← admin dashboard (/dashboard)
│   │   │   └── driver/page.tsx    ← driver home (/driver)
│   │   ├── layout.tsx             ← fonts + metadata
│   │   └── globals.css            ← design tokens (change --brand to re-theme)
│   ├── components/ui/             ← button, card, input, badge (shadcn-style)
│   └── lib/
│       ├── utils.ts               ← cn() class helper
│       └── supabase/              ← browser + server Supabase clients
├── .env.local.example             ← copy to .env.local, add your keys
└── package.json
```

**Tech decisions (and why):**

| Choice | Why |
|--------|-----|
| Next.js 15 App Router | The current industry standard; every tutorial and AI assistant knows it. Server Components keep secrets off the browser. |
| Tailwind v4 + hand-rolled shadcn-style components | You own 4 small files (button/card/input/badge) instead of a generator. Easy to read, easy to restyle. Add the real `shadcn` CLI later if you want more components. |
| Supabase (same project you have) | Your data, users, and PINs are already there. Supabase Auth adds proper email/password login for office staff; Row Level Security enforces company isolation at the database level. |
| Design tokens in `globals.css` | Change `--brand` once → whole site re-themes. Per-company theming later = set that variable from the company row. |

---

## 2. Setup — exact commands

You need **Node.js 18.18+ or 20+** (nodejs.org, LTS installer).

```bash
# 1. get the code
git clone https://github.com/airunsmybusiness-gif/ticketdrop-saas-.git
cd ticketdrop-saas-/web

# 2. install dependencies (one command, ~2 min)
npm install

# 3. connect Supabase
cp .env.local.example .env.local
# then open .env.local and paste your values from
# Supabase → Project Settings → API:
#   NEXT_PUBLIC_SUPABASE_URL      = Project URL
#   NEXT_PUBLIC_SUPABASE_ANON_KEY = anon public key

# 4. run it
npm run dev
# → open http://localhost:3000
```

Deploy later with **Vercel** (best for Next.js: `vercel.com` → Import repo → set the
two env vars → Deploy, root directory = `web/`) or Railway (works too — same env vars).

---

## 3. What's already built

| Page | URL | State |
|------|-----|-------|
| Landing page | `/` | ✅ Done — dark premium hero, feature grid, 4-step "how it works", CTA. Conversion-focused copy aimed at hauling owners. |
| Office login | `/login` | ✅ UI done, wired to Supabase Auth email/password (`signInWithPassword`). Create office users in Supabase → Authentication → Add user. |
| Driver PIN login | `/driver/login` | ✅ UI done (name + big glove-friendly PIN pad). Posts to `/api/auth/driver` — a small route you add in Phase 2 that checks the bcrypt `pin_hash` in your existing `users` table. |
| Admin dashboard | `/dashboard` | ✅ Skeleton — stat cards + recent-loads list with mock data, ready to wire to Supabase queries. |
| Driver home | `/driver` | ✅ Skeleton — new-request and active-load cards with Accept / Start actions, phone-first layout. |

Everything builds clean (`npm run build` → 6 static routes, no errors).

---

## 4. Migration plan (Streamlit → Next.js)

**Phase 0 — now.** Streamlit app stays live for real work. Next.js runs alongside on
the same database. Show the landing page to prospects immediately if you like.

**Phase 1 — read-only dashboard (small, safe).**
Wire `/dashboard` stats + recent loads to Supabase `select`s filtered by `company_id`.
No writes, zero risk: if numbers match the Streamlit dashboard, it's correct.

**Phase 2 — driver flow (biggest payoff).**
1. Add `/api/auth/driver`: look up the user by name + company, verify PIN against
   `pin_hash` (`bcryptjs` package), set a session cookie.
2. Wire `/driver` to list the driver's loads; Accept / Start / Decline update `loads`
   + `load_status_history` exactly like `services/status.py` does today (same status
   names, same transitions).
3. Build the field-ticket completion form (volumes, hazards checklist, photo upload,
   signature) writing to the same `tickets` columns.
Drivers switch to the new app; office keeps using Streamlit. The data is shared, so
dispatch sees driver updates instantly.

**Phase 3 — office flow.** Dispatch form, AR verify/invoice screens. The PDFs are
already solved: keep the Python generators (`services/invoice.py`,
`services/field_ticket.py`) running as a tiny internal service the Next.js app calls,
or port them to `pdf-lib` later. Don't re-do working PDFs on day one.

**Phase 4 — cutover.** Point your domain at the Next.js app; retire the Streamlit UI.
The database never moved, so there is no data migration at all.

**Security note for Phase 1+:** enable **Row Level Security** on your Supabase tables
so each company can only read its own rows — Supabase → Table Editor → enable RLS,
with policies matching `company_id`. (The Streamlit app connects with the service
password, so it bypasses RLS and keeps working.)

---

## 5. Design system cheat-sheet

- **Re-theme**: edit `--brand` in `src/app/globals.css`.
- **Reusable pieces**: `Button` (primary/secondary/ghost/outline), `Card`, `Input`,
  `Label`, `Badge` (brand/green/amber/grey) in `src/components/ui/`.
- **Look**: near-black background `#07070b`, soft purple glow, dotted-grid hero,
  1px `white/10` borders, generous spacing, Geist font. Professional, not flashy.
