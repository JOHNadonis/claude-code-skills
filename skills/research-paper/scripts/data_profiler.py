#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas>=2.0.0",
#     "openpyxl>=3.1.0",
#     "pyreadstat>=1.2.0",
# ]
# ///
"""
Data profiler for academic research datasets.
Scans a CSV/Excel/Stata file and outputs a structured JSON profile.

Usage:
    uv run data_profiler.py --input /path/to/data.csv --output /tmp/work/data_profile.json
"""

import argparse
import json
import os
import sys
from pathlib import Path

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Reading
# ---------------------------------------------------------------------------

FORMAT_MAP = {
    ".csv": "csv",
    ".xlsx": "excel",
    ".xls": "excel",
    ".dta": "stata",
}


def detect_format(path: str) -> str:
    ext = Path(path).suffix.lower()
    fmt = FORMAT_MAP.get(ext)
    if fmt is None:
        raise ValueError(f"Unsupported file extension: {ext}")
    return fmt


def read_data(path: str, fmt: str, encoding: str = "utf-8") -> pd.DataFrame:
    if fmt == "csv":
        for enc in [encoding, "gbk", "gb2312", "latin-1"]:
            try:
                return pd.read_csv(path, encoding=enc)
            except (UnicodeDecodeError, UnicodeError):
                continue
        raise ValueError(
            f"Cannot decode CSV with any of the attempted encodings (tried {encoding}, gbk, gb2312, latin-1)"
        )
    elif fmt == "excel":
        return pd.read_excel(path, engine="openpyxl")
    elif fmt == "stata":
        return pd.read_stata(path, convert_categoricals=False)
    else:
        raise ValueError(f"Unknown format: {fmt}")


# ---------------------------------------------------------------------------
# Variable role hinting
# ---------------------------------------------------------------------------

_ID_TOKENS = {"id", "code", "no"}
_TIME_TOKENS = {"year", "date", "wave", "time", "period"}


def _name_contains(col_name: str, tokens: set[str]) -> bool:
    """Check if column name contains any token as substring, suffix, or delimited part."""
    lowered = col_name.lower()
    return any(tok in lowered for tok in tokens)


def infer_role(col: pd.Series) -> str:
    name = col.name
    n = len(col)
    n_unique = col.nunique()
    unique_ratio = n_unique / n if n > 0 else 0

    # time check (dtype first, then name)
    if pd.api.types.is_datetime64_any_dtype(col):
        return "time"
    if _name_contains(name, _TIME_TOKENS):
        return "time"

    # id check: name match is sufficient (panel data has repeated ids)
    if _name_contains(name, _ID_TOKENS):
        return "id"

    # binary
    if n_unique == 2:
        return "binary"

    # categorical
    if pd.api.types.is_object_dtype(col) or isinstance(col.dtype, pd.CategoricalDtype):
        return "categorical"
    if pd.api.types.is_numeric_dtype(col) and unique_ratio < 0.05:
        return "categorical"

    # continuous (numeric fallthrough)
    if pd.api.types.is_numeric_dtype(col):
        return "continuous"

    return "categorical"


# ---------------------------------------------------------------------------
# Per-variable statistics
# ---------------------------------------------------------------------------

def compute_stats(col: pd.Series, role: str) -> dict:
    if role in ("continuous", "binary") and pd.api.types.is_numeric_dtype(col):
        desc = col.describe()
        return {
            "mean": _safe_float(desc.get("mean")),
            "std": _safe_float(desc.get("std")),
            "min": _safe_float(desc.get("min")),
            "max": _safe_float(desc.get("max")),
            "25%": _safe_float(desc.get("25%")),
            "50%": _safe_float(desc.get("50%")),
            "75%": _safe_float(desc.get("75%")),
        }
    elif role == "time":
        if pd.api.types.is_numeric_dtype(col):
            return {
                "min": _safe_json(col.min()),
                "max": _safe_json(col.max()),
                "n_unique": int(col.nunique()),
            }
        return {
            "min": str(col.min()),
            "max": str(col.max()),
            "n_unique": int(col.nunique()),
        }
    else:
        # categorical / id / other
        vc = col.value_counts(dropna=False).head(10)
        return {
            "value_counts": {
                _safe_json_key(k): int(v) for k, v in vc.items()
            }
        }


def _safe_float(val) -> float | None:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return None
    return round(float(val), 6)


def _safe_json(val):
    """Make a value JSON-serialisable."""
    if val is None:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        f = float(val)
        return None if np.isnan(f) else round(f, 6)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, (pd.Timestamp,)):
        return str(val)
    return val


def _safe_json_key(val) -> str:
    if val is None or (isinstance(val, float) and np.isnan(val)):
        return "<NA>"
    return str(val)


# ---------------------------------------------------------------------------
# Panel detection
# ---------------------------------------------------------------------------

