#!/usr/bin/env python3
"""Generate market summary from latest-24h.json.

Default: rule-based template summary (zero cost).
Optional: LLM-powered summary if ANTHROPIC_API_KEY or OPENAI_API_KEY is set.

Usage:
    python scripts/generate_summary.py --data-dir data --output-dir data
    python scripts/generate_summary.py --data-dir data --output-dir data --no-llm
"""

from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

MARKET_LABELS = {
    "a_stock": "A股", "us_stock": "美股", "hk_stock": "港股",
    "macro": "宏观", "crypto": "加密", "commodity": "大宗",
    "forex": "外汇", "general": "综合",
}

DISPLAY_ORDER = ["a_stock", "us_stock", "hk_stock", "macro", "crypto", "commodity", "forex", "general"]


# ─────────────────────── Rule-based summary ──────────────────────


def rule_based_summary(items: list[dict]) -> dict:
    # Separate Polymarket items
    poly_items = [i for i in items if i.get("site_id") == "polymarket"]
    news_items = [i for i in items if i.get("site_id") != "polymarket"]

    # Group news by market_tags
    market_groups: dict[str, list[dict]] = defaultdict(list)
    for item in news_items:
        for tag in item.get("market_tags", ["general"]):
            market_groups[tag].append(item)

    sections: dict[str, dict] = {}
    for tag in DISPLAY_ORDER:
        tag_items = market_groups.get(tag, [])
        if not tag_items:
            continue
        high = [i for i in tag_items if i.get("importance") == "high"]
        medium = [i for i in tag_items if i.get("importance") == "medium"]

        # Top headlines: high > medium > recent
        top_pool = high + medium + sorted(tag_items, key=lambda x: x.get("published_at", ""), reverse=True)
        seen: set[str] = set()
        top_headlines: list[str] = []
        for item in top_pool:
            title = (item.get("title_zh") or item.get("title", "")).strip()
            if title and title not in seen:
                seen.add(title)
                top_headlines.append(title)
            if len(top_headlines) >= 5:
                break

        sections[tag] = {
            "total": len(tag_items),
            "high_importance": len(high),
            "top_headlines": top_headlines,
            "sources": sorted(set(i.get("site_name", "") for i in tag_items if i.get("site_name"))),
        }

    total = len(items)
    high_total = sum(1 for i in items if i.get("importance") == "high")

    lines = [f"【市场概览】过去24小时共 {total} 条金融快讯，{high_total} 条标记为重要。"]
    for tag in DISPLAY_ORDER:
        if tag not in sections:
            continue
        s = sections[tag]
        label = MARKET_LABELS.get(tag, tag)
        headlines_str = "；".join(s["top_headlines"][:3])
        if headlines_str:
            lines.append(f"\n【{label}】{s['total']} 条动态，{s['high_importance']} 条重要。焦点：{headlines_str}。")
        else:
            lines.append(f"\n【{label}】{s['total']} 条动态。")

    # Polymarket prediction market section
    if poly_items:
        # Sort by volume
        poly_sorted = sorted(
            poly_items,
            key=lambda x: (x.get("meta") or {}).get("volume_24h", 0),
            reverse=True,
        )
        lines.append(f"\n【预测市场 Polymarket】{len(poly_items)} 个活跃预测事件：")
        for p in poly_sorted[:8]:
            meta = p.get("meta") or {}
            title = (p.get("title_zh") or p.get("title", "")).strip()
            outcomes = meta.get("outcomes", [])
            vol = meta.get("volume_24h", 0)
            # Top outcomes
            top = sorted(outcomes, key=lambda x: x.get("prob", 0), reverse=True)[:3]
            odds_parts = []
            for o in top:
                lbl = o.get("label_zh") or o.get("label", "")
                odds_parts.append(f"{lbl} {o.get('prob', 0):.0f}%")
            odds_str = " | ".join(odds_parts) if odds_parts else ""
            vol_str = f"${vol:,.0f}" if vol else ""
            line = f"  - {title}"
            if odds_str:
                line += f"（{odds_str}）"
            if vol_str:
                line += f" [交易量{vol_str}]"
            lines.append(line)

    return {
        "type": "rule_based",
        "text": "\n".join(lines),
        "sections": sections,
        "total_items": total,
        "high_importance_items": high_total,
    }


# ─────────────────────── LLM summary (optional) ─────────────────


