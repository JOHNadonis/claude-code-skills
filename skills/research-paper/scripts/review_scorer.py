#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = [
#     "pandas>=2.0.0",
# ]
# ///
"""
Mechanical review scorer for academic research papers.

Checks structural completeness, word counts, table/figure counts,
reference counts, and coefficient consistency against regression output.
Produces a JSON report with mechanical checks, a scoring template
(for Claude to fill in), and auto-scored hints.

Usage:
    uv run review_scorer.py \
      --paper /tmp/work/paper.md \
      --regression-results /tmp/work/regression_results.json \
      --output /tmp/work/review_mechanical.json
"""

import argparse
import json
import re
import sys
from pathlib import Path


# ---------------------------------------------------------------------------
# Section aliases (all lowercase)
# ---------------------------------------------------------------------------
SECTION_ALIASES: dict[str, list[str]] = {
    "abstract": ["abstract"],
    "introduction": ["introduction"],
    "literature_review": [
        "literature review",
        "related work",
        "previous studies",
        "theoretical framework",
    ],
    "data_and_methodology": [
        "data",
        "methodology",
        "data and method",
        "data and methodology",
        "empirical strategy",
        "research design",
    ],
    "results": ["results", "findings", "empirical results", "main results"],
    "robustness": [
        "robustness",
        "sensitivity",
        "robustness check",
        "robustness checks",
        "additional analysis",
    ],
    "conclusion": ["conclusion", "discussion", "concluding remarks"],
    "references": ["references", "bibliography"],
}

REQUIRED_SECTIONS = [
    "abstract",
    "introduction",
    "literature_review",
    "data_and_methodology",
    "results",
    "conclusion",
    "references",
]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _build_alias_lookup() -> dict[str, str]:
    """Return {alias: canonical_name} mapping."""
    lookup: dict[str, str] = {}
    for canonical, aliases in SECTION_ALIASES.items():
        for alias in aliases:
            lookup[alias] = canonical
    return lookup


ALIAS_LOOKUP = _build_alias_lookup()


def _detect_sections(lines: list[str]) -> list[tuple[str, int]]:
    """Return [(canonical_section_name, line_index), ...] for each heading found."""
    sections: list[tuple[str, int]] = []
    for i, line in enumerate(lines):
        match = re.match(r"^#{1,3}\s+(.+)", line)
        if not match:
            continue
        heading_text = match.group(1).strip().lower()
        # Strip trailing markers like "###" or numbering like "1."
        heading_text = re.sub(r"^[\d.]+\s*", "", heading_text)
        heading_text = heading_text.strip("#").strip()
        for alias, canonical in ALIAS_LOOKUP.items():
            if alias in heading_text or heading_text in alias:
                sections.append((canonical, i))
                break
    return sections


def _count_words(text: str) -> int:
    return len(text.split())


def _section_word_counts(
    lines: list[str], sections: list[tuple[str, int]]
) -> dict[str, int]:
    """Count words between each detected section heading and the next."""
    counts: dict[str, int] = {}
    for idx, (name, start_line) in enumerate(sections):
        end_line = sections[idx + 1][1] if idx + 1 < len(sections) else len(lines)
        body = "\n".join(lines[start_line + 1 : end_line])
        counts[name] = _count_words(body)
    return counts


def _count_tables(text: str) -> int:
    """Count Markdown tables (groups of consecutive lines starting with |)."""
    table_count = 0
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("|"):
            if not in_table:
                table_count += 1
                in_table = True
        else:
            in_table = False
    return table_count


def _count_figures_referenced(text: str) -> int:
    """Count references to 'Figure X' or 'Fig. X'."""
    return len(re.findall(r"\bFig(?:ure)?\.?\s+\d+", text, re.IGNORECASE))


def _count_references(lines: list[str], sections: list[tuple[str, int]]) -> int:
    """Count entries in the References section."""
    ref_start = None
    for idx, (name, line_idx) in enumerate(sections):
        if name == "references":
            ref_start = line_idx + 1
            ref_end = sections[idx + 1][1] if idx + 1 < len(sections) else len(lines)
            break
    if ref_start is None:
        return 0

    count = 0
    for line in lines[ref_start:ref_end]:
        stripped = line.strip()
        if not stripped:
            continue
        # Lines that look like citation entries:
        # - Start with author-style text (capital letter)
        # - Start with [N] or N. numbering
        # - Start with a dash/bullet
        if re.match(r"^(\[?\d+\]?\.?\s|[A-Z]|[-*•])", stripped):
            count += 1
    return count