def detect_panel(df: pd.DataFrame, var_infos: list[dict]) -> dict:
    id_candidates = [v["name"] for v in var_infos if v["role_hint"] == "id"]
    time_candidates = [v["name"] for v in var_infos if v["role_hint"] == "time"]

    if not id_candidates or not time_candidates:
        return {
            "detected": False,
            "id_var_candidates": id_candidates,
            "time_var_candidates": time_candidates,
            "n_entities": None,
            "n_periods": None,
            "balanced": None,
        }

    # Use the first plausible id and time variable
    id_var = id_candidates[0]
    time_var = time_candidates[0]

    n_entities = df[id_var].nunique()
    n_periods = df[time_var].nunique()

    # Check balance: each entity should appear exactly n_periods times
    counts = df.groupby(id_var)[time_var].nunique()
    balanced = bool((counts == n_periods).all())

    return {
        "detected": True,
        "id_var_candidates": id_candidates,
        "time_var_candidates": time_candidates,
        "n_entities": int(n_entities),
        "n_periods": int(n_periods),
        "balanced": balanced,
    }


# ---------------------------------------------------------------------------
# Correlations
# ---------------------------------------------------------------------------

def top_correlations(
    df: pd.DataFrame, var_infos: list[dict], top_n: int = 10
) -> list[dict]:
    skip_vars = {
        v["name"] for v in var_infos if v["role_hint"] in ("id", "time")
    }
    num_cols = [
        c for c in df.select_dtypes(include="number").columns if c not in skip_vars
    ]
    if len(num_cols) < 2:
        return []

    corr_matrix = df[num_cols].corr()

    pairs: list[dict] = []
    seen: set[tuple[str, str]] = set()
    for i, c1 in enumerate(num_cols):
        for j, c2 in enumerate(num_cols):
            if i >= j:
                continue
            key = (c1, c2)
            if key in seen:
                continue
            seen.add(key)
            val = corr_matrix.loc[c1, c2]
            if pd.isna(val):
                continue
            pairs.append({"var1": c1, "var2": c2, "corr": round(float(val), 4)})

    pairs.sort(key=lambda p: abs(p["corr"]), reverse=True)
    return pairs[:top_n]


# ---------------------------------------------------------------------------
# Data quality
# ---------------------------------------------------------------------------

def assess_quality(df: pd.DataFrame) -> dict:
    missing_pct = df.isnull().mean()
    return {
        "duplicate_rows": int(df.duplicated().sum()),
        "all_missing_cols": sorted(
            missing_pct[missing_pct == 1.0].index.tolist()
        ),
        "high_missing_cols": sorted(
            missing_pct[(missing_pct > 0.5) & (missing_pct < 1.0)].index.tolist()
        ),
        "constant_cols": sorted(
            [c for c in df.columns if df[c].nunique(dropna=False) <= 1]
        ),
    }


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------

def sample_rows(df: pd.DataFrame, n: int) -> list[dict]:
    head = df.head(n)
    records = []
    for _, row in head.iterrows():
        record = {}
        for col in head.columns:
            record[col] = _safe_json(row[col])
        records.append(record)
    return records


def sample_values(col: pd.Series, n: int) -> list:
    non_null = col.dropna()
    if len(non_null) == 0:
        return []
    vals = non_null.head(n).tolist()
    return [_safe_json(v) for v in vals]


# ---------------------------------------------------------------------------
# Main profiling
# ---------------------------------------------------------------------------

def profile(
    input_path: str,
    fmt: str | None = None,
    sample_n: int = 5,
    encoding: str = "utf-8",
) -> dict:
    path = os.path.abspath(input_path)
    if fmt is None:
        fmt = detect_format(path)

    df = read_data(path, fmt, encoding)

    size_mb = round(os.path.getsize(path) / (1024 * 1024), 2)

    file_info = {
        "path": path,
        "format": fmt,
        "rows": len(df),
        "columns": len(df.columns),
        "size_mb": size_mb,
    }

    # Per-variable profiling
    var_infos: list[dict] = []
    for col_name in df.columns:
        col = df[col_name]
        role = infer_role(col)
        missing_pct = round(float(col.isnull().mean()) * 100, 2)
        var_infos.append(
            {
                "name": col_name,
                "dtype": str(col.dtype),
                "role_hint": role,
                "missing_pct": missing_pct,
                "unique_count": int(col.nunique()),
                "stats": compute_stats(col, role),
                "sample_values": sample_values(col, sample_n),
            }
        )

    panel = detect_panel(df, var_infos)
    corrs = top_correlations(df, var_infos, top_n=10)
    quality = assess_quality(df)
    samples = sample_rows(df, sample_n)

    return {
        "file_info": file_info,
        "variables": var_infos,
        "panel_structure": panel,
        "correlations_top10": corrs,
        "data_quality": quality,
        "sample_data": samples,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Profile a dataset (CSV/Excel/Stata) and output structured JSON."
    )
    parser.add_argument(
        "--input", required=True, help="Path to the input data file"
    )
    parser.add_argument(
        "--output", required=True, help="Path to write the JSON profile"
    )
    parser.add_argument(
        "--format",
        choices=["csv", "excel", "stata"],
        default=None,
        help="File format (auto-detected from extension if omitted)",
    )
    parser.add_argument(
        "--sample-rows",
        type=int,
        default=5,
        help="Number of sample rows to include (default: 5)",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding for CSV files (default: utf-8)",
    )

    args = parser.parse_args()

    try:
        result = profile(
            input_path=args.input,
            fmt=args.format,
            sample_n=args.sample_rows,
            encoding=args.encoding,
        )
    except Exception as exc:
        result = {"error": str(exc)}

    output_path = os.path.abspath(args.output)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    json_str = json.dumps(result, indent=2, ensure_ascii=False, default=str)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(json_str)

    print(json_str)
    print(f"\nProfile saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
