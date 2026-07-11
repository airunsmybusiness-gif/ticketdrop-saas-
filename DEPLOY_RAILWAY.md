# Deploying TicketDrop on Railway

A step-by-step guide written for someone who is **not** a professional developer.
Total time: about 30–45 minutes the first time. You'll do three things:
**(A)** secure your database, **(B)** set up the database tables, **(C)** deploy the app.

---

## Before you start
You need:
- Your GitHub account (the code is already pushed there).
- Your Supabase account (your database).
- A Railway account — sign up free at **railway.app** (log in with GitHub).

---

## A. Secure your database (do this first — 5 min)

Your old database password was exposed in the code history, so it must be changed.

1. Go to **supabase.com** → your project → **Project Settings** → **Database**.
2. Under **Database password**, click **Reset database password**. Copy the new password somewhere safe.
3. Still on that page, find **Connection string** → **URI**. Copy it. It looks like:
   ```
   postgresql://postgres.xxxx:YOUR-NEW-PASSWORD@aws-1-us-east-1.pooler.supabase.com:5432/postgres
   ```
   Make sure the new password is in it. **This whole line is your `DATABASE_URL`.** Keep it handy for step C.

---

## B. Set up the database tables (10 min)

1. In Supabase, open **SQL Editor** → **New query**.
2. Open the file **`schema.sql`** from your repo, copy everything, paste it in, click **Run**.
   (This adds the `companies` table, the secure-PIN column, and speed-up indexes. It's safe — it won't delete anything.)
3. New query again. Open **`seed.sql`**, copy/paste/**Run**. This creates your starter logins:

   | Role | Name | Starting PIN |
   |------|------|--------------|
   | Admin | Admin | **246810** |
   | Dispatch | Dispatch | **135790** |
   | AR / Billing | Billing | **112233** |
   | Any existing drivers | (their names) | **1234** |

   > Change every PIN in the app's **Settings → Users** after your first login.

---

## C. Deploy the app on Railway (15 min)

1. Go to **railway.app** → **New Project** → **Deploy from GitHub repo**.
2. Pick your **ticketdrop** repository and confirm. Railway starts building automatically
   (it reads `railway.toml` and `requirements.txt` for you — nothing to configure there).
3. When the build finishes, open the service → **Variables** tab → **New Variable**:
   - **Name:** `DATABASE_URL`
   - **Value:** the connection string you copied in step A.3
   - Click **Add**. Railway redeploys automatically.
4. Open the **Settings** tab of the service → **Networking** → **Generate Domain**.
   Railway gives you a public URL like `ticketdrop-production.up.railway.app`.
5. Open that URL. You should see the **Sign in** screen. Log in as **Admin / 246810**.

🎉 That's it — you're live.

---

## First things to do once you're in
1. **Settings → Company:** set the company name, tagline, and brand color. (This restyles the whole app.)
2. **Settings → Users:** change the Admin/Dispatch/Billing PINs, and add your real drivers with their own PINs.
3. **Settings → Trucks / Trailers / Customers:** add your equipment and customers.

---

## Adding a second company later
No code changes needed. In Supabase SQL Editor:
```sql
INSERT INTO companies (name, tagline, primary_color)
VALUES ('New Hauling Co', 'Dispatch & Field Tickets', '#2563EB');
```
Then add that company's users in the app (or via SQL with the new company's `id`).
The login screen will show a **company picker** as soon as more than one company exists,
and each company only ever sees its own loads, tickets, and users.

---

## Troubleshooting
- **"DATABASE_URL is not set"** → you missed step C.3, or there's a typo in the variable name.
- **Login screen says "No companies configured"** → run `schema.sql` and `seed.sql` (step B).
- **App is slow to first load** → free hosting tiers sleep when idle; the first visit wakes it (~30s). Upgrade the service to keep it always-on once you have a paying customer.
- **Wrong PIN** → PINs are case-sensitive digits; reset them in Settings → Users (as Admin).

> **Note:** Railway and Render work almost identically. If you ever prefer Render, the only
> differences are the dashboard layout and that you set the start command manually:
> `streamlit run app.py --server.port $PORT --server.address 0.0.0.0`.
