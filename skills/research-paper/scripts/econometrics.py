#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas>=2.0.0",
#     "numpy>=1.24.0",
#     "statsmodels>=0.14.0",
#     "linearmodels>=6.0",
#     "openpyxl>=3.1.0",
#     "pyreadstat>=1.2.0",
# ]
# ///
"""
Econometric analysis execution engine.

Takes a regression specification (JSON) and a dataset, runs the regressions,
and outputs structured results as JSON. Designed to be driven by Claude as
part of an academic research paper pipeline.

Usage:
    uv run econometrics.py \
        --data /path/to/dataset.csv \
        --spec /tmp/work/regression_spec.json \
        --output /tmp/work/regression_results.json
"""

from __future__ import annotations

import argparse
import json
import sys
import warnings
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.diagnostic import het_breuschpagan
from statsmodels.stats.outliers_influence import variance_inflation_factor

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_data(path: str) -> pd.DataFrame:
    """Load dataset from CSV, Excel, or Stata. CSV tries utf-8 then gbk."""
    p = Path(path)
    suffix = p.suffix.lower()

    if suffix == ".csv":
        for enc in ("utf-8", "gbk"):
            try:
                return pd.read_csv(p, encoding=enc)
            except UnicodeDecodeError:
                continue
        raise ValueError(f"Cannot decode CSV file {path} with utf-8 or gbk")
    elif suffix in (".xls", ".xlsx"):
        return pd.read_excel(p)
    elif suffix == ".dta":
        import pyreadstat
        df, _ = pyreadstat.read_dta(str(p))
        return df
    else:
        raise ValueError(f"Unsupported file extension: {suffix}")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SAFE_NAMESPACE: dict[str, Any] = {
    "np": np,
    "pd": pd,
    "log": np.log,
    "exp": np.exp,
    "sqrt": np.sqrt,
    "abs": np.abs,
}


def _stars(p: float) -> str:
    if p < 0.01:
        return "***"
    if p < 0.05:
        return "**"
    if p < 0.1:
        return "*"
    return ""


def _coef_dict(name: str, coef: float, se: float, t: float, p: float) -> dict:
    return {
        "coef": round(coef, 6),
        "se": round(se, 6),
        "t": round(t, 3),
        "p": round(p, 4),
        "ci_low": round(coef - 1.96 * se, 6),
        "ci_high": round(coef + 1.96 * se, 6),
        "stars": _stars(p),
    }


def _format_number(x: float, decimals: int = 3) -> str:
    """Format a number: integers with commas, floats with fixed decimals."""
    if isinstance(x, int) or (isinstance(x, float) and x == int(x) and abs(x) > 10):
        return f"{int(x):,}"
    return f"{x:.{decimals}f}"


# ---------------------------------------------------------------------------
# ASCII regression table
# ---------------------------------------------------------------------------

def format_regression_table(
    model_name: str,
    coefficients: dict[str, dict],
    stats: dict[str, Any],
) -> str:
    """Build a clean ASCII regression table."""
    sep = "\u2500" * 53

    lines = [sep, f"{'':>20}  {model_name}", sep]

    for var, info in coefficients.items():
        coef_str = f"{info['coef']:.3f}{info['stars']}"
        se_str = f"({info['se']:.3f})"
        lines.append(f"{var:<22}{coef_str:>12}    {se_str}")

    lines.append(sep)

    if "n_obs" in stats:
        lines.append(f"{'N':<22}{_format_number(stats['n_obs']):>12}")
    if "r_squared" in stats:
        lines.append(f"{'R\u00b2':<22}{stats['r_squared']:>12.3f}")
    if "adj_r_squared" in stats:
        lines.append(f"{'Adj. R\u00b2':<22}{stats['adj_r_squared']:>12.3f}")
    if "within_r_squared" in stats:
        lines.append(f"{'Within R\u00b2':<22}{stats['within_r_squared']:>12.3f}")
    if "f_statistic" in stats:
        lines.append(f"{'F-statistic':<22}{stats['f_statistic']:>12.1f}")

    lines.append(sep)
    lines.append("*** p<0.01, ** p<0.05, * p<0.1")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Apply transformations
