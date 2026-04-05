"""
IS455 wrangling helpers — copied from pipeline.ipynb (do not edit for course parity).
"""
import numpy as np
import pandas as pd
from datetime import datetime as dt
from scipy.stats import yeojohnson
from scipy import stats


def basic_wrangling(df, features=None, missing_threshold=0.95, unique_threshold=0.95, messages=True):
    if features is None:
        features = df.columns
    for feat in features:
        if feat in df.columns:
            missing = df[feat].isna().sum()
            unique = df[feat].nunique()
            rows = df.shape[0]
            if missing / rows >= missing_threshold:
                if messages:
                    print(
                        f"Dropping {feat}: {missing} missing values out of {rows} ({round(missing / rows, 2)})"
                    )
                df.drop(columns=[feat], inplace=True)
            elif unique / rows >= unique_threshold:
                if df[feat].dtype in ["int64", "object"]:
                    if messages:
                        print(
                            f"Dropping {feat}: {unique} unique values out of {rows} ({round(unique / rows, 2)})"
                        )
                    df.drop(columns=[feat], inplace=True)
            elif unique == 1:
                if messages:
                    print(
                        f"Dropping {feat}: Contains only one unique value ({df[feat].unique()[0]})"
                    )
                df.drop(columns=[feat], inplace=True)
    return df


def parse_date(df, features=None, days_since_today=False, drop_date=True, messages=True):
    if features is None:
        features = []
    for feat in features:
        if feat in df.columns:
            df[feat] = pd.to_datetime(df[feat])
            df[f"{feat}_year"] = df[feat].dt.year
            df[f"{feat}_month"] = df[feat].dt.month
            df[f"{feat}_day"] = df[feat].dt.day
            df[f"{feat}_weekday"] = df[feat].dt.day_name()
            if days_since_today:
                df[f"{feat}_days_until_today"] = (dt.today() - df[feat]).dt.days
            if drop_date:
                df.drop(columns=[feat], inplace=True)
    return df


def skew_correct(df, feature, methods=None, messages=True, visualize=False):
    if methods is None:
        methods = ["none", "cbrt", "sqrt", "log1p", "yeojohnson"]
    if feature not in df.columns:
        return df
    x = pd.to_numeric(df[feature], errors="coerce")
    if x.notna().sum() == 0:
        return df

    def _shift_nonneg(s: pd.Series):
        min_val = s.min(skipna=True)
        if pd.isna(min_val):
            return s, 0.0
        shift = -float(min_val) if min_val < 0 else 0.0
        return s + shift, shift

    x_shifted, _shift_amt = _shift_nonneg(x)
    candidates = {"none": x.astype("float64")}
    candidates["cbrt"] = np.cbrt(x_shifted.clip(lower=0)).astype("float64")
    candidates["sqrt"] = np.sqrt(x_shifted.clip(lower=0)).astype("float64")
    candidates["log1p"] = np.log1p(x_shifted.clip(lower=0)).astype("float64")
    if "yeojohnson" in methods:
        try:
            x_nonmissing = x.dropna().to_numpy(dtype="float64")
            yj_vals, _ = yeojohnson(x_nonmissing)
            yj_series = x.astype("float64").copy()
            yj_series.loc[x.dropna().index] = yj_vals
            candidates["yeojohnson"] = yj_series
        except Exception:
            pass
    best_name, best_series, best_score = None, None, np.inf
    for name in methods:
        if name not in candidates:
            continue
        sk = candidates[name].skew(skipna=True)
        score = abs(sk) if not pd.isna(sk) else np.inf
        if score < best_score:
            best_score, best_name, best_series = score, name, candidates[name]
    df[f"{feature}_skewfix"] = best_series.astype("float64")
    return df


def missing_drop(
    df, label="", features=None, messages=True, row_threshold=0.9, col_threshold=0.5
):
    df.dropna(axis=1, thresh=round(col_threshold * df.shape[0]), inplace=True)
    df.dropna(axis=0, thresh=round(row_threshold * df.shape[1]), inplace=True)
    if label != "":
        df.dropna(axis=0, subset=[label], inplace=True)

    def generate_missing_table():
        df_results = pd.DataFrame(columns=["Missing", "column", "rows"])
        for feat in df:
            missing = df[feat].isna().sum()
            if missing > 0:
                memory_col = df.drop(columns=[feat]).count().sum()
                memory_rows = df.dropna(subset=[feat]).count().sum()
                df_results.loc[feat] = [missing, memory_col, memory_rows]
        return df_results

    df_results = generate_missing_table()
    while df_results.shape[0] > 0:
        best = df_results[["column", "rows"]].max(axis=1).iloc[0]
        max_axis = df_results.columns[df_results.isin([best]).any()][0]
        df_results.sort_values(by=[max_axis], ascending=False, inplace=True)
        if max_axis == "rows":
            df.dropna(axis=0, subset=[df_results.index[0]], inplace=True)
        else:
            df.drop(columns=[df_results.index[0]], inplace=True)
        df_results = generate_missing_table()
    return df


def clean_outlier(df, features=None, method="remove", messages=True, skew_threshold=1):
    if features is None:
        features = []
    for feat in features:
        if feat in df.columns and pd.api.types.is_numeric_dtype(df[feat]):
            skew = df[feat].skew()
            if abs(skew) > skew_threshold:
                q1, q3 = df[feat].quantile(0.25), df[feat].quantile(0.75)
                min_val, max_val = q1 - 1.5 * (q3 - q1), q3 + 1.5 * (q3 - q1)
            else:
                m, s = df[feat].mean(), df[feat].std()
                min_val, max_val = m - 3 * s, m + 3 * s
            if method == "remove":
                df = df[(df[feat] >= min_val) & (df[feat] <= max_val)]
            elif method == "replace":
                df.loc[df[feat] < min_val, feat] = min_val
                df.loc[df[feat] > max_val, feat] = max_val
    return df
