"""Generate supabase/seed.sql from shop.db (run from project root: python scripts/generate_seed_sql.py)."""
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "shop.db"
OUT = ROOT / "supabase" / "seed.sql"

# Keep each INSERT small enough for Supabase SQL Editor / PostgREST limits.
ORDERS_PER_BATCH = 800


def esc(s):
    if s is None:
        return "NULL"
    return "'" + str(s).replace("'", "''") + "'"


def main():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    c.execute("SELECT * FROM customers ORDER BY customer_id")
    rows = c.fetchall()

    lines = [
        "-- Generated from shop.db — full export (all customers + all orders).",
        "-- Run after schema.sql. Resets IDs to match SQLite.",
        "",
        "truncate table public.orders, public.customers restart identity cascade;",
        "",
        "INSERT INTO public.customers (customer_id, full_name, email, gender, birthdate, created_at, city, state, zip_code, customer_segment, loyalty_tier, is_active) VALUES",
    ]
    vals = []
    for r in rows:
        d = dict(r)
        ts = str(d["created_at"]).replace(" ", "T")
        vals.append(
            "(%s, %s, %s, %s, %s, %s::timestamptz, %s, %s, %s, %s, %s, %s)"
            % (
                d["customer_id"],
                esc(d["full_name"]),
                esc(d["email"]),
                esc(d["gender"]),
                esc(d["birthdate"]),
                esc(ts),
                esc(d["city"]),
                esc(d["state"]),
                esc(d["zip_code"]),
                esc(d["customer_segment"]),
                esc(d["loyalty_tier"]),
                d["is_active"],
            )
        )
    lines.append(",\n".join(vals) + ";")
    lines.append("")
    lines.append(
        "SELECT setval(pg_get_serial_sequence('public.customers','customer_id'), (SELECT MAX(customer_id) FROM public.customers));"
    )
    lines.append("")

    c.execute("SELECT * FROM orders ORDER BY order_id")
    orows = c.fetchall()

    def order_row_sql(d: dict) -> str:
        promo = "NULL" if d["promo_code"] is None else esc(d["promo_code"])
        odt = str(d["order_datetime"]).replace(" ", "T")
        return (
            "(%d, %d, %s::timestamptz, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NULL, NULL, NULL)"
            % (
                d["order_id"],
                d["customer_id"],
                esc(odt),
                esc(d["billing_zip"]),
                esc(d["shipping_zip"]),
                esc(d["shipping_state"]),
                esc(d["payment_method"]),
                esc(d["device_type"]),
                esc(d["ip_country"]),
                d["promo_used"],
                promo,
                d["order_subtotal"],
                d["shipping_fee"],
                d["tax_amount"],
                d["order_total"],
                d["risk_score"],
                d["is_fraud"],
            )
        )

    insert_header = (
        "INSERT INTO public.orders (order_id, customer_id, order_datetime, billing_zip, shipping_zip, "
        "shipping_state, payment_method, device_type, ip_country, promo_used, promo_code, order_subtotal, "
        "shipping_fee, tax_amount, order_total, risk_score, is_fraud, needs_review, priority_rank, scored_at) VALUES"
    )

    for i in range(0, len(orows), ORDERS_PER_BATCH):
        chunk = orows[i : i + ORDERS_PER_BATCH]
        ovals = [order_row_sql(dict(r)) for r in chunk]
        lines.append(insert_header)
        lines.append(",\n".join(ovals) + ";")
        lines.append("")

    lines.append(
        "SELECT setval(pg_get_serial_sequence('public.orders','order_id'), (SELECT MAX(order_id) FROM public.orders));"
    )
    lines.append("")

    OUT.write_text("\n".join(lines), encoding="utf-8")
    conn.close()
    print(f"Wrote {OUT} ({len(rows)} customers, {len(orows)} orders)")


if __name__ == "__main__":
    main()
