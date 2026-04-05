# IS455 — Get the site running (Supabase + Vercel)

This project has:

- **`web/`** — Next.js app (deploy this to Vercel). It talks to **Supabase** (Postgres). It does **not** run Python; scoring runs in a Node API route (your real model is trained in the notebook).
- **`pipeline.ipynb`** — CRISP-DM notebook. By default it reads **`shop.db`** (SQLite). You can point it at **Supabase** instead (same `orders`/`customers` join as production) with `DATA_SOURCE=supabase` and `DATABASE_URL` set to your Postgres connection string.
- **`scripts/train_from_supabase.py`** — Trains a **logistic fraud model** on all labeled rows in Supabase and saves weights into **`ml_scoring_config`** so **`/api/score`** can use them (Python does not run on Vercel).
- **`supabase/ml_scoring_config.sql`** — Adds the `ml_scoring_config` table (run once if you already applied an older `schema.sql` without this table). Fresh installs: **`schema.sql`** already includes it.
- **`supabase/seed.sql`** — Generated from your **`shop.db`** (`python scripts/generate_seed_sql.py`): **all** customers and **all** orders from SQLite. Run in Supabase after **`schema.sql`** so Postgres matches your local DB for training and the app.
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

## Part D — Jupyter notebook + data source

1. Install Python (3.10+) and Jupyter if needed.
2. **Option A — Local SQLite (default):** Keep **`shop.db`** next to **`pipeline.ipynb`**. (Optional test DB: `python create_shop_db.py` writes **`shop_synthetic.db`** — change `DB_PATH` if you use that file.)
3. **Option B — Supabase (same data as production):** In Supabase → **Project Settings** → **Database**, copy the **URI** connection string. Before starting Jupyter, set environment variables (PowerShell example):

```powershell
$env:DATA_SOURCE = "supabase"
$env:DATABASE_URL = "postgresql://postgres:YOUR_PASSWORD@db.YOUR_REF.supabase.co:5432/postgres"
```

4. Install notebook dependencies (add **`psycopg2-binary`** if you use Option B):

```bash
pip install pandas numpy scikit-learn xgboost matplotlib seaborn scipy statsmodels joblib psycopg2-binary
```

5. Start Jupyter, open **`pipeline.ipynb`**, run all cells. Upload the completed **`.ipynb`** where your course asks.

The live site always uses **Supabase**. The notebook can use either **`shop.db`** or Supabase so your EDA matches production when you want it to.

---

## Part E — Daily fraud model in production (optional but recommended)

Training stays **off Vercel** (e.g. your laptop or GitHub Actions). The app **reads** stored coefficients from Postgres.

1. In Supabase **SQL Editor**, run **`supabase/ml_scoring_config.sql`** once if that table is missing (skip if you re-ran the full **`schema.sql`** that already creates `ml_scoring_config`).
2. Install training deps: `pip install -r scripts/requirements-train.txt`.
3. Set **`DATABASE_URL`** to the same Postgres URI as in Part D Option B, then run:

```bash
python scripts/train_from_supabase.py
```

4. After a successful run, **Run scoring** on **`/admin`** uses the trained model. If no row exists in **`ml_scoring_config`**, scoring falls back to the built-in heuristic.
5. **Automated daily retrain:** add **`DATABASE_URL`** as a **GitHub Actions secret** on your repo. The workflow **`.github/workflows/daily-fraud-train.yml`** runs on a schedule (and can be triggered manually). Adjust the cron time if you prefer a different UTC hour.

---

## Quick checklist before you submit

| Requirement | Where |
|-------------|--------|
| Select customer (no login) | `/` |
| Place order → saved to DB | `/order` + Supabase `orders` table |
| Admin order history | `/admin` |
| Run scoring → refresh priority queue | **Run scoring** on `/admin` |
| Notebook CRISP-DM + `is_fraud` | `pipeline.ipynb` + `shop.db` (or Supabase via `DATA_SOURCE`) |
| Daily fraud model → live scoring | `scripts/train_from_supabase.py` + `ml_scoring_config` table |
| Live URL | Your Vercel **Production** link |

---

## If something breaks

- **“Failed to load customers” / red error on home page** — Open **`/api/customers`** in the browser (e.g. `http://localhost:3000/api/customers` or your Vercel URL + `/api/customers`). The JSON `error` field now shows the **real** Supabase message (not a generic failure).
- **“Missing … SUPABASE_SERVICE_ROLE_KEY”** — Add all three env vars to **`web/.env.local`** (local) **or** Vercel → **Settings → Environment Variables** (production). After changing Vercel env vars, **Redeploy**. Local: restart `npm run dev` after editing `.env.local`.
- **“relation … does not exist” / schema cache** — In Supabase **SQL Editor**, run **`supabase/schema.sql`**, then **`supabase/seed.sql`**, in that order. Tables must exist before the app can read them.
- **Works locally but not on Vercel** — Vercel does not read `.env.local`; you must set the same variables in the Vercel project and redeploy.
- **“permission denied for schema public”** — In Supabase → **SQL Editor**, run **`supabase/grants_public.sql`** (grants the API roles access to the `public` schema). Then reload the app.
- **Empty customer list (no error)** — Seed data missing; run **`seed.sql`** or insert rows into `customers`.
- **Build fails on Vercel** — **Root Directory** = **`web`**.

Good luck.