# ---------------------------------------------------------------------------

def apply_transformations(
    df: pd.DataFrame,
    transformations: dict[str, str],
    warnings_list: list[str],
) -> pd.DataFrame:
    """Apply variable transformations defined in the spec.

    Categorical specs like ``C(province)`` are skipped here—they are handled
    at model-fitting time via the formula API or pd.get_dummies.
    """
    df = df.copy()
    ns = {**SAFE_NAMESPACE}

    for var_name, expr in transformations.items():
        # Skip categorical markers — handled elsewhere
        if expr.strip().startswith("C("):
            continue
        try:
            # Make all existing columns available in the eval namespace
            col_ns = {col: df[col] for col in df.columns}
            col_ns.update(ns)
            df[var_name] = eval(expr, {"__builtins__": {}}, col_ns)  # noqa: S307
        except Exception as exc:
            warnings_list.append(f"Transformation '{var_name} = {expr}' failed: {exc}")

    return df


# ---------------------------------------------------------------------------
# Resolve controls / categorical expansions
# ---------------------------------------------------------------------------

def resolve_independent_vars(
    independent: list[str],
    controls: list[str] | None,
    transformations: dict[str, str],
    df: pd.DataFrame,
    warnings_list: list[str],
) -> tuple[list[str], pd.DataFrame]:
    """Expand controls (including categoricals) and return final var list + df."""
    all_vars = list(independent)
    controls = controls or []

    for ctrl in controls:
        expr = transformations.get(ctrl, ctrl)
        # Categorical: C(col)
        if expr.strip().startswith("C("):
            col = expr.strip()[2:-1]
            if col not in df.columns:
                warnings_list.append(f"Categorical column '{col}' not found; skipping control '{ctrl}'")
                continue
            dummies = pd.get_dummies(df[col], prefix=col, drop_first=True, dtype=float)
            for dc in dummies.columns:
                if dc not in df.columns:
                    df[dc] = dummies[dc]
            all_vars.extend(dummies.columns.tolist())
        else:
            # Plain variable name
            all_vars.append(ctrl)

    return all_vars, df


# ---------------------------------------------------------------------------
# Missing-data report
# ---------------------------------------------------------------------------

def _warn_missing(
    df: pd.DataFrame,
    cols: list[str],
    model_name: str,
    warnings_list: list[str],
) -> pd.DataFrame:
    """Drop rows with NaN in *cols*, emit warnings for significant missingness."""
    before = len(df)
    sub = df.dropna(subset=[c for c in cols if c in df.columns])
    after = len(sub)
    if before > 0 and after < before:
        pct = (before - after) / before * 100
        # Per-variable breakdown
        for c in cols:
            if c in df.columns:
                miss = df[c].isna().sum()
                if miss > 0:
                    mpct = miss / before * 100
                    warnings_list.append(
                        f"[{model_name}] Variable '{c}' has {mpct:.1f}% missing ({miss:,} rows)"
                    )
        warnings_list.append(
            f"[{model_name}] Dropped {before - after:,} rows ({pct:.1f}%) due to missing values"
        )
    return sub


# ---------------------------------------------------------------------------
# Model runners
# ---------------------------------------------------------------------------