def _extract_coefficients_from_paper(text: str) -> list[str]:
    """Extract numeric coefficient-like values from paper text.

    Looks for patterns like -0.085, 0.123**, 1.45***, etc.
    """
    pattern = r"(?<!\d)(-?\d+\.\d{2,})\*{0,3}"
    return re.findall(pattern, text)


def _check_coefficient_consistency(
    paper_text: str, regression: dict
) -> dict:
    """Check if coefficients mentioned in paper match regression output."""
    result: dict = {
        "checked": True,
        "mismatches": [],
        "details": "",
    }

    # Collect all coefficient values from regression results
    reg_coefficients: set[str] = set()

    def _collect_coefficients(obj: object, depth: int = 0) -> None:
        if depth > 10:
            return
        if isinstance(obj, dict):
            for key, val in obj.items():
                if key in ("coefficient", "coef", "beta", "estimate"):
                    if isinstance(val, (int, float)):
                        # Store rounded to several decimal places
                        reg_coefficients.add(f"{val:.3f}")
                        reg_coefficients.add(f"{val:.4f}")
                        reg_coefficients.add(f"{val:.2f}")
                else:
                    _collect_coefficients(val, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                _collect_coefficients(item, depth + 1)

    _collect_coefficients(regression)

    if not reg_coefficients:
        result["details"] = "No coefficients found in regression output to check"
        return result

    paper_coefficients = _extract_coefficients_from_paper(paper_text)
    mismatches = []

    for coef in paper_coefficients:
        # Check if this coefficient (or a close match) exists in regression output
        coef_float = float(coef)
        found = False
        for reg_coef in reg_coefficients:
            if abs(float(reg_coef) - coef_float) < 0.0005:
                found = True
                break
        if not found:
            # Only flag as mismatch if it looks like a regression coefficient
            # (not page numbers, years, sample sizes, etc.)
            if abs(coef_float) < 100:
                mismatches.append(coef)

    if mismatches:
        result["mismatches"] = mismatches
        result["details"] = (
            f"Found {len(mismatches)} coefficient(s) in paper not matching "
            f"regression output: {', '.join(mismatches)}"
        )
    else:
        result["details"] = "All coefficients in paper match regression output"

    return result


def _auto_score_completeness(missing: list[str]) -> int:
    score = 10 - 2 * len(missing)
    return max(score, 0)


def _auto_score_data_fitness(regression: dict | None) -> int:
    """Heuristic score based on regression diagnostics."""
    if regression is None:
        return 5  # neutral when no data

    score = 5  # baseline

    def _find_value(obj: object, keys: set[str], depth: int = 0) -> float | None:
        if depth > 10:
            return None
        if isinstance(obj, dict):
            for k, v in obj.items():
                if k.lower() in keys and isinstance(v, (int, float)):
                    return float(v)
                found = _find_value(v, keys, depth + 1)
                if found is not None:
                    return found
        elif isinstance(obj, list):
            for item in obj:
                found = _find_value(item, keys, depth + 1)
                if found is not None:
                    return found
        return None

    nobs = _find_value(regression, {"n", "nobs", "observations", "n_obs", "num_obs"})
    r2 = _find_value(regression, {"r_squared", "r2", "rsquared", "r_sq"})

    if nobs is not None:
        if nobs >= 10000:
            score += 2
        elif nobs >= 1000:
            score += 1
        elif nobs < 100:
            score -= 2

    if r2 is not None:
        if r2 >= 0.5:
            score += 2
        elif r2 >= 0.2:
            score += 1
        elif r2 < 0.05:
            score -= 1

    return max(min(score, 10), 0)


def _auto_score_robustness(regression: dict | None) -> int:
    """Heuristic score based on robustness checks in regression results."""
    if regression is None:
        return 5

    score = 3  # baseline

    # Count robustness-related entries
    robustness_keywords = {"robustness", "sensitivity", "alternative", "subsample", "placebo"}

    def _count_robustness(obj: object, depth: int = 0) -> int:
        if depth > 10:
            return 0
        count = 0
        if isinstance(obj, dict):
            for k, v in obj.items():
                if any(kw in k.lower() for kw in robustness_keywords):
                    count += 1
                count += _count_robustness(v, depth + 1)
        elif isinstance(obj, list):
            for item in obj:
                count += _count_robustness(item, depth + 1)
        return count

    rob_count = _count_robustness(regression)
    if rob_count >= 4:
        score += 4
    elif rob_count >= 2:
        score += 2
    elif rob_count >= 1:
        score += 1

    return max(min(score, 10), 0)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def build_review(paper_path: str, regression_path: str | None) -> dict:
    """Build the full mechanical review JSON."""
    lines: list[str] = []
    paper_text = ""

    try:
        paper_text = Path(paper_path).read_text(encoding="utf-8")
        lines = paper_text.splitlines()
    except Exception as e:
        return {"error": f"Cannot read paper: {e}"}

    regression: dict | None = None
    if regression_path:
        try:
            regression = json.loads(
                Path(regression_path).read_text(encoding="utf-8")
            )
        except Exception as e:
            print(f"Warning: Cannot read regression results: {e}", file=sys.stderr)

    # --- Section detection ---
    detected = _detect_sections(lines)
    detected_names = {name for name, _ in detected}

    sections_present = {
        sec: sec in detected_names for sec in SECTION_ALIASES
    }
    sections_missing = [
        sec for sec in SECTION_ALIASES if sec not in detected_names
    ]

    # --- Word counts ---
    total_word_count = _count_words(paper_text)
    section_wc = _section_word_counts(lines, detected)
    # Ensure all canonical sections appear in output
    for sec in SECTION_ALIASES:
        if sec not in section_wc:
            section_wc[sec] = 0

    # --- Tables, figures, references ---
    tables_count = _count_tables(paper_text)
    figures_referenced = _count_figures_referenced(paper_text)
    references_count = _count_references(lines, detected)

    # --- Coefficient consistency ---
    if regression is not None:
        coeff_check = _check_coefficient_consistency(paper_text, regression)
    else:
        coeff_check = {
            "checked": False,
            "mismatches": [],
            "details": "No regression results provided",
        }

    # --- Auto scores ---
    completeness = _auto_score_completeness(sections_missing)
    data_fitness_hint = _auto_score_data_fitness(regression)
    robustness_hint = _auto_score_robustness(regression)

    return {
        "mechanical_checks": {
            "sections_present": sections_present,
            "sections_missing": sections_missing,
            "total_word_count": total_word_count,
            "section_word_counts": section_wc,
            "tables_count": tables_count,
            "figures_referenced": figures_referenced,
            "references_count": references_count,
            "coefficient_consistency": coeff_check,
        },
        "scoring_template": {
            "novelty": {
                "score": None,
                "max": 10,
                "guidance": (
                    "Does the research question offer new insight? "
                    "Is it just replication?"
                ),
            },
            "causal_identification": {
                "score": None,
                "max": 10,
                "guidance": (
                    "Is the identification strategy convincing? "
                    "Are endogeneity concerns addressed?"
                ),
            },
            "data_fitness": {
                "score": None,
                "max": 10,
                "guidance": (
                    "Is this dataset appropriate for the research question? "
                    "Sufficient observations?"
                ),
            },
            "writing_quality": {
                "score": None,
                "max": 10,
                "guidance": (
                    "Is the paper clearly written? Logical flow? "
                    "Professional tone?"
                ),
            },
            "robustness": {
                "score": None,
                "max": 10,
                "guidance": (
                    "Are robustness checks comprehensive? "
                    "Do results hold across specifications?"
                ),
            },
        },
        "auto_scores": {
            "completeness": completeness,
            "data_fitness_hint": data_fitness_hint,
            "robustness_hint": robustness_hint,
        },
        "pass_threshold": 7.0,
        "max_rounds": 3,
    }


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Mechanical review scorer for research papers"
    )
    parser.add_argument(
        "--paper",
        required=True,
        help="Path to the paper Markdown file",
    )
    parser.add_argument(
        "--regression-results",
        default=None,
        help="Path to regression_results.json (optional)",
    )
    parser.add_argument(
        "--output",
        required=True,
        help="Path to write the review JSON output",
    )
    args = parser.parse_args()

    review = build_review(args.paper, args.regression_results)

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(review, f, indent=2, ensure_ascii=False)

    print(f"Review saved to {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
