"""
Apply artifacts/model.joblib (notebook pipeline) to all orders in Supabase.
Same wrangling + sklearn Pipeline as notebook_pipeline_train.py.
Run after train_from_supabase.py or via GitHub Actions.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import joblib
import numpy as np
import psycopg2

from notebook_pipeline_train import (
    TARGET_COL,
    connect_pg,
    load_raw_frame_supabase,
    wrangle_like_notebook,
)


def score_orders(database_url: str, joblib_path: str | Path) -> int:
    thresh = float(os.environ.get("REVIEW_THRESHOLD_PROB", "0.42"))

    joblib_path = Path(joblib_path)
    if not joblib_path.is_file():
        print(f"Missing model: {joblib_path}", file=sys.stderr)
        return 1

    final_model = joblib.load(joblib_path)
    raw = load_raw_frame_supabase(database_url)
    df = wrangle_like_notebook(raw.copy(), keep_order_id=True)

    if TARGET_COL not in df.columns:
        print("Target column missing after wrangling.", file=sys.stderr)
        return 1
    if "order_id" not in df.columns:
        print("order_id missing after wrangling (keep_order_id bug).", file=sys.stderr)
        return 1

    order_ids = df["order_id"].astype(int).values
    X = df.drop(columns=[TARGET_COL, "order_id"])
    proba = final_model.predict_proba(X)[:, 1].astype(float)

    conn = connect_pg(database_url)
    try:
        with conn.cursor() as cur:
            for oid, p in zip(order_ids, proba):
                risk = float(min(99.9, max(0.1, round(p * 1000) / 10)))
                # psycopg2 cannot bind numpy.bool_; use native bool
                needs = bool(float(p) >= thresh)
                cur.execute(
                    """
                    UPDATE public.orders
                    SET risk_score = %s, needs_review = %s, scored_at = now()
                    WHERE order_id = %s
                    """,
                    (risk, needs, int(oid)),
                )
        conn.commit()

        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT order_id FROM public.orders
                ORDER BY risk_score DESC NULLS LAST, order_id
                """
            )
            rows = cur.fetchall()
        rank = 1
        with conn.cursor() as cur:
            for (oid,) in rows:
                cur.execute(
                    "UPDATE public.orders SET priority_rank = %s WHERE order_id = %s",
                    (rank, oid),
                )
                rank += 1
        conn.commit()
    finally:
        conn.close()

    print(json.dumps({"ok": True, "scored_orders": len(order_ids)}, indent=2))
    return 0


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("Set DATABASE_URL", file=sys.stderr)
        return 1
    root = Path(__file__).resolve().parents[1]
    joblib_path = root / "artifacts" / "model.joblib"
    return score_orders(url, joblib_path)


if __name__ == "__main__":
    raise SystemExit(main())