def run_ols(
    spec: dict,
    df: pd.DataFrame,
    transformations: dict[str, str],
    warnings_list: list[str],
) -> dict:
    """Run an OLS regression."""
    dep = spec["dependent"]
    indep = list(spec.get("independent", []))
    controls = spec.get("controls", [])
    robust = spec.get("robust_se", False)
    cluster = spec.get("cluster_var")

    indep_all, df = resolve_independent_vars(indep, controls, transformations, df, warnings_list)

    all_cols = [dep] + [v for v in indep_all if v in df.columns]
    if cluster:
        all_cols.append(cluster)
    df_clean = _warn_missing(df, all_cols, spec["name"], warnings_list)

    y = df_clean[dep].astype(float)
    X = sm.add_constant(df_clean[[v for v in indep_all if v in df_clean.columns]].astype(float))

    model = sm.OLS(y, X)

    if cluster and cluster in df_clean.columns:
        groups = df_clean[cluster]
        result = model.fit(cov_type="cluster", cov_kwds={"groups": groups})
    elif robust:
        result = model.fit(cov_type="HC1")
    else:
        result = model.fit()

    coefficients: dict[str, dict] = {}
    for name in result.params.index:
        if name == "const":
            continue
        coefficients[name] = _coef_dict(
            name,
            result.params[name],
            result.bse[name],
            result.tvalues[name],
            result.pvalues[name],
        )

    stats = {
        "n_obs": int(result.nobs),
        "r_squared": round(float(result.rsquared), 4),
        "adj_r_squared": round(float(result.rsquared_adj), 4),
        "f_statistic": round(float(result.fvalue), 2) if hasattr(result, "fvalue") and result.fvalue is not None else None,
        "f_pvalue": round(float(result.f_pvalue), 4) if hasattr(result, "f_pvalue") and result.f_pvalue is not None else None,
    }

    return {
        "type": "ols",
        **stats,
        "coefficients": coefficients,
        "regression_table_text": format_regression_table(spec["name"], coefficients, stats),
        "_result_obj": result,  # kept for diagnostics, stripped before JSON output
    }


def run_panel_fe(
    spec: dict,
    df: pd.DataFrame,
    transformations: dict[str, str],
    warnings_list: list[str],
) -> dict:
    """Run a Panel Fixed-Effects regression."""
    from linearmodels.panel import PanelOLS

    dep = spec["dependent"]
    indep = list(spec.get("independent", []))
    entity_var = spec["entity_var"]
    time_var = spec["time_var"]
    cluster = spec.get("cluster_var")

    all_cols = [dep, entity_var, time_var] + indep
    if cluster:
        all_cols.append(cluster)
    df_clean = _warn_missing(df, all_cols, spec["name"], warnings_list)
    df_clean = df_clean.set_index([entity_var, time_var])

    y = df_clean[dep].astype(float)
    X = df_clean[indep].astype(float)

    model = PanelOLS(y, X, entity_effects=True, drop_absorbed=True)

    if cluster and cluster in df_clean.columns:
        result = model.fit(cov_type="clustered", cluster_entity=False, clusters=df_clean[cluster])
    elif cluster:
        # cluster_var equals entity or time
        result = model.fit(cov_type="clustered", cluster_entity=True)
    else:
        result = model.fit(cov_type="robust")

    coefficients: dict[str, dict] = {}
    for name in result.params.index:
        coefficients[name] = _coef_dict(
            name,
            result.params[name],
            result.std_errors[name],
            result.tstats[name],
            result.pvalues[name],
        )

    stats = {
        "n_obs": int(result.nobs),
        "r_squared": round(float(result.rsquared), 4),
        "within_r_squared": round(float(result.rsquared_within), 4) if hasattr(result, "rsquared_within") else None,
        "f_statistic": round(float(result.f_statistic.stat), 2) if result.f_statistic is not None else None,
        "f_pvalue": round(float(result.f_statistic.pval), 4) if result.f_statistic is not None else None,
    }

    return {
        "type": "panel_fe",
        **stats,
        "coefficients": coefficients,
        "regression_table_text": format_regression_table(spec["name"], coefficients, stats),
        "_result_obj": result,
    }


