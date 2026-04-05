-- Run in Supabase: SQL Editor → New query → Paste → Run
-- Mirrors real shop.db (SQLite) + deployment columns for the Next.js app.

drop table if exists public.orders cascade;
drop table if exists public.customers cascade;

create table public.customers (
  customer_id serial primary key,
  full_name text not null,
  email text not null,
  gender text not null,
  birthdate text not null,
  created_at timestamptz not null,
  city text,
  state text,
  zip_code text,
  customer_segment text,
  loyalty_tier text,
  is_active integer not null default 1
);

create table public.orders (
  order_id bigserial primary key,
  customer_id integer not null references public.customers (customer_id) on delete cascade,
  order_datetime timestamptz not null,
  billing_zip text,
  shipping_zip text,
  shipping_state text,
  payment_method text not null,
  device_type text not null,
  ip_country text not null,
  promo_used integer not null default 0,
  promo_code text,
  order_subtotal numeric not null,
  shipping_fee numeric not null,
  tax_amount numeric not null,
  order_total numeric not null,
  risk_score double precision not null,
  is_fraud integer not null default 0,
  needs_review boolean default false,
  priority_rank integer,
  scored_at timestamptz
);

alter table public.customers disable row level security;
alter table public.orders disable row level security;
