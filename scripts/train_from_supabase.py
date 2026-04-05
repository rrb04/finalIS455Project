#!/usr/bin/env python3
"""
Train a daily fraud model from Supabase (orders + customers) and upsert row
`ml_scoring_config` id=1 so the Next.js /api/score route can apply it without Python.

Requires: DATABASE_URL (Postgres connection string from Supabase).
Optional: REVIEW_THRESHOLD_PROB (default 0.42) to align with the heuristic queue.

pip install pandas numpy scikit-learn psycopg2-binary
"""

from __future__ import annotations

import json
import math
import os
import sys
from datetime import datetime, timezone
from urllib.parse import quote

import numpy as np
import pandas as pd
import psycopg2
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

QUERY = """
SELECT o.order_total::float8 AS order_total,
       o.is_fraud::int AS is_fraud,
       c.customer_segment
FROM public.orders o
JOIN public.customers c ON o.customer_id = c.customer_id
WHERE o.is_fraud IN (0, 1)
"""


def sanitize_for_jsonb(obj: object) -> object:
    """JSON / Postgres jsonb do not allow NaN or Infinity; sklearn may emit them."""
    if isinstance(obj, dict):
        return {str(k): sanitize_for_jsonb(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_jsonb(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return None
    return obj


def _split_postgres_url(url: str) -> tuple[str, str, str] | None:
    """Return (scheme, userinfo, hostpart) or None if not a postgres URL."""
    for scheme in ("postgresql://", "postgres://"):
        if url.startswith(scheme):
            rest = url[len(scheme) :]
            break
    else:
        return None
    if "@" not in rest:
        return None
    userinfo, hostpart = rest.rsplit("@", 1)
    return scheme, userinfo, hostpart


def extract_password_from_postgres_url(url: str) -> str | None:
    parts = _split_postgres_url(url)
    if not parts:
        return None
    _, userinfo, _ = parts
    if ":" not in userinfo:
        return None
    _, password = userinfo.split(":", 1)
    return password


def password_has_invalid_percent_escape(password: str) -> bool:
    """True if password contains '%' not followed by two hex digits (invalid in a URI)."""
    hex_digits = set("0123456789abcdefABCDEF")
    i = 0
    n = len(password)
    while i < n:
        if password[i] != "%":
            i += 1
            continue
        if i + 2 >= n:
            return True
        if password[i + 1] not in hex_digits or password[i + 2] not in hex_digits:
            return True
        i += 3
    return False


def encode_password_in_postgres_url(url: str) -> str:
    """
    URI passwords must percent-encode special characters (e.g. % -> %25).
    Raw '%' in a Supabase password breaks psycopg2.parse_dsn with "invalid percent-encoded token".
    """
    parts = _split_postgres_url(url)
    if not parts:
        return url
    scheme, userinfo, hostpart = parts
    if ":" not in userinfo:
        return url
    user, password = userinfo.split(":", 1)
    return f"{scheme}{user}:{quote(password, safe='')}@{hostpart}"


def connect_postgres(url: str):
    # If password has a raw % that is not valid %XX, psycopg2 fails before we can try/except.
    pw = extract_password_from_postgres_url(url)
    if pw is not None and password_has_invalid_percent_escape(pw):
        return psycopg2.connect(encode_password_in_postgres_url(url))
    try:
        return psycopg2.connect(url)
    except psycopg2.Error as e:
        msg = str(e).lower()
        if "percent" in msg or "invalid dsn" in msg:
            fixed = encode_password_in_postgres_url(url)
            if fixed != url:
                return psycopg2.connect(fixed)
        raise


def build_xy(df: pd.DataFrame):
    y = df["is_fraud"].astype(int).values
    seg = df["customer_segment"].fillna("unknown").astype(str).str.lower()
    categories = sorted(seg.unique())
    ref = categories[0]
    dummies = pd.get_dummies(seg, prefix="seg")
    ref_col = "seg_" + ref
    if ref_col in dummies.columns:
        dummies = dummies.drop(columns=[ref_col])

    ot = df[["order_total"]].astype(float).values
    scaler = StandardScaler()
    ot_z = scaler.fit_transform(ot)

    if dummies.shape[1] == 0:
        X = ot_z
        dummy_cols: list[str] = []
    else:
        X = np.hstack([ot_z, dummies.values.astype(float)])
        dummy_cols = list(dummies.columns)

    segment_coef: dict[str, float] = {ref: 0.0}
    for col in dummy_cols:
        name = col[4:] if col.startswith("seg_") else col
        segment_coef[name] = 0.0

    return X, y, scaler, ref, dummy_cols, segment_coef


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("Set DATABASE_URL to your Supabase Postgres connection string.", file=sys.stderr)
        return 1

    thresh = float(os.environ.get("REVIEW_THRESHOLD_PROB", "0.42"))

    df = pd.read_sql_query(QUERY, connect_postgres(url))
    if len(df) < 30:
        print(f"Need at least 30 labeled rows; got {len(df)}.", file=sys.stderr)
        return 1
    if df["is_fraud"].nunique() < 2:
        print("Need both fraud and non-fraud labels in the data.", file=sys.stderr)
        return 1

    X, y, scaler, ref, dummy_cols, segment_coef = build_xy(df)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=27, stratify=y
    )

    lr = LogisticRegression(max_iter=4000, class_weight="balanced")
    lr.fit(X_train, y_train)

    coef = lr.coef_[0]
    coef_ot = float(coef[0])
    for i, col in enumerate(dummy_cols):
        name = col[4:] if col.startswith("seg_") else col
        segment_coef[name] = float(coef[i + 1])

    try:
        val_auc = roc_auc_score(y_val, lr.predict_proba(X_val)[:, 1])
        if val_auc is not None and (math.isnan(float(val_auc)) or math.isinf(float(val_auc))):
            val_auc = None
    except ValueError:
        val_auc = None

    config = {
        "version": 2,
        "intercept": float(lr.intercept_[0]),
        "scaler_mean": float(scaler.mean_[0]),
        "scaler_scale": float(scaler.scale_[0]),
        "coef_order_total": coef_ot,
        "segment_coef": segment_coef,
        "review_threshold_prob": thresh,
    }

    metrics = {
        "train_rows": int(len(X_train)),
        "val_rows": int(len(X_val)),
        "reference_segment": ref,
        "roc_auc_val": val_auc,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    conn = connect_postgres(url)
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                insert into public.ml_scoring_config (id, config, trained_at, metrics)
                values (1, %s::jsonb, now(), %s::jsonb)
                on conflict (id) do update set
                  config = excluded.config,
                  trained_at = excluded.trained_at,
                  metrics = excluded.metrics
                """,
                (
                    json.dumps(sanitize_for_jsonb(config)),
                    json.dumps(sanitize_for_jsonb(metrics)),
                ),
            )
        conn.commit()
    finally:
        conn.close()

    print(json.dumps(sanitize_for_jsonb({"ok": True, "metrics": metrics}), indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
