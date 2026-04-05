# IS455 — Get the site running (Supabase + Vercel)

This project has:

- **`web/`** — Next.js app (deploy this to Vercel). It talks to **Supabase** (Postgres). It does **not** run Python; scoring runs in a Node API route (your real model is trained in the notebook).
- **`pipeline.ipynb`** — CRISP-DM notebook; uses **`shop.db`** in this folder (SQLite). Your real file has `customers` (`full_name`, `email`, …) and `orders` (`order_total`, `risk_score`, `is_fraud`, …).
- **`supabase/seed.sql`** — Generated from your **`shop.db`** (`python scripts/generate_seed_sql.py`). Run in Supabase after **`schema.sql`** so Postgres matches SQLite.
- **`create_shop_db.py`** — Optional: writes **`shop_synthetic.db`** only (never overwrites **`shop.db`**).

---

## Part A — Supabase (database for the live site)

1. Go to [https://supabase.com](https://supabase.com) and sign in.
2. **New project** → pick a name, password, region → **Create**.
3. Wait until the project is **ready** (green).
4. Open **SQL Editor** → **New query**.
5. Open the file **`supabase/schema.sql`** in this repo, copy **all** of it, paste into Supabase, click **Run**. You should see “Success”.
6. (Recommended) Run **`supabase/seed.sql`** the same way (real sample rows from your **`shop.db`**). To refresh seed after changing SQLite: `python scripts/generate_seed_sql.py`.
7. Get your keys: **Project Settings** (gear) → **API**:
   - **Project URL** → this is `NEXT_PUBLIC_SUPABASE_URL`
   - **`anon` `public`** key → `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - **`service_role` `secret`** key → `SUPABASE_SERVICE_ROLE_KEY` (keep private; only used on the server)

---

## Part B — Run the app on your computer

1. Install [Node.js](https://nodejs.org/) LTS if you do not have it.
2. In a terminal:

```bash
cd web
```

On **Windows Command Prompt**: `copy .env.local.example .env.local`  
On **PowerShell**: `Copy-Item .env.local.example .env.local`

3. Edit **`web/.env.local`** and paste the three values from Supabase (see Part A step 7).

4. Install and start:

```bash
npm install
npm run dev
```

5. Open **http://localhost:3000** in your browser.
   - **Select customer** → pick someone → **Place new order**.
   - **New order** → save an order (writes to Supabase).
   - **Admin / history** → see orders → **Run scoring** → priority queue updates.

If you see database errors, re-check that `schema.sql` ran and `.env.local` has no extra spaces or quotes.

---

## Part C — Deploy to Vercel (live URL for the assignment)

1. Push this project to **GitHub** (or GitLab / Bitbucket).
2. Go to [https://vercel.com](https://vercel.com) → **Add New…** → **Project** → import your repo.
3. Important: set **Root Directory** to **`web`** (the folder that contains `package.json`).
4. Under **Environment Variables**, add the **same three** names as in `.env.local`:
   - `NEXT_PUBLIC_SUPABASE_URL`
   - `NEXT_PUBLIC_SUPABASE_ANON_KEY`
   - `SUPABASE_SERVICE_ROLE_KEY`  
   Use the values from Supabase (Part A).
5. Click **Deploy**. When it finishes, copy the **Production** URL — that is what you submit.

---

## Part D — Jupyter notebook + `shop.db` (Part 2 of the assignment)

1. Install Python (3.10+) and Jupyter if needed.
2. Keep your real **`shop.db`** next to **`pipeline.ipynb`**. (Optional test DB: `python create_shop_db.py` writes **`shop_synthetic.db`** only — point the notebook at it by changing `DB_PATH` if you use that file.)
3. Install notebook dependencies (examples — adjust if your class uses a conda env):

```bash
pip install pandas numpy scikit-learn xgboost matplotlib seaborn scipy statsmodels joblib
```

4. Start Jupyter, open **`pipeline.ipynb`**, run all cells. Upload the completed **`.ipynb`** where your course asks.

**Note:** The live website uses **Supabase**, not `shop.db`. The notebook uses **`shop.db`** locally so you can do CRISP-DM and train/export models without Python on Vercel.

---

## Quick checklist before you submit

| Requirement | Where |
|-------------|--------|
| Select customer (no login) | `/` |
| Place order → saved to DB | `/order` + Supabase `orders` table |
| Admin order history | `/admin` |
| Run scoring → refresh priority queue | **Run scoring** on `/admin` |
| Notebook CRISP-DM + `is_fraud` | `pipeline.ipynb` + `shop.db` |
| Live URL | Your Vercel **Production** link |

---

## If something breaks

- **“Failed to load customers” / red error on home page** — Open **`/api/customers`** in the browser (e.g. `http://localhost:3000/api/customers` or your Vercel URL + `/api/customers`). The JSON `error` field now shows the **real** Supabase message (not a generic failure).
- **“Missing … SUPABASE_SERVICE_ROLE_KEY”** — Add all three env vars to **`web/.env.local`** (local) **or** Vercel → **Settings → Environment Variables** (production). After changing Vercel env vars, **Redeploy**. Local: restart `npm run dev` after editing `.env.local`.
- **“relation … does not exist” / schema cache** — In Supabase **SQL Editor**, run **`supabase/schema.sql`**, then **`supabase/seed.sql`**, in that order. Tables must exist before the app can read them.
- **Works locally but not on Vercel** — Vercel does not read `.env.local`; you must set the same variables in the Vercel project and redeploy.
- **Empty customer list (no error)** — Seed data missing; run **`seed.sql`** or insert rows into `customers`.
- **Build fails on Vercel** — **Root Directory** = **`web`**.

Good luck.