def run_panel_re(
    spec: dict,
    df: pd.DataFrame,
    transformations: dict[str, str],
    warnings_list: list[str],
) -> dict:
    """Run a Panel Random-Effects regression."""
    from linearmodels.panel import RandomEffects

    dep = spec["dependent"]
    indep = list(spec.get("independent", []))
    entity_var = spec["entity_var"]
    time_var = spec["time_var"]

    all_cols = [dep, entity_var, time_var] + indep
    df_clean = _warn_missing(df, all_cols, spec["name"], warnings_list)
    df_clean = df_clean.set_index([entity_var, time_var])

    y = df_clean[dep].astype(float)
    X = sm.add_constant(df_clean[indep].astype(float))

    model = RandomEffects(y, X)
    result = model.fit()

    coefficients: dict[str, dict] = {}
    for name in result.params.index:
        if name == "const":
            continue
        coefficients[name] = _coef_dict(
            name,
            result.params[name],
            result.std_errors[name],
            result.tstats[name],
            result.pvalues[name],
        )

    stats = {
        "n_obs": int(result.nobs),
        "r_squared": round(float(result.rsquared), 4),
        "within_r_squared": round(float(result.rsquared_within), 4) if hasattr(result, "rsquared_within") else None,
    }

    return {
        "type": "panel_re",
        **stats,
        "coefficients": coefficients,
        "regression_table_text": format_regression_table(spec["name"], coefficients, stats),
        "_result_obj": result,
    }


def run_iv_2sls(
    spec: dict,
    df: pd.DataFrame,
    transformations: dict[str, str],
    warnings_list: list[str],
) -> dict:
    """Run an IV/2SLS regression."""
    from linearmodels.iv import IV2SLS

    dep = spec["dependent"]
    endogenous = spec.get("endogenous", [])
    instruments = spec.get("instruments", [])
    exogenous = spec.get("exogenous", [])
    entity_var = spec.get("entity_var")
    time_var = spec.get("time_var")

    all_cols = [dep] + endogenous + instruments + exogenous
    if entity_var:
        all_cols.append(entity_var)
    if time_var:
        all_cols.append(time_var)
    df_clean = _warn_missing(df, all_cols, spec["name"], warnings_list)

    if entity_var and time_var:
        df_clean = df_clean.set_index([entity_var, time_var])

    y = df_clean[dep].astype(float)
    endog = df_clean[endogenous].astype(float)
    exog = sm.add_constant(df_clean[exogenous].astype(float)) if exogenous else sm.add_constant(pd.DataFrame(index=df_clean.index))
    instr = df_clean[instruments].astype(float)

    model = IV2SLS(y, exog, endog, instr)
    result = model.fit(cov_type="robust")

    coefficients: dict[str, dict] = {}
    for name in result.params.index:
        if name == "const":
            continue
        coefficients[name] = _coef_dict(
            name,
            result.params[name],
            result.std_errors[name],
            result.tstats[name],
            result.pvalues[name],
        )

    stats = {
        "n_obs": int(result.nobs),
        "r_squared": round(float(result.rsquared), 4),
        "f_statistic": round(float(result.f_statistic.stat), 2) if result.f_statistic is not None else None,
        "f_pvalue": round(float(result.f_statistic.pval), 4) if result.f_statistic is not None else None,
    }

    # First-stage diagnostics
    first_stage: dict[str, Any] = {}
    if hasattr(result, "first_stage"):
        try:
            fs = result.first_stage
            if fs is not None:
                first_stage["diagnostics"] = str(fs)
        except Exception:
            pass

    out = {
        "type": "iv_2sls",
        **stats,
        "coefficients": coefficients,
        "regression_table_text": format_regression_table(spec["name"], coefficients, stats),
        "_result_obj": result,
    }
    if first_stage:
        out["first_stage"] = first_stage
    return out


MODEL_RUNNERS = {
    "ols": run_ols,
    "panel_fe": run_panel_fe,
    "panel_re": run_panel_re,
    "iv_2sls": run_iv_2sls,
}


# ---------------------------------------------------------------------------
# Diagnostics
# ---------------------------------------------------------------------------

