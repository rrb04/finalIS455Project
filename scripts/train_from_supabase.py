#!/usr/bin/env python3
"""
Daily retrain entrypoint (GitHub Actions + local). Trains the same pipeline as
pipeline.ipynb via notebook_pipeline_train.py, saves artifacts/model.joblib,
then scores all orders in Supabase (see score_supabase_orders.py).

Requires: DATABASE_URL
Optional: REVIEW_THRESHOLD_PROB (default 0.42) — used when writing needs_review

pip install -r scripts/requirements-train.txt
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if _SCRIPT_DIR not in sys.path:
    sys.path.insert(0, _SCRIPT_DIR)

from notebook_pipeline_train import (  # noqa: E402
    load_raw_frame_supabase,
    save_artifacts,
    train_notebook_pipeline,
)
from score_supabase_orders import score_orders  # noqa: E402


def main() -> int:
    url = os.environ.get("DATABASE_URL", "").strip()
    if not url:
        print("Set DATABASE_URL to your Supabase Postgres connection string.", file=sys.stderr)
        return 1

    root = Path(__file__).resolve().parents[1]
    artifacts_dir = root / "artifacts"

    df = load_raw_frame_supabase(url)
    try:
        model, metrics, _, _ = train_notebook_pipeline(df)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1

    save_artifacts(model, metrics, artifacts_dir)

    joblib_path = artifacts_dir / "model.joblib"
    rc = score_orders(url, joblib_path)
    if rc != 0:
        return rc

    print(json.dumps({"ok": True, "metrics": metrics, "artifacts": str(artifacts_dir)}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
