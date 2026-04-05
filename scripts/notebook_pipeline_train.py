"""
Mirrors pipeline.ipynb (Phases 3–6): same wrangling, ColumnTransformer, model
comparison, RandomizedSearchCV, final_model. Used by train_from_supabase.py so
GitHub Actions trains the same model as the submitted notebook (data from Supabase).
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import psycopg2
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.model_selection import RandomizedSearchCV, train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from xgboost import XGBClassifier

from is455_wrangling import basic_wrangling, clean_outlier, missing_drop, parse_date, skew_correct

TARGET_COL = "is_fraud"
RANDOM_STATE = 27

SQLITE_JOIN = """
SELECT o.*, c.gender, c.city, c.state, c.customer_segment, c.loyalty_tier, c.birthdate, c.created_at as customer_created_at
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
"""

POSTGRES_JOIN = """
SELECT o.*, c.gender, c.city, c.state, c.customer_segment, c.loyalty_tier, c.birthdate, c.created_at as customer_created_at
FROM public.orders o
JOIN public.customers c ON o.customer_id = c.customer_id
"""


def _encode_pg_url(url: str) -> str:
    from urllib.parse import quote

    for scheme in ("postgresql://", "postgres://"):
        if url.startswith(scheme):
            rest = url[len(scheme) :]
            break
    else:
        return url
    if "@" not in rest:
        return url
    userinfo, hostpart = rest.rsplit("@", 1)
    if ":" not in userinfo:
        return url
    user, password = userinfo.split(":", 1)
    hex_digits = set("0123456789abcdefABCDEF")
    i, n = 0, len(password)
    while i < n:
        if password[i] != "%":
            i += 1
            continue
        if i + 2 >= n or password[i + 1] not in hex_digits or password[i + 2] not in hex_digits:
            return f"{scheme}{user}:{quote(password, safe='')}@{hostpart}"
        i += 3
    return url


def connect_pg(url: str):
    try:
        return psycopg2.connect(url)
    except psycopg2.Error:
        return psycopg2.connect(_encode_pg_url(url))


def load_raw_frame_sqlite(path: str | Path) -> pd.DataFrame:
    conn = sqlite3.connect(str(path))
    try:
        return pd.read_sql_query(SQLITE_JOIN, conn)
    finally:
        conn.close()


def load_raw_frame_supabase(database_url: str) -> pd.DataFrame:
    return pd.read_sql_query(POSTGRES_JOIN, connect_pg(database_url))


def wrangle_like_notebook(df: pd.DataFrame, *, keep_order_id: bool = False) -> pd.DataFrame:
    # Training: order_id is dropped as near-unique (basic_wrangling). Scoring needs it to map rows.
    wrangle_feats = [c for c in df.columns if not (keep_order_id and c == "order_id")]
    df = basic_wrangling(df, features=wrangle_feats, messages=False)
    date_cols = ["order_datetime", "birthdate", "customer_created_at"]
    df = parse_date(df, features=[c for c in date_cols if c in df.columns], messages=False)
    num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if TARGET_COL in num_cols:
        num_cols.remove(TARGET_COL)
    if keep_order_id and "order_id" in num_cols:
        num_cols.remove("order_id")
    for col in num_cols:
        df = skew_correct(df, col, methods=["none", "log1p"])
    df = missing_drop(df, label=TARGET_COL)
    df = clean_outlier(df, features=num_cols)
    return df


def train_notebook_pipeline(df: pd.DataFrame):
    """Returns (final_model, metrics_dict, X_test, y_test)."""
    df = wrangle_like_notebook(df.copy())
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=RANDOM_STATE
    )

    numeric_features = X.select_dtypes(include=["int64", "float64"]).columns
    categorical_features = X.select_dtypes(include=["object"]).columns

    preprocessor = ColumnTransformer(
        transformers=[
            (
                "num",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler()),
                    ]
                ),
                numeric_features,
            ),
            (
                "cat",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("encoder", OneHotEncoder(handle_unknown="ignore")),
                    ]
                ),
                categorical_features,
            ),
        ]
    )

    results = []
    models = [
        ("Baseline", DummyClassifier(strategy="stratified")),
        ("Linear", LogisticRegression(max_iter=1000)),
        ("Ensemble", XGBClassifier(random_state=RANDOM_STATE)),
    ]

    for name, model in models:
        pipe = Pipeline(steps=[("preprocessor", preprocessor), ("classifier", model)])
        pipe.fit(X_train, y_train)
        y_pred = pipe.predict(X_test)
        y_prob = (
            pipe.predict_proba(X_test)[:, 1]
            if hasattr(model, "predict_proba")
            else y_pred
        )
        results.append(
            {
                "Model": name,
                "Accuracy": accuracy_score(y_test, y_pred),
                "F1": f1_score(y_test, y_pred, average="weighted"),
                "ROC AUC": roc_auc_score(y_test, y_prob),
            }
        )

    comparison_df = pd.DataFrame(results)
    best_model_name = comparison_df.sort_values(by="F1", ascending=False).iloc[0]["Model"]

    if best_model_name == "Ensemble":
        param_dist = {
            "classifier__n_estimators": [50, 100, 200],
            "classifier__max_depth": [3, 6, 10],
            "classifier__learning_rate": [0.01, 0.1, 0.2],
        }
        best_clf = XGBClassifier(random_state=RANDOM_STATE)
    else:
        param_dist = {"classifier__C": [0.1, 1, 10]}
        best_clf = LogisticRegression(max_iter=1000)

    tuned_pipe = Pipeline(
        steps=[("preprocessor", preprocessor), ("classifier", best_clf)]
    )
    random_search = RandomizedSearchCV(
        tuned_pipe,
        param_distributions=param_dist,
        n_iter=5,
        cv=3,
        random_state=RANDOM_STATE,
    )
    random_search.fit(X_train, y_train)
    final_model = random_search.best_estimator_

    y_pred = final_model.predict(X_test)
    metrics = {
        "accuracy": float(accuracy_score(y_test, y_pred)),
        "f1_score": float(f1_score(y_test, y_pred, average="weighted")),
        "roc_auc": float(roc_auc_score(y_test, final_model.predict_proba(X_test)[:, 1])),
        "best_model_name": best_model_name,
        "best_params": {k: (v.item() if hasattr(v, "item") else v) for k, v in random_search.best_params_.items()},
    }

    return final_model, metrics, X_test, y_test


def save_artifacts(
    final_model,
    metrics: dict,
    out_dir: str | Path,
    *,
    write_metrics_md: bool = True,
) -> None:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(final_model, out_dir / "model.joblib")
    with open(out_dir / "metrics.json", "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    if write_metrics_md:
        with open(out_dir / "metrics.md", "w", encoding="utf-8") as f:
            f.write("# Model Performance Metrics\n\n")
            f.write(f"- **Accuracy**: {metrics['accuracy']:.4f}\n")
            f.write(f"- **F1 Score**: {metrics['f1_score']:.4f}\n")
            f.write(f"- **ROC AUC**: {metrics['roc_auc']:.4f}\n")