def run_diagnostics(
    requested: list[str],
    model_results: dict[str, dict],
    df: pd.DataFrame,
    spec: dict,
    warnings_list: list[str],
) -> dict[str, Any]:
    """Run requested diagnostic tests across fitted models."""
    diag: dict[str, Any] = {}

    for test in requested:
        try:
            if test == "hausman":
                diag["hausman"] = _diag_hausman(model_results, warnings_list)
            elif test == "vif":
                diag["vif"] = _diag_vif(model_results, df, spec, warnings_list)
            elif test == "breusch_pagan":
                diag["breusch_pagan"] = _diag_breusch_pagan(model_results, warnings_list)
            elif test == "durbin_wu_hausman":
                diag["durbin_wu_hausman"] = _diag_durbin_wu_hausman(model_results, warnings_list)
            else:
                warnings_list.append(f"Unknown diagnostic test: {test}")
        except Exception as exc:
            diag[test] = {"error": str(exc)}
            warnings_list.append(f"Diagnostic '{test}' failed: {exc}")

    return diag


def _diag_hausman(
    model_results: dict[str, dict],
    warnings_list: list[str],
) -> dict:
    """Hausman test: compare FE vs RE if both are available."""
    fe_result = None
    re_result = None
    for _name, res in model_results.items():
        obj = res.get("_result_obj")
        if obj is None:
            continue
        if res["type"] == "panel_fe" and fe_result is None:
            fe_result = obj
        elif res["type"] == "panel_re" and re_result is None:
            re_result = obj

    if fe_result is None or re_result is None:
        return {"error": "Need both panel_fe and panel_re models for Hausman test"}

    # Common coefficients (exclude const)
    fe_params = fe_result.params
    re_params = re_result.params
    common = [v for v in fe_params.index if v in re_params.index and v != "const"]

    if not common:
        return {"error": "No common coefficients between FE and RE models"}

    b_fe = fe_params[common].values
    b_re = re_params[common].values
    diff = b_fe - b_re

    cov_fe = fe_result.cov[common].loc[common].values if hasattr(fe_result, "cov") else np.diag(fe_result.std_errors[common].values ** 2)
    cov_re = re_result.cov[common].loc[common].values if hasattr(re_result, "cov") else np.diag(re_result.std_errors[common].values ** 2)

    cov_diff = cov_fe - cov_re

    try:
        stat = float(diff @ np.linalg.inv(cov_diff) @ diff)
    except np.linalg.LinAlgError:
        # Use pseudo-inverse if singular
        stat = float(diff @ np.linalg.pinv(cov_diff) @ diff)
        warnings_list.append("Hausman test used pseudo-inverse due to singular covariance difference")

    from scipy import stats as sp_stats

    df_test = len(common)
    p_value = float(1 - sp_stats.chi2.cdf(stat, df_test))

    conclusion = "Reject H0: use fixed effects" if p_value < 0.05 else "Fail to reject H0: random effects may be consistent"

    return {
        "statistic": round(stat, 3),
        "p_value": round(p_value, 4),
        "df": df_test,
        "conclusion": conclusion,
    }


def _diag_vif(
    model_results: dict[str, dict],
    df: pd.DataFrame,
    spec: dict,
    warnings_list: list[str],
) -> dict:
    """Compute VIF for the first OLS model's independent variables."""
    # Find the first OLS model
    ols_spec = None
    for m in spec.get("models", []):
        if m["type"] == "ols":
            ols_spec = m
            break

    if ols_spec is None:
        return {"error": "No OLS model found for VIF computation"}

    indep = list(ols_spec.get("independent", []))
    # Only keep columns that exist in df
    indep = [v for v in indep if v in df.columns]

    if not indep:
        return {"error": "No valid independent variables for VIF"}

    df_sub = df[indep].dropna().astype(float)
    X = sm.add_constant(df_sub)

    vif_dict: dict[str, float] = {}
    for i, col in enumerate(X.columns):
        if col == "const":
            continue
        try:
            vif_val = variance_inflation_factor(X.values, i)
            vif_dict[col] = round(float(vif_val), 2)
        except Exception as exc:
            warnings_list.append(f"VIF for '{col}' failed: {exc}")

    return vif_dict