def build_llm_prompt(items: list[dict]) -> str:
    """Build a prompt with top headlines grouped by market + Polymarket predictions."""
    poly_items = [i for i in items if i.get("site_id") == "polymarket"]
    news_items = [i for i in items if i.get("site_id") != "polymarket"]

    market_groups: dict[str, list[str]] = defaultdict(list)
    for item in news_items:
        title = (item.get("title_zh") or item.get("title", "")).strip()
        if not title:
            continue
        for tag in item.get("market_tags", ["general"]):
            if len(market_groups[tag]) < 10:
                imp = item.get("importance", "normal")
                prefix = "🔴 " if imp == "high" else ""
                market_groups[tag].append(f"{prefix}{title}")

    sections = []
    for tag in DISPLAY_ORDER:
        headlines = market_groups.get(tag, [])
        if not headlines:
            continue
        label = MARKET_LABELS.get(tag, tag)
        bullet_list = "\n".join(f"  - {h}" for h in headlines)
        sections.append(f"【{label}】\n{bullet_list}")

    # Polymarket section
    if poly_items:
        poly_sorted = sorted(
            poly_items,
            key=lambda x: (x.get("meta") or {}).get("volume_24h", 0),
            reverse=True,
        )
        poly_lines = []
        for p in poly_sorted[:10]:
            meta = p.get("meta") or {}
            title = (p.get("title_zh") or p.get("title", "")).strip()
            outcomes = meta.get("outcomes", [])
            vol = meta.get("volume_24h", 0)
            top = sorted(outcomes, key=lambda x: x.get("prob", 0), reverse=True)[:3]
            odds_parts = []
            for o in top:
                lbl = o.get("label_zh") or o.get("label", "")
                odds_parts.append(f"{lbl} {o.get('prob', 0):.0f}%")
            odds_str = " | ".join(odds_parts)
            poly_lines.append(f"  - {title}（{odds_str}）[24h交易量 ${vol:,.0f}]")
        sections.append(f"【预测市场 Polymarket】\n" + "\n".join(poly_lines))

    headlines_block = "\n\n".join(sections)

    return (
        "你是一位专业金融分析师。请根据以下过去24小时的金融快讯标题和Polymarket预测市场数据，"
        "生成一份简洁的中文市场速览摘要（400-600字）。\n"
        "要求：\n"
        "1. 按市场分类概述（A股、美股、港股、宏观、加密等）\n"
        "2. 突出标记为🔴的重要事件\n"
        "3. 单独用一个【预测市场信号】章节，分析Polymarket数据反映的市场预期和情绪\n"
        "4. 对每个关键预测给出简短的交易含义解读（如：Fed降息概率高→利好成长股）\n"
        "5. 语言简练专业，适合金融从业者快速阅读\n"
        "6. 不要编造不在标题中的信息\n\n"
        f"--- 快讯标题与预测数据 ---\n\n{headlines_block}"
    )


def llm_summary_anthropic(items: list[dict], api_key: str) -> str | None:
    prompt = build_llm_prompt(items)
    try:
        resp = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json={
                "model": "claude-3-5-haiku-latest",
                "max_tokens": 1024,
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["content"][0]["text"]
    except Exception as exc:
        print(f"Anthropic LLM failed: {exc}")
        return None


def llm_summary_openai(items: list[dict], api_key: str) -> str | None:
    prompt = build_llm_prompt(items)
    try:
        resp = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
            },
            timeout=30,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]
    except Exception as exc:
        print(f"OpenAI LLM failed: {exc}")
        return None


# ─────────────────────── Main ────────────────────────────────────


def main() -> int:
    parser = argparse.ArgumentParser(description="Generate market summary")
    default_data_dir = Path(__file__).resolve().parents[1] / "data"
    parser.add_argument("--data-dir", default=str(default_data_dir), help="Directory containing latest-24h.json")
    parser.add_argument("--output-dir", default=str(default_data_dir), help="Output directory")
    parser.add_argument("--no-llm", action="store_true", help="Force rule-based even if API key is set")
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load latest data
    src = data_dir / "latest-24h.json"
    if not src.exists():
        print(f"{src} not found, writing empty summary.")
        result = {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "ok": False, "error": f"{src} not found",
            "type": "rule_based", "text": "", "sections": {},
            "total_items": 0, "high_importance_items": 0,
        }
        (output_dir / "market-summary.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
        return 0

    payload = json.loads(src.read_text(encoding="utf-8"))
    items = payload.get("items_finance", payload.get("items", []))
    print(f"Loaded {len(items)} finance items from {src}")

    # Rule-based summary (always computed as fallback)
    rb = rule_based_summary(items)

    # Try LLM if available
    llm_text = None
    summary_type = "rule_based"

    if not args.no_llm:
        anthropic_key = os.environ.get("ANTHROPIC_API_KEY", "")
        openai_key = os.environ.get("OPENAI_API_KEY", "")

        if anthropic_key:
            print("Attempting Anthropic LLM summary...")
            llm_text = llm_summary_anthropic(items, anthropic_key)
        elif openai_key:
            print("Attempting OpenAI LLM summary...")
            llm_text = llm_summary_openai(items, openai_key)

    if llm_text:
        summary_type = "llm"
        text = llm_text
        print("Using LLM summary.")
    else:
        text = rb["text"]
        if not args.no_llm and (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("OPENAI_API_KEY")):
            print("LLM failed, falling back to rule-based.")
        else:
            print("Using rule-based summary.")

    result = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "type": summary_type,
        "total_items": rb["total_items"],
        "high_importance_items": rb["high_importance_items"],
        "text": text,
        "sections": rb["sections"],
        "ok": True,
        "error": None,
    }

    out_path = output_dir / "market-summary.json"
    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Wrote {out_path} — {rb['total_items']} items, type={summary_type}")
    print(f"Preview: {text[:200]}...")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
