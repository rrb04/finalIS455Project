-- Run once in Supabase SQL Editor (safe if tables already exist — no drops).
-- Stores JSON weights so the Vercel app can score orders without running Python.

create table if not exists public.ml_scoring_config (
  id integer primary key default 1 check (id = 1),
  config jsonb not null,
  trained_at timestamptz not null default now(),
  metrics jsonb
);

grant all on public.ml_scoring_config to anon, authenticated, service_role;