def _diag_breusch_pagan(
    model_results: dict[str, dict],
    warnings_list: list[str],
) -> dict:
    """Breusch-Pagan heteroskedasticity test on the first OLS model."""
    ols_result = None
    for _name, res in model_results.items():
        if res["type"] == "ols" and "_result_obj" in res:
            ols_result = res["_result_obj"]
            break

    if ols_result is None:
        return {"error": "No OLS model available for Breusch-Pagan test"}

    resid = ols_result.resid
    exog = ols_result.model.exog

    lm_stat, lm_pval, f_stat, f_pval = het_breuschpagan(resid, exog)

    conclusion = "Heteroskedasticity detected" if lm_pval < 0.05 else "No significant heteroskedasticity"

    return {
        "statistic": round(float(lm_stat), 3),
        "p_value": round(float(lm_pval), 4),
        "f_statistic": round(float(f_stat), 3),
        "f_p_value": round(float(f_pval), 4),
        "conclusion": conclusion,
    }


def _diag_durbin_wu_hausman(
    model_results: dict[str, dict],
    warnings_list: list[str],
) -> dict:
    """Durbin-Wu-Hausman endogeneity test for IV models.

    Compare OLS and IV estimates; if they differ significantly the
    endogenous regressors are indeed endogenous.
    """
    iv_result = None
    iv_name = None
    for name, res in model_results.items():
        if res["type"] == "iv_2sls" and "_result_obj" in res:
            iv_result = res["_result_obj"]
            iv_name = name
            break

    if iv_result is None:
        return {"error": "No IV/2SLS model available for Durbin-Wu-Hausman test"}

    # linearmodels IV2SLS results expose a wu_hausman method if available
    try:
        wh = iv_result.wu_hausman()
        return {
            "statistic": round(float(wh.stat), 3),
            "p_value": round(float(wh.pval), 4),
            "conclusion": "Endogeneity confirmed: IV preferred" if wh.pval < 0.05 else "No endogeneity detected: OLS may be consistent",
        }
    except Exception:
        pass

    # Fallback: manual augmented regression approach
    warnings_list.append(
        f"[{iv_name}] Wu-Hausman via linearmodels not available; "
        "returning placeholder. Consider manual augmented regression."
    )
    return {"error": "Wu-Hausman test not available for this IV specification"}


# ---------------------------------------------------------------------------
# Robustness checks
# ---------------------------------------------------------------------------

def run_robustness(
    robustness_specs: list[dict],
    base_models: dict[str, dict],
    model_specs: dict[str, dict],
    df: pd.DataFrame,
    transformations: dict[str, str],
    errors_list: list[str],
    warnings_list: list[str],
) -> dict[str, dict]:
    """Run robustness checks based on spec."""
    results: dict[str, dict] = {}

    for rob in robustness_specs:
        name = rob["name"]
        base_name = rob["base_model"]
        print(f"  Running robustness: {name}...", file=sys.stderr)

        if base_name not in model_specs:
            errors_list.append(f"[{name}] Base model '{base_name}' not found in spec")
            continue

        # Deep-copy the base spec, then apply overrides
        import copy
        mod_spec = copy.deepcopy(model_specs[base_name])
        mod_spec["name"] = name

        # Apply filter
        df_rob = df
        if "filter" in rob:
            try:
                mask = df_rob.eval(rob["filter"])
                df_rob = df_rob[mask].copy()
                if len(df_rob) == 0:
                    errors_list.append(f"[{name}] Filter '{rob['filter']}' resulted in 0 rows")
                    continue
            except Exception as exc:
                errors_list.append(f"[{name}] Filter '{rob['filter']}' failed: {exc}")
                continue

        # Apply dependent override
        if "dependent_override" in rob:
            mod_spec["dependent"] = rob["dependent_override"]

        # Apply independent override
        if "independent_override" in rob:
            mod_spec["independent"] = rob["independent_override"]

        # Run model
        model_type = mod_spec["type"]
        runner = MODEL_RUNNERS.get(model_type)
        if runner is None:
            errors_list.append(f"[{name}] Unsupported model type: {model_type}")
            continue

        try:
            res = runner(mod_spec, df_rob, transformations, warnings_list)
            # Strip internal object
            res.pop("_result_obj", None)
            results[name] = res
        except Exception as exc:
            errors_list.append(f"[{name}] {type(exc).__name__}: {exc}")

    return results


