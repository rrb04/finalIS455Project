"""
Shared fraud model training: same logic used by pipeline.ipynb (deployment cells)
and by train_from_supabase.py / GitHub Actions.

Produces:
  - sklearn artifacts (joblib) for course / reproducibility
  - JSON config (version 2) consumed by web/lib/scoringFromConfig.ts

Deployable model = logistic regression on scaled order_total + customer_segment
(one-hot, reference category = lexicographically first segment).
"""

from __future__ import annotations

import json
import math
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import numpy as np
import pandas as pd
import psycopg2
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

TRAINING_QUERY = """
SELECT o.order_total::float8 AS order_total,
       o.is_fraud::int AS is_fraud,
       c.customer_segment
FROM public.orders o
JOIN public.customers c ON o.customer_id = c.customer_id
WHERE o.is_fraud IN (0, 1)
"""

SQLITE_TRAINING_QUERY = """
SELECT o.order_total AS order_total,
       o.is_fraud AS is_fraud,
       c.customer_segment
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.is_fraud IN (0, 1)
"""


@dataclass
class ProductionTrainResult:
    config: dict
    metrics: dict
    """Sklearn logistic regression (raw features: scaled total + segment dummies)."""
    classifier: LogisticRegression
    scaler: StandardScaler
    reference_segment: str
    dummy_column_names: list[str]


