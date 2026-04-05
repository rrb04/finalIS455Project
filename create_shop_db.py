"""
Optional synthetic SQLite file for testing (does NOT touch your real shop.db).
Output default: shop_synthetic.db

Usage:
  python create_shop_db.py
  python create_shop_db.py --output other.db
"""
import argparse
import random
import sqlite3
from datetime import datetime, timedelta

random.seed(27)

SEGMENTS = ["standard", "budget", "premium"]
TIERS = ["none", "silver", "gold"]
GENDERS = ["Male", "Female", "Non-binary"]
PAYMENTS = ["card", "paypal", "bank"]
DEVICES = ["mobile", "desktop", "tablet"]
COUNTRIES = ["US", "CA", "GB", "IN", "NG"]


def build(path: str) -> None:
    conn = sqlite3.connect(path)
    c = conn.cursor()
    c.executescript(
        """
        PRAGMA foreign_keys = OFF;
        DROP TABLE IF EXISTS orders;
        DROP TABLE IF EXISTS customers;
        PRAGMA foreign_keys = ON;

        CREATE TABLE customers (
            customer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            full_name TEXT NOT NULL,
            email TEXT NOT NULL,
            gender TEXT NOT NULL,
            birthdate TEXT NOT NULL,
            created_at TEXT NOT NULL,
            city TEXT,
            state TEXT,
            zip_code TEXT,
            customer_segment TEXT,
            loyalty_tier TEXT,
            is_active INTEGER NOT NULL DEFAULT 1
        );

        CREATE TABLE orders (
            order_id INTEGER PRIMARY KEY AUTOINCREMENT,
            customer_id INTEGER NOT NULL,
            order_datetime TEXT NOT NULL,
            billing_zip TEXT,
            shipping_zip TEXT,
            shipping_state TEXT,
            payment_method TEXT NOT NULL,
            device_type TEXT NOT NULL,
            ip_country TEXT NOT NULL,
            promo_used INTEGER NOT NULL DEFAULT 0,
            promo_code TEXT,
            order_subtotal REAL NOT NULL,
            shipping_fee REAL NOT NULL,
            tax_amount REAL NOT NULL,
            order_total REAL NOT NULL,
            risk_score REAL NOT NULL,
            is_fraud INTEGER NOT NULL DEFAULT 0,
            FOREIGN KEY (customer_id) REFERENCES customers(customer_id)
        );
        """
    )

    for i in range(250):
        city = random.choice(["Clayton", "Oxford", "Fairview", "Auburn"])
        state = random.choice(["CO", "OH", "MI", "TX", "NY"])
        z = f"{10000 + random.randint(0, 89999)}"
        birth = datetime(1960, 1, 1) + timedelta(days=random.randint(0, 20000))
        created = datetime(2025, 1, 1) + timedelta(days=random.randint(0, 300))
        c.execute(
            """INSERT INTO customers (full_name, email, gender, birthdate, created_at,
               city, state, zip_code, customer_segment, loyalty_tier, is_active)
               VALUES (?,?,?,?,?,?,?,?,?,?,1)""",
            (
                f"Customer {i}",
                f"user{i}@example.com",
                random.choice(GENDERS),
                birth.strftime("%Y-%m-%d"),
                created.strftime("%Y-%m-%d %H:%M:%S"),
                city,
                state,
                z,
                random.choice(SEGMENTS),
                random.choice(TIERS),
            ),
        )

    for _ in range(5000):
        cid = random.randint(1, 250)
        od = datetime(2025, 6, 1) + timedelta(hours=random.randint(0, 9000))
        sub = round(random.uniform(10, 2000), 2)
        ship = round(random.uniform(6, 25), 2)
        tax = round(sub * 0.08, 2)
        total = round(sub + ship + tax, 2)
        risk = round(random.uniform(0.1, 100.0), 1)
        fraud = 1 if (risk > 85 and random.random() < 0.4) or random.random() < 0.03 else 0
        c.execute(
            """INSERT INTO orders (customer_id, order_datetime, billing_zip, shipping_zip,
               shipping_state, payment_method, device_type, ip_country, promo_used, promo_code,
               order_subtotal, shipping_fee, tax_amount, order_total, risk_score, is_fraud)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                cid,
                od.strftime("%Y-%m-%d %H:%M:%S"),
                f"{10000 + random.randint(0, 89999)}",
                f"{10000 + random.randint(0, 89999)}",
                random.choice(["CO", "NY", "WA", "TX"]),
                random.choice(PAYMENTS),
                random.choice(DEVICES),
                random.choice(COUNTRIES),
                1 if random.random() < 0.2 else 0,
                random.choice([None, "SAVE10", "WELCOME"]) if random.random() < 0.15 else None,
                sub,
                ship,
                tax,
                total,
                risk,
                fraud,
            ),
        )

    conn.commit()
    conn.close()
    print(f"Wrote {path}")


def main():
    p = argparse.ArgumentParser()
    p.add_argument(
        "--output",
        default="shop_synthetic.db",
        help="Output path (default: shop_synthetic.db — never overwrites shop.db)",
    )
    args = p.parse_args()
    build(args.output)


if __name__ == "__main__":
    main()