# ---------------------------------------------------------------------------
# Main orchestrator
# ---------------------------------------------------------------------------

def run_all(spec: dict, df: pd.DataFrame) -> dict:
    """Execute the full regression spec and return structured results."""
    errors: list[str] = []
    warn: list[str] = []

    transformations: dict[str, str] = spec.get("transformations", {})

    # Apply transformations
    df = apply_transformations(df, transformations, warn)

    # Build lookup of model specs by name
    model_specs: dict[str, dict] = {}
    for m in spec.get("models", []):
        model_specs[m["name"]] = m

    # --- Run models ---
    model_results: dict[str, dict] = {}
    for m in spec.get("models", []):
        name = m["name"]
        model_type = m["type"]
        print(f"Running model: {name}...", file=sys.stderr)

        runner = MODEL_RUNNERS.get(model_type)
        if runner is None:
            errors.append(f"[{name}] Unsupported model type: {model_type}")
            continue

        try:
            model_results[name] = runner(m, df, transformations, warn)
        except Exception as exc:
            errors.append(f"[{name}] {type(exc).__name__}: {exc}")

    # --- Robustness ---
    robustness_results: dict[str, dict] = {}
    if spec.get("robustness"):
        print("Running robustness checks...", file=sys.stderr)
        robustness_results = run_robustness(
            spec["robustness"], model_results, model_specs, df, transformations, errors, warn
        )

    # --- Diagnostics ---
    diagnostics: dict[str, Any] = {}
    if spec.get("diagnostics"):
        print("Running diagnostics...", file=sys.stderr)
        diagnostics = run_diagnostics(spec["diagnostics"], model_results, df, spec, warn)

    # --- Assemble output (strip internal objects) ---
    output_models: dict[str, dict] = {}
    for name, res in model_results.items():
        clean = {k: v for k, v in res.items() if k != "_result_obj"}
        output_models[name] = clean

    return {
        "models": output_models,
        "robustness": robustness_results,
        "diagnostics": diagnostics,
        "errors": errors,
        "warnings": warn,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Econometric analysis execution engine"
    )
    parser.add_argument(
        "--data", required=True, help="Path to dataset (CSV, Excel, or Stata)"
    )
    parser.add_argument(
        "--spec", required=True, help="Path to regression_spec.json"
    )
    parser.add_argument(
        "--output", required=True, help="Path to write regression_results.json"
    )
    args = parser.parse_args()

    # Suppress noisy warnings from statsmodels / linearmodels
    warnings.filterwarnings("ignore", category=FutureWarning)

    # Load spec
    print(f"Loading spec: {args.spec}", file=sys.stderr)
    with open(args.spec, "r", encoding="utf-8") as f:
        spec = json.load(f)

    # Load data
    print(f"Loading data: {args.data}", file=sys.stderr)
    try:
        df = load_data(args.data)
    except Exception as exc:
        result = {"models": {}, "robustness": {}, "diagnostics": {}, "errors": [f"Data load failed: {exc}"], "warnings": []}
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
        print(f"FATAL: {exc}", file=sys.stderr)
        sys.exit(1)

    print(f"Dataset: {len(df):,} rows x {len(df.columns)} columns", file=sys.stderr)

    # Run
    result = run_all(spec, df)

    # Write output
    Path(args.output).parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    # Summary
    n_models = len(result["models"])
    n_errors = len(result["errors"])
    n_warnings = len(result["warnings"])
    print(f"\nDone: {n_models} model(s), {n_errors} error(s), {n_warnings} warning(s)", file=sys.stderr)
    print(f"Results written to: {args.output}", file=sys.stderr)

    if result["errors"]:
        print("\nErrors:", file=sys.stderr)
        for e in result["errors"]:
            print(f"  - {e}", file=sys.stderr)

    if result["warnings"]:
        print("\nWarnings:", file=sys.stderr)
        for w in result["warnings"]:
            print(f"  - {w}", file=sys.stderr)


if __name__ == "__main__":
    main()