def sanitize_for_jsonb(obj: object) -> object:
    if isinstance(obj, dict):
        return {str(k): sanitize_for_jsonb(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [sanitize_for_jsonb(v) for v in obj]
    if isinstance(obj, (float, np.floating)):
        v = float(obj)
        if math.isnan(v) or math.isinf(v):
            return None
    return obj


# --- Postgres URL helpers (same as train_from_supabase) ---


def _split_postgres_url(url: str) -> tuple[str, str, str] | None:
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
    hex_digits = set("0123456789abcdefABCDEF")
    i, n = 0, len(password)
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
    parts = _split_postgres_url(url)
    if not parts:
        return url
    scheme, userinfo, hostpart = parts
    if ":" not in userinfo:
        return url
    user, password = userinfo.split(":", 1)
    return f"{scheme}{user}:{quote(password, safe='')}@{hostpart}"


def connect_postgres(url: str):
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


def load_training_frame_from_supabase(database_url: str) -> pd.DataFrame:
    return pd.read_sql_query(TRAINING_QUERY, connect_postgres(database_url))


def load_training_frame_from_sqlite(db_path: str | Path) -> pd.DataFrame:
    conn = sqlite3.connect(str(db_path))
    try:
        return pd.read_sql_query(SQLITE_TRAINING_QUERY, conn)
    finally:
        conn.close()


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


def train_production_logistic(
    df: pd.DataFrame,
    *,
    random_state: int = 27,
    review_threshold_prob: float = 0.42,
) -> ProductionTrainResult:
    """Train deployable logistic model; fills segment_coef for API export."""
    if len(df) < 30:
        raise ValueError(f"Need at least 30 labeled rows; got {len(df)}.")
    if df["is_fraud"].nunique() < 2:
        raise ValueError("Need both fraud and non-fraud labels.")

    X, y, scaler, ref, dummy_cols, segment_coef = build_xy(df)
    X_train, X_val, y_train, y_val = train_test_split(
        X, y, test_size=0.2, random_state=random_state, stratify=y
    )

    lr = LogisticRegression(max_iter=4000, class_weight="balanced")
    lr.fit(X_train, y_train)

    y_val_pred = lr.predict(X_val)
    acc_val = float(accuracy_score(y_val, y_val_pred))
    f1_val = float(f1_score(y_val, y_val_pred, average="weighted"))

    coef = lr.coef_[0]
    coef_ot = float(coef[0])
    for i, col in enumerate(dummy_cols):
        name = col[4:] if col.startswith("seg_") else col
        segment_coef[name] = float(coef[i + 1])

    try:
        val_auc = roc_auc_score(y_val, lr.predict_proba(X_val)[:, 1])
        if val_auc is not None and (
            math.isnan(float(val_auc)) or math.isinf(float(val_auc))
        ):
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
        "review_threshold_prob": review_threshold_prob,
    }

    metrics = {
        "train_rows": int(len(X_train)),
        "val_rows": int(len(X_val)),
        "reference_segment": ref,
        "accuracy_val": acc_val,
        "f1_weighted_val": f1_val,
        "roc_auc_val": val_auc,
        "trained_at": datetime.now(timezone.utc).isoformat(),
    }

    return ProductionTrainResult(
        config=config,
        metrics=metrics,
        classifier=lr,
        scaler=scaler,
        reference_segment=ref,
        dummy_column_names=dummy_cols,
    )


def save_joblib_bundle(
    result: ProductionTrainResult,
    path: str | Path,
) -> None:
    """Save Python-side model for grading / local inference (not used by Vercel)."""
    import joblib

    bundle = {
        "classifier": result.classifier,
        "scaler": result.scaler,
        "reference_segment": result.reference_segment,
        "dummy_column_names": result.dummy_column_names,
        "config": result.config,
        "metrics": result.metrics,
    }
    joblib.dump(bundle, path)


def save_metrics_json(metrics: dict, path: str | Path) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(sanitize_for_jsonb(metrics), f, indent=2)


def save_accuracy_md(
    result: ProductionTrainResult,
    path: str | Path,
    *,
    research_metrics: dict | None = None,
) -> None:
    """Human-readable report: production model + optional Phase 5 research metrics."""
    m = result.metrics
    acc = m.get("accuracy_val")
    f1 = m.get("f1_weighted_val")
    auc = m.get("roc_auc_val")
    acc_s = f"{acc:.4f}" if acc is not None else "—"
    f1_s = f"{f1:.4f}" if f1 is not None else "—"
    auc_s = f"{auc:.4f}" if auc is not None else "—"

    research_block = ""
    if research_metrics:
        ra = research_metrics.get("accuracy")
        rf = research_metrics.get("f1_score")
        rauc = research_metrics.get("roc_auc")
        ra_s = f"{float(ra):.4f}" if ra is not None else "—"
        rf_s = f"{float(rf):.4f}" if rf is not None else "—"
        rauc_s = f"{float(rauc):.4f}" if rauc is not None else "—"
        research_block = f"""

---

## Research model (Phases 4–5 in `pipeline.ipynb`)

Your **tuned** `final_model` (full preprocessing + many features — often **XGBoost**). This is **not** what Vercel runs; it is the stronger offline benchmark.

**Test set** (the same `train_test_split` as Phase 3: `X_test`, `y_test`).

| Metric | Value |
|--------|-------|
| **Accuracy** | {ra_s} |
| F1 (weighted) | {rf_s} |
| ROC AUC | {rauc_s} |

_Why two tables? The **site** uses a tiny **logistic** model (only `order_total` + `customer_segment`) so weights fit in **JSON** and run in **TypeScript**. That is easier to ship than XGBoost, so accuracy is usually **lower** than the research model — not a bug._
"""

    body = f"""# Fraud model — accuracy report

## Production model (live site + GitHub Actions)

Deployable **logistic regression** — same as `scripts/train_from_supabase.py` and **`ml_scoring_config`**.

**Validation holdout** (20%, stratified by `is_fraud`), features: `order_total` + `customer_segment` only.

| Metric | Value |
|--------|-------|
| **Accuracy** | {acc_s} |
| F1 (weighted) | {f1_s} |
| ROC AUC | {auc_s} |
| Training rows | {m.get("train_rows", "—")} |
| Validation rows | {m.get("val_rows", "—")} |
| Reference segment | `{m.get("reference_segment", "—")}` |

_Trained at: {m.get("trained_at", "—")}_
{research_block}"""
    Path(path).write_text(body.strip() + "\n", encoding="utf-8")


def fraud_probability_from_bundle(
    bundle: dict,
    order_total: float,
    segment: str | None,
) -> float:
    """Same math as web/lib/scoringFromConfig.ts (for notebook verification)."""
    cfg = bundle.get("config") or bundle
    z = (order_total - cfg["scaler_mean"]) / (cfg["scaler_scale"] or 1.0)
    seg = (segment or "").lower()
    seg_c = (
        cfg["segment_coef"].get(seg)
        or cfg["segment_coef"].get("unknown")
        or cfg["segment_coef"].get("other")
        or 0.0
    )
    logit = cfg["intercept"] + cfg["coef_order_total"] * z + seg_c
    if logit > 40:
        return 1.0
    if logit < -40:
        return 0.0
    return 1.0 / (1.0 + math.exp(-logit))


def upsert_ml_scoring_config(
    database_url: str,
    config: dict,
    metrics: dict,
) -> None:
    conn = connect_postgres(database_url)
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
