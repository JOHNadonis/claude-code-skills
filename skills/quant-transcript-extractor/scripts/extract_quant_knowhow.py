#!/usr/bin/env python3
"""Extract quant-relevant candidates from noisy transcript text.

This script is intentionally deterministic and lightweight:
- Normalizes common transcript artifacts
- Splits text into sentence units
- Tags categories using keyword rules
- Parses simple numeric parameters
- Emits candidate rule items for downstream LLM reasoning
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


FILLER_PATTERNS = [
    r"\b(um+|uh+|erm+|hmm+|ah+)\b",
    r"(?:^|\s)(?:嗯+|啊+|呃+|就是|然后|其实)(?:\s|$)",
]

NOISE_PATTERNS = [
    r"\[\d{1,2}:\d{2}(?::\d{2})?\]",  # [00:12] or [00:12:33]
    r"(speaker\s*\d+|讲师|老师|主持人|嘉宾)\s*[:：]",
]

CATEGORY_KEYWORDS: dict[str, list[str]] = {
    "entry": ["买入", "开仓", "做多", "入场", "突破", "金叉", "long", "entry"],
    "exit": ["卖出", "平仓", "离场", "止盈", "清仓", "exit", "close"],
    "risk": ["止损", "回撤", "风险", "风控", "熔断", "drawdown", "risk"],
    "position": ["仓位", "加仓", "减仓", "满仓", "半仓", "position", "sizing"],
    "filter": ["过滤", "不做", "跳过", "黑名单", "白名单", "filter"],
    "invalidation": ["失效", "作废", "无效", "不用", "停止", "invalidation"],
    "regime": ["震荡", "趋势", "牛市", "熊市", "波动率", "regime"],
    "cost": ["手续费", "滑点", "冲击成本", "成本", "fee", "slippage"],
    "execution": ["成交", "挂单", "市价", "限价", "执行", "execution"],
    "metric": ["夏普", "sharpe", "胜率", "回撤", "收益", "calmar", "年化"],
}

ACTION_HINTS = ["买入", "卖出", "开仓", "平仓", "止损", "止盈", "加仓", "减仓", "不做"]
CONDITION_HINTS = ["如果", "当", "只要", "一旦", "若", "unless", "if", "when"]


@dataclass
class Candidate:
    id: str
    category: str
    text: str
    condition: str
    action: str
    params: list[dict[str, str]]
    confidence: str


def normalize(text: str) -> str:
    out = text
    for pat in NOISE_PATTERNS:
        out = re.sub(pat, " ", out, flags=re.IGNORECASE)
    for pat in FILLER_PATTERNS:
        out = re.sub(pat, " ", out, flags=re.IGNORECASE)
    out = re.sub(r"[ \t]+", " ", out)
    out = re.sub(r"\n{3,}", "\n\n", out)
    return out.strip()


def split_sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[。！？!?;；\n])\s+", text)
    sentences: list[str] = []
    for p in parts:
        p = p.strip(" \n\t-")
        if len(p) < 8:
            continue
        sentences.append(p)
    return sentences


def tag_category(sentence: str) -> tuple[str, int]:
    best = ("other", 0)
    for cat, kws in CATEGORY_KEYWORDS.items():
        score = sum(1 for kw in kws if kw.lower() in sentence.lower())
        if score > best[1]:
            best = (cat, score)
    return best


def extract_params(sentence: str) -> list[dict[str, str]]:
    params: list[dict[str, str]] = []
    patterns = [
        (r"(\d+(?:\.\d+)?)\s*%", "percent"),
        (r"(\d+(?:\.\d+)?)\s*bps?", "bps"),
        (r"万(\d+(?:\.\d+)?)", "per_10k"),
        (r"(\d+)\s*(天|日|分钟|min|hour|小时)", "window"),
        (r"(\d+(?:\.\d+)?)\s*[xX倍]", "multiple"),
    ]
    for pat, unit in patterns:
        for m in re.finditer(pat, sentence, flags=re.IGNORECASE):
            params.append({"value": m.group(1), "unit": unit, "raw": m.group(0)})
    return params


def extract_condition(sentence: str) -> str:
    for hint in CONDITION_HINTS:
        idx = sentence.lower().find(hint.lower())
        if idx >= 0:
            return sentence[idx:].strip()
    return ""


def extract_action(sentence: str) -> str:
    for action in ACTION_HINTS:
        if action in sentence:
            return action
    if re.search(r"\b(buy|sell|long|short|exit)\b", sentence, flags=re.IGNORECASE):
        return "trade_action_detected"
    return ""


def confidence(score: int, condition: str, action: str, params: Iterable[dict[str, str]]) -> str:
    param_count = len(list(params))
    if score >= 2 and action and (condition or param_count > 0):
        return "high"
    if score >= 1 and (action or condition):
        return "medium"
    return "low"


def build_candidates(sentences: list[str]) -> list[Candidate]:
    out: list[Candidate] = []
    n = 0
    for s in sentences:
        cat, score = tag_category(s)
        if cat == "other":
            continue
        params = extract_params(s)
        cond = extract_condition(s)
        action = extract_action(s)
        conf = confidence(score, cond, action, params)
        n += 1
        out.append(
            Candidate(
                id=f"R{n:04d}",
                category=cat,
                text=s,
                condition=cond,
                action=action,
                params=params,
                confidence=conf,
            )
        )
    return out


def summarize(candidates: list[Candidate]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for c in candidates:
        counts[c.category] = counts.get(c.category, 0) + 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser(description="Extract quant know-how from transcript text.")
    parser.add_argument("--input", required=True, help="Path to transcript text/markdown file.")
    parser.add_argument("--output", required=True, help="Path to output JSON.")
    args = parser.parse_args()

    src = Path(args.input)
    dst = Path(args.output)
    text = src.read_text(encoding="utf-8")
    normalized = normalize(text)
    sentences = split_sentences(normalized)
    candidates = build_candidates(sentences)

    payload = {
        "meta": {
            "source": str(src),
            "sentence_count": len(sentences),
            "candidate_count": len(candidates),
        },
        "summary": summarize(candidates),
        "candidates": [asdict(c) for c in candidates],
    }

    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[ok] wrote {dst} with {len(candidates)} candidates")


if __name__ == "__main__":
    main()
